import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { evidenceGraph } from "@/lib/structured-data";

const name = "Evidencia, validación y límites";
const description =
  "Fuentes, identidades, auditoría actuarial y límites profesionales de los modelos abiertos de suite_actuarial.";
const path = "/evidencia/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={evidenceGraph(name, description)} />
      {children}
    </>
  );
}
