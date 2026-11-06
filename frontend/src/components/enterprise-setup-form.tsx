"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { FormEvent } from "react";
import type { Locale } from "@/i18n/messages";
import { api } from "@/lib/api";
import { loginPath } from "@/lib/routes";

const text: Record<Locale, Record<string, string>> = {
  de: { title:"Unternehmen einrichten", intro:"Erstellen Sie Ihr Unternehmen und das erste Administratorkonto. Anschließend bauen Sie Standorte, Abteilungen, Arbeitsplätze, Equipment, Positionen und Aufgaben im Betrieb-Bereich auf.", company:"Unternehmensname", email:"Administrator-E-Mail", password:"Passwort (mindestens 12 Zeichen)", submit:"Unternehmen erstellen", done:"Das Unternehmen und das Administratorkonto sind bereits angelegt. Melden Sie sich mit diesem Konto an oder öffnen Sie den Betrieb, wenn Sie bereits angemeldet sind.", login:"Zur Anmeldung", open:"Betrieb öffnen", error:"Einrichtung konnte nicht abgeschlossen werden." },
  ru: { title:"Создание предприятия", intro:"Создайте предприятие и первую учётную запись администратора. Затем в разделе «Предприятие» настройте площадки, подразделения, рабочие места, оборудование, должности и обязанности.", company:"Название предприятия", email:"Электронная почта администратора", password:"Пароль (не менее 12 символов)", submit:"Создать предприятие", done:"Предприятие и учётная запись администратора уже созданы. Войдите в эту учётную запись или откройте раздел «Предприятие», если вы уже вошли.", login:"Войти в существующую учётную запись", open:"Открыть предприятие", error:"Не удалось завершить настройку." },
  en: { title:"Set up your enterprise", intro:"Create your enterprise and the first administrator account. Then configure sites, departments, workstations, equipment, positions and duties in the Enterprise area.", company:"Company name", email:"Administrator email", password:"Password (at least 12 characters)", submit:"Create enterprise", done:"The company and administrator account already exist. Sign in with that account or open Enterprise if you are already signed in.", login:"Sign in to the existing account", open:"Open Enterprise", error:"Setup could not be completed." },
};

export function EnterpriseSetupForm({ locale }: { locale: Locale }) {
  const t = text[locale]; const router = useRouter();
  const [required, setRequired] = useState<boolean | null>(null);
  const [name, setName] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  useEffect(() => { api<{setup_required:boolean}>("/api/v1/setup/status").then(async x=>{setRequired(x.setup_required);if(x.setup_required){setSignedIn(false);return}try{await api("/api/v1/auth/me");setSignedIn(true)}catch{setSignedIn(false)}}).catch(e=>{setError(e instanceof Error?e.message:t.error);setRequired(false);setSignedIn(false)}) }, [t.error]);
  async function submit(e: FormEvent) { e.preventDefault(); setBusy(true); setError(""); try { await api("/api/v1/setup", { method:"POST", body:JSON.stringify({company_name:name,email,password}) }); router.push(`/${locale}/betrieb`); router.refresh(); } catch(e) { setError(e instanceof Error?e.message:t.error); } finally { setBusy(false); } }
  if (required === null || (!required && signedIn === null)) return <main className="content"><p>{locale === "ru" ? "Загрузка…" : locale === "de" ? "Wird geladen…" : "Loading…"}</p></main>;
  return <main className="content"><section className="auth-card"><span className="eyebrow">WorkFlow Production · {locale === "ru" ? "Конструктор предприятия" : locale === "de" ? "Betrieb konfigurieren" : "Enterprise builder"}</span><h1>{t.title}</h1><p>{required ? t.intro : t.done}</p>{required ? <form className="enterprise-form" onSubmit={submit}><label>{t.company}<input required minLength={2} maxLength={180} value={name} onChange={e=>setName(e.target.value)}/></label><label>{t.email}<input type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label>{t.password}<input type="password" required minLength={12} maxLength={256} autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)}/></label>{error&&<div className="enterprise-error" role="alert">{error}</div>}<button className="primary-button" disabled={busy}>{busy?"…":t.submit}</button></form> : signedIn ? <Link className="primary-button" href={`/${locale}/betrieb`}>{t.open}</Link> : <Link className="primary-button" href={loginPath(locale)}>{t.login}</Link>}</section></main>;
}
