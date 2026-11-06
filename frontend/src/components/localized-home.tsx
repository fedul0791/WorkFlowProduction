import type { Locale } from "@/i18n/messages";
import { messages } from "@/i18n/messages";
import { AppShell } from "@/components/app-shell";
import Link from "next/link";

export function LocalizedHome({ locale }: { locale: Locale }) {
  const t = messages[locale];

  return (
    <div lang={locale}>
      <AppShell locale={locale}>
        <main className="content">
          <div className="eyebrow">{t.eyebrow}</div>
          <section className="hero" aria-labelledby="welcome-title">
            <div className="hero-content">
              <div className="hero-kicker"><span className="status-dot" />{t.stageLabel}</div>
              <h1 id="welcome-title">{t.title}</h1>
              <p>{t.intro}</p>
              <Link className="hero-action" href={`/${locale}/betrieb`}>{t.builderLink}<span aria-hidden="true">↗</span></Link>
            </div>
            <aside className="builder-visual" aria-label={t.builderDiagramLabel}>
              <div className="visual-caption"><span>WFP / 01</span><span>ENTERPRISE MAP</span></div>
              <div className="blueprint-tree">
                <div className="blueprint-node blueprint-root"><span>01</span><strong>{t.companyBlock}</strong></div>
                <div className="blueprint-branches">
                  <div className="blueprint-node"><span>02</span><strong>{t.siteBlock}</strong></div>
                  <div className="blueprint-node"><span>03</span><strong>{t.departmentBlock}</strong></div>
                  <div className="blueprint-node"><span>04</span><strong>{t.areaBlock}</strong></div>
                  <div className="blueprint-node"><span>05</span><strong>{t.workstationBlock}</strong></div>
                  <div className="blueprint-node"><span>06</span><strong>{t.equipmentBlock}</strong></div>
                </div>
              </div>
              <span className="visual-coordinate">52° 31′ 12.0″ N&nbsp;&nbsp; 13° 24′ 18.0″ E</span>
            </aside>
          </section>

          <div className="section-heading">
            <div>
              <h2>{t.foundationTitle}</h2>
              <p>{t.foundationSubtitle}</p>
            </div>
          </div>
          <section className="foundation-card" aria-label={t.foundationTitle}>
            <div className="foundation-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 19V9l8-5 8 5v10" /><path d="M8 19v-6h8v6M3 19h18" /><path d="M9 9h.01M15 9h.01" />
              </svg>
            </div>
            <div>
              <h3>{t.foundationCardTitle}</h3>
              <p>{t.foundationCardBody}</p>
            </div>
          </section>
          <p className="footer-note">{t.footer}</p>
        </main>
      </AppShell>
    </div>
  );
}
