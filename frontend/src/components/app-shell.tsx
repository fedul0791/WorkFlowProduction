"use client";
import { useState } from "react";
import Link from "next/link";
import type { Locale } from "@/i18n/messages";
import { messages, locales } from "@/i18n/messages";
import { loginPath } from "@/lib/routes";
import { ThemeToggle } from "@/components/theme-toggle";
import { UserMenu } from "@/components/user-menu";
const localeNames:Record<Locale,string>={de:"DE",ru:"RU",en:"EN"};
function BrandMark(){return <span className="brand-mark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 17.5 9.5 6l5 11.5L20 6"/><path d="M7 17.5h10"/></svg></span>}
type Section="home"|"enterprise"|"personnel"|"administration"|"auth";
const paths:Record<Exclude<Section,"auth">,string>={home:"",enterprise:"betrieb",personnel:"mitarbeiter",administration:"administration"};
export function AppShell({children,locale,active="home"}:{children:React.ReactNode;locale:Locale;active?:Section}){
const [navigationOpen,setNavigationOpen]=useState(active!=="enterprise");
const t=messages[locale];
const items:[Exclude<Section,"auth">,string,React.ReactNode][]=[
["home",t.home,<><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/></>],
["enterprise",t.enterprise,<><path d="M3 21V8l9-5 9 5v13"/><path d="M8 21v-7h8v7M3 11h18"/></>],
["personnel",t.personnel,<><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.5-3.4 2.7-5 6.5-5 1.4 0 2.5.2 3.4.7M16 11h6m-3-3v6"/></>],
["administration",t.administration,<><path d="M12 3 20 7v5c0 4.5-3.2 7.4-8 9-4.8-1.6-8-4.5-8-9V7z"/><path d="m9 12 2 2 4-4"/></>]];
const label=active==="auth"?t.signIn:items.find(x=>x[0]===active)?.[1]??t.home;
return <div className={`app-shell ${navigationOpen?"":"nav-collapsed"}`}><aside className="sidebar"><Link className="brand" href={`/${locale}`} aria-label="WorkFlow Production"><BrandMark/><span className="brand-copy"><strong>WorkFlow</strong><span>Production</span></span></Link><div className="workspace-label">{t.workspace}</div><nav aria-label={t.navigation}>{items.map(([key,name,icon])=><Link key={key} className={`nav-link ${active===key?"active":""}`} href={`/${locale}/${paths[key]}`} aria-current={active===key?"page":undefined}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{icon}</svg>{name}</Link>)}</nav><div className="sidebar-bottom"><div className="tenant-chip"><span className="tenant-avatar" aria-hidden="true">WF</span><span><strong>{t.platformName}</strong><small>{t.foundationLabel}</small></span></div></div></aside><div className="main-column"><header className="topbar"><div className="breadcrumb"><button className="navigation-toggle" type="button" aria-label={navigationOpen?(locale==="ru"?"Свернуть меню":"Hide navigation"):(locale==="ru"?"Показать меню":"Show navigation")} aria-expanded={navigationOpen} onClick={()=>setNavigationOpen(value=>!value)}>☰</button>{t.breadcrumb} <span aria-hidden="true"> / </span><strong>{label}</strong></div><div className="topbar-actions"><nav className="language-switch" aria-label={t.language}>{locales.map(item=><Link key={item} href={active==="auth"?loginPath(item):`/${item}`} lang={item} aria-current={locale===item?"page":undefined}>{localeNames[item]}</Link>)}</nav><ThemeToggle locale={locale}/><UserMenu locale={locale}/></div></header>{children}</div></div>}
