import { type NextRequest, NextResponse } from "next/server";

const supportedLocales = new Set(["de", "ru", "en"]);

export function proxy(request: NextRequest) {
  const locale = request.nextUrl.pathname.split("/")[1];
  if (!supportedLocales.has(locale)) {
    return NextResponse.next();
  }

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-workflow-locale", locale);

  return NextResponse.next({
    request: { headers: requestHeaders },
  });
}

export const config = {
  matcher: ["/de", "/de/:path*", "/ru", "/ru/:path*", "/en", "/en/:path*"],
};
