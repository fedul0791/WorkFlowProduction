import { AppShell } from "@/components/app-shell";
import { EnterpriseStructure } from "@/components/enterprise-structure";
import { EnterpriseBuilder } from "@/components/enterprise-builder";
import type { Locale } from "@/i18n/messages";

export function EnterprisePage({ locale }: { locale: Locale }) {
  return <AppShell locale={locale} active="enterprise"><EnterpriseBuilder locale={locale} /></AppShell>;
}
