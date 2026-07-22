import { createContext, useContext, useEffect, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);
export function AuthProvider({children}) {
  const [user, setUser] = useState(null);
  const [avatarRevision, setAvatarRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);
  useEffect(() => {
    function sessionEnded(event) {
      setUser(null);
      setSessionExpired(event.detail?.reason === "expired");
    }
    window.addEventListener("auth:session-ended", sessionEnded);
    if (!localStorage.getItem("access_token")) {
      setLoading(false);
      return () => window.removeEventListener("auth:session-ended", sessionEnded);
    }
    api.get("/auth/me/")
      .then(({data}) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
    return () => window.removeEventListener("auth:session-ended", sessionEnded);
  }, []);
  async function login(email, password) {
    const {data} = await api.post("/auth/login/", {email, password});
    localStorage.setItem("access_token", data.access); localStorage.setItem("refresh_token", data.refresh);
    const profile = await api.get("/auth/me/"); setUser(profile.data); setSessionExpired(false); return profile.data;
  }
  function updateUser(nextUser, {avatarChanged = false} = {}) {
    setUser(nextUser);
    if (avatarChanged) setAvatarRevision(Date.now());
  }
  async function logout() {
    const refresh = localStorage.getItem("refresh_token");
    try { if (refresh) await api.post("/auth/logout/", {refresh}); } catch { /* Local logout must always succeed. */ }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    setSessionExpired(false);
  }
  return <AuthContext.Provider value={{user, loading, login, logout, setUser, updateUser, avatarRevision, sessionExpired}}>{children}</AuthContext.Provider>;
}
export const useAuth = () => useContext(AuthContext);
