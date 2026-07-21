import { createContext, useContext, useEffect, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);
export function AuthProvider({children}) {
  const [user, setUser] = useState(null);
  const [avatarRevision, setAvatarRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!localStorage.getItem("access_token")) return setLoading(false);
    api.get("/auth/me/")
  .then(({ data }) => setUser(data))
  .catch(() => setUser(null))
  .finally(() => setLoading(false));
  }, []);
  async function login(email, password) {
    const {data} = await api.post("/auth/login/", {email, password});
    localStorage.setItem("access_token", data.access); localStorage.setItem("refresh_token", data.refresh);
    const profile = await api.get("/auth/me/"); setUser(profile.data); return profile.data;
  }
  function updateUser(nextUser, {avatarChanged = false} = {}) {
    setUser(nextUser);
    if (avatarChanged) setAvatarRevision(Date.now());
  }
  function logout() { localStorage.clear(); setUser(null); }
  return <AuthContext.Provider value={{user, loading, login, logout, setUser, updateUser, avatarRevision}}>{children}</AuthContext.Provider>;
}
export const useAuth = () => useContext(AuthContext);
