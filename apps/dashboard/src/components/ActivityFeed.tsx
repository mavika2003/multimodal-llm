import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Image,
  Mic,
  Code,
  Video,
  HelpCircle,
  ChevronRight,
} from "lucide-react";
import type { IncidentRow } from "../lib/types";
import { activityState, formatTime, severityTone } from "../lib/incidents";
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion";

const MODALITY_ICON: Record<string, typeof FileText> = {
  text: FileText,
  code: Code,
  image: Image,
  audio: Mic,
  video: Video,
  document: FileText,
};

function ModalityIcon({ modality }: { modality: string }) {
  const Icon = MODALITY_ICON[modality] ?? HelpCircle;
  return <Icon size={15} aria-hidden />;
}

export function ActivityFeed({
  items,
  onOpen,
  compact,
}: {
  items: IncidentRow[];
  onOpen: (id: string) => void;
  compact?: boolean;
}) {
  const reduced = usePrefersReducedMotion();

  if (items.length === 0) {
    return (
      <motion.div className="empty-state card" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <p className="empty-title">No activity yet</p>
        <p className="empty-body">
          Use Demo Chat to trigger a local scan. Events will appear here as they are recorded in
          SQLite.
        </p>
      </motion.div>
    );
  }

  return (
    <ul className="activity-list" aria-label="Live activity">
      <AnimatePresence initial={false}>
        {items.map((i) => {
          const tone = severityTone(i.severity);
          return (
            <motion.li
              key={i.id}
              className={`activity-row tone-${tone}`}
              initial={reduced ? false : { opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <button
                type="button"
                className="activity-row-btn"
                onClick={() => onOpen(i.id)}
              >
                <span className="mono muted">{formatTime(i.observed_at)}</span>
                <span className="activity-mod">
                  <ModalityIcon modality={i.modality} />
                  {!compact && <span>{i.modality}</span>}
                </span>
                <span className="activity-title">{i.title}</span>
                <span className={`pill pill-${tone}`}>{i.severity}</span>
                <span className="mono muted activity-state">{activityState(i)}</span>
                <ChevronRight size={14} className="activity-chevron" aria-hidden />
              </button>
            </motion.li>
          );
        })}
      </AnimatePresence>
    </ul>
  );
}