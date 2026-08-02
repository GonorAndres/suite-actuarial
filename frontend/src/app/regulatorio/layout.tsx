import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Referencia regulatoria y RCS";
const description =
  "Escenarios pedagógicos de RCS, capital, deducibilidad y retenciones con alcance visible.";
const path = "/regulatorio/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("regulatorio", name, description)} />
      {children}
    </>
  );
}
