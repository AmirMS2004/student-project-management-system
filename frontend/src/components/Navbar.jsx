import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";
import { ROLE_LABELS } from "../constants.js";
import NotificationBell from "./NotificationBell.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  function handleLogout() {
    setMenuOpen(false);
    logout();
    navigate("/login");
  }

  return (
    <header className="navbar">
      <div className="navbar-inner container">
        <Link to="/" className="brand" onClick={() => setMenuOpen(false)}>
          سامانه پروژه‌های دانشجویی
        </Link>
        <button
          className="hamburger-btn"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="باز کردن منو"
        >
          {menuOpen ? "✕" : "☰"}
        </button>
        <div className={`navbar-menu ${menuOpen ? "navbar-menu-open" : ""}`}>
          {user && user.role === "admin" && (
            <nav className="nav-links">
              <Link to="/admin">داشبورد مدیریت</Link>
              <Link to="/admin/users">کاربران</Link>
              <Link to="/admin/settings">تنظیمات</Link>
              <Link to="/profile">پروفایل</Link>
            </nav>
          )}
          {user && user.role !== "admin" && (
            <nav className="nav-links">
              <Link to="/">خانه</Link>
              <Link to="/projects">پروژه‌ها</Link>
              <Link to="/calendar">رویدادهای پیش‌رو</Link>
              {user.role === "professor" && <Link to="/stats">داشبورد آماری</Link>}
              <Link to="/profile">پروفایل</Link>
            </nav>
          )}
          <div className="navbar-right">
            <button
              className="theme-toggle-btn"
              onClick={toggleTheme}
              title={theme === "dark" ? "حالت روشن" : "حالت تاریک"}
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
            {user ? (
              <>
                <NotificationBell />
                <Link to="/profile" className="user-chip user-chip-link">
                  {user.full_name} ({ROLE_LABELS[user.role]})
                </Link>
                <button className="btn btn-secondary" onClick={handleLogout}>
                  خروج
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-secondary">
                  ورود
                </Link>
                <Link to="/register" className="btn btn-primary">
                  ثبت‌نام
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
