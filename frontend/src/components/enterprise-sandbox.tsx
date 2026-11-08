"use client";

import type { Locale } from "@/i18n/messages";
import { EnterpriseCadCanvas } from "@/components/enterprise-cad-canvas";

export function EnterpriseSandbox({ locale }: { locale: Locale }) {
  return (
    <div className="sandbox-mode-shell">
      <EnterpriseCadCanvas locale={locale} />
    </div>
  );
}
