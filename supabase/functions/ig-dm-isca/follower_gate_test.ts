import { canDeliverLinks, verifyFollow } from "./follower_gate.ts";
function equal(actual: unknown, expected: unknown, message: string) {
  if (actual !== expected) throw new Error(message + ": " + String(actual));
}
const response = (data: unknown, status = 200) =>
  async (_url: string, _init?: RequestInit) => new Response(JSON.stringify(data), { status });
Deno.test("Libera apenas perfil confirmado como seguidor", async () => {
  const state = await verifyFollow({ scopedId: "777", token: "fake", facebook: false,
                                   version: "v27.0", fetchImpl: response({is_user_follow_business:true})});
  equal(state, "following", "state"); equal(canDeliverLinks(state), true, "allow");
});
Deno.test("Recusa não seguidores", async () => {
  const state = await verifyFollow({ scopedId: "777", token: "fake", facebook: false,
                                   version: "v27.0", fetchImpl: response({is_user_follow_business:false})});
  equal(state, "not_following", "state"); equal(canDeliverLinks(state), false, "block");
});
Deno.test("Recusa perfil sem campo, mesmo com status 200", async () => {
  const state = await verifyFollow({ scopedId: "777", token: "fake", facebook: false,
                                   version: "v27.0", fetchImpl: response({username:"teste"})});
  equal(state, "unknown", "state"); equal(canDeliverLinks(state), false, "block");
});
Deno.test("Recusa falha de permissão Meta", async () => {
  const state = await verifyFollow({ scopedId: "777", token: "fake", facebook: false,
                                   version: "v27.0", fetchImpl: response({error:"permission"},403)});
  equal(state, "unknown", "state"); equal(canDeliverLinks(state), false, "block");
});
Deno.test("Recusa falha de rede", async () => {
  const state = await verifyFollow({ scopedId: "777", token: "fake", facebook: false,
    version: "v27.0", fetchImpl: async () => { throw new Error("offline"); }});
  equal(state, "unknown", "state"); equal(canDeliverLinks(state), false, "block");
});
Deno.test("Recusa token ou ID ausente", async () => {
  const params = { scopedId:"", token:"", facebook:true, version:"v27.0", fetchImpl: response({is_user_follow_business:true}) };
  const state = await verifyFollow(params);
  equal(state,"unknown","state"); equal(canDeliverLinks(state),false,"block");
});
Deno.test("Chama User Profile API com token e ID correto", async () => {
  const fetchImpl = async (url: string, init?: RequestInit) => {
    equal(url, "https://graph.instagram.com/v27.0/777?fields=is_user_follow_business", "url");
    const auth = new Headers(init?.headers).get("Authorization");
    equal(auth, "Bearer fake", "auth");
    return new Response(JSON.stringify({is_user_follow_business:true}),{status:200});
  };
  const state=await verifyFollow({scopedId:"777",token:"fake",facebook:false,version:"v27.0",fetchImpl});
  equal(canDeliverLinks(state),true,"verified");
});
