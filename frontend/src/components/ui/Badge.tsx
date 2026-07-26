import type { ReactNode } from "react";

const variantStyles = {
  success: "bg-sage/10 text-sage border border-sage/40",
  warning: "bg-amber/10 text-amber border border-amber/40",
  error: "bg-terracotta/10 text-terracotta border border-terracotta/40",
  info: "bg-navy/5 text-navy border border-navy/30",
} as const;

interface BadgeProps {
  variant: "success" | "warning" | "error" | "info";
  children: ReactNode;
  className?: string;
}

export default function Badge({
  variant,
  children,
  className = "",
}: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-bold uppercase tracking-widest",
        variantStyles[variant],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </span>
  );
}
