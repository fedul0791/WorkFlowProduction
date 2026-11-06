"use client";
import { useState } from "react";
import type { Locale } from "@/i18n/messages";
import { EnterpriseSandbox } from "@/components/enterprise-sandbox";
import { EnterpriseStructure } from "@/components/enterprise-structure";
import { WorkforceAdmin } from "@/components/workforce-admin";

type Tab = "sandbox" | "details" | "positions" | "qualifications";
const labels: Record<Locale, Record<Tab, string>> = {
  de: { sandbox: "Betrieb zusammenbauen", details: "Strukturdetails", positions: "Positionen und Aufgaben", qualifications: "Qualifikationen" },
  ru: { sandbox: "Собрать предприятие", details: "Подробная структура", positions: "Должности и обязанности", qualifications: "Квалификации" },
  en: { sandbox: "Assemble enterprise", details: "Structure details", positions: "Positions and duties", qualifications: "Qualifications" },
};

export function EnterpriseBuilder({ locale }: { locale: Locale }) {
  const [tab, setTab] = useState<Tab>("sandbox");
  return <div className="enterprise-builder">
    <nav className="builder-tabs" aria-label={locale === "ru" ? "Настройка предприятия" : locale === "de" ? "Betrieb einrichten" : "Enterprise setup"}>
      {(Object.keys(labels[locale]) as Tab[]).map((item) => <button type="button" key={item} className={tab === item ? "active" : ""} aria-current={tab === item ? "page" : undefined} onClick={() => setTab(item)}>{labels[locale][item]}</button>)}
    </nav>
    {tab === "sandbox" ? <EnterpriseSandbox locale={locale} /> : tab === "details" ? <EnterpriseStructure locale={locale} /> : <WorkforceAdmin locale={locale} section={tab} />}
  </div>;
}
