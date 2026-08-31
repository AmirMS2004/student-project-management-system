import React, { useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { ROLE_LABELS } from "../constants.js";

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <div>
      <h1>پروفایل من</h1>
      <div className="grid-2">
        <ProfileForm user={user} />
        <PasswordForm />
      </div>
    </div>
  );
}

function ProfileForm({ user }) {
  const { updateProfile } = useAuth();
  const [form, setForm] = useState({
    full_name: user.full_name,
    email: user.email,
    phone_number: user.phone_number,
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess(false);
    setSubmitting(true);
    try {
      await updateProfile(form);
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || "خطا در ذخیره تغییرات");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h3>اطلاعات حساب</h3>
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">تغییرات ذخیره شد.</div>}
      <label>
        نام و نام خانوادگی
        <input
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          required
        />
      </label>
      <label>
        ایمیل
        <input
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
      </label>
      <label>
        شماره موبایل
        <input
          type="tel"
          pattern="^09\d{9}$"
          title="شماره موبایل باید به فرم 09xxxxxxxxx باشد"
          value={form.phone_number}
          onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
          required
        />
      </label>
      <label>
        نقش
        <input value={ROLE_LABELS[user.role]} disabled />
      </label>
      <button className="btn btn-primary" type="submit" disabled={submitting}>
        {submitting ? "در حال ذخیره..." : "ذخیره تغییرات"}
      </button>
    </form>
  );
}

function PasswordForm() {
  const { changePassword } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (newPassword !== confirmPassword) {
      setError("رمز عبور جدید و تکرار آن یکسان نیستند");
      return;
    }

    setSubmitting(true);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || "خطا در تغییر رمز عبور");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h3>تغییر رمز عبور</h3>
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">رمز عبور با موفقیت تغییر کرد.</div>}
      <label>
        رمز عبور فعلی
        <input
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
        />
      </label>
      <label>
        رمز عبور جدید
        <input
          type="password"
          minLength={6}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
        />
      </label>
      <label>
        تکرار رمز عبور جدید
        <input
          type="password"
          minLength={6}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
      </label>
      <button className="btn btn-primary" type="submit" disabled={submitting}>
        {submitting ? "در حال تغییر..." : "تغییر رمز عبور"}
      </button>
    </form>
  );
}
