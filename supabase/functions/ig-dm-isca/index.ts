// DM automática das iscas da @otalogia (API do Instagram com login do Instagram).
// Comentário com a palavra (ex.: BRIEFING) -> resposta pública + DM perguntando "Você já me segue?" (Sim / Ainda não).
// "Sim" (ou a palavra no direct) -> confere se segue de verdade: segue = link do PDF; não segue = botão do perfil + "Pronto, segui".
// Palavras e links vêm de iscas/links.json na main (gerado pelo entregar.yml), então isca nova não pede deploy.
// Secrets: IG_TOKEN, IG_APP_SECRET, IG_VERIFY_TOKEN.
// Token permanente: IG_TOKEN = token de Usuário do Sistema (Business Manager) da Página ligada à @otalogia e IG_GRAPH=facebook.
// Sem IG_GRAPH, usa a API com login do Instagram (token de 60 dias).

const FB = Deno.env.get("IG_GRAPH") === "facebook";
const API = FB ? "https://graph.facebook.com/v23.0" : "https://graph.instagram.com/v23.0";
const LINKS = "https://raw.githubusercontent.com/otaluiz/otalogia-post/main/iscas/links.json";
const env = (k: string) => Deno.env.get(k) ?? "";

type Iscas = Record<string, { link: string; titulo: string }>;
let cache: { em: number; iscas: Iscas } | null = null;

async function iscas(): Promise<Iscas> {
  if (cache && Date.now() - cache.em < 300_000) return cache.iscas;
  const r = await fetch(LINKS);
  cache = { em: Date.now(), iscas: r.ok ? await r.json() : {} };
  return cache.iscas;
}

// primeira palavra do texto que é uma isca com link (sem acento, maiúscula)
async function palavra(texto = ""): Promise<string | null> {
  const mapa = await iscas();
  const norm = texto.normalize("NFD").replace(/\p{M}/gu, "").toUpperCase();
  return norm.split(/[^A-Z0-9]+/).find((p) => mapa[p]?.link.startsWith("http")) ?? null;
}

async function ig(caminho: string, corpo?: unknown) {
  const r = await fetch(`${API}/${caminho}`, {
    method: corpo ? "POST" : "GET",
    headers: { Authorization: `Bearer ${env("IG_TOKEN")}`, "Content-Type": "application/json" },
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  const j = await r.json();
  if (!r.ok) console.error(caminho, JSON.stringify(j));
  return j;
}

const PERFIL = "https://www.instagram.com/otalogia/";
const modelo = (texto: string, buttons: unknown[]) => ({
  attachment: { type: "template", payload: { template_type: "button", text: texto, buttons } },
});
const sim = (p: string, titulo = "Sim, já sigo ✅") => ({ type: "postback", title: titulo, payload: `ISCA:${p}` });
// pergunta se segue: "Sim" confere o follow antes de liberar; "Ainda não" manda o botão do perfil
const pergunta = (texto: string, p: string) =>
  modelo(texto, [sim(p), { type: "postback", title: "Ainda não", payload: `SEGUIR:${p}` }]);
const seguir = (texto: string, p: string) =>
  modelo(texto, [{ type: "web_url", title: "Seguir @otalogia", url: PERFIL }, sim(p, "Pronto, segui ✅")]);

async function entregar(eu: string, quem: string, p: string) {
  const perfil = await ig(`${quem}?fields=username,is_user_follow_business`);
  const isca = (await iscas())[p];
  if (perfil.is_user_follow_business) {
    await ig(`${FB ? "me" : eu}/messages`, { recipient: { id: quem }, message: { text: `Aqui está: ${isca.titulo} 👇\n${isca.link}` } });
  } else {
    await ig(`${FB ? "me" : eu}/messages`, {
      recipient: { id: quem },
      message: seguir("Ainda não achei seu follow 👀 Toca em Seguir, segue a @otalogia e depois toca em Pronto. O material chega na hora.", p),
    });
  }
}

async function assinaturaOk(req: Request, corpo: string) {
  const chave = await crypto.subtle.importKey("raw", new TextEncoder().encode(env("IG_APP_SECRET")), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", chave, new TextEncoder().encode(corpo)));
  const hex = "sha256=" + [...sig].map((b) => b.toString(16).padStart(2, "0")).join("");
  return hex === req.headers.get("x-hub-signature-256");
}

Deno.serve(async (req) => {
  const url = new URL(req.url);
  if (req.method === "GET") {
    const ok = url.searchParams.get("hub.mode") === "subscribe" && url.searchParams.get("hub.verify_token") === env("IG_VERIFY_TOKEN");
    return new Response(ok ? url.searchParams.get("hub.challenge") : "forbidden", { status: ok ? 200 : 403 });
  }
  const corpo = await req.text();
  if (!env("IG_APP_SECRET") || !(await assinaturaOk(req, corpo))) return new Response("assinatura inválida", { status: 401 });

  for (const entrada of JSON.parse(corpo).entry ?? []) {
    const eu = String(entrada.id);
    for (const c of entrada.changes ?? []) {
      const v = c.value ?? {};
      if (c.field !== "comments" || v.from?.id === eu) continue;
      const p = await palavra(v.text);
      if (!p) continue;
      await ig(`${v.id}/replies`, { message: "Te mandei no direct 📩" });
      await ig(`${FB ? "me" : eu}/messages`, {
        recipient: { comment_id: v.id },
        message: pergunta(`Oi! Seu material ${p} está separado 📎 Ele é liberado só pra quem segue a @otalogia. Você já me segue?`, p),
      });
    }
    for (const m of entrada.messaging ?? []) {
      const quem = m.sender?.id;
      if (!quem || quem === eu || m.message?.is_echo) continue;
      const [acao, chave] = String(m.postback?.payload ?? "").split(":");
      if (acao === "SEGUIR" && (await iscas())[chave]) {
        await ig(`${FB ? "me" : eu}/messages`, { recipient: { id: quem }, message: seguir("Bora! Toca em Seguir e depois em Pronto, segui que eu libero o material 👇", chave) });
        continue;
      }
      const p = acao === "ISCA" ? chave : await palavra(m.message?.text);
      if (p && (await iscas())[p]) await entregar(eu, quem, p);
    }
  }
  return new Response("ok");
});
