import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Reaseguro proporcional y exceso de pérdida";
const description =
  "Cuota parte, exceso de pérdida, stop loss, retención y recuperación mediante casos reproducibles.";
const path = "/reaseguro/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("reaseguro", name, description)} />
      {children}
    </>
  );
}
