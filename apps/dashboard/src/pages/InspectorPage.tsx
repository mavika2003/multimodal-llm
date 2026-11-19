import { useState } from "react";
import { motion } from "framer-motion";
import { FileText, Image, Mic, Video, Code, Loader2 } from "lucide-react";
import { inspectorAsk } from "../api";
import type { InspectorResult } from "../lib/types";

const MODALITIES = [
  { id: "document", label: "Document", icon: FileText },
  { id: "text", label: "Text", icon: FileText },
  { id: "image", label: "Image", icon: Image },
  { id: "audio", label: "Audio", icon: Mic },
  { id: "video", label: "Video", icon: Video },
  { id: "code", label: "Code", icon: Code },
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
  const [phase, setPhase] = useState<"idle" | "scanning" | "done" | "error">("idle");
  const [result, setResult] = useState<InspectorResult | null>(null);

  return (
    <motion.div className="page-stack" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
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

      <div className="inspector-grid">
        <section className="card">
          <h2 className="card-title">Input</h2>
          <p className="card-sub">
            Paste synthetic demo content. Inspector Q&amp;A uses your selected modality in the API
            request.
          </p>

          <div
            className="drop-zone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const file = e.dataTransfer.files?.[0];
              if (file && file.type.startsWith("text")) {
                file.text().then(setDoc);
              }
            }}
          >
            <label className="field">
              <span className="field-label">Content</span>
              <textarea
                rows={6}
                value={doc}
                onChange={(e) => setDoc(e.target.value)}
                className="input"
              />
            </label>
          </div>

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
                  modality === "code" ? "text" : modality === "document" ? "document" : modality;
                const raw = await inspectorAsk(q, doc, apiModality);
                setResult({
                  answer: String(raw.answer ?? ""),
                  citations: Array.isArray(raw.citations) ? raw.citations.map(String) : [],
                  abstained: Boolean(raw.abstained),
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
            {phase === "scanning" && "Scanning locally via /inspector/ask"}
            {phase === "done" && "Results available"}
            {phase === "error" && "Analysis failed"}
          </p>

          {!result ? (
            <p className="muted">Grounded answer and citations appear here.</p>
          ) : (
            <>
              {result.abstained ? <span className="pill pill-warning">Abstained</span> : null}
              <p className="inspector-answer">{result.answer}</p>
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
    </motion.div>
  );
}