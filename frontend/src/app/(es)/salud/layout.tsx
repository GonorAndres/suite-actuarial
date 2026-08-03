import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Gastos médicos y costo compartido";
const description =
  "Caso y calculadoras de GMM, deducible, coaseguro y accidentes con limitaciones explícitas.";
const path = "/salud/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("salud", name, description)} />
      {children}
    </>
  );
}
