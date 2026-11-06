import { AppShell } from "@/components/app-shell";
import { WorkforceAdmin } from "@/components/workforce-admin";
import { EmployeeDirectory } from "@/components/employee-directory";
import type { Locale } from "@/i18n/messages";
type Section="employees"|"positions"|"qualifications"|"authorizations"|"users"|"permissions";
export function WorkforcePage({locale,section}:{locale:Locale;section:Section}){
  if(section==="employees") return <AppShell locale={locale} active="personnel"><EmployeeDirectory locale={locale}/></AppShell>;
  const t={de:{employees:"Mitarbeiter",positions:"Positionen",qualifications:"Qualifikationen",authorizations:"Produktionsfreigaben",users:"Benutzerverwaltung",permissions:"Systemrollen & Rechte"},ru:{employees:"Сотрудники",positions:"Должности",qualifications:"Квалификации",authorizations:"Производственные допуски",users:"Учётные записи",permissions:"Системные роли и права"},en:{employees:"Employees",positions:"Positions",qualifications:"Qualifications",authorizations:"Production authorizations",users:"Accounts",permissions:"System roles & permissions"}}[locale];
  const personnel=section==="positions"||section==="qualifications"||section==="authorizations";
  return <AppShell locale={locale} active={personnel?"personnel":"administration"}><div className="workforce-subnav">{personnel?<><a href={`/${locale}/mitarbeiter`}>{t.employees}</a><a href={`/${locale}/positionen`} aria-current={section==="positions"?"page":undefined}>{t.positions}</a><a href={`/${locale}/qualifikationen`} aria-current={section==="qualifications"?"page":undefined}>{t.qualifications}</a>{section==="authorizations"&&<span>{t.authorizations}</span>}</>:<><a href={`/${locale}/benutzerverwaltung`} aria-current={section==="users"?"page":undefined}>{t.users}</a><a href={`/${locale}/rollen`} aria-current={section==="permissions"?"page":undefined}>{t.permissions}</a></>}</div><WorkforceAdmin locale={locale} section={section}/></AppShell>
}
