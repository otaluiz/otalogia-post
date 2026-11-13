/** Monta resposta pública em um comentário Instagram (nunca em uma DM).
 * Meta: POST /{IG_COMMENT_ID}/replies, instagram_business_manage_comments.
 */
export const PUBLIC_REPLIES = [
  "Confere lá na sua DM!",
  "Opa, tá na sua DM!",
  "Dá uma olhada na sua DM!",
] as const;

export function makePublicReplyRequest(args: {
  host: string; version: string; commentId: string; token: string; message: string;
}): { url: string; init: RequestInit } {
  if (!/^\d{5,}$/.test(args.commentId)) throw new Error("Invalid IG comment id");
  if (!/^v\d+\.\d+$/.test(args.version)) throw new Error("Invalid Graph API version");
  if (!["https://graph.instagram.com", "https://graph.facebook.com"].includes(args.host))
    throw new Error("Invalid API host");
  if (!args.token || !PUBLIC_REPLIES.includes(args.message as typeof PUBLIC_REPLIES[number]))
    throw new Error("Invalid reply parameters");
  return {
    url: args.host + "/" + args.version + "/" + args.commentId + "/replies",
    init: {
      method: "POST",
      headers: { "Authorization": "Bearer " + args.token, "Content-Type": "application/json" },
      body: JSON.stringify({ message: args.message }),
    },
  };
}
