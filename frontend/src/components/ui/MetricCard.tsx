"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/design-system";

interface MetricCardProps {
  label: string;
  value: string;
  variant?: "default" | "primary" | "accent";
  sublabel?: string;
  icon?: ReactNode;
  className?: string;
}

const variantStyles = {
  default: "bg-offwhite border border-navy/8 text-navy",
  primary: "bg-navy text-cream",
  accent:
    "bg-gradient-to-r from-terracotta to-amber text-white",
} as const;

const labelStyles = {
  default: "text-navy/50",
  primary: "text-cream/60",
  accent: "text-white/70",
} as const;

const sublabelStyles = {
  default: "text-navy/40",
  primary: "text-cream/50",
  accent: "text-white/60",
} as const;

export default function MetricCard({
  label,
  value,
  variant = "default",
  sublabel,
  icon,
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl p-5 shadow-sm transition-all duration-300 hover:shadow-md hover:-translate-y-0.5",
        variantStyles[variant],
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p
            className={cn(
              "text-xs font-semibold uppercase tracking-wider mb-2",
              labelStyles[variant],
            )}
          >
            {label}
          </p>
          <p className="text-3xl font-heading font-bold tabular-nums leading-tight truncate">
            {value}
          </p>
          {sublabel && (
            <p
              className={cn(
                "text-sm mt-1.5",
                sublabelStyles[variant],
              )}
            >
              {sublabel}
            </p>
          )}
        </div>
        {icon && (
          <div className="shrink-0 opacity-60">{icon}</div>
        )}
      </div>
    </div>
  );
}
