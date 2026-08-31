/**
 * Every date in the UI is shown in the Jalali (Persian solar) calendar with
 * Persian digits. "fa-IR" already implies the Persian calendar in the
 * Intl/ICU data browsers ship with, so a plain toLocaleDateString/
 * toLocaleString call is enough — this module exists so every screen goes
 * through one place instead of repeating that call (and the null-guard)
 * everywhere.
 */

export function formatJalaliDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleDateString("fa-IR");
}

export function formatJalaliDateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("fa-IR");
}
