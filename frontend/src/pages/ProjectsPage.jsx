import React, { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { STATUS_LABELS } from "../constants.js";

const SEARCH_DEBOUNCE_MS = 350;

function useDebouncedValue(value, delayMs) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

export default function ProjectsPage() {
  const { user } = useAuth();
  if (user.role === "admin") {
    return <Navigate to="/admin" replace />;
  }
  return user.role === "professor" ? <ProfessorView /> : <StudentView />;
}

function ProfessorView() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [briefFile, setBriefFile] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, SEARCH_DEBOUNCE_MS);

  async function load() {
    setLoading(true);
    const params = { mine: true };
    if (debouncedSearch) params.search = debouncedSearch;
    const res = await client.get("/projects", { params });
    setProjects(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const res = await client.post("/projects", { title, abstract });
      if (briefFile) {
        const formData = new FormData();
        formData.append("file", briefFile);
        await client.post(`/projects/${res.data.id}/brief-file`, formData);
      }
      setTitle("");
      setAbstract("");
      setBriefFile(null);
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "خطا در ایجاد پروژه");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>پروژه‌های من</h1>
        <button className="btn btn-primary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "انصراف" : "+ تعریف موضوع پروژه جدید"}
        </button>
      </div>

      {showForm && (
        <form className="card" onSubmit={handleCreate} style={{ marginBottom: 24 }}>
          {error && <div className="alert alert-error">{error}</div>}
          <label>
            عنوان پروژه
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          <label>
            چکیده
            <textarea
              rows={3}
              value={abstract}
              onChange={(e) => setAbstract(e.target.value)}
            />
          </label>
          <label>
            فایل توضیحات تکمیلی (اختیاری)
            <input
              type="file"
              onChange={(e) => setBriefFile(e.target.files[0] || null)}
            />
          </label>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "در حال ثبت..." : "ثبت پروژه"}
          </button>
        </form>
      )}

      <SearchBox value={search} onChange={setSearch} />

      {loading ? (
        <p>در حال بارگذاری...</p>
      ) : (
        <ProjectTable projects={projects} />
      )}
    </div>
  );
}

function StudentView() {
  const [tab, setTab] = useState("open");
  const [projects, setProjects] = useState([]);
  const [professors, setProfessors] = useState([]);
  const [professorId, setProfessorId] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const debouncedSearch = useDebouncedValue(search, SEARCH_DEBOUNCE_MS);

  useEffect(() => {
    client.get("/users/professors").then((res) => setProfessors(res.data));
  }, []);

  async function load() {
    setLoading(true);
    const params = tab === "mine" ? { mine: true } : { status_filter: "open" };
    if (tab === "open" && professorId) {
      params.professor_id = professorId;
    }
    if (debouncedSearch) params.search = debouncedSearch;
    const res = await client.get("/projects", { params });
    setProjects(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, professorId, debouncedSearch]);

  return (
    <div>
      <h1>پروژه‌ها</h1>
      <div className="tabs">
        <button
          className={`tab ${tab === "open" ? "tab-active" : ""}`}
          onClick={() => setTab("open")}
        >
          پروژه‌های قابل انتخاب
        </button>
        <button
          className={`tab ${tab === "mine" ? "tab-active" : ""}`}
          onClick={() => setTab("mine")}
        >
          پروژه من
        </button>
      </div>

      <SearchBox value={search} onChange={setSearch} />

      {tab === "open" && (
        <div className="filter-row">
          <label className="filter-label">
            انتخاب استاد
            <select value={professorId} onChange={(e) => setProfessorId(e.target.value)}>
              <option value="">همه اساتید</option>
              {professors.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.full_name}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {loading ? <p>در حال بارگذاری...</p> : <ProjectTable projects={projects} />}
    </div>
  );
}

function SearchBox({ value, onChange }) {
  return (
    <div className="search-row">
      <input
        type="search"
        className="search-input"
        placeholder="جست‌وجو در عنوان یا چکیده پروژه..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

export function ProjectTable({ projects }) {
  if (projects.length === 0) {
    return <p className="muted">پروژه‌ای یافت نشد</p>;
  }
  return (
    <div className="table-scroll">
      <table className="table">
        <thead>
          <tr>
            <th>عنوان</th>
            <th>استاد</th>
            <th>دانشجو</th>
            <th>وضعیت</th>
            <th>پیشرفت</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {projects.map((p) => (
            <tr key={p.id}>
              <td>{p.title}</td>
              <td>{p.professor?.full_name}</td>
              <td>{p.student?.full_name || "-"}</td>
              <td>
                <span className={`badge badge-${p.status}`}>{STATUS_LABELS[p.status]}</span>
              </td>
              <td>{p.progress_percent}%</td>
              <td>
                <Link className="btn btn-secondary btn-sm" to={`/projects/${p.id}`}>
                  مشاهده
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
