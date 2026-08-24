/**
 * Single-hop canonical host/protocol redirect for Cloudflare Pages.
 * Only applies to the production hostnames. Preview *.pages.dev URLs are left alone.
 */
const APEX = "ascentiant.health";
const CANONICAL_HOSTS = new Set([APEX, `www.${APEX}`]);

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const host = url.hostname.toLowerCase();

  if (!CANONICAL_HOSTS.has(host)) {
    return context.next();
  }

  const needsHttps = url.protocol !== "https:";
  const needsApex = host === `www.${APEX}`;

  if (needsHttps || needsApex) {
    url.protocol = "https:";
    url.hostname = APEX;
    url.port = "";
    return Response.redirect(url.href, 301);
  }

  return context.next();
}
