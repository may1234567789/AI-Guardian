const STORAGE_KEY = "sentinelai-api-base-url";
const DEFAULT_API_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 12000;

export function getApiBaseUrl() {
  return localStorage.getItem(STORAGE_KEY) || DEFAULT_API_URL.replace(/\/+$/, "");
}

export function setApiBaseUrl(value) {
  const parsed = new URL(value.trim());
  if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error("Enter an HTTP or HTTPS base URL without credentials, query parameters, or a fragment.");
  }
  const normalized = parsed.toString().replace(/\/+$/, "");
  localStorage.setItem(STORAGE_KEY, normalized);
  return normalized;
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const message = payload?.detail || payload?.message || payload?.error || `Request failed (${response.status}).`;
      throw new Error(typeof message === "string" ? message : JSON.stringify(message));
    }
    return payload;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The backend did not respond within 12 seconds. Check the API URL and server status.");
    }
    if (error instanceof TypeError) {
      throw new Error(`Could not connect to the backend at ${getApiBaseUrl()}. Check that it is running and allows this origin.`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

function post(path, body) {
  return request(path, { method: "POST", body: JSON.stringify(body) });
}

export const healthCheck = () => request("/health");
export const getStats = () => request("/stats");
export const getEvaluationSummary = () => request("/evaluation/summary");
export const scanPrompt = (payload) => post("/scan", payload);
export const scanOutput = (payload) => post("/scan-output", payload);
export const checkAction = (payload) => post("/check-action", payload);
export const getEvents = (params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
  });
  return request(`/events${query.size ? `?${query}` : ""}`);
};
export const getEventDetails = (requestId) => request(`/events/${encodeURIComponent(requestId)}`);
