import Link from "next/link";
import type { Locale } from "@/i18n/messages";
import { messages } from "@/i18n/messages";
import { AppShell } from "@/components/app-shell";

export function AdministrationHome({ locale }: { locale: Locale }) {
  const t = messages[locale];
  return <AppShell locale={locale} active="administration"><main className="workforce-page"><header className="enterprise-heading"><div><span className="eyebrow">{t.administration}</span><h1>{t.administration}</h1><p>{t.administrationDescription}</p></div></header><div className="admin-link-grid"><Link className="admin-link-card" href={`/${locale}/benutzerverwaltung`}><span className="admin-link-icon" aria-hidden="true">◎</span><strong>{t.manageAccounts}</strong><span>{t.users}</span></Link><Link className="admin-link-card" href={`/${locale}/rollen`}><span className="admin-link-icon" aria-hidden="true">⌘</span><strong>{t.manageRoles}</strong><span>{t.permissions}</span></Link></div></main></AppShell>;
}
