import React, { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { STATUS_LABELS } from "../constants.js";
import { formatJalaliDateTime } from "../utils/date.js";

export default function HomePage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [upcomingMeetings, setUpcomingMeetings] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(user.role !== "admin");

  useEffect(() => {
    if (user.role === "admin") return;
    async function load() {
      setLoading(true);
      const [projRes, notifRes] = await Promise.all([
        client.get("/projects", { params: { mine: true } }),
        client.get("/notifications", { params: { unread_only: true } }),
      ]);
      setProjects(projRes.data);
      setNotifications(notifRes.data);

      const meetingLists = await Promise.all(
        projRes.data.map((p) =>
          client
            .get(`/projects/${p.id}/meetings`)
            .then((r) => r.data.map((m) => ({ ...m, projectTitle: p.title })))
            .catch(() => [])
        )
      );
      const now = new Date();
      const upcoming = meetingLists
        .flat()
        .filter((m) => new Date(m.scheduled_at) >= now)
        .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));
      setUpcomingMeetings(upcoming);
      setLoading(false);
    }
    load();
  }, []);

  if (user.role === "admin") {
    return <Navigate to="/admin" replace />;
  }

  if (loading) return <div className="page-loading">در حال بارگذاری...</div>;

  const inProgress = projects.filter((p) => p.status === "in_progress");

  return (
    <div>
      <h1>صفحه اصلی</h1>
      <div className="stat-row">
        <div className="stat-card">
          <div className="stat-value">{projects.length}</div>
          <div className="stat-label">تعداد پروژه‌ها</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{inProgress.length}</div>
          <div className="stat-label">پروژه‌های در حال انجام</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{upcomingMeetings.length}</div>
          <div className="stat-label">جلسات آینده</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{notifications.length}</div>
          <div className="stat-label">اعلان‌های خوانده‌نشده</div>
        </div>
      </div>

      <div className="grid-2">
        <section className="card">
          <h3>پروژه‌های در حال انجام</h3>
          {inProgress.length === 0 && <p className="muted">موردی وجود ندارد</p>}
          <ul className="simple-list">
            {inProgress.map((p) => (
              <li key={p.id}>
                <Link to={`/projects/${p.id}`}>{p.title}</Link>
                <span className={`badge badge-${p.status}`}>
                  {STATUS_LABELS[p.status]}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h3>جلسات آینده</h3>
          {upcomingMeetings.length === 0 && <p className="muted">جلسه‌ای ثبت نشده است</p>}
          <ul className="simple-list">
            {upcomingMeetings.slice(0, 8).map((m) => (
              <li key={m.id}>
                <span>{m.projectTitle}</span>
                <span className="muted">{formatJalaliDateTime(m.scheduled_at)}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h3>اعلان‌های اخیر</h3>
          {notifications.length === 0 && <p className="muted">اعلانی وجود ندارد</p>}
          <ul className="simple-list">
            {notifications.slice(0, 8).map((n) => (
              <li key={n.id}>{n.content}</li>
            ))}
          </ul>
        </section>

        {user.role === "student" && (
          <section className="card">
            <h3>شروع کنید</h3>
            <p className="muted">
              می‌توانید پروژه‌های موجود را مشاهده کرده و برای انتخاب آن‌ها درخواست دهید.
            </p>
            <Link className="btn btn-primary" to="/projects">
              مشاهده پروژه‌ها
            </Link>
          </section>
        )}
        {user.role === "professor" && (
          <section className="card">
            <h3>مدیریت پروژه‌ها</h3>
            <p className="muted">پروژه جدید تعریف کنید یا وضعیت پروژه‌های فعلی را ببینید.</p>
            <Link className="btn btn-primary" to="/projects">
              مدیریت پروژه‌ها
            </Link>
          </section>
        )}
      </div>
    </div>
  );
}
