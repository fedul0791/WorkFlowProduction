import type { Locale } from "@/i18n/messages";
export function loginPath(locale:Locale){return locale==="de"?"/de/anmelden":`/${locale}/login`}
export function setupPath(locale:Locale){return locale==="de"?"/de/einrichtung":locale==="ru"?"/ru/nastroika":"/en/setup"}
