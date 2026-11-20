const API = "http://127.0.0.1:8765/api/v1";
const TOKEN = "dev-local-token";
const DASHBOARD_ORIGIN = "http://127.0.0.1:5173";

/** Video scans may run Whisper + VLM locally; allow generous client timeout. */
const VIDEO_SCAN_TIMEOUT_MS = 12 * 60 * 1000;
const DEFAULT_SCAN_TIMEOUT_MS = 3 * 60 * 1000;

export type ScanDecision = {
  scan_id: string;
  action_id: string;
  decision: string;
  modality?: string;
  filename?: string;
  extracted_text?: string;
  scan_error_code?: string;
  scan_request_id?: string;
  stages_ms?: Record<string, number>;
  findings: Array<{
    id: string;
    category: string;
    severity: string;
    excerpt_redacted: string;
    explanation_redacted: string;
    anchor: Record<string, unknown>;
  }>;
};

export class ScanError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function headers(): Promise<HeadersInit> {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${TOKEN}`,
  };
}

async function throwScanHttpError(r: Response): Promise<never> {
  const body = await r.text();
  if (r.status === 413) {
    throw new ScanError("FILE_TOO_LARGE", "File exceeds server size limit (25MB).", 413);
  }
  if (r.status === 401 || r.status === 403) {
    throw new ScanError("UNAUTHORIZED", "API auth or origin rejected the request.", r.status);
  }
  if (r.status === 503) {
    try {
      const j = JSON.parse(body) as { detail?: { error_code?: string; message?: string } };
      const d = j.detail;
      throw new ScanError(
        d?.error_code ?? "SCAN_FAILED",
        d?.message ?? "Server could not finish scan.",
        503,
      );
    } catch (e) {
      if (e instanceof ScanError) throw e;
      throw new ScanError("SCAN_FAILED", body || "Server scan failed.", 503);
    }
  }
  throw new ScanError("HTTP_ERROR", body || `HTTP ${r.status}`, r.status);
}

function timeoutMsForFile(file: File): number {
  const n = file.name.toLowerCase();
  if (/\.(mp4|webm|mov|mkv|m4v)$/.test(n)) return VIDEO_SCAN_TIMEOUT_MS;
  if (/\.(mp3|wav|m4a)$/.test(n)) return VIDEO_SCAN_TIMEOUT_MS;
  return DEFAULT_SCAN_TIMEOUT_MS;
}

export async function scanText(
  actionId: string,
  content: string,
  modality: "text" | "code" = "text",
): Promise<ScanDecision> {
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), DEFAULT_SCAN_TIMEOUT_MS);
  try {
    const r = await fetch(`${API}/scans/text`, {
      method: "POST",
      headers: await headers(),
      signal: ac.signal,
      body: JSON.stringify({
        action_id: actionId,
        source: "local-demo-chat",
        destination_origin: DASHBOARD_ORIGIN,
        modality,
        content,
      }),
    });
    if (!r.ok) await throwScanHttpError(r);
    return r.json();
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ScanError("CLIENT_TIMEOUT", "Text scan timed out.", 0);
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export async function scanImage(actionId: string, file: File): Promise<ScanDecision> {
  const fd = new FormData();
  fd.append("action_id", actionId);
  fd.append("file", file);
  const r = await fetch(`${API}/scans/image`, {
    method: "POST",
    headers: { Authorization: `Bearer ${TOKEN}` },
    body: fd,
  });
  if (!r.ok) await throwScanHttpError(r);
  return r.json();
}

/** Multimodal pre-send scan: document, image, audio, video, code, text (by extension). */
export async function scanFile(actionId: string, file: File): Promise<ScanDecision> {
  const fd = new FormData();
  fd.append("action_id", actionId);
  fd.append("file", file);
  const ac = new AbortController();
  const ms = timeoutMsForFile(file);
  const timer = setTimeout(() => ac.abort(), ms);
  try {
    const r = await fetch(`${API}/scans/file`, {
      method: "POST",
      headers: { Authorization: `Bearer ${TOKEN}`, Origin: DASHBOARD_ORIGIN },
      signal: ac.signal,
      body: fd,
    });
    if (!r.ok) await throwScanHttpError(r);
    return r.json();
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ScanError(
        "CLIENT_TIMEOUT",
        "Scan timed out (video may need several minutes; keep API and Ollama running).",
        0,
      );
    }
    if (e instanceof TypeError) {
      throw new ScanError(
        "BACKEND_UNAVAILABLE",
        "Cannot reach AIRLOCK API at :8765. Is make api running?",
        0,
      );
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export async function redactText(
  actionId: string,
  content: string,
  scan: ScanDecision,
  modality: "text" | "code" | "document" | "audio" | "video" = "text",
): Promise<string> {
  const r = await fetch(`${API}/redactions`, {
    method: "POST",
    headers: await headers(),
    body: JSON.stringify({
      action_id: actionId,
      modality,
      content_text: content,
      finding_ids: scan.findings.map((f) => f.id),
      findings: scan.findings,
    }),
  });
  const data = await r.json();
  return data.sanitized_text as string;
}

export async function verifyText(actionId: string, content: string): Promise<ScanDecision> {
  const r = await fetch(`${API}/scans/verify-text`, {
    method: "POST",
    headers: await headers(),
    body: JSON.stringify({ content, action_id: actionId }),
  });
  return r.json();
}

async function fileToBase64(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i]!);
  }
  return btoa(binary);
}

export async function redactImage(
  actionId: string,
  file: File,
  scan: ScanDecision,
): Promise<Blob> {
  const image_base64 = await fileToBase64(file);
  const r = await fetch(`${API}/redactions`, {
    method: "POST",
    headers: await headers(),
    body: JSON.stringify({
      action_id: actionId,
      modality: "image",
      image_base64,
      finding_ids: scan.findings.map((f) => f.id),
      findings: scan.findings,
    }),
  });
  if (!r.ok) throw new Error(await r.text());
  const data = await r.json();
  const dataUrl = data.sanitized_image_base64 as string;
  const b64 = dataUrl.split(",")[1] ?? "";
  const raw = atob(b64);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i += 1) {
    out[i] = raw.charCodeAt(i);
  }
  return new Blob([out], { type: "image/png" });
}