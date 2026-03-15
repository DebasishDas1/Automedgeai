import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function proxy(req: NextRequest) {
  const host = req.headers.get("host") || ""
  const url = req.nextUrl.clone()

  const hostname = host.split(":")[0]

  let subdomain = ""

  // Local dev (demo-hvac.localhost)
  if (hostname.endsWith(".localhost")) {
    subdomain = hostname.replace(".localhost", "")
  }

  // Production (demo-hvac.automedge.com)
  else if (hostname.split(".").length > 2) {
    subdomain = hostname.split(".")[0]
  }

  // Ignore main domains
  if (
    hostname === "localhost" ||
    hostname.startsWith("127.") ||
    hostname.startsWith("192.168") ||
    subdomain === "" ||
    subdomain === "www"
  ) {
    return NextResponse.next()
  }

  // Prevent infinite rewrite
  if (url.pathname.startsWith(`/${subdomain}`)) {
    return NextResponse.next()
  }

  url.pathname = `/${subdomain}${url.pathname}`

  return NextResponse.rewrite(url)
}

export const config = {
  matcher: [
    "/((?!_next|favicon.ico|api|robots.txt|sitemap.xml|.*\\..*).*)",
  ],
}
