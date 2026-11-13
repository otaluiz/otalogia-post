import { verifyFollow, canDeliverLinks } from "./follower_gate.ts";
// API_AUTO (Meta app 2124703308119813): Instagram DM e private replies.
// Duas contas: @idea_lab7 e @otalogia; sem usar credenciais do app api-CRM.
// Links só são enviados após verificação is_user_follow_business=true.
// Exige API_AUTO_APP_SECRET e tokens/IDs profissionais configurados no Supabase.
const V = "v27.0";
const env = (k: string) => (Deno.env.get(k) || "").trim();
type Material = { link?: string; links?: Array<string | { link: string; titulo?: string }>; titulo: string; categoria?: string; carousel_id?: string };
type Registry = Record<string, Material>;
type Account = { name: "otalogia" | "aidealab"; id: string; token: string; facebook: boolean };
// Os links NÃO ficam mais em arquivos publicamente acessíveis do GitHub.
const cache: Record<string, { until: number; data: Registry } | undefined> = {};

function account(id: string): Account | null {
  // Somente credenciais emitidas para o app Meta API_AUTO (2124703308119813).
  // O app api-CRM não é utilizado nesta integração.
  const aiId = env("API_AUTO_IG_ID_AIDEALAB");
  const otId = env("API_AUTO_IG_ID_OTALOGIA");
  if (!aiId || !otId || aiId === otId) {
    console.error("Instagram IDs do API_AUTO ausentes ou iguais: sem entrega");
    return null;
  }
  if (id === aiId && env("API_AUTO_IG_TOKEN_AIDEALAB")) {
    return { name: "aidealab", id: aiId, token: env("API_AUTO_IG_TOKEN_AIDEALAB"),
             facebook: env("API_AUTO_IG_GRAPH_AIDEALAB") === "facebook" };
  }
  if (id === otId && env("API_AUTO_IG_TOKEN_OTALOGIA")) {
    return { name: "otalogia", id: otId, token: env("API_AUTO_IG_TOKEN_OTALOGIA"),
             facebook: env("API_AUTO_IG_GRAPH_OTALOGIA") === "facebook" };
  }
  return null;
}

