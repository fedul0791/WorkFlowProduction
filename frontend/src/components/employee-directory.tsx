"use client";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import type { Locale } from "@/i18n/messages";
import { messages } from "@/i18n/messages";
import { api, type ApiUser } from "@/lib/api";
import { loginPath } from "@/lib/routes";

type Employee = { id: string; full_name: string; employee_number: string; site_id: string | null; is_active: boolean };
type Site = { id: string; name: string };
const words = {
  de: { sub: "Mitarbeiter suchen, filtern und öffnen.", search: "Name oder Personalnummer suchen", site: "Standort filtern", all: "Alle Standorte", create: "Mitarbeiter anlegen", name: "Vollständiger Name", number: "Personalnummer", save: "Anlegen", loading: "Mitarbeiter werden geladen…", empty: "Keine Mitarbeiter gefunden.", error: "Daten konnten nicht geladen werden.", catalog: "Personalstammdaten" },
  ru: { sub: "Поиск, фильтрация и карточки сотрудников.", search: "Поиск по имени или табельному номеру", site: "Фильтр по площадке", all: "Все площадки", create: "Добавить сотрудника", name: "ФИО", number: "Табельный номер", save: "Создать", loading: "Загрузка сотрудников…", empty: "Сотрудники не найдены.", error: "Не удалось загрузить данные.", catalog: "Справочники персонала" },
  en: { sub: "Search, filter, and open employee records.", search: "Search name or employee number", site: "Filter by site", all: "All sites", create: "Add employee", name: "Full name", number: "Employee number", save: "Create", loading: "Loading employees…", empty: "No employees found.", error: "Could not load data.", catalog: "Personnel reference data" },
};

export function EmployeeDirectory({ locale }: { locale: Locale }) {
  const t = words[locale]; const base = messages[locale];
  const [me, setMe] = useState<ApiUser | null>(null); const [rows, setRows] = useState<Employee[]>([]); const [sites, setSites] = useState<Site[]>([]);
  const [query, setQuery] = useState(""); const [site, setSite] = useState(""); const [name, setName] = useState(""); const [number, setNumber] = useState(""); const [newSite, setNewSite] = useState(""); const [busy, setBusy] = useState(true); const [error, setError] = useState("");
  const load = useCallback(async () => { setBusy(true); try { const user = await api<ApiUser>("/api/v1/auth/me"); setMe(user); setRows(await api<Employee[]>("/api/v1/employees")); setSites(user.permissions.includes("structure:read") ? await api<Site[]>("/api/v1/sites") : []); } catch (e) { setError(e instanceof Error ? e.message : t.error); } finally { setBusy(false); } }, [t.error]);
  useEffect(() => { void load(); }, [load]);
  const filtered = useMemo(() => rows.filter(r => (!site || r.site_id === site) && (!query || `${r.full_name} ${r.employee_number}`.toLocaleLowerCase(locale).includes(query.toLocaleLowerCase(locale)))), [rows, site, query, locale]);
  async function create(e: FormEvent) { e.preventDefault(); setError(""); try { await api("/api/v1/employees", { method: "POST", body: JSON.stringify({ employee_number: number, full_name: name, site_id: newSite || null }) }); setName(""); setNumber(""); setNewSite(""); await load(); } catch (err) { setError(err instanceof Error ? err.message : t.error); } }
  return <main className="workforce-page" lang={locale}>
    <header className="enterprise-heading"><div><span className="eyebrow">{base.personnel}</span><h1>{base.employees}</h1><p>{t.sub}</p></div><nav className="section-shortcuts" aria-label={t.catalog}><span>{t.catalog}:</span><Link href={`/${locale}/positionen`}>{base.positions}</Link><Link href={`/${locale}/qualifikationen`}>{base.qualifications}</Link></nav></header>
    {error && <div className="enterprise-error" role="alert">{error}</div>}
    {busy ? <p>{t.loading}</p> : !me ? <section className="enterprise-empty"><h2>{base.signIn}</h2><p>{error}</p><Link className="primary-button" href={loginPath(locale)}>{base.signIn}</Link></section> : <>
      <div className="directory-tools"><label className="search-field"><span>{t.search}</span><input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder={t.search} /></label>{sites.length > 0 && <label className="filter-field"><span>{t.site}</span><select value={site} onChange={e => setSite(e.target.value)}><option value="">{t.all}</option>{sites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label>}</div>
      {me.permissions.includes("employees:write") && <form className="workforce-form" onSubmit={create}><label>{t.name}<input required minLength={2} value={name} onChange={e => setName(e.target.value)} /></label><label>{t.number}<input required value={number} onChange={e => setNumber(e.target.value)} /></label>{sites.length>0&&<label>{t.site}<select value={newSite} onChange={e=>setNewSite(e.target.value)}><option value="">—</option>{sites.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label>}<button className="primary-button">{t.save}</button></form>}
      <div className="employee-directory">{filtered.length ? filtered.map(row => <Link className="employee-directory-row" key={row.id} href={`/${locale}/mitarbeiter/${row.id}`}><span className="employee-avatar" aria-hidden="true">{row.full_name.split(/\s+/).map(x => x[0]).slice(0, 2).join("").toUpperCase()}</span><span className="employee-identity"><strong>{row.full_name}</strong><small>{row.employee_number}</small></span><span className="employee-site">{sites.find(s => s.id === row.site_id)?.name ?? (row.site_id ? "—" : "")}</span><span className={`employee-status ${row.is_active ? "is-active" : "is-inactive"}`}>{row.is_active ? "●" : "○"}</span><span className="row-arrow" aria-hidden="true">›</span></Link>) : <p className="empty-directory">{t.empty}</p>}</div>
    </>}
  </main>;
}
