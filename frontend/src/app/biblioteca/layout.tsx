import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { libraryGraph } from "@/lib/structured-data";

const name = "Biblioteca de modelos actuariales";
const description =
  "Casos explicados y calculadoras de vida, daños, salud, pensiones, reservas, reaseguro y referencia regulatoria en México.";
const path = "/biblioteca/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={libraryGraph(name, description)} />
      {children}
    </>
  );
}