async function registry(name: string): Promise<Registry> {
  const current = cache[name];
  if (current && current.until > Date.now()) return current.data;
  const serviceUrl = env("SUPABASE_URL"), serviceKey = env("SUPABASE_SERVICE_ROLE_KEY");
  if (!serviceUrl || !serviceKey) throw new Error("Catálogo privado indisponível: secret não configurado");
  if (name !== "aidealab" && name !== "otalogia") throw new Error("Perfil não autorizado");
  const params = new URLSearchParams({
    profile: "eq." + name,
    enabled: "eq.true",
    select: "keyword,title,category,documents"
  });
  const response = await fetch(serviceUrl + "/rest/v1/ig_dm_catalog?" + params.toString(), {
    headers: { apikey: serviceKey, Authorization: "Bearer " + serviceKey }
  });
  if (!response.ok) {
    console.error("Falha no catálogo privado", name, response.status);
    throw new Error("Não foi possível consultar catálogo aprovado");
  }
  const rows = await response.json() as Array<{keyword:string; title:string; category:string; documents:unknown[]}>;
  const data: Registry = {};
  for (const row of rows) {
    if (!/^[A-Z0-9_]{3,30}$/.test(row.keyword)) continue;
    if (!Array.isArray(row.documents)) continue;
    data[row.keyword] = { categoria: row.category, titulo: row.title,
                          links: row.documents as Array<string | {link:string; titulo?:string}> };
  }
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

// Meta User Profile API: somente depois de o usuário enviar mensagem por iniciativa própria
// existe consentimento para consultar o perfil. Comentário isolado NÃO permite essa consulta.
async function followerStatus(a: Account, scopedUserId: string) {
  return verifyFollow({ scopedId: scopedUserId, token: a.token, facebook: a.facebook, version: V });
}

function promptToReply(a: Account, keyword: string): string {
  const profile = a.name === "otalogia" ? "@otalogia" : "@idea_lab7";
  return "Recebi seu comentário sobre " + keyword + "! 📩\n" +
         "Para proteger o material exclusivo de quem segue " + profile +
         ", responda esta mensagem com " + keyword + ". " +
         "Vou confirmar que você segue o perfil antes de enviar o PDF.";
}

function documentText(item: Material): string {
  const docs = documents(item);
  const title = item.categoria ? "Materiais da categoria " + item.categoria : "Aqui está seu material";
  return title + ":\n" +
         docs.map((d, i) => "\n" + (i + 1) + ". " + d.titulo + "\n" + d.link).join("\n") +
         "\n\nSe tiver dúvidas, pode responder esta mensagem.";
}

async function sendText(a: Account, recipient: Record<string, string>, text: string, eventId: string) {
  if (!eventId || !(await claim(a, eventId))) return;
  const host = a.facebook ? "https://graph.facebook.com" : "https://graph.instagram.com";
  const endpoint = host + "/" + V + "/" + (a.facebook ? "me" : a.id) + "/messages";
  try {
    const response = await fetch(endpoint, {
      method: "POST", headers: { Authorization: "Bearer " + a.token, "Content-Type": "application/json" },
      body: JSON.stringify({ recipient, message: { text } }),
    });
    if (!response.ok) {
      console.error("Meta recusou envio", a.name, response.status, (await response.text()).slice(0, 200));
      throw new Error("Envio negado pela Meta: " + response.status);
    }
  } catch (error) { await release(a, eventId); throw error; }
}

async function deliverIfFollower(a: Account, senderId: string, item: Material, word: string, mid: string) {
  // Não confiar em texto "já sigo", botão ou cache: consulta real em CADA tentativa.
  const status = await followerStatus(a, senderId);
  const recipient = { id: senderId };
  if (!canDeliverLinks(status)) {
    const profile = a.name === "otalogia" ? "@otalogia" : "@idea_lab7";
    const message = status === "not_following"
      ? "O material é exclusivo para seguidores. Siga " + profile +
        " e envie " + word + " novamente aqui na DM para eu confirmar."
      : "Ainda não consegui confirmar seu follow em " + profile +
        ". Por segurança não envio links sem confirmação. Tente novamente em alguns minutos.";
    await sendText(a, recipient, message, "notice:" + mid);
    return;
  }
  const docs = documents(item);
  if (!docs.length) return;
  // Único caminho pelo qual o webhook entrega URLs de arquivos.
  await sendText(a, recipient, documentText(item), "dm:" + mid);
}

Deno.serve(async (req: Request) => {
  if (req.method === "GET") {
    const url = new URL(req.url);
    const token = url.searchParams.get("hub.verify_token") || "";
    const challenge = url.searchParams.get("hub.challenge") || "";
    if (url.searchParams.get("hub.mode") !== "subscribe" || !token) {
      return new Response("forbidden", { status: 403 });
    }
    // A Meta recebe o segredo de verificação; apenas seu hash é armazenado no código.
    const tokenHash = Array.from(new Uint8Array(
      await crypto.subtle.digest("SHA-256", new TextEncoder().encode(token)),
      b => b.toString(16).padStart(2, "0")).join("");
    if (tokenHash !== "421cdb2aa087e00b2c5358658583dcc4d7f61e72975ee3b888fffe4850b1462f") {
      return new Response("forbidden", { status: 403 });
    }
    return new Response(challenge, { status: 200 });
  }
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });
  const body = await req.text();
  if (body.length > 1_000_000) return new Response("large body", { status: 413 });
  const signature = req.headers.get("x-hub-signature-256") || "";
  // Somente a assinatura HMAC emitida pelo APP SECRET do API_AUTO autoriza o evento.
  const ok = await signatureOk(body, signature, env("API_AUTO_APP_SECRET"));
  if (!ok) return new Response("bad signature", { status: 401 });
  let data: { entry?: Record<string, any>[] };
  try { data = JSON.parse(body); } catch { return new Response("invalid json", { status: 400 }); }
  try {
    for (const entry of data.entry || []) {
      const id = String(entry.id || "");
      const a = account(id);
      if (!a) { console.warn("Conta não configurada:", id); continue; }
      const links = await registry(a.name);
      for (const change of entry.changes || []) {
        if (change.field !== "comments") continue;
        const c = change.value || {};
        const word = keyword(String(c.text || ""), links);
        if (!c.id || !word || String(c.from?.id || "") === id) continue;
        // Tentativa de follow real: a Meta só libera User Profile quando o usuário já
        // iniciou conversa anteriormente. Sem consentimento, devolve UNKNOWN => sem link.
        const commenter = String(c.from?.id || "");
        const commentFollow = commenter ? await followerStatus(a, commenter) : "unknown";
        const privateReply = canDeliverLinks(commentFollow)
          ? documentText(links[word])
          : promptToReply(a, word);
        // Meta permite apenas uma private reply por comentário.
        await sendText(a, { comment_id: String(c.id) }, privateReply, "comment:" + c.id);
      }
      for (const msg of entry.messaging || []) {
        const sender = String(msg.sender?.id || "");
        if (!sender || sender === id || msg.message?.is_echo || msg.is_self) continue;
        const word = keyword(String(msg.message?.text || ""), links);
        const messageId = String(msg.message?.mid || "");
        if (word && messageId) await deliverIfFollower(a, sender, links[word], word, messageId);
      }
    }
  } catch (err) {
    console.error("Falha webhook Instagram:", String(err));
    return new Response("retry later", { status: 503 });
  }
  return new Response("ok");
});
