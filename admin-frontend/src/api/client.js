import { getToken, clearToken } from "./auth.js";

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

async function handle(response) {
  if (response.status === 401 || response.status === 403) {
    clearToken();
    window.location.reload();
    throw new Error("Session expired. Please sign in again.");
  }
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    let message = text;
    try { message = JSON.parse(text).detail || text; } catch { /* not JSON */ }
    throw new Error(message || `Request failed with status ${response.status}`);
  }
  return response.json();
}

// Turns a path like "/uploads/x.jpg" into a full URL the browser can load
export function fileUrl(path) {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `${API_URL}${path.startsWith("/") ? "" : "/"}${path}`;
}

export async function fetchComplaints({ status, issueType } = {}) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (issueType) params.set("issue_type", issueType);
  const query = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_URL}/complaints${query}`, { headers: authHeaders() });
  return handle(response);
}

export async function fetchStats() {
  const response = await fetch(`${API_URL}/complaints/stats/summary`, { headers: authHeaders() });
  return handle(response);
}

export async function fetchHotspots() {
  const response = await fetch(`${API_URL}/complaints/stats/hotspots`, { headers: authHeaders() });
  return handle(response);
}

export async function fetchExplanation(id) {
  const response = await fetch(`${API_URL}/complaints/${id}/explanation`, { headers: authHeaders() });
  return handle(response);
}

export async function updateStatus(id, status) {
  const response = await fetch(`${API_URL}/complaints/${id}/status`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ status })
  });
  return handle(response);
}

// Marks a complaint resolved. The after photo is optional.
export async function resolveComplaint(id, afterPhoto) {
  const form = new FormData();
  if (afterPhoto) form.append("after_photo", afterPhoto);
  const response = await fetch(`${API_URL}/complaints/${id}/resolve`, {
    method: "POST",
    headers: authHeaders(), // no Content-Type: the browser adds it with the boundary
    body: form
  });
  return handle(response);
}