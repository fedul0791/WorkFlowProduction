import { AppShell } from "@/components/app-shell";
import { LoginForm } from "@/components/login-form";
import type { Locale } from "@/i18n/messages";
export function LocalizedLogin({locale}:{locale:Locale}){return <AppShell locale={locale} active="auth"><LoginForm locale={locale}/></AppShell>}
