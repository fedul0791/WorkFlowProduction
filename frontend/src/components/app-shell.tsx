"use client";
import { useEffect, useState } from "react";
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
const [navigationOpen,setNavigationOpen]=useState(false);
const [settingsOpen,setSettingsOpen]=useState(false);
const [fontScale,setFontScale]=useState(1);
const [reduceMotion,setReduceMotion]=useState(false);
const [preferencesReady,setPreferencesReady]=useState(false);
const t=messages[locale];
const updateNavigationOpen=(open:boolean)=>{
  setNavigationOpen(open);
  if(open)document.documentElement.dataset.navigationOpen="true";
  else delete document.documentElement.dataset.navigationOpen;
};
useEffect(()=>{
  if(document.documentElement.dataset.navigationOpen==="true")setNavigationOpen(true);
},[]);
useEffect(()=>{
  try{
    const storedScale=Number(localStorage.getItem("wfp-font-scale"));
    if([0.85,1,1.15,1.3].includes(storedScale))setFontScale(storedScale);
    setReduceMotion(localStorage.getItem("wfp-reduce-motion")==="true");
  }catch(error){
    console.error("Unable to load display preferences",error);
  }finally{
    setPreferencesReady(true);
  }
},[]);
useEffect(()=>{
  if(!preferencesReady)return;
  document.documentElement.style.setProperty("--ui-font-scale",String(fontScale));
  document.documentElement.dataset.reduceMotion=String(reduceMotion);
  try{
    localStorage.setItem("wfp-font-scale",String(fontScale));
    localStorage.setItem("wfp-reduce-motion",String(reduceMotion));
  }catch(error){
    console.error("Unable to save display preferences",error);
  }
},[fontScale,reduceMotion,preferencesReady]);
useEffect(()=>{
  if(!settingsOpen)return;
  const closeOnEscape=(event:KeyboardEvent)=>{
    if(event.key==="Escape")setSettingsOpen(false);
  };
  window.addEventListener("keydown",closeOnEscape);
  return ()=>window.removeEventListener("keydown",closeOnEscape);
},[settingsOpen]);
const items:[Exclude<Section,"auth">,string,React.ReactNode][]=[
["home",t.home,<><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/></>],
["enterprise",t.enterprise,<><path d="M3 21V8l9-5 9 5v13"/><path d="M8 21v-7h8v7M3 11h18"/></>],
["personnel",t.personnel,<><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.5-3.4 2.7-5 6.5-5 1.4 0 2.5.2 3.4.7M16 11h6m-3-3v6"/></>],
["administration",t.administration,<><path d="M12 3 20 7v5c0 4.5-3.2 7.4-8 9-4.8-1.6-8-4.5-8-9V7z"/><path d="m9 12 2 2 4-4"/></>]];
const label=active==="auth"?t.signIn:items.find(x=>x[0]===active)?.[1]??t.home;
return (
  <div className={`app-shell ${navigationOpen?"":"nav-collapsed"}`}>
    <aside className="sidebar">
      <Link className="brand" href={`/${locale}`} aria-label="WorkFlow Production">
        <span className="brand-mark brand-abbreviation" aria-hidden="true">WFP</span>
        <span className="brand-copy"><strong>WorkFlow</strong><span>Production</span></span>
      </Link>
      <div className="workspace-label">{t.workspace}</div>
      <nav aria-label={t.navigation}>
        {items.map(([key,name,icon])=>(
          <Link key={key} className={`nav-link ${active===key?"active":""}`} href={`/${locale}/${paths[key]}`} aria-label={name} aria-current={active===key?"page":undefined} onClick={()=>updateNavigationOpen(true)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{icon}</svg>
            <span className="nav-label">{name}</span>
          </Link>
        ))}
        <button className="nav-link sidebar-settings" type="button" aria-label={t.siteSettings} onClick={()=>setSettingsOpen(true)}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z"/>
            <path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.7a8.4 8.4 0 0 1-1.5.9l-.3 1.8h-2.8l-.3-1.8a8.4 8.4 0 0 1-1.5-.9l-1.7.7-1.4-2.4 1.4-1.1a7.7 7.7 0 0 1 0-1.8l-1.4-1.1 1.4-2.4 1.7.7a8.4 8.4 0 0 1 1.5-.9l.3-1.8h2.8l.3 1.8a8.4 8.4 0 0 1 1.5.9l1.7-.7 1.4 2.4-1.4 1.1a7.7 7.7 0 0 1 0 1.8Z" transform="translate(-1 -1)"/>
          </svg>
          <span className="nav-label">{t.siteSettings}</span>
        </button>
      </nav>
      <div className="sidebar-bottom"><div className="tenant-chip"><span className="tenant-avatar" aria-hidden="true">WF</span><span className="tenant-copy"><strong>{t.platformName}</strong><small>{t.foundationLabel}</small></span></div></div>
    </aside>
    <div
      className="main-column"
      onClick={event=>{
        if(navigationOpen&&!(event.target instanceof Element&&event.target.closest(".navigation-toggle")))updateNavigationOpen(false);
      }}
      onKeyDown={event=>{if(event.key==="Escape")updateNavigationOpen(false);}}
    >
      <header className="topbar">
        <div className="breadcrumb">
          <Link className="topbar-brand" href={`/${locale}`} aria-label="WorkFlow Production"><BrandMark/></Link>
          <button className="navigation-toggle" type="button" aria-label={navigationOpen?(locale==="ru"?"Свернуть меню":"Hide navigation"):(locale==="ru"?"Показать меню":"Show navigation")} aria-expanded={navigationOpen} onClick={event=>{event.stopPropagation();updateNavigationOpen(!navigationOpen)}}>☰</button>
          <span className="breadcrumb-context">{t.breadcrumb}</span><span className="breadcrumb-separator" aria-hidden="true"> / </span><strong>{label}</strong>
        </div>
        <div className="topbar-actions">
          <nav className="language-switch" aria-label={t.language}>{locales.map(item=><Link key={item} href={active==="auth"?loginPath(item):`/${item}`} lang={item} aria-current={locale===item?"page":undefined}>{localeNames[item]}</Link>)}</nav>
          <ThemeToggle locale={locale}/>
          <UserMenu locale={locale}/>
        </div>
      </header>
      {children}
    </div>
    {settingsOpen&&<div className="site-settings-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)setSettingsOpen(false);}}>
      <section className="site-settings-dialog" role="dialog" aria-modal="true" aria-labelledby="site-settings-title">
        <button className="modal-close" type="button" aria-label={t.settingsClose} onClick={()=>setSettingsOpen(false)}>×</button>
        <span className="site-settings-eyebrow">{t.siteSettings}</span>
        <h2 id="site-settings-title">{t.displaySettings}</h2>
        <fieldset className="font-size-setting">
          <legend>{t.fontSize}</legend>
          <div className="font-size-options" role="group" aria-label={t.fontSize}>
            {[0.85,1,1.15,1.3].map((scale,index)=><button key={scale} type="button" className={fontScale===scale?"active":""} aria-pressed={fontScale===scale} onClick={()=>setFontScale(scale)}>
              <span style={{fontSize:`${Math.round(100*scale)}%`}}>Аа</span>
              <small>{[t.fontSmall,t.fontDefault,t.fontLarge,t.fontExtraLarge][index]}</small>
            </button>)}
          </div>
        </fieldset>
        <label className="settings-switch">
          <span><strong>{t.reduceMotion}</strong><small>{t.reduceMotionHint}</small></span>
          <input type="checkbox" checked={reduceMotion} onChange={event=>setReduceMotion(event.target.checked)}/>
        </label>
        <p className="site-settings-note">{t.settingsSaved}</p>
      </section>
    </div>}
  </div>
)}
