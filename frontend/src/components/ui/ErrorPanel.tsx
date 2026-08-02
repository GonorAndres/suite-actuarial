import { cn } from "@/lib/design-system";

interface ErrorPanelProps {
  /** Localized heading, e.g. t("error_calculo_titulo"). */
  titulo: string;
  /**
   * What went wrong, already reduced to readable text. The typed client
   * parses the API's `detail` out of the response body, so this is the
   * validator's own sentence, never a JSON envelope or a status prefix.
   */
  mensaje: string;
  className?: string;
}

/**
 * Failure state for a calculation panel.
 *
 * Shared by every workbench so a rejected input reads the same way
 * everywhere: what failed, then why, in the API's own words.
 */
export default function ErrorPanel({
  titulo,
  mensaje,
  className,
}: ErrorPanelProps) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-sm border border-terracotta/40 bg-terracotta/5 px-4 py-3",
        className,
      )}
    >
      <p className="text-xs font-bold uppercase tracking-widest text-terracotta">
        {titulo}
      </p>
      <p className="mt-1 text-sm leading-relaxed text-navy">{mensaje}</p>
    </div>
  );
}
