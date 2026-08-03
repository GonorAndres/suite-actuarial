import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Reserves: Chain Ladder, Mack, and ODP bootstrap";
const description =
  "Claims development, tail, and uncertainty explained with tests and model limits.";
const path = "/en/reservas/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("reservas", name, description, "en")} />
      {children}
    </>
  );
}
