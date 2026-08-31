import React from "react";
import DatePicker from "react-multi-date-picker";
import persian from "react-date-object/calendars/persian";
import persian_fa from "react-date-object/locales/persian_fa";
import TimePicker from "react-multi-date-picker/plugins/time_picker";

function pad(n) {
  return String(n).padStart(2, "0");
}

// Keeps the same "YYYY-MM-DD" / "YYYY-MM-DDTHH:mm" string shape the rest of
// the app (and the backend) already expects from native date inputs — only
// how the user picks the date changes, not what gets sent over the wire.
function toLocalString(dateObject, withTime) {
  if (!dateObject) return "";
  const d = dateObject.toDate();
  const datePart = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  return withTime ? `${datePart}T${pad(d.getHours())}:${pad(d.getMinutes())}` : datePart;
}

export default function PersianDateInput({ value, onChange, withTime = false, required = false }) {
  return (
    <DatePicker
      calendar={persian}
      locale={persian_fa}
      value={value ? new Date(value) : ""}
      onChange={(dateObject) => onChange(toLocalString(dateObject, withTime))}
      format={withTime ? "YYYY/MM/DD HH:mm" : "YYYY/MM/DD"}
      plugins={withTime ? [<TimePicker key="time" hideSeconds />] : []}
      calendarPosition="bottom-right"
      inputClass="persian-date-input"
      required={required}
      editable={false}
    />
  );
}
