import React, { useEffect, useState } from "react";
import client from "../api/client.js";
import { ProjectTable } from "./ProjectsPage.jsx";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([client.get("/admin/stats"), client.get("/projects")]).then(
      ([statsRes, projectsRes]) => {
        setStats(statsRes.data);
        setProjects(projectsRes.data);
        setLoading(false);
      }
    );
  }, []);

  if (loading) return <div className="page-loading">در حال بارگذاری...</div>;

  return (
    <div>
      <h1>داشبورد مدیریت گروه</h1>
      <div className="stat-row">
        <div className="stat-card">
          <div className="stat-value">{stats.total_professors}</div>
          <div className="stat-label">تعداد اساتید</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.total_students}</div>
          <div className="stat-label">تعداد دانشجویان</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.total_projects}</div>
          <div className="stat-label">تعداد پروژه‌ها</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.open_projects}</div>
          <div className="stat-label">پروژه‌های باز</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.active_projects}</div>
          <div className="stat-label">پروژه‌های در حال انجام</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.completed_projects}</div>
          <div className="stat-label">پروژه‌های خاتمه‌یافته</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {stats.average_duration_days != null
              ? `${Math.round(stats.average_duration_days)} روز`
              : "-"}
          </div>
          <div className="stat-label">میانگین مدت انجام پروژه</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.average_progress_percent}%</div>
          <div className="stat-label">میانگین درصد پیشرفت</div>
        </div>
      </div>

      <h3 style={{ marginTop: 24 }}>همه‌ی پروژه‌های سامانه</h3>
      <ProjectTable projects={projects} />
    </div>
  );
}
