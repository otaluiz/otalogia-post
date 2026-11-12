/** Gate central de seguidores (Meta User Profile API).
 * Proibido liberar links quando status for false ou indefinido.
 * Chamar SOMENTE após o usuário enviar DM, porque comentário isolado não dá
 * consentimento para consultar a User Profile API.
 */
export type FollowStatus = "following" | "not_following" | "unknown";
export type FetchFn = (input: string, init?: RequestInit) => Promise<Response>;

export async function verifyFollow(params: {
  scopedId: string;
  token: string;
  facebook: boolean;
  version: string;
  fetchImpl?: FetchFn;
}): Promise<FollowStatus> {
  if (!params.scopedId || !params.token) return "unknown";
  const host = params.facebook ? "https://graph.facebook.com" : "https://graph.instagram.com";
  const url = host + "/" + params.version + "/" + encodeURIComponent(params.scopedId) +
              "?fields=is_user_follow_business";
  try {
    const response = await (params.fetchImpl || fetch)(url, {
      headers: { Authorization: "Bearer " + params.token },
      signal: AbortSignal.timeout(9000),
    });
    if (!response.ok) return "unknown";
    const profile = await response.json() as { is_user_follow_business?: unknown };
    if (profile?.is_user_follow_business === true) return "following";
    if (profile?.is_user_follow_business === false) return "not_following";
  } catch {
    return "unknown";
  }
  return "unknown";
}
export const canDeliverLinks = (status: FollowStatus): boolean => status === "following";
