// Meta webhook: @otalogia + @idea_lab7. Recebe comentários e DMs iniciados pelos usuários.
// Envia um único link público para o PDF, sem exigir follow. Verificação HMAC e idempotência.
// Secrets legados @otalogia: IG_TOKEN, IG_APP_SECRET, IG_VERIFY_TOKEN, IG_GRAPH.
// Secrets extras @idea_lab7: IG_ID_AIDEALAB, IG_TOKEN_AIDEALAB,
// IG_APP_SECRET_AIDEALAB (somente para outro app), IG_VERIFY_TOKEN_AIDEALAB, IG_GRAPH_AIDEALAB.
// Definir IG_ID_OTALOGIA quando ativar os dois perfis no mesmo endpoint.
const V = "v27.0";
const env = (k: string) => (Deno.env.get(k) || "").trim();
type Material = { link?: string; links?: Array<string | { link: string; titulo?: string }>; titulo: string; categoria?: string; carousel_id?: string };
type Registry = Record<string, Material>;
type Account = { name: "otalogia" | "aidealab"; id: string; token: string; facebook: boolean };
const source: Record<string, string> = {
  otalogia: "https://raw.githubusercontent.com/otaluiz/otalogia-post/main/iscas/links.json",
  aidealab: "https://raw.githubusercontent.com/otaluiz/aidealab-post/main/iscas/links.json",
};
const cache: Record<string, { until: number; data: Registry } | undefined> = {};

function account(id: string): Account | null {
  const aiId = env("IG_ID_AIDEALAB") || env("IG_PAGE_ID_AIDEALAB");
  const otId = env("IG_ID_OTALOGIA") || env("IG_PAGE_ID_OTALOGIA");
  if (aiId && aiId === id && env("IG_TOKEN_AIDEALAB")) {
    return { name: "aidealab", id: env("IG_ID_AIDEALAB") || id,
             token: env("IG_TOKEN_AIDEALAB"), facebook: env("IG_GRAPH_AIDEALAB") === "facebook" };
  }
  if (otId && otId === id && env("IG_TOKEN")) {
    return { name: "otalogia", id: env("IG_ID_OTALOGIA") || id,
             token: env("IG_TOKEN"), facebook: env("IG_GRAPH") === "facebook" };
  }
  // Compatibilidade com a versão anterior até instalar token e ID da segunda conta.
  if (!otId && !env("IG_TOKEN_AIDEALAB") && env("IG_TOKEN")) {
    return { name: "otalogia", id, token: env("IG_TOKEN"), facebook: env("IG_GRAPH") === "facebook" };
  }
  return null;
}

async function registry(name: string): Promise<Registry> {
  const current = cache[name];
  if (current && current.until > Date.now()) return current.data;
  const response = await fetch(source[name], { headers: { accept: "application/json" } });
  if (name === "aidealab" && response.status === 404) return {};
  if (!response.ok) throw new Error("Falha no catálogo de PDFs: " + response.status);
  const data = await response.json() as Registry;
  if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("Catálogo inválido");
  cache[name] = { until: Date.now() + 300_000, data };
  return data;
}
function documents(item?: Material): Array<{ link: string; titulo: string }> {
  if (!item) return [];
  const received = Array.isArray(item.links) && item.links.length ? item.links : (item.link ? [item.link] : []);
  const urls = new Set<string>();
  const docs: Array<{ link: string; titulo: string }> = [];
  for (const raw of received) {
    const url = typeof raw === "string" ? raw : raw?.link;
    if (typeof url !== "string" || !/^https:\/\/drive\.google\.com\/file\/d\/[A-Za-z0-9_-]+\/view/.test(url)) continue;
    if (urls.has(url)) continue;
    urls.add(url);
    docs.push({ link: url, titulo: typeof raw === "string" ? item.titulo : raw.titulo || item.titulo });
  }
  // A Private Replies API permite uma única mensagem por comentário.
  // Limite editorial por categoria: no máximo 5 PDFs com título/URL.
  return docs.slice(0, 5);
}
function keyword(text: string, links: Registry): string | null {
  const parts = text.normalize("NFD").replace(/\p{M}/gu, "").toUpperCase().split(/[^A-Z0-9_]+/);
  return parts.find((p) => documents(links[p]).length > 0) || null;
}

async function signatureOk(body: string, provided: string, secret: string): Promise<boolean> {
  if (!secret || !provided.startsWith("sha256=")) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret),
                                            { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const bytes = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body)));
  const expected = "sha256=" + Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  if (expected.length !== provided.length) return false;
  let difference = 0;
  for (let i = 0; i < expected.length; i++)
    difference |= expected.charCodeAt(i) ^ provided.charCodeAt(i);
  return difference === 0;
}

