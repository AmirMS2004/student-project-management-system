import React, { createContext, useContext, useEffect, useState } from "react";
import client from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    client
      .get("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem("token");
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    const res = await client.post("/auth/login", { email, password });
    localStorage.setItem("token", res.data.access_token);
    setUser(res.data.user);
    return res.data.user;
  }

  async function register(payload) {
    const res = await client.post("/auth/register", payload);
    localStorage.setItem("token", res.data.access_token);
    setUser(res.data.user);
    return res.data.user;
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
  }

  async function updateProfile(payload) {
    const res = await client.patch("/auth/me", payload);
    setUser(res.data);
    return res.data;
  }

  async function changePassword(currentPassword, newPassword) {
    await client.post("/auth/me/password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, updateProfile, changePassword }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
