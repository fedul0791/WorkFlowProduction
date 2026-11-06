import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export const metadata: Metadata = {
  title: "WorkFlow Production",
  description: "Production management platform foundation",
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const requestedLocale = (await headers()).get("x-workflow-locale");
  const locale = requestedLocale === "ru" || requestedLocale === "en" ? requestedLocale : "de";

  return (
    <html lang={locale}>
      <body>{children}</body>
    </html>
  );
}
