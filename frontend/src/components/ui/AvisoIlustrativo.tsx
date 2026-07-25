import type { ReactNode } from "react";

import { cn } from "@/lib/design-system";
import type { CalculationMetadata } from "@/lib/types";

interface AvisoIlustrativoProps {
  /**
   * Result metadata from the API. The notice renders only when the backend
   * marked the calculation as illustrative — the frontend never decides on its
   * own which numbers are trustworthy.
   */
  metadata?: CalculationMetadata | null;
  /** Localized heading, e.g. t("aviso_ilustrativo_titulo"). */
  titulo: string;
  /** Localized explanation of what this specific model does not do. */
  children: ReactNode;
  className?: string;
}

/**
 * Limitation notice for results the package marks `validation_tier:
 * "illustrative"` — figures produced by a method that does not meet the
 * definition its name suggests. Shown next to the number, not in a footnote.
 */
export default function AvisoIlustrativo({
  metadata,
  titulo,
  children,
  className = "",
}: AvisoIlustrativoProps) {
  if (metadata?.validation_tier !== "illustrative") return null;

  return (
    <div
      role="note"
      className={cn(
        "border-l-2 border-amber bg-amber/5 px-4 py-3 text-sm text-navy",
        className,
      )}
    >
      <p className="font-bold uppercase tracking-widest text-xs text-amber">
        {titulo}
      </p>
      <p className="mt-1 leading-relaxed">{children}</p>
    </div>
  );
}
