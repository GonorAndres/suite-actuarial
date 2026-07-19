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
        "bg-white rounded-md border border-navy/15 shadow-sm p-6",
        hoverable &&
          "transition-all duration-200 hover:border-navy/40 hover:shadow-md",
        className,
      )}
    >
      {title && (
        <>
          <h3 className="font-heading text-xl font-bold text-navy mb-2">
            {title}
          </h3>
          <div className="h-px bg-navy/15 mb-4" aria-hidden="true" />
        </>
      )}
      {children}
    </div>
  );
}
