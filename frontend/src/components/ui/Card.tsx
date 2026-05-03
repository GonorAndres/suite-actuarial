import type { ReactNode } from "react";
import { cn } from "@/lib/design-system";

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
}

export default function Card({
  title,
  children,
  className,
  hoverable = false,
}: CardProps) {
  return (
    <div
      className={cn(
        "bg-offwhite rounded-xl border border-navy/8 shadow-sm p-6",
        hoverable &&
          "gradient-border-hover hover:shadow-lg hover:-translate-y-1.5 transition-all duration-300",
        className,
      )}
    >
      {title && (
        <h3 className="font-heading text-xl font-bold text-navy mb-4">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
