import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client.js";
import { formatJalaliDate, formatJalaliDateTime } from "../utils/date.js";

const EVENT_ICONS = {
  meeting: "🗓️",
  defense: "🎓",
  report_deadline: "📝",
};

function groupByDay(events) {
  const groups = [];
  let currentKey = null;
  for (const event of events) {
    const key = formatJalaliDate(event.occurs_at);
    if (key !== currentKey) {
      groups.push({ key, events: [] });
      currentKey = key;
    }
    groups[groups.length - 1].events.push(event);
  }
  return groups;
}

export default function CalendarPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await client.get("/calendar/events");
      setEvents(res.data);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <div className="page-loading">در حال بارگذاری...</div>;

  const groups = groupByDay(events);

  return (
    <div>
      <h1>رویدادهای پیش‌رو</h1>
      {events.length === 0 && (
        <p className="muted">رویداد پیش رویی (جلسه، دفاع یا موعد گزارش) ثبت نشده است</p>
      )}
      {groups.map((group) => (
        <div key={group.key} className="card" style={{ marginBottom: 16 }}>
          <h3>{group.key}</h3>
          <ul className="simple-list">
            {group.events.map((event, idx) => (
              <li key={`${event.event_type}-${event.project_id}-${idx}`}>
                <span>
                  {EVENT_ICONS[event.event_type]} {event.title}
                  {event.extra && <span className="muted"> — {event.extra}</span>}
                </span>
                <span className="muted">{formatJalaliDateTime(event.occurs_at)}</span>
              </li>
            ))}
          </ul>
          <div className="btn-row">
            {[...new Set(group.events.map((e) => e.project_id))].map((projectId) => (
              <Link
                key={projectId}
                className="btn btn-secondary btn-sm"
                to={`/projects/${projectId}`}
              >
                مشاهده پروژه
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
