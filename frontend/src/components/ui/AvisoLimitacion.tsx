import type { ReactNode } from "react";

import { cn } from "@/lib/design-system";

interface AvisoLimitacionProps {
  /** Localized heading, e.g. t("aviso_alcance_titulo"). */
  titulo: string;
  /** Localized explanation of what this specific model does not do. */
  children: ReactNode;
  className?: string;
}

/**
 * Scope notice shown next to a figure, never in a footnote.
 *
 * Unlike `AvisoIlustrativo`, this one renders unconditionally: the caller has
 * already decided the limitation applies, typically because the API returned a
 * `disclaimer` field alongside the numbers.
 */
export default function AvisoLimitacion({
  titulo,
  children,
  className = "",
}: AvisoLimitacionProps) {
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
      <div className="mt-1 leading-relaxed space-y-1">{children}</div>
    </div>
  );
}
