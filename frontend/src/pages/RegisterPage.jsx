import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone_number: "",
    password: "",
    role: "student",
    invite_code: "",
  });
  const [captcha, setCaptcha] = useState(null);
  const [captchaAnswer, setCaptchaAnswer] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadCaptcha() {
    const res = await client.get("/auth/captcha");
    setCaptcha(res.data);
    setCaptchaAnswer("");
  }

  useEffect(() => {
    loadCaptcha();
  }, []);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register({
        ...form,
        captcha_id: captcha.captcha_id,
        captcha_answer: captchaAnswer,
      });
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "خطا در ثبت‌نام");
      loadCaptcha();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={handleSubmit}>
        <h2>ثبت‌نام</h2>
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          نقش
          <select value={form.role} onChange={(e) => update("role", e.target.value)}>
            <option value="student">دانشجو</option>
            <option value="professor">استاد راهنما</option>
          </select>
        </label>
        <label>
          نام و نام خانوادگی
          <input
            value={form.full_name}
            onChange={(e) => update("full_name", e.target.value)}
            required
          />
        </label>
        <label>
          ایمیل
          <input
            type="email"
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
            required
          />
        </label>
        <label>
          شماره موبایل
          <input
            type="tel"
            placeholder="09123456789"
            pattern="^09\d{9}$"
            title="شماره موبایل باید به فرم 09xxxxxxxxx باشد"
            value={form.phone_number}
            onChange={(e) => update("phone_number", e.target.value)}
            required
          />
        </label>
        <label>
          رمز عبور
          <input
            type="password"
            minLength={6}
            value={form.password}
            onChange={(e) => update("password", e.target.value)}
            required
          />
        </label>
        {form.role === "professor" && (
          <label>
            کد دعوت استاد
            <input
              value={form.invite_code}
              onChange={(e) => update("invite_code", e.target.value)}
              placeholder="کدی که از مدیر گروه دریافت کرده‌اید"
              required
            />
          </label>
        )}
        <label>
          کد امنیتی
          {captcha && (
            <div className="captcha-row">
              <img
                className="captcha-img"
                src={`data:image/png;base64,${captcha.image_base64}`}
                alt="کد امنیتی"
              />
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={loadCaptcha}
                title="کد جدید"
              >
                🔄
              </button>
            </div>
          )}
          <input
            value={captchaAnswer}
            onChange={(e) => setCaptchaAnswer(e.target.value)}
            placeholder="کد داخل تصویر را وارد کنید"
            required
          />
        </label>
        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "در حال ثبت‌نام..." : "ثبت‌نام"}
        </button>
        <p className="auth-switch">
          قبلا ثبت‌نام کرده‌اید؟ <Link to="/login">ورود</Link>
        </p>
      </form>
    </div>
  );
}
