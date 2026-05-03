"use client";

import { useState } from "react";
import { cn } from "@/lib/design-system";

interface Segment {
  label: string;
  value: number;
  color: string;
}

interface ProgressBarProps {
  segments: Segment[];
  total?: number;
  showLabels?: boolean;
  className?: string;
  formatValue?: (value: number) => string;
}

export default function ProgressBar({
  segments,
  total,
  showLabels = true,
  className,
  formatValue = (v) => v.toLocaleString("es-MX", { maximumFractionDigits: 2 }),
}: ProgressBarProps) {
  const computedTotal =
    total ?? segments.reduce((sum, s) => sum + s.value, 0);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (computedTotal === 0) return null;

  return (
    <div className={cn("space-y-3", className)}>
      {/* Bar */}
      <div className="relative h-8 rounded-full overflow-hidden bg-navy/5 flex">
        {segments.map((seg, i) => {
          const pct = (seg.value / computedTotal) * 100;
          if (pct <= 0) return null;
          return (
            <div
              key={i}
              className="relative h-full transition-all duration-500 ease-out first:rounded-l-full last:rounded-r-full"
              style={{
                width: `${pct}%`,
                backgroundColor: seg.color,
              }}
              onMouseEnter={() => setHoveredIdx(i)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              {/* Tooltip */}
              {hoveredIdx === i && (
                <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-navy text-cream text-xs font-semibold px-2.5 py-1 rounded-md whitespace-nowrap shadow-lg z-10">
                  {seg.label}: {formatValue(seg.value)}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-navy" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Labels */}
      {showLabels && (
        <div className="flex flex-wrap gap-x-5 gap-y-1">
          {segments.map((seg, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span
                className="inline-block w-3 h-3 rounded-sm shrink-0"
                style={{ backgroundColor: seg.color }}
              />
              <span className="text-navy/60">{seg.label}</span>
              <span className="font-semibold text-navy tabular-nums">
                {formatValue(seg.value)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
