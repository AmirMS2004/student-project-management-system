import React, { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import {
  DEFENSE_OUTCOME_LABELS,
  REQUEST_STATUS_LABELS,
  STATUS_LABELS,
  WEEKDAY_OPTIONS,
} from "../constants.js";
import { isPreviewable, openOrDownloadFile } from "../utils/file.js";
import { formatJalaliDate, formatJalaliDateTime } from "../utils/date.js";
import PersianDateInput from "../components/PersianDateInput.jsx";

const TABS = [
  { key: "overview", label: "کلیات" },
  { key: "requests", label: "درخواست‌ها" },
  { key: "meetings", label: "جلسات" },
  { key: "reports", label: "گزارش‌ها" },
  { key: "grades", label: "نمرات" },
  { key: "files", label: "فایل‌ها" },
  { key: "messages", label: "پیام‌ها" },
];

const TAB_CATEGORY = {
  overview: "project",
  requests: "request",
  meetings: "meeting",
  reports: "report",
  grades: "grade",
  files: "file",
  messages: "message",
};

export default function ProjectDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState(null);
  const [tab, setTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [unreadCategories, setUnreadCategories] = useState(new Set());

  const loadProject = useCallback(async () => {
    try {
      const res = await client.get(`/projects/${id}`);
      setProject(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "خطا در دریافت اطلاعات پروژه");
    } finally {
      setLoading(false);
    }
  }, [id]);

  const loadUnreadCategories = useCallback(async () => {
    try {
      const res = await client.get("/notifications", {
        params: { project_id: id, unread_only: true },
      });
      setUnreadCategories(new Set(res.data.map((n) => n.category).filter(Boolean)));
    } catch {
      /* ignore */
    }
  }, [id]);

  useEffect(() => {
    loadProject();
    loadUnreadCategories();
    const interval = setInterval(loadUnreadCategories, 15000);
    return () => clearInterval(interval);
  }, [loadProject, loadUnreadCategories]);

  async function handleTabClick(key) {
    setTab(key);
    const category = TAB_CATEGORY[key];
    if (category && unreadCategories.has(category)) {
      setUnreadCategories((prev) => {
        const next = new Set(prev);
        next.delete(category);
        return next;
      });
      try {
        await client.post("/notifications/read-by-category", null, {
          params: { project_id: id, category },
        });
      } catch {
        /* ignore */
      }
    }
  }

  if (loading) return <div className="page-loading">در حال بارگذاری...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!project) return null;

  const isOwner = user.role === "professor" && project.professor_id === user.id;
  const isAssignedStudent = user.role === "student" && project.student_id === user.id;
  const isMember = isOwner || isAssignedStudent;

  const visibleTabs = TABS.filter((t) => {
    if (t.key === "requests") return isOwner;
    if (["meetings", "reports", "grades", "files", "messages"].includes(t.key)) {
      return isMember;
    }
    return true;
  });

  return (
    <div>
      <h1>{project.title}</h1>
      <div className="tabs">
        {visibleTabs.map((t) => (
          <button
            key={t.key}
            className={`tab ${tab === t.key ? "tab-active" : ""}`}
            onClick={() => handleTabClick(t.key)}
          >
            {t.label}
            {unreadCategories.has(TAB_CATEGORY[t.key]) && (
              <span className="tab-dot" title="محتوای جدید" />
            )}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <OverviewTab project={project} isOwner={isOwner} onUpdated={loadProject} />
      )}
      {tab === "requests" && isOwner && (
        <RequestsTab project={project} onDecided={loadProject} />
      )}
      {tab === "meetings" && isMember && (
        <MeetingsTab projectId={project.id} isOwner={isOwner} />
      )}
      {tab === "reports" && isMember && (
        <ReportsTab projectId={project.id} isOwner={isOwner} />
      )}
      {tab === "grades" && isMember && (
        <GradesTab project={project} isOwner={isOwner} onGradesChanged={loadProject} />
      )}
      {tab === "files" && isMember && <FilesTab projectId={project.id} />}
      {tab === "messages" && isMember && (
        <MessagesTab project={project} currentUser={user} />
      )}

      {user.role === "student" &&
        !isMember &&
        project.status === "open" &&
        tab === "overview" && <RequestProjectBox projectId={project.id} />}
    </div>
  );
}

function OverviewTab({ project, isOwner, onUpdated }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    status: project.status,
    progress_percent: project.progress_percent,
    start_date: project.start_date ? project.start_date.slice(0, 10) : "",
    end_date: project.end_date ? project.end_date.slice(0, 10) : "",
    defense_date: project.defense_date ? project.defense_date.slice(0, 16) : "",
    defense_outcome: project.defense_outcome || "",
    defense_outcome_notes: project.defense_outcome_notes || "",
    abstract: project.abstract || "",
    report_weekday:
      project.report_weekday != null ? String(project.report_weekday) : "",
    report_deadline_time: project.report_deadline_time || "23:59",
  });
  const [error, setError] = useState("");
  const [uploadingBrief, setUploadingBrief] = useState(false);

  async function handleSave(e) {
    e.preventDefault();
    setError("");
    try {
      await client.patch(`/projects/${project.id}`, {
        ...form,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        defense_date: form.defense_date || null,
        defense_outcome: form.defense_outcome || null,
        defense_outcome_notes: form.defense_outcome ? form.defense_outcome_notes : null,
        progress_percent: Number(form.progress_percent),
        report_weekday: form.report_weekday === "" ? null : Number(form.report_weekday),
        report_deadline_time: form.report_weekday === "" ? null : form.report_deadline_time,
      });
      setEditing(false);
      onUpdated();
    } catch (err) {
      setError(err.response?.data?.detail || "خطا در ذخیره تغییرات");
    }
  }

  async function downloadBrief() {
    await openOrDownloadFile(
      `/projects/${project.id}/brief-file/download`,
      project.brief_original_filename
    );
  }

  async function downloadDossierPdf() {
    await openOrDownloadFile(
      `/projects/${project.id}/export-pdf`,
      `project-${project.id}-dossier.pdf`
    );
  }

  async function downloadArchiveZip() {
    await openOrDownloadFile(
      `/projects/${project.id}/export-zip`,
      `project-${project.id}-archive.zip`
    );
  }

  async function handleBriefUpload(e) {
    const selected = e.target.files[0];
    if (!selected) return;
    setUploadingBrief(true);
    try {
      const formData = new FormData();
      formData.append("file", selected);
      await client.post(`/projects/${project.id}/brief-file`, formData);
      onUpdated();
    } finally {
      setUploadingBrief(false);
      e.target.value = "";
    }
  }

  return (
    <div className="card">
      {!editing ? (
        <>
          <dl className="detail-list">
            <dt>چکیده</dt>
            <dd>{project.abstract || "-"}</dd>
            <dt>استاد راهنما</dt>
            <dd>{project.professor?.full_name}</dd>
            <dt>دانشجو</dt>
            <dd>{project.student?.full_name || "هنوز انتخاب نشده"}</dd>
            <dt>وضعیت</dt>
            <dd>
              <span className={`badge badge-${project.status}`}>
                {STATUS_LABELS[project.status]}
              </span>
            </dd>
            <dt>تاریخ شروع</dt>
            <dd>{formatJalaliDate(project.start_date)}</dd>
            <dt>تاریخ پایان</dt>
            <dd>{formatJalaliDate(project.end_date)}</dd>
            <dt>تاریخ دفاع</dt>
            <dd>
              {project.defense_date ? (
                <span className="badge badge-defense">
                  {formatJalaliDateTime(project.defense_date)}
                </span>
              ) : (
                "-"
              )}
            </dd>
            <dt>نتیجه دفاع</dt>
            <dd>
              {project.defense_outcome ? (
                <>
                  <span className={`badge badge-outcome-${project.defense_outcome}`}>
                    {DEFENSE_OUTCOME_LABELS[project.defense_outcome]}
                  </span>
                  {project.defense_outcome_notes && (
                    <span className="muted"> — {project.defense_outcome_notes}</span>
                  )}
                </>
              ) : (
                <span className="muted">ثبت نشده</span>
              )}
            </dd>
            <dt>موعد گزارش هفتگی</dt>
            <dd>
              {project.report_weekday != null ? (
                <span className="badge badge-defense">
                  هر {WEEKDAY_OPTIONS.find((w) => w.value === project.report_weekday)?.label}{" "}
                  ساعت {project.report_deadline_time}
                </span>
              ) : (
                <span className="muted">تعیین نشده</span>
              )}
            </dd>
            <dt>درصد پیشرفت</dt>
            <dd>
              <div className="progress-bar">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${project.progress_percent}%` }}
                />
              </div>
              {project.progress_percent}%
            </dd>
            <dt>نمره نهایی</dt>
            <dd>
              {project.average_grade != null ? (
                <>
                  <strong>{project.average_grade}</strong>
                  <span className="muted"> (میانگین {project.grade_count} مرحله)</span>
                </>
              ) : (
                <span className="muted">هنوز نمره‌ای ثبت نشده</span>
              )}
            </dd>
            <dt>فایل توضیحات تکمیلی</dt>
            <dd>
              {project.brief_original_filename ? (
                <button className="btn btn-secondary btn-sm" onClick={downloadBrief}>
                  {isPreviewable(project.brief_original_filename) ? "مشاهده" : "دانلود"} «
                  {project.brief_original_filename}»
                </button>
              ) : (
                <span className="muted">ثبت نشده</span>
              )}
              {isOwner && (
                <label className="btn btn-secondary btn-sm brief-upload-btn">
                  {uploadingBrief
                    ? "در حال بارگذاری..."
                    : project.brief_original_filename
                      ? "جایگزینی فایل"
                      : "بارگذاری فایل"}
                  <input
                    type="file"
                    hidden
                    onChange={handleBriefUpload}
                    disabled={uploadingBrief}
                  />
                </label>
              )}
            </dd>
          </dl>
          <div className="btn-row">
            {isOwner && (
              <button className="btn btn-secondary" onClick={() => setEditing(true)}>
                ویرایش پروژه
              </button>
            )}
            <button className="btn btn-secondary" onClick={downloadDossierPdf}>
              دانلود پرونده PDF
            </button>
            <button className="btn btn-secondary" onClick={downloadArchiveZip}>
              دانلود آرشیو ZIP
            </button>
          </div>
        </>
      ) : (
        <form onSubmit={handleSave}>
          {error && <div className="alert alert-error">{error}</div>}
          <label>
            چکیده
            <textarea
              rows={3}
              value={form.abstract}
              onChange={(e) => setForm({ ...form, abstract: e.target.value })}
            />
          </label>
          <label>
            وضعیت
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
            >
              {Object.entries(STATUS_LABELS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            درصد پیشرفت
            <input
              type="number"
              min={0}
              max={100}
              value={form.progress_percent}
              onChange={(e) => setForm({ ...form, progress_percent: e.target.value })}
            />
          </label>
          <label>
            تاریخ شروع
            <PersianDateInput
              value={form.start_date}
              onChange={(v) => setForm({ ...form, start_date: v })}
            />
          </label>
          <label>
            تاریخ پایان
            <PersianDateInput
              value={form.end_date}
              onChange={(v) => setForm({ ...form, end_date: v })}
            />
          </label>
          <label>
            تاریخ و ساعت دفاع
            <PersianDateInput
              withTime
              value={form.defense_date}
              onChange={(v) => setForm({ ...form, defense_date: v })}
            />
          </label>
          <label>
            نتیجه دفاع
            <select
              value={form.defense_outcome}
              onChange={(e) => setForm({ ...form, defense_outcome: e.target.value })}
            >
              <option value="">ثبت نشده</option>
              {Object.entries(DEFENSE_OUTCOME_LABELS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          {form.defense_outcome && (
            <label>
              توضیحات نتیجه دفاع
              <textarea
                rows={2}
                value={form.defense_outcome_notes}
                onChange={(e) =>
                  setForm({ ...form, defense_outcome_notes: e.target.value })
                }
              />
            </label>
          )}
          <label>
            موعد گزارش هفتگی (برای یادآوری در رویدادهای پیش‌روی دانشجو)
            <select
              value={form.report_weekday}
              onChange={(e) => setForm({ ...form, report_weekday: e.target.value })}
            >
              <option value="">غیرفعال</option>
              {WEEKDAY_OPTIONS.map((w) => (
                <option key={w.value} value={w.value}>
                  هر {w.label}
                </option>
              ))}
            </select>
          </label>
          {form.report_weekday !== "" && (
            <label>
              ساعت موعد گزارش
              <input
                type="time"
                value={form.report_deadline_time}
                onChange={(e) => setForm({ ...form, report_deadline_time: e.target.value })}
              />
            </label>
          )}
          <div className="btn-row">
            <button className="btn btn-primary" type="submit">
              ذخیره
            </button>
            <button
              className="btn btn-secondary"
              type="button"
              onClick={() => setEditing(false)}
            >
              انصراف
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

function RequestProjectBox({ projectId }) {
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function handleRequest(e) {
    e.preventDefault();
    setError("");
    try {
      await client.post(`/projects/${projectId}/requests`, { message });
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || "خطا در ثبت درخواست");
    }
  }

  if (sent) {
    return <div className="alert alert-success">درخواست شما برای استاد ارسال شد.</div>;
  }

  return (
    <form className="card" onSubmit={handleRequest} style={{ marginTop: 16 }}>
      <h3>درخواست انتخاب این پروژه</h3>
      {error && <div className="alert alert-error">{error}</div>}
      <label>
        توضیح دلیل علاقه‌مندی (اختیاری)
        <textarea rows={2} value={message} onChange={(e) => setMessage(e.target.value)} />
      </label>
      <button className="btn btn-primary" type="submit">
        ارسال درخواست
      </button>
    </form>
  );
}

function RequestsTab({ project, onDecided }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const res = await client.get(`/projects/${project.id}/requests`);
    setRequests(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project.id]);

  async function decide(requestId, approve) {
    await client.patch(`/requests/${requestId}`, { approve });
    load();
    onDecided();
  }

  if (loading) return <p>در حال بارگذاری...</p>;
  if (requests.length === 0) return <p className="muted">درخواستی ثبت نشده است</p>;

  return (
    <div className="table-scroll">
    <table className="table">
      <thead>
        <tr>
          <th>دانشجو</th>
          <th>پیام</th>
          <th>وضعیت</th>
          <th>تاریخ</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {requests.map((r) => (
          <tr key={r.id}>
            <td>{r.student?.full_name}</td>
            <td>{r.message || "-"}</td>
            <td>{REQUEST_STATUS_LABELS[r.status]}</td>
            <td>{formatJalaliDate(r.requested_at)}</td>
            <td>
              {r.status === "pending" && (
                <div className="btn-row">
                  <button className="btn btn-primary btn-sm" onClick={() => decide(r.id, true)}>
                    تایید
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => decide(r.id, false)}
                  >
                    رد
                  </button>
                </div>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
    </div>
  );
}

function MeetingsTab({ projectId, isOwner }) {
  const [meetings, setMeetings] = useState([]);
  const [meetingRequests, setMeetingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ scheduled_at: "", location: "" });
  const [proposeForm, setProposeForm] = useState({
    scheduled_at: "",
    location: "",
    message: "",
  });
  const [reportDrafts, setReportDrafts] = useState({});

  async function load() {
    setLoading(true);
    const [meetingsRes, requestsRes] = await Promise.all([
      client.get(`/projects/${projectId}/meetings`),
      client.get(`/projects/${projectId}/meeting-requests`),
    ]);
    setMeetings(meetingsRes.data);
    setMeetingRequests(requestsRes.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleCreate(e) {
    e.preventDefault();
    await client.post(`/projects/${projectId}/meetings`, form);
    setForm({ scheduled_at: "", location: "" });
    load();
  }

  async function handlePropose(e) {
    e.preventDefault();
    await client.post(`/projects/${projectId}/meeting-requests`, proposeForm);
    setProposeForm({ scheduled_at: "", location: "", message: "" });
    load();
  }

  async function decideRequest(requestId, approve) {
    await client.patch(`/meeting-requests/${requestId}`, { approve });
    load();
  }

  async function saveReport(meetingId) {
    const report = reportDrafts[meetingId];
    if (!report) return;
    await client.patch(`/meetings/${meetingId}`, { report });
    load();
  }

  if (loading) return <p>در حال بارگذاری...</p>;

  const pendingRequests = meetingRequests.filter((r) => r.status === "pending");

  return (
    <div>
      {isOwner && pendingRequests.length > 0 && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3>درخواست‌های زمان جلسه از دانشجو</h3>
          {pendingRequests.map((r) => (
            <div key={r.id} className="btn-row" style={{ marginBottom: 8 }}>
              <div>
                <strong>{formatJalaliDateTime(r.scheduled_at)}</strong>
                {r.location && <span className="muted"> — {r.location}</span>}
                {r.message && <div className="muted">{r.message}</div>}
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => decideRequest(r.id, true)}
              >
                تایید
              </button>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => decideRequest(r.id, false)}
              >
                رد
              </button>
            </div>
          ))}
        </div>
      )}

      {isOwner && (
        <form className="card" onSubmit={handleCreate} style={{ marginBottom: 16 }}>
          <h3>تعیین زمان جلسه جدید</h3>
          <label>
            زمان جلسه
            <PersianDateInput
              withTime
              required
              value={form.scheduled_at}
              onChange={(v) => setForm({ ...form, scheduled_at: v })}
            />
          </label>
          <label>
            مکان / لینک
            <input
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
            />
          </label>
          <button className="btn btn-primary" type="submit">
            ثبت جلسه
          </button>
        </form>
      )}

      {!isOwner && (
        <form className="card" onSubmit={handlePropose} style={{ marginBottom: 16 }}>
          <h3>پیشنهاد زمان جلسه</h3>
          <label>
            زمان پیشنهادی
            <PersianDateInput
              withTime
              required
              value={proposeForm.scheduled_at}
              onChange={(v) => setProposeForm({ ...proposeForm, scheduled_at: v })}
            />
          </label>
          <label>
            مکان / لینک
            <input
              value={proposeForm.location}
              onChange={(e) =>
                setProposeForm({ ...proposeForm, location: e.target.value })
              }
            />
          </label>
          <label>
            توضیح (اختیاری)
            <input
              value={proposeForm.message}
              onChange={(e) =>
                setProposeForm({ ...proposeForm, message: e.target.value })
              }
            />
          </label>
          <button className="btn btn-primary" type="submit">
            ارسال پیشنهاد
          </button>
        </form>
      )}

      {!isOwner && meetingRequests.length > 0 && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3>پیشنهادهای من</h3>
          {meetingRequests.map((r) => (
            <div key={r.id} className="btn-row" style={{ marginBottom: 8 }}>
              <span>{formatJalaliDateTime(r.scheduled_at)}</span>
              <span className={`badge badge-request-${r.status}`}>
                {REQUEST_STATUS_LABELS[r.status]}
              </span>
            </div>
          ))}
        </div>
      )}

      {meetings.length === 0 && <p className="muted">جلسه‌ای ثبت نشده است</p>}
      {meetings.map((m) => (
        <div className="card" key={m.id} style={{ marginBottom: 12 }}>
          <strong>{formatJalaliDateTime(m.scheduled_at)}</strong>
          {m.location && <div className="muted">{m.location}</div>}
          {m.report ? (
            <p>{m.report}</p>
          ) : (
            <p className="muted">گزارشی برای این جلسه ثبت نشده است</p>
          )}
          {isOwner && (
            <div className="btn-row">
              <input
                placeholder="ثبت گزارش جلسه..."
                value={reportDrafts[m.id] ?? m.report ?? ""}
                onChange={(e) =>
                  setReportDrafts({ ...reportDrafts, [m.id]: e.target.value })
                }
              />
              <button className="btn btn-secondary btn-sm" onClick={() => saveReport(m.id)}>
                ذخیره گزارش
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function ReportsTab({ projectId, isOwner }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [content, setContent] = useState("");
  const [reportFile, setReportFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [commentDrafts, setCommentDrafts] = useState({});

  async function load() {
    setLoading(true);
    const res = await client.get(`/projects/${projectId}/reports`);
    setReports(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function submitReport(e) {
    e.preventDefault();
    if (!content.trim()) return;
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("content", content);
      if (reportFile) formData.append("file", reportFile);
      await client.post(`/projects/${projectId}/reports`, formData);
      setContent("");
      setReportFile(null);
      load();
    } finally {
      setSubmitting(false);
    }
  }

  async function saveComment(reportId) {
    const comment = commentDrafts[reportId];
    if (!comment) return;
    await client.patch(`/reports/${reportId}`, { professor_comment: comment });
    load();
  }

  async function downloadAttachment(reportId, filename) {
    await openOrDownloadFile(`/reports/${reportId}/download`, filename);
  }

  if (loading) return <p>در حال بارگذاری...</p>;

  return (
    <div>
      {!isOwner && (
        <form className="card" onSubmit={submitReport} style={{ marginBottom: 16 }}>
          <h3>ثبت گزارش هفتگی</h3>
          <textarea
            rows={3}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="پیشرفت این هفته را بنویسید..."
          />
          <label>
            پیوست فایل (اختیاری)
            <input
              type="file"
              onChange={(e) => setReportFile(e.target.files[0] || null)}
            />
          </label>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "در حال ارسال..." : "ارسال گزارش"}
          </button>
        </form>
      )}

      {reports.length === 0 && <p className="muted">گزارشی ثبت نشده است</p>}
      {reports.map((r) => (
        <div className="card" key={r.id} style={{ marginBottom: 12 }}>
          <div className="muted">{formatJalaliDateTime(r.created_at)}</div>
          <p>{r.content}</p>
          {r.attachment_original_filename && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => downloadAttachment(r.id, r.attachment_original_filename)}
            >
              📎 {isPreviewable(r.attachment_original_filename) ? "مشاهده" : "دانلود"} «
              {r.attachment_original_filename}»
            </button>
          )}
          {r.professor_comment && (
            <div className="callout">نظر استاد: {r.professor_comment}</div>
          )}
          {isOwner && !r.professor_comment && (
            <div className="btn-row">
              <input
                placeholder="نظر خود را بنویسید..."
                value={commentDrafts[r.id] ?? ""}
                onChange={(e) =>
                  setCommentDrafts({ ...commentDrafts, [r.id]: e.target.value })
                }
              />
              <button className="btn btn-secondary btn-sm" onClick={() => saveComment(r.id)}>
                ثبت نظر
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function GradesTab({ project, isOwner, onGradesChanged }) {
  const projectId = project.id;
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ stage: "", score: "", comment: "" });
  const [editingStage, setEditingStage] = useState(null);

  async function load() {
    setLoading(true);
    const res = await client.get(`/projects/${projectId}/grades`);
    setGrades(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleSubmit(e) {
    e.preventDefault();
    await client.post(`/projects/${projectId}/grades`, {
      ...form,
      score: Number(form.score),
    });
    setForm({ stage: "", score: "", comment: "" });
    setEditingStage(null);
    load();
    onGradesChanged();
  }

  function startEdit(grade) {
    setEditingStage(grade.stage);
    setForm({ stage: grade.stage, score: String(grade.score), comment: grade.comment || "" });
  }

  function cancelEdit() {
    setEditingStage(null);
    setForm({ stage: "", score: "", comment: "" });
  }

  if (loading) return <p>در حال بارگذاری...</p>;

  return (
    <div>
      <div className="card final-grade-card">
        <div className="stat-value">
          {project.average_grade != null ? project.average_grade : "-"}
        </div>
        <div className="stat-label">
          نمره نهایی (میانگین {project.grade_count} مرحله)
        </div>
      </div>

      {isOwner && (
        <form className="card" onSubmit={handleSubmit} style={{ margin: "16px 0" }}>
          <h3>{editingStage ? `ویرایش نمره «${editingStage}»` : "ثبت نمره مرحله"}</h3>
          <label>
            نام مرحله
            <input
              required
              disabled={!!editingStage}
              value={form.stage}
              onChange={(e) => setForm({ ...form, stage: e.target.value })}
              placeholder="مثلا: پروپوزال، میان‌ترم، دفاع نهایی"
            />
          </label>
          <label>
            نمره (۰ تا ۱۰۰)
            <input
              type="number"
              min={0}
              max={100}
              required
              value={form.score}
              onChange={(e) => setForm({ ...form, score: e.target.value })}
            />
          </label>
          <label>
            توضیح
            <textarea
              rows={2}
              value={form.comment}
              onChange={(e) => setForm({ ...form, comment: e.target.value })}
            />
          </label>
          <div className="btn-row">
            <button className="btn btn-primary" type="submit">
              {editingStage ? "ذخیره تغییرات" : "ثبت نمره"}
            </button>
            {editingStage && (
              <button className="btn btn-secondary" type="button" onClick={cancelEdit}>
                انصراف
              </button>
            )}
          </div>
        </form>
      )}

      {grades.length === 0 && <p className="muted">نمره‌ای ثبت نشده است</p>}
      {grades.length > 0 && (
        <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>مرحله</th>
              <th>نمره</th>
              <th>توضیح</th>
              <th>تاریخ</th>
              {isOwner && <th></th>}
            </tr>
          </thead>
          <tbody>
            {grades.map((g) => (
              <tr key={g.id}>
                <td>{g.stage}</td>
                <td>{g.score}</td>
                <td>{g.comment || "-"}</td>
                <td>{formatJalaliDate(g.graded_at)}</td>
                {isOwner && (
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => startEdit(g)}>
                      ویرایش
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      )}
    </div>
  );
}

function FilesTab({ projectId }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const [description, setDescription] = useState("");
  const [uploading, setUploading] = useState(false);

  async function load() {
    setLoading(true);
    const res = await client.get(`/projects/${projectId}/files`);
    setFiles(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleUpload(e) {
    e.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("description", description);
    try {
      await client.post(`/projects/${projectId}/files`, formData);
      setSelectedFile(null);
      setDescription("");
      load();
    } finally {
      setUploading(false);
    }
  }

  async function download(fileId, filename) {
    await openOrDownloadFile(`/files/${fileId}/download`, filename);
  }

  if (loading) return <p>در حال بارگذاری...</p>;

  return (
    <div>
      <form className="card" onSubmit={handleUpload} style={{ marginBottom: 16 }}>
        <h3>بارگذاری فایل</h3>
        <input
          type="file"
          onChange={(e) => setSelectedFile(e.target.files[0])}
          required
        />
        <input
          placeholder="توضیح فایل (اختیاری)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={uploading}>
          {uploading ? "در حال بارگذاری..." : "بارگذاری"}
        </button>
      </form>

      {files.length === 0 && <p className="muted">فایلی بارگذاری نشده است</p>}
      <div className="table-scroll">
      <table className="table">
        <thead>
          <tr>
            <th>نام فایل</th>
            <th>نوع</th>
            <th>توضیح</th>
            <th>تاریخ</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {files.map((f) => (
            <tr key={f.id}>
              <td>{f.original_filename}</td>
              <td>{f.category === "required" ? "موردنیاز (استاد)" : "تحویلی (دانشجو)"}</td>
              <td>{f.description || "-"}</td>
              <td>{formatJalaliDate(f.uploaded_at)}</td>
              <td>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => download(f.id, f.original_filename)}
                >
                  {isPreviewable(f.original_filename) ? "مشاهده" : "دانلود"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}

function MessagesTab({ project, currentUser }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [content, setContent] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [sending, setSending] = useState(false);

  const recipientId =
    currentUser.role === "professor" ? project.student_id : project.professor_id;

  async function load() {
    setLoading(true);
    const res = await client.get(`/projects/${project.id}/messages`);
    setMessages(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project.id]);

  async function handleSend(e) {
    e.preventDefault();
    if (!content.trim() && !attachment) return;
    setSending(true);
    try {
      const formData = new FormData();
      formData.append("recipient_id", recipientId);
      formData.append("content", content);
      if (attachment) formData.append("file", attachment);
      await client.post(`/projects/${project.id}/messages`, formData);
      setContent("");
      setAttachment(null);
      load();
    } finally {
      setSending(false);
    }
  }

  async function downloadAttachment(messageId, filename) {
    await openOrDownloadFile(`/messages/${messageId}/download`, filename);
  }

  if (loading) return <p>در حال بارگذاری...</p>;

  return (
    <div className="card">
      <div className="message-list">
        {messages.length === 0 && <p className="muted">پیامی وجود ندارد</p>}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`message-bubble ${
              m.sender_id === currentUser.id ? "message-mine" : "message-theirs"
            }`}
          >
            <div className="message-sender">{m.sender?.full_name}</div>
            {m.content && <div>{m.content}</div>}
            {m.attachment_original_filename && (
              <button
                type="button"
                className="btn btn-secondary btn-sm message-attachment-btn"
                onClick={() => downloadAttachment(m.id, m.attachment_original_filename)}
                title={
                  isPreviewable(m.attachment_original_filename)
                    ? "مشاهده فایل"
                    : "دانلود فایل"
                }
              >
                📎 {m.attachment_original_filename}
              </button>
            )}
            <div className="message-time">{formatJalaliDateTime(m.sent_at)}</div>
          </div>
        ))}
      </div>
      {recipientId ? (
        <form onSubmit={handleSend} style={{ marginTop: 12 }}>
          {attachment && (
            <div className="attachment-preview">
              📎 {attachment.name}
              <button
                type="button"
                className="link-btn"
                onClick={() => setAttachment(null)}
              >
                حذف
              </button>
            </div>
          )}
          <div className="btn-row">
            <input
              style={{ flex: 1 }}
              placeholder="پیام خود را بنویسید..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <label className="btn btn-secondary" title="پیوست فایل">
              📎
              <input
                type="file"
                hidden
                onChange={(e) => setAttachment(e.target.files[0] || null)}
              />
            </label>
            <button className="btn btn-primary" type="submit" disabled={sending}>
              {sending ? "..." : "ارسال"}
            </button>
          </div>
        </form>
      ) : (
        <p className="muted">هنوز طرف مقابلی برای این پروژه تعیین نشده است</p>
      )}
    </div>
  );
}
