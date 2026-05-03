import type { ReactNode } from "react";

const variantStyles = {
  success: "bg-sage/20 text-sage border border-sage/30",
  warning: "bg-amber/20 text-amber border border-amber/30",
  error: "bg-red-50 text-red-700 border border-red-200",
  info: "bg-navy/10 text-navy border border-navy/20",
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
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-widest",
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
