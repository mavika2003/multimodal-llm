import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FileText, Image, Mic, Video, Code, Loader2, Upload } from "lucide-react";
import {
  fetchDemoFixtureBlob,
  fetchDemoFixtureText,
  fetchHackathonManifest,
  inspectorAsk,
  inspectorCodeTask,
  inspectorIngest,
  runInspectorCode,
  type HackathonDemoItem,
} from "../api";
import type { IngestResult } from "../api";
import type { InspectorResult } from "../lib/types";
import { severityTone } from "../lib/incidents";

const MODALITIES = [
  { id: "document", label: "Document", icon: FileText, accept: ".pdf,.txt,.md,.json,.csv" },
  { id: "text", label: "Text", icon: FileText, accept: ".txt,.md" },
  { id: "image", label: "Image", icon: Image, accept: "image/*" },
  { id: "audio", label: "Audio", icon: Mic, accept: "audio/*,.txt,.vtt,.srt" },
  { id: "video", label: "Video", icon: Video, accept: "video/*" },
  { id: "code", label: "Code", icon: Code, accept: "" },
] as const;

type Modality = (typeof MODALITIES)[number]["id"];

export function InspectorPage() {
  const [modality, setModality] = useState<Modality>("document");
  const [q, setQ] = useState(
    "What kinds of information did AIRLOCK stop me from sharing today?",
  );
  const [doc, setDoc] = useState(
    "Project Phoenix launches in Q2. Contact: demo.user@example.com",
  );
  const [uploadName, setUploadName] = useState<string | null>(null);
  const [ingest, setIngest] = useState<IngestResult | null>(null);
  const [phase, setPhase] = useState<"idle" | "scanning" | "done" | "error">("idle");
  const [result, setResult] = useState<InspectorResult | null>(null);
  const [codePrompt, setCodePrompt] = useState(
    "Write Python to count incidents by modality from fixtures/synthetic_only/incidents.json",
  );
  const [codeOut, setCodeOut] = useState("");
  const [codeRun, setCodeRun] = useState<{ ok: boolean; stdout?: string; error?: string } | null>(
    null,
  );
  const [codeBusy, setCodeBusy] = useState(false);
  const [imageB64, setImageB64] = useState<string | null>(null);
  const [demoItems, setDemoItems] = useState<HackathonDemoItem[]>([]);

  const activeTab = MODALITIES.find((m) => m.id === modality)!;

  useEffect(() => {
    fetchHackathonManifest()
      .then((m) => setDemoItems(m.items))
      .catch(() => setDemoItems([]));
  }, []);

  async function loadHackathonItem(item: HackathonDemoItem) {
    if (item.modality === "code") {
      setModality("code");
      setCodePrompt(item.sample_question);
      return;
    }
    const mod = item.modality as Exclude<Modality, "code">;
    setModality(mod);
    setQ(item.sample_question);
    setResult(null);
    setIngest(null);
    setUploadName(item.file);
    setPhase("idle");
    try {
      if (/\.(png|jpe?g)$/i.test(item.file)) {
        const blob = await fetchDemoFixtureBlob(item.file);
        const dataUrl = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result));
          reader.onerror = reject;
          reader.readAsDataURL(blob);
        });
        setImageB64(dataUrl);
        const file = new File([blob], item.file, { type: blob.type || "image/png" });
        const ing = await inspectorIngest("image", file);
        setIngest(ing);
        setDoc(ing.extracted_preview);
      } else {
        setImageB64(null);
        setDoc(await fetchDemoFixtureText(item.file));
      }
    } catch {
      setPhase("error");
    }
  }

  async function handleFile(file: File | null) {
    if (!file) return;
    setUploadName(file.name);
    if (modality === "text" || modality === "document") {
      if (file.type.startsWith("text") || file.name.match(/\.(txt|md|json|csv|log)$/i)) {
        setDoc(await file.text());
        return;
      }
    }
    setPhase("scanning");
    try {
      const apiMod = modality === "code" ? "text" : modality;
      const ing = await inspectorIngest(apiMod, file);
      setIngest(ing);
      setDoc(ing.extracted_preview);
      if (modality === "image" && file.type.startsWith("image/")) {
        const dataUrl = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result));
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
        setImageB64(dataUrl);
      }
      setPhase("idle");
    } catch {
      setPhase("error");
    }
  }

  return (
    <motion.div className="page-stack" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <section className="card">
        <h2 className="card-title">IEEE hackathon kit (five modalities)</h2>
        <p className="card-sub">
          One interface: load synthetic fixtures, then Run inspector query. Uses local Ollama +
          Tesseract OCR + rule scanners. Pull{" "}
          <span className="mono">qwen2.5-coder:3b</span> and optionally a vision model (llava /
          qwen2.5vl).
        </p>
        <div className="drawer-footer-actions" style={{ flexWrap: "wrap", gap: 8 }}>
          {demoItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className="btn btn-ghost"
              onClick={() => loadHackathonItem(item)}
            >
              {item.modality}: {item.id}
            </button>
          ))}
        </div>
      </section>
      <section className="modality-tabs" role="tablist" aria-label="Inspector modality">
        {MODALITIES.map((m) => (
          <button
            key={m.id}
            type="button"
            role="tab"
            aria-selected={modality === m.id}
            className={`mod-tab ${modality === m.id ? "active" : ""}`}
            onClick={() => setModality(m.id)}
          >
            <m.icon size={16} aria-hidden />
            {m.label}
          </button>
        ))}
      </section>

      {modality === "code" ? (
        <div className="inspector-grid">
          <section className="card">
            <h2 className="card-title">Code task (local Ollama)</h2>
            <p className="card-sub">
              Generates sandboxed Python against fixture data. Requires Ollama running with your
              coder model pulled.
            </p>
            <label className="field">
              <span className="field-label">Prompt</span>
              <textarea
                className="input"
                rows={4}
                value={codePrompt}
                onChange={(e) => setCodePrompt(e.target.value)}
              />
            </label>
            <button
              type="button"
              className="btn btn-primary"
              disabled={codeBusy}
              onClick={async () => {
                setCodeBusy(true);
                setCodeRun(null);
                try {
                  const res = await inspectorCodeTask(codePrompt);
                  setCodeOut(res.code);
                } catch {
                  setCodeOut("// Code generation failed. Is Ollama running?");
                }
                setCodeBusy(false);
              }}
            >
              {codeBusy ? <Loader2 className="spin" size={16} /> : null}
              Generate code
            </button>
          </section>
          <section className="card">
            <h2 className="card-title">Output</h2>
            <textarea className="input mono" rows={14} value={codeOut} onChange={(e) => setCodeOut(e.target.value)} />
            <button
              type="button"
              className="btn btn-ghost"
              disabled={!codeOut || codeBusy}
              onClick={async () => {
                setCodeBusy(true);
                try {
                  const res = await runInspectorCode("code-task-demo", codeOut);
                  setCodeRun(res);
                } catch {
                  setCodeRun({ ok: false, error: "Run failed" });
                }
                setCodeBusy(false);
              }}
            >
              Run in sandbox
            </button>
            {codeRun ? (
              <pre className="receiver-pre mono">{JSON.stringify(codeRun, null, 2)}</pre>
            ) : null}
          </section>
        </div>
      ) : (
        <div className="inspector-grid">
          <section className="card">
            <h2 className="card-title">Input</h2>
            <p className="card-sub">
              Upload a file for multimodal ingest (PDF, image OCR, audio transcript, video frame)
              or paste synthetic demo text. Then ask a grounded question.
            </p>

            <label className="field file-field">
              <span className="field-label">Upload</span>
              <div className="file-row">
                <Upload size={16} aria-hidden />
                <input
                  type="file"
                  accept={activeTab.accept}
                  onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
                />
                {uploadName ? <span className="muted small">{uploadName}</span> : null}
              </div>
            </label>

            <div
              className="drop-zone"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                void handleFile(e.dataTransfer.files?.[0] ?? null);
              }}
            >
              <label className="field">
                <span className="field-label">Extracted / pasted content</span>
                <textarea
                  rows={6}
                  value={doc}
                  onChange={(e) => setDoc(e.target.value)}
                  className="input"
                />
              </label>
            </div>

            {ingest && ingest.findings.length > 0 ? (
              <ul className="finding-list">
                {ingest.findings.map((f) => (
                  <li key={f.id} className="card finding-card">
                    <span className={`pill pill-${severityTone(f.severity)}`}>{f.severity}</span>
                    <p className="finding-cat mono">{f.category}</p>
                    <p className="finding-excerpt">{f.excerpt_redacted}</p>
                  </li>
                ))}
              </ul>
            ) : null}
            {ingest?.notes ? <p className="muted small">{ingest.notes}</p> : null}

            <label className="field">
              <span className="field-label">Question</span>
              <input className="input" value={q} onChange={(e) => setQ(e.target.value)} />
            </label>

            <button
              type="button"
              className="btn btn-primary"
              disabled={phase === "scanning"}
              onClick={async () => {
                setPhase("scanning");
                setResult(null);
                try {
                  const apiModality =
                    modality === "document" ? "document" : modality === "text" ? "text" : modality;
                  const raw = await inspectorAsk(q, doc, apiModality, {
                    image_base64: imageB64 ?? undefined,
                  });
                  setResult({
                    answer: String(raw.answer ?? ""),
                    citations: Array.isArray(raw.citations) ? raw.citations.map(String) : [],
                    abstained: Boolean(raw.abstained),
                    sound_events: Array.isArray(raw.sound_events)
                      ? raw.sound_events.map(String)
                      : undefined,
                    model_used: raw.model_used ? String(raw.model_used) : null,
                  });
                  setPhase("done");
                } catch {
                  setPhase("error");
                }
              }}
            >
              {phase === "scanning" ? <Loader2 className="spin" size={16} /> : null}
              {phase === "scanning" ? "Analyzing locally…" : "Run inspector query"}
            </button>

            {phase === "error" ? (
              <p className="text-coral small" role="alert">
                Analysis failed. Check that the local API is running.
              </p>
            ) : null}
          </section>

          <section className="card results-card">
            <h2 className="card-title">Results</h2>
            <p className="card-sub mono">
              {phase === "idle" && "Waiting for input"}
              {phase === "scanning" && "Scanning locally via /inspector/ingest and /inspector/ask"}
              {phase === "done" && "Results available"}
              {phase === "error" && "Analysis failed"}
            </p>

            {!result ? (
              <p className="muted">Grounded answer and citations appear here.</p>
            ) : (
              <>
                {result.abstained ? <span className="pill pill-warning">Abstained</span> : null}
                <p className="inspector-answer">{result.answer}</p>
                {result.model_used ? (
                  <p className="muted small mono">Model: {result.model_used}</p>
                ) : null}
                {result.sound_events && result.sound_events.length > 0 ? (
                  <p className="muted small">Sounds: {result.sound_events.join(", ")}</p>
                ) : null}
                {result.citations.length > 0 ? (
                  <ul className="citation-list mono">
                    {result.citations.map((c) => (
                      <li key={c}>{c}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted small">No incident citations returned.</p>
                )}
              </>
            )}
          </section>
        </div>
      )}
    </motion.div>
  );
}