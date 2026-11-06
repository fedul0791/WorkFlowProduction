"use client";
import { useEffect, useState } from "react";
import type { Locale } from "@/i18n/messages";

export function ThemeToggle({locale}:{locale:Locale}) {
  const [dark,setDark]=useState(false);
  useEffect(()=>{const saved=localStorage.getItem("workflow-theme");const active=saved==="dark";setDark(active);document.documentElement.dataset.theme=active?"dark":"light";},[]);
  function toggle(){const next=!dark;setDark(next);document.documentElement.dataset.theme=next?"dark":"light";localStorage.setItem("workflow-theme",next?"dark":"light");}
  const label=dark?(locale==="ru"?"Включить светлую тему":locale==="de"?"Helles Design aktivieren":"Switch to light theme"):(locale==="ru"?"Включить тёмную тему":locale==="de"?"Dunkles Design aktivieren":"Switch to dark theme");
  return <button className="theme-toggle" type="button" onClick={toggle} aria-label={label} title={label}><span aria-hidden="true">{dark?"☼":"◐"}</span></button>;
}
