import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client.js";

const CHART_WIDTH = 640;
const CHART_HEIGHT = 160;
const CHART_PADDING = 24;

function GradeTrendChart({ projects }) {
  const graded = projects.filter((p) => p.average_grade != null);
  if (graded.length === 0) {
    return <p className="muted">هنوز نمره‌ای برای رسم نمودار ثبت نشده است</p>;
  }

  const usableWidth = CHART_WIDTH - CHART_PADDING * 2;
  const usableHeight = CHART_HEIGHT - CHART_PADDING * 2;
  const stepX = graded.length > 1 ? usableWidth / (graded.length - 1) : 0;

  const points = graded.map((p, i) => {
    const x = CHART_PADDING + i * stepX;
    const y = CHART_PADDING + usableHeight * (1 - p.average_grade / 100);
    return { x, y, project: p };
  });

  const linePath = points.map((pt) => `${pt.x},${pt.y}`).join(" ");

  return (
    <div style={{ overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        style={{ width: "100%", minWidth: 480, height: CHART_HEIGHT }}
      >
        <line
          x1={CHART_PADDING}
          y1={CHART_HEIGHT - CHART_PADDING}
          x2={CHART_WIDTH - CHART_PADDING}
          y2={CHART_HEIGHT - CHART_PADDING}
          stroke="var(--border-strong)"
          strokeWidth="1"
        />
        <polyline points={linePath} fill="none" stroke="var(--primary)" strokeWidth="2" />
        {points.map((pt, i) => (
          <g key={pt.project.id}>
            <circle cx={pt.x} cy={pt.y} r="4" fill="var(--primary)" />
            <text
              x={pt.x}
              y={pt.y - 10}
              textAnchor="middle"
              fontSize="11"
              fill="var(--text)"
            >
              {pt.project.average_grade}
            </text>
            <text
              x={pt.x}
              y={CHART_HEIGHT - CHART_PADDING + 16}
              textAnchor="middle"
              fontSize="11"
              fill="var(--text-muted)"
            >
              {`پروژه ${i + 1}`}
            </text>
          </g>
        ))}
      </svg>
      <ul className="simple-list">
        {graded.map((p, i) => (
          <li key={p.id}>
            <Link to={`/projects/${p.id}`}>{`پروژه ${i + 1}: ${p.title}`}</Link>
            <span className="muted">{p.average_grade}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function DashboardStatsPage() {
  const [stats, setStats] = useState(null);
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    client.get("/dashboard/stats").then((res) => setStats(res.data));
    client.get("/projects", { params: { mine: true } }).then((res) => setProjects(res.data));
  }, []);

  if (!stats) return <div className="page-loading">در حال بارگذاری...</div>;

  const bars = [
    { label: "تعداد پروژه‌ها", value: stats.total_projects, max: stats.total_projects || 1 },
    { label: "پروژه‌های فعال", value: stats.active_projects, max: stats.total_projects || 1 },
    {
      label: "پروژه‌های خاتمه‌یافته",
      value: stats.completed_projects,
      max: stats.total_projects || 1,
    },
  ];

  return (
    <div>
      <h1>داشبورد مدیریتی</h1>
      <div className="stat-row">
        <div className="stat-card">
          <div className="stat-value">{stats.total_projects}</div>
          <div className="stat-label">تعداد پروژه‌ها</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.active_projects}</div>
          <div className="stat-label">پروژه‌های فعال</div>
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

      <div className="card">
        <h3>نمودار پروژه‌ها</h3>
        {bars.map((b) => (
          <div key={b.label} className="chart-row">
            <div className="chart-label">{b.label}</div>
            <div className="chart-track">
              <div
                className="chart-fill"
                style={{ width: `${(b.value / b.max) * 100}%` }}
              />
            </div>
            <div className="chart-value">{b.value}</div>
          </div>
        ))}
      </div>

      {projects.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3>درصد پیشرفت هر پروژه</h3>
          {projects.map((p) => (
            <div key={p.id} className="chart-row">
              <div className="chart-label" title={p.title}>
                {p.title}
              </div>
              <div className="chart-track">
                <div
                  className="chart-fill"
                  style={{ width: `${p.progress_percent}%` }}
                />
              </div>
              <div className="chart-value">{p.progress_percent}%</div>
            </div>
          ))}
        </div>
      )}

      {projects.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <h3>روند نمره نهایی پروژه‌ها</h3>
          <GradeTrendChart projects={projects} />
        </div>
      )}
    </div>
  );
}
