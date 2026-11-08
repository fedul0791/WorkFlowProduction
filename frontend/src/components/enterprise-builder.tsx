"use client";
import { useState } from "react";
import type { Locale } from "@/i18n/messages";
import { EnterpriseSandbox } from "@/components/enterprise-sandbox";
import { EnterpriseStructure } from "@/components/enterprise-structure";
import { EnterpriseStructureTree } from "@/components/enterprise-structure-tree";
import { WorkforceAdmin } from "@/components/workforce-admin";

type Tab = "sandbox" | "details" | "positions" | "qualifications";
const labels: Record<Locale, Record<Tab, string>> = {
  de: { sandbox: "Visueller Plan", details: "Struktur und Daten", positions: "Positionen und Aufgaben", qualifications: "Qualifikationen" },
  ru: { sandbox: "Визуальный план", details: "Структура и данные", positions: "Должности и обязанности", qualifications: "Квалификации" },
  en: { sandbox: "Visual plan", details: "Structure and data", positions: "Positions and duties", qualifications: "Qualifications" },
};

export function EnterpriseBuilder({ locale }: { locale: Locale }) {
  const [tab, setTab] = useState<Tab>("sandbox");
  return (
    <main className="workforce-page">
      <nav
        className="tabs-row"
        aria-label={locale === "ru" ? "Настройка предприятия" : locale === "de" ? "Betrieb einrichten" : "Enterprise setup"}
      >
        {(Object.keys(labels[locale]) as Tab[]).map((item) => (
          <button
            key={item}
            type="button"
            className={tab === item ? "active" : ""}
            aria-current={tab === item ? "page" : undefined}
            onClick={() => setTab(item)}
          >
            {labels[locale][item]}
          </button>
        ))}
      </nav>
      <div className="content-item">
        {tab === "sandbox" ? <EnterpriseSandbox locale={locale} /> : tab === "details" ? (
          <div className="enterprise-data-page">
            <EnterpriseStructureTree locale={locale} />
            <EnterpriseStructure locale={locale} />
          </div>
        ) : <WorkforceAdmin locale={locale} section={tab} />}
      </div>
    </main>
  );
}
