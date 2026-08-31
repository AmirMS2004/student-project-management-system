import React, { useEffect, useState } from "react";
import client from "../api/client.js";
import { ROLE_LABELS } from "../constants.js";
import { formatJalaliDate } from "../utils/date.js";

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [roleFilter, setRoleFilter] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const params = roleFilter ? { role: roleFilter } : {};
    const res = await client.get("/admin/users", { params });
    setUsers(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roleFilter]);

  return (
    <div>
      <h1>کاربران سامانه</h1>
      <div className="filter-row">
        <label className="filter-label">
          نقش
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="">همه</option>
            <option value="professor">استاد</option>
            <option value="student">دانشجو</option>
            <option value="admin">مدیر گروه</option>
          </select>
        </label>
      </div>

      {loading ? (
        <p>در حال بارگذاری...</p>
      ) : users.length === 0 ? (
        <p className="muted">کاربری یافت نشد</p>
      ) : (
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th>نام</th>
                <th>ایمیل</th>
                <th>شماره موبایل</th>
                <th>نقش</th>
                <th>تاریخ عضویت</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>{u.phone_number}</td>
                  <td>
                    <span className={`badge badge-role-${u.role}`}>
                      {ROLE_LABELS[u.role]}
                    </span>
                  </td>
                  <td>{formatJalaliDate(u.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
