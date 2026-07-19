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
  default: "bg-white border-t-2 border-t-navy text-navy",
  primary: "bg-navy border-t-2 border-t-navy text-offwhite",
  accent: "bg-white border-t-2 border-t-terracotta text-navy",
} as const;

const labelStyles = {
  default: "text-navy/55",
  primary: "text-offwhite/70",
  accent: "text-terracotta",
} as const;

const sublabelStyles = {
  default: "text-navy/45",
  primary: "text-offwhite/55",
  accent: "text-navy/45",
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
        "rounded-sm border border-navy/15 p-5 shadow-sm",
        variantStyles[variant],
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p
            className={cn(
              "text-xs font-semibold uppercase tracking-widest mb-2",
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
