// DM automática das iscas da @otalogia (API do Instagram com login do Instagram).
// Comentário com a palavra (ex.: BRIEFING) -> resposta pública + DM com botão "Já te sigo".
// Clicou no botão (ou mandou a palavra no direct) -> confere se segue: segue = manda o link do PDF; não segue = pede o follow.
// Palavras e links vêm de iscas/links.json na main (gerado pelo entregar.yml), então isca nova não pede deploy.
// Secrets: IG_TOKEN, IG_APP_SECRET, IG_VERIFY_TOKEN.

const API = "https://graph.instagram.com/v23.0";
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

const botao = (texto: string, p: string) => ({
  attachment: {
    type: "template",
    payload: { template_type: "button", text: texto, buttons: [{ type: "postback", title: "Já te sigo ✅", payload: `ISCA:${p}` }] },
  },
});

async function entregar(eu: string, quem: string, p: string) {
  const perfil = await ig(`${quem}?fields=username,is_user_follow_business`);
  const isca = (await iscas())[p];
  if (perfil.is_user_follow_business) {
    await ig(`${eu}/messages`, { recipient: { id: quem }, message: { text: `Aqui está: ${isca.titulo} 👇\n${isca.link}` } });
  } else {
    await ig(`${eu}/messages`, {
      recipient: { id: quem },
      message: botao("Ainda não achei seu follow 👀 Me segue na @otalogia e toca no botão de novo que o material chega na hora.", p),
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
      await ig(`${eu}/messages`, {
        recipient: { comment_id: v.id },
        message: botao(`Oi! Seu material ${p} está separado. O envio é só pra quem me segue: me segue na @otalogia e toca no botão 👇`, p),
      });
    }
    for (const m of entrada.messaging ?? []) {
      const quem = m.sender?.id;
      if (!quem || quem === eu || m.message?.is_echo) continue;
      const p = m.postback?.payload?.startsWith("ISCA:") ? m.postback.payload.slice(5) : await palavra(m.message?.text);
      if (p && (await iscas())[p]) await entregar(eu, quem, p);
    }
  }
  return new Response("ok");
});
