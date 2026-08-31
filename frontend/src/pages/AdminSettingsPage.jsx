import React, { useEffect, useState } from "react";
import client from "../api/client.js";

export default function AdminSettingsPage() {
  const [inviteCode, setInviteCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    client.get("/admin/settings").then((res) => {
      setInviteCode(res.data.professor_invite_code);
      setLoading(false);
    });
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess(false);
    setSaving(true);
    try {
      const res = await client.patch("/admin/settings", {
        professor_invite_code: inviteCode,
      });
      setInviteCode(res.data.professor_invite_code);
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || "خطا در ذخیره تغییرات");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="page-loading">در حال بارگذاری...</div>;

  return (
    <div>
      <h1>تنظیمات سامانه</h1>
      <form className="card" onSubmit={handleSubmit} style={{ maxWidth: 460 }}>
        <h3>کد دعوت ثبت‌نام استاد</h3>
        <p className="muted" style={{ marginTop: -6 }}>
          هرکس در فرم ثبت‌نام نقش «استاد راهنما» را انتخاب کند، برای تکمیل ثبت‌نام باید همین کد
          را وارد کند. این کد را فقط در اختیار اساتید واقعی قرار دهید و در صورت لو رفتن، همین‌جا
          تغییرش دهید.
        </p>
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">کد دعوت به‌روزرسانی شد.</div>}
        <label>
          کد دعوت فعلی
          <input
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value)}
            minLength={4}
            maxLength={100}
            required
          />
        </label>
        <button className="btn btn-primary" type="submit" disabled={saving}>
          {saving ? "در حال ذخیره..." : "ذخیره تغییرات"}
        </button>
      </form>
    </div>
  );
}
