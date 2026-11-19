const API = "http://127.0.0.1:8765/api/v1";
const TOKEN = "dev-local-token";

export type ScanDecision = {
  scan_id: string;
  action_id: string;
  decision: string;
  findings: Array<{
    id: string;
    category: string;
    severity: string;
    excerpt_redacted: string;
    explanation_redacted: string;
    anchor: Record<string, unknown>;
  }>;
};

async function headers(): Promise<HeadersInit> {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${TOKEN}`,
  };
}

export async function scanText(
  actionId: string,
  content: string,
): Promise<ScanDecision> {
  const r = await fetch(`${API}/scans/text`, {
    method: "POST",
    headers: await headers(),
    body: JSON.stringify({
      action_id: actionId,
      source: "local-demo-chat",
      destination_origin: "http://127.0.0.1:5174",
      modality: "text",
      content,
    }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function scanImage(
  actionId: string,
  file: File,
): Promise<ScanDecision> {
  const fd = new FormData();
  fd.append("action_id", actionId);
  fd.append("file", file);
  const r = await fetch(`${API}/scans/image`, {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}` },
    body: fd,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function redactText(
  actionId: string,
  content: string,
  scan: ScanDecision,
): Promise<string> {
  const r = await fetch(`${API}/redactions`, {
    method: "POST",
    headers: await headers(),
    body: JSON.stringify({
      action_id: actionId,
      modality: "text",
      content_text: content,
      finding_ids: scan.findings.map((f) => f.id),
      findings: scan.findings,
    }),
  });
  const data = await r.json();
  return data.sanitized_text as string;
}

export async function verifyText(
  actionId: string,
  content: string,
): Promise<ScanDecision> {
  const r = await fetch(`${API}/scans/verify-text`, {
    method: "POST",
    headers: await headers(),
    body: JSON.stringify({ content, action_id: actionId }),
  });
  return r.json();
}