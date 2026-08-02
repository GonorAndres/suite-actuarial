import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Reservas: Chain Ladder, Mack y bootstrap ODP";
const description =
  "Desarrollo de siniestros, cola e incertidumbre explicados con pruebas y límites del modelo.";
const path = "/reservas/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("reservas", name, description)} />
      {children}
    </>
  );
}
