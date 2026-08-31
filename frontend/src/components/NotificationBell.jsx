import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client.js";
import { formatJalaliDateTime } from "../utils/date.js";

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const navigate = useNavigate();

  async function load() {
    try {
      const res = await client.get("/notifications");
      setNotifications(res.data);
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 20000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  async function markRead(id) {
    await client.post(`/notifications/${id}/read`);
    load();
  }

  async function markAllRead() {
    await client.post("/notifications/read-all");
    load();
  }

  async function handleNotifClick(n) {
    if (!n.is_read) {
      await client.post(`/notifications/${n.id}/read`);
      load();
    }
    setOpen(false);
    if (n.link) {
      navigate(n.link);
    }
  }

  return (
    <div className="notif-bell" ref={ref}>
      <button className="notif-bell-btn" onClick={() => setOpen((o) => !o)}>
        🔔
        {unreadCount > 0 && <span className="notif-badge">{unreadCount}</span>}
      </button>
      {open && (
        <div className="notif-dropdown">
          <div className="notif-dropdown-header">
            <strong>اعلان‌ها</strong>
            {unreadCount > 0 && (
              <button className="link-btn" onClick={markAllRead}>
                همه را خوانده شد علامت بزن
              </button>
            )}
          </div>
          {notifications.length === 0 && (
            <div className="notif-empty">اعلانی وجود ندارد</div>
          )}
          {notifications.slice(0, 15).map((n) => (
            <div
              key={n.id}
              className={`notif-item ${n.is_read ? "" : "notif-unread"}`}
              onClick={() => handleNotifClick(n)}
            >
              <div>{n.content}</div>
              <div className="notif-time">{formatJalaliDateTime(n.created_at)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
