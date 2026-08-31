export const STATUS_LABELS = {
  open: "باز",
  pending: "در انتظار تایید",
  in_progress: "در حال انجام",
  completed: "خاتمه‌یافته",
  rejected: "رد شده",
};

export const REQUEST_STATUS_LABELS = {
  pending: "در انتظار",
  approved: "تایید شده",
  rejected: "رد شده",
};

export const ROLE_LABELS = {
  admin: "مدیر گروه",
  professor: "استاد",
  student: "دانشجو",
};

// Value = JS Date.getDay() convention isn't used here — the backend stores
// Python's date.weekday() (Monday=0 .. Sunday=6). Ordered Saturday-first to
// match how the Persian week is normally listed.
export const WEEKDAY_OPTIONS = [
  { value: 5, label: "شنبه" },
  { value: 6, label: "یکشنبه" },
  { value: 0, label: "دوشنبه" },
  { value: 1, label: "سه‌شنبه" },
  { value: 2, label: "چهارشنبه" },
  { value: 3, label: "پنجشنبه" },
  { value: 4, label: "جمعه" },
];

export const DEFENSE_OUTCOME_LABELS = {
  pass: "قبول",
  needs_revision: "نیاز به اصلاح",
  fail: "رد",
};
