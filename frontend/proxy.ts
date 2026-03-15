import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(req: NextRequest) {
  const host = req.headers.get("host") || "";
  const url = req.nextUrl.clone();

  const hostname = host.split(":")[0];

  if (
    hostname === "localhost" ||
    hostname.startsWith("192.168") ||
    hostname.startsWith("127.0.0.1")
  ) {
    return NextResponse.next();
  }

  let subdomain = "";

  if (hostname.endsWith(".localhost")) {
    subdomain = hostname.replace(".localhost", "");
  } else if (hostname.split(".").length > 2) {
    subdomain = hostname.split(".")[0];
  }

  if (subdomain && subdomain !== "www") {
    url.pathname = `/${subdomain}${url.pathname}`;
    return NextResponse.rewrite(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
