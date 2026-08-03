import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Seguros de daños y tarificación";
const description =
  "Deducibles, auto, incendio, RC, bonus-malus y frecuencia-severidad explicados desde la decisión actuarial.";
const path = "/danos/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("danos", name, description)} />
      {children}
    </>
  );
}
