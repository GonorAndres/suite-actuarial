import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { apiDocsGraph } from "@/lib/structured-data";

const name = "Referencia de API";
const description =
  "Contratos REST de la interfaz técnica de suite_actuarial.";
const path = "/api-docs/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={apiDocsGraph(name, description)} />
      {children}
    </>
  );
}
