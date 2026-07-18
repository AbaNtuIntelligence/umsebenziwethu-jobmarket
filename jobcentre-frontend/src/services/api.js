import axios from "axios";

const api = axios.create({baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api"});
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use((response) => response, async (error) => {
  const original = error.config;
  if (error.response?.status === 401 && !original?._retry && localStorage.getItem("refresh_token")) {
    original._retry = true;
    try {
      const {data} = await axios.post(`${api.defaults.baseURL}/auth/token/refresh/`, {refresh: localStorage.getItem("refresh_token")});
      localStorage.setItem("access_token", data.access);
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch { localStorage.removeItem("access_token"); localStorage.removeItem("refresh_token"); }
  }
  return Promise.reject(error);
});
export default api;

export function mediaUrl(value, cacheKey) {
  if (!value) return null;
  if (/^(blob:|data:)/i.test(value)) return value;
  const resolved = new URL(value, `${new URL(api.defaults.baseURL, window.location.origin).origin}/`);
  if (cacheKey) resolved.searchParams.set("v", cacheKey);
  return resolved.toString();
}

export function errorMessage(error) {
  const data = error.response?.data?.errors || error.response?.data;
  if (!data) return "Could not connect to the server.";
  if (typeof data === "string") return data;
  return Object.entries(data).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(" ") : value}`).join(" ");
}
