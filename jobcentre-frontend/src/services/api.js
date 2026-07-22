import axios from "axios";

const api = axios.create({baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api"});
let refreshPromise = null;

function clearAuth(reason = "expired") {
  const hadSession = Boolean(localStorage.getItem("access_token") || localStorage.getItem("refresh_token"));
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  if (hadSession) window.dispatchEvent(new CustomEvent("auth:session-ended", {detail: {reason}}));
}

function requestPath(config) {
  return new URL(config.url || "", `${api.defaults.baseURL}/`).pathname;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  const method = (config.method || "get").toLowerCase();
  const path = requestPath(config);
  const isPublicJobRead = method === "get" && /\/jobs(?:\/\d+)?\/$/.test(path);
  const isPublicAuth = /\/auth\/(?:login|logout|register|token\/refresh|password-reset|password-reset-confirm)\/$/.test(path);
  if (token && !isPublicJobRead && !isPublicAuth) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use((response) => response, async (error) => {
  const original = error.config;
  const path = original ? requestPath(original) : "";
  const isPublicAuth = /\/auth\/(?:login|logout|register|token\/refresh)\/$/.test(path);
  const refreshToken = localStorage.getItem("refresh_token");

  if (error.response?.status === 401 && !isPublicAuth && !original?._retry && refreshToken) {
    original._retry = true;
    try {
      if (!refreshPromise) {
        refreshPromise = axios.post(`${api.defaults.baseURL}/auth/token/refresh/`, {refresh: refreshToken})
          .finally(() => { refreshPromise = null; });
      }
      const {data} = await refreshPromise;
      localStorage.setItem("access_token", data.access);
      if (data.refresh) localStorage.setItem("refresh_token", data.refresh);
      original.headers = original.headers || {};
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch {
      clearAuth("expired");
    }
  } else if (error.response?.status === 401 && !isPublicAuth && !refreshToken) {
    clearAuth("expired");
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
  const responseData = error.response?.data;
  if (typeof responseData?.detail === "string") return responseData.detail;
  const data = responseData?.errors || responseData;
  if (!data) return "Could not connect to the server.";
  if (typeof data === "string") return data;
  const messages = [];
  function collect(value, label = "") {
    if (typeof value === "string" || typeof value === "number") {
      messages.push(label ? `${label}: ${value}` : String(value));
    } else if (Array.isArray(value)) {
      value.forEach((item) => collect(item, label));
    } else if (value && typeof value === "object") {
      Object.entries(value).forEach(([key, nested]) => collect(nested, key === "non_field_errors" ? "" : key));
    }
  }
  collect(data);
  return messages.join(" ") || "Request failed. Please try again.";
}
