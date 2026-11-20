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
  opts?: { image_base64?: string; context_hint?: string },
) {
  const r = await fetch(`${API}/inspector/ask`, {
    method: "POST",
    headers: h(),
    body: JSON.stringify({
      question,
      content_text,
      modality,
      image_base64: opts?.image_base64,
      context_hint: opts?.context_hint,
    }),
  });
  return r.json();
}

export type HackathonDemoItem = {
  id: string;
  modality: string;
  file: string;
  sample_question: string;
  abstention_question?: string;
  context_hint?: string;
};

export async function fetchHackathonManifest(): Promise<{ items: HackathonDemoItem[] }> {
  const r = await fetch(`${API}/demo/hackathon-manifest`, { headers: h() });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function fetchDemoFixtureBlob(filename: string): Promise<Blob> {
  const r = await fetch(`${API}/demo/fixtures/${encodeURIComponent(filename)}`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
  });
  if (!r.ok) throw new Error(await r.text());
  return r.blob();
}

export async function fetchDemoFixtureText(filename: string): Promise<string> {
  const blob = await fetchDemoFixtureBlob(filename);
  return blob.text();
}

export type IngestResult = {
  sound_events?: string[];
  models_used?: string[];
  modality: string;
  filename: string;
  extracted_preview: string;
  char_count: number;
  findings: Array<{
    id: string;
    category: string;
    severity: string;
    excerpt_redacted: string;
  }>;
  notes?: string | null;
  sound_events?: string[];
  models_used?: string[];
};

export async function inspectorIngest(modality: string, file: File): Promise<IngestResult> {
  const fd = new FormData();
  fd.append("modality", modality);
  fd.append("file", file);
  const r = await fetch(`${API}/inspector/ingest`, {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}` },
    body: fd,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function inspectorCodeTask(prompt: string): Promise<{ id: string; code: string }> {
  const r = await fetch(`${API}/inspector/code-task`, {
    method: "POST",
    headers: h(),
    body: JSON.stringify({ prompt }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function runInspectorCode(taskId: string, code: string) {
  const r = await fetch(`${API}/inspector/code-task/${encodeURIComponent(taskId)}/run`, {
    method: "POST",
    headers: h(),
    body: JSON.stringify({ code }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}