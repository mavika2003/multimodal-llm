const API = "http://127.0.0.1:8765/api/v1";
const TOKEN = "dev-local-token";

const h = (): HeadersInit => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${TOKEN}`,
});

export async function fetchHealth() {
  const r = await fetch(`${API}/health`);
  return r.json();
}

export async function fetchAnalytics() {
  const r = await fetch(`${API}/analytics/summary`, { headers: h() });
  return r.json();
}

export async function fetchIncidents() {
  const r = await fetch(`${API}/incidents`, { headers: h() });
  return r.json();
}

export async function fetchIncident(id: string) {
  const r = await fetch(`${API}/incidents/${id}`, { headers: h() });
  return r.json();
}

export async function triageIncident(id: string, review_status: string) {
  const r = await fetch(`${API}/incidents/${id}/triage`, {
    method: "PATCH",
    headers: h(),
    body: JSON.stringify({ review_status }),
  });
  return r.json();
}

export async function inspectorAsk(
  question: string,
  content_text?: string,
  modality = "document",
) {
  const r = await fetch(`${API}/inspector/ask`, {
    method: "POST",
    headers: h(),
    body: JSON.stringify({ question, content_text, modality }),
  });
  return r.json();
}