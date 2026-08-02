import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { labGraph } from "@/lib/structured-data";

const name = "Caso guiado: seguro dotal educativo 20/10";
const description =
  "De la promesa contractual a la prima, reserva y validación independiente de un seguro dotal.";
const path = "/lab/";

export const metadata = routeMetadata({ name, description, path, title: name });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={labGraph(name, description)} />
      {children}
    </>
  );
}
