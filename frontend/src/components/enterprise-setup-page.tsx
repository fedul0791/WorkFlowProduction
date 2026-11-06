import type { Locale } from "@/i18n/messages";
import { AppShell } from "@/components/app-shell";
import { EnterpriseSetupForm } from "@/components/enterprise-setup-form";
export function EnterpriseSetupPage({locale}:{locale:Locale}) { return <AppShell locale={locale} active="enterprise"><EnterpriseSetupForm locale={locale}/></AppShell>; }
