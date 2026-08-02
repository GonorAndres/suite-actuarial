import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Seguros de vida: primas y reservas";
const description =
  "Caso explicado y calculadoras de seguro temporal, vida entera y dotal con supuestos y validación visibles.";
const path = "/vida/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("vida", name, description)} />
      {children}
    </>
  );
}
