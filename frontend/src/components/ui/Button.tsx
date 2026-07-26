"use client";

import type { ReactNode, ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/design-system";

const variantStyles = {
  primary:
    "bg-navy text-offwhite border border-navy hover:bg-navy/90 rounded-sm",
  secondary:
    "bg-terracotta text-offwhite border border-terracotta hover:bg-terracotta/90 rounded-sm",
  outline:
    "border border-navy/30 text-navy hover:border-navy hover:bg-navy/5 rounded-sm",
} as const;

const sizeStyles = {
  sm: "px-3 py-1 text-xs",
  md: "px-5 py-2.5 text-sm",
  lg: "px-7 py-3 text-base",
} as const;

interface ButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  variant?: "primary" | "secondary" | "outline";
  size?: "sm" | "md" | "lg";
  children: ReactNode;
}

export default function Button({
  variant = "primary",
  size = "md",
  children,
  disabled = false,
  className,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={cn(
        "transition-colors duration-150 font-semibold uppercase tracking-wider",
        variantStyles[variant],
        sizeStyles[size],
        disabled && "opacity-50 cursor-not-allowed",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
