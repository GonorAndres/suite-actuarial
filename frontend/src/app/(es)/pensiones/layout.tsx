import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Pensiones, Ley 73/97 y rentas vitalicias";
const description =
  "Beneficios de retiro, saldo individual, rentas vitalicias y funciones de conmutación, con los supuestos a la vista.";
const path = "/pensiones/";

export const metadata = routeMetadata({ name, description, path });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("pensiones", name, description)} />
      {children}
    </>
  );
}
