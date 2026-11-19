import type { CSSProperties } from "react";

type Point = { label: string; count: number };

export function BarChart({
  data,
  barColor = "var(--blue)",
  emptyLabel = "No data in local store yet",
}: {
  data: Point[];
  barColor?: string;
  emptyLabel?: string;
}) {
  if (data.length === 0) {
    return <p className="empty-inline">{emptyLabel}</p>;
  }

  const max = Math.max(1, ...data.map((d) => d.count));

  return (
    <div className="bar-chart" role="img" aria-label="Bar chart">
      {data.map((d) => (
        <div key={d.label} className="bar-row">
          <span className="bar-label">{d.label}</span>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={
                {
                  width: `${(d.count / max) * 100}%`,
                  background: barColor,
                } as CSSProperties
              }
            />
          </div>
          <span className="bar-count">{d.count}</span>
        </div>
      ))}
    </div>
  );
}