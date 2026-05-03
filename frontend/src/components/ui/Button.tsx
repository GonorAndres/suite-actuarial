"use client";

import type { ReactNode, ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/design-system";

const variantStyles = {
  primary:
    "bg-terracotta text-cream hover:bg-terracotta/90 hover:shadow-md hover:shadow-terracotta/20 rounded-full",
  secondary:
    "bg-sage text-cream hover:bg-sage/90 hover:shadow-md hover:shadow-sage/20 rounded-full",
  outline:
    "border border-amber/40 text-navy/70 hover:bg-amber/10 hover:text-terracotta rounded-full",
} as const;

const sizeStyles = {
  sm: "px-3 py-1 text-sm",
  md: "px-5 py-2.5",
  lg: "px-7 py-3 text-lg hover:animate-pulse-subtle",
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
        "transition-all duration-200 font-medium",
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