async function claim(a: Account, eventId: string): Promise<boolean> {
  const url = env("SUPABASE_URL"), key = env("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) { console.warn("Idempotência desativada: configure service_role"); return true; }
  const response = await fetch(url + "/rest/v1/ig_dm_events?on_conflict=perfil,event_id", {
    method: "POST",
    headers: { apikey: key, Authorization: "Bearer " + key, "Content-Type": "application/json",
               Prefer: "resolution=ignore-duplicates,return=representation" },
    body: JSON.stringify({ perfil: a.name, event_id: eventId }),
  });
  if (!response.ok) throw new Error("Idempotência falhou " + response.status);
  return (await response.json() as unknown[]).length > 0;
}
async function release(a: Account, eventId: string) {
  const url = env("SUPABASE_URL"), key = env("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) return;
  const args = new URLSearchParams({ perfil: "eq." + a.name, event_id: "eq." + eventId });
  const response = await fetch(url + "/rest/v1/ig_dm_events?" + args.toString(), {
    method: "DELETE", headers: { apikey: key, Authorization: "Bearer " + key },
  });
  if (!response.ok) console.error("Falha ao remover registro após erro:", response.status);
}

async function send(a: Account, recipient: Record<string, string>, item: Material, eventId: string) {
  if (!(await claim(a, eventId))) return;
  const host = a.facebook ? "https://graph.facebook.com" : "https://graph.instagram.com";
  const endpoint = host + "/" + V + "/" + (a.facebook ? "me" : a.id) + "/messages";
  const docs = documents(item);
  if (!docs.length) throw new Error("Categoria sem PDFs aprovados: envio bloqueado");
  const title = item.categoria ? "Materiais da categoria " + item.categoria : "Aqui está seu material";
  const text = title + ":\\n" +
               docs.map((d, i) => "\\n" + (i + 1) + ". " + d.titulo + "\\n" + d.link).join("\\n") +
               "\\n\\nSe tiver dúvidas, pode responder esta mensagem.";
  try {
    const response = await fetch(endpoint, {
      method: "POST", headers: { Authorization: "Bearer " + a.token, "Content-Type": "application/json" },
      body: JSON.stringify({ recipient, message: { text } }),
    });
    if (!response.ok) {
      console.error("Meta recusou envio", a.name, response.status, (await response.text()).slice(0, 350));
      throw new Error("Envio negado pela Meta: " + response.status);
    }
  } catch (error) { await release(a, eventId); throw error; }
}

Deno.serve(async (req: Request) => {
  if (req.method === "GET") {
    const u = new URL(req.url);
    const token = u.searchParams.get("hub.verify_token");
    const known = [env("IG_VERIFY_TOKEN"), env("IG_VERIFY_TOKEN_AIDEALAB")].filter(Boolean);
    const ok = u.searchParams.get("hub.mode") === "subscribe" && !!token && known.includes(token);
    return new Response(ok ? u.searchParams.get("hub.challenge") || "" : "forbidden",
                        { status: ok ? 200 : 403 });
  }
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });
  const body = await req.text();
  if (body.length > 1_000_000) return new Response("large body", { status: 413 });
  const signature = req.headers.get("x-hub-signature-256") || "";
  const sigOt = await signatureOk(body, signature, env("IG_APP_SECRET"));
  const sigAi = await signatureOk(body, signature, env("IG_APP_SECRET_AIDEALAB"));
  if (!sigOt && !sigAi) return new Response("bad signature", { status: 401 });
  let data: { entry?: Record<string, any>[] };
  try { data = JSON.parse(body); } catch { return new Response("invalid json", { status: 400 }); }
  try {
    for (const entry of data.entry || []) {
      const id = String(entry.id || "");
      const a = account(id);
      if (!a) { console.warn("Conta não configurada:", id); continue; }
      if (env("IG_APP_SECRET_AIDEALAB") && env("IG_APP_SECRET") &&
          env("IG_APP_SECRET_AIDEALAB") !== env("IG_APP_SECRET") &&
          ((a.name === "aidealab" && !sigAi) || (a.name === "otalogia" && !sigOt))) {
        return new Response("wrong account signature", { status: 401 });
      }
      const links = await registry(a.name);
      for (const change of entry.changes || []) {
        if (change.field !== "comments") continue;
        const c = change.value || {};
        const word = keyword(String(c.text || ""), links);
        if (!c.id || !word || String(c.from?.id || "") === id) continue;
        // Private reply: uma mensagem, somente texto/link, em até 7 dias do comentário.
        await send(a, { comment_id: String(c.id) }, links[word], "comment:" + c.id);
      }
      for (const msg of entry.messaging || []) {
        const sender = String(msg.sender?.id || "");
        if (!sender || sender === id || msg.message?.is_echo || msg.is_self) continue;
        const word = keyword(String(msg.message?.text || ""), links);
        const messageId = String(msg.message?.mid || "");
        if (word && messageId) await send(a, { id: sender }, links[word], "dm:" + messageId);
      }
    }
  } catch (err) {
    console.error("Falha webhook Instagram:", String(err));
    return new Response("retry later", { status: 503 });
  }
  return new Response("ok");
});
