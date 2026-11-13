import { makePublicReplyRequest, PUBLIC_REPLIES } from "./public_comment_reply.ts";
function expect(condition: boolean, reason: string) {
  if (!condition) throw new Error(reason);
}
Deno.test("três mensagens diferentes aprovadas", () => {
  expect(PUBLIC_REPLIES.length === 3, "three phrases");
  expect(new Set(PUBLIC_REPLIES).size === 3, "unique phrases");
});
Deno.test("chamada pública usa /{ig-comment-id}/replies, sem DM", () => {
  const request = makePublicReplyRequest({
    host:"https://graph.instagram.com",version:"v27.0",
    commentId:"17870913679156914",token:"test-only",message:PUBLIC_REPLIES[0]
  });
  expect(request.url === "https://graph.instagram.com/v27.0/17870913679156914/replies", "correct endpoint");
  expect(request.init.method === "POST", "post");
  expect(JSON.parse(request.init.body as string).message === PUBLIC_REPLIES[0], "message");
  expect(!request.url.includes("/messages"), "not DM");
});
Deno.test("aceita host Facebook Graph com permissão de comentários", () => {
  const request = makePublicReplyRequest({
    host:"https://graph.facebook.com",version:"v27.0",
    commentId:"17870913679156914",token:"test-only",message:PUBLIC_REPLIES[1]
  });
  expect(request.url.includes("graph.facebook.com"), "host");
});
Deno.test("bloqueia ids inválidos, mensagens diferentes e host desconhecido", () => {
  const base={host:"https://graph.instagram.com",version:"v27.0",
    commentId:"17870913679156914",token:"test-only",message:PUBLIC_REPLIES[2] as string};
  for (const overrides of [{commentId:"../",},{message:"Já recebeu o PDF!"},{host:"https://attacker.example"}]) {
    let rejected=false;
    try{makePublicReplyRequest({...base,...overrides})}catch{rejected=true}
    expect(rejected,"should reject");
  }
});
