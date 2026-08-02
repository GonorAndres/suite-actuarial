import AvisoLimitacion from "./AvisoLimitacion";
import Badge from "./Badge";

interface AvisoModeloProps {
  /** `validation_tier` exactly as the API returned it. */
  tier?: string | null;
  /** `disclaimer` exactly as the API returned it. */
  disclaimer?: string | null;
  /** Localized heading for the scope notice, e.g. t("reg_aviso_alcance"). */
  titulo: string;
  /** Localized caption for the tier badge, e.g. t("nivel_validacion"). */
  etiquetaNivel: string;
  className?: string;
}

/**
 * Disclosure block for a realm whose response carries `validation_tier` and
 * `disclaimer`: the badge states how far the data behind the figure was
 * validated, the notice states what the model does not do.
 *
 * The frontend never invents either one. When the endpoint sends neither
 * field, nothing renders — an absent disclosure is visible as an absence, not
 * papered over with a default.
 */
export default function AvisoModelo({
  tier,
  disclaimer,
  titulo,
  etiquetaNivel,
  className,
}: AvisoModeloProps) {
  if (!tier && !disclaimer) return null;

  return (
    <div className={className}>
      {tier && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs uppercase tracking-widest text-navy/50">
            {etiquetaNivel}
          </span>
          <Badge
            variant={
              tier === "supported"
                ? "success"
                : tier === "deprecated"
                  ? "error"
                  : "warning"
            }
          >
            {tier}
          </Badge>
        </div>
      )}
      {disclaimer && (
        <AvisoLimitacion titulo={titulo}>
          <p>{disclaimer}</p>
        </AvisoLimitacion>
      )}
    </div>
  );
}
