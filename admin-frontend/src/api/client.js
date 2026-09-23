const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handle(response) {
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(text || `Request failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchComplaints({ status, issueType } = {}) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (issueType) params.set("issue_type", issueType);
  const query = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_URL}/complaints${query}`);
  return handle(response);
}

export async function fetchStats() {
  const response = await fetch(`${API_URL}/complaints/stats/summary`);
  return handle(response);
}

export async function updateStatus(id, status) {
  const response = await fetch(`${API_URL}/complaints/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });
  return handle(response);
}
