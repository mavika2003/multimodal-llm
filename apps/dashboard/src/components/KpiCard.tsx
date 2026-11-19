import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { AnimatedNumber } from "./AnimatedNumber";
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion";

type Props = {
  label: string;
  value: number;
  description: string;
  icon: LucideIcon;
  accent?: "emerald" | "amber" | "coral" | "blue";
  delay?: number;
};

const ACCENT_CLASS: Record<NonNullable<Props["accent"]>, string> = {
  emerald: "kpi-accent-emerald",
  amber: "kpi-accent-amber",
  coral: "kpi-accent-coral",
  blue: "kpi-accent-blue",
};

export function KpiCard({ label, value, description, icon: Icon, accent = "blue", delay = 0 }: Props) {
  const reduced = usePrefersReducedMotion();

  return (
    <motion.article
      className="card kpi-card"
      initial={reduced ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, delay }}
      whileHover={reduced ? undefined : { y: -2 }}
    >
      <div className={`kpi-icon-wrap ${ACCENT_CLASS[accent]}`}>
        <Icon size={18} aria-hidden />
      </div>
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">
        <AnimatedNumber value={value} />
      </p>
      <p className="kpi-desc">{description}</p>
    </motion.article>
  );
}