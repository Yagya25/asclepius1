import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("apbi_access");
    if (!token) { setLoading(false); return; }
    api.get("/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => { localStorage.removeItem("apbi_access"); localStorage.removeItem("apbi_refresh"); })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email, password, remember) => {
    const { data } = await api.post("/auth/login", { email, password, remember });
    localStorage.setItem("apbi_access", data.access_token);
    localStorage.setItem("apbi_refresh", data.refresh_token);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (name, email, password, role) => {
    const { data } = await api.post("/auth/register", { name, email, password, role });
    localStorage.setItem("apbi_access", data.access_token);
    localStorage.setItem("apbi_refresh", data.refresh_token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async (allDevices = false) => {
    try { await api.post(allDevices ? "/auth/logout-all" : "/auth/logout"); } catch (e) {}
    localStorage.removeItem("apbi_access");
    localStorage.removeItem("apbi_refresh");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
