import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Pensions, Law 73/97, and life annuities";
const description =
  "Retirement benefits, individual account balance, life annuities, and commutation functions, with the assumptions in plain sight.";
const path = "/en/pensiones/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("pensiones", name, description, "en")} />
      {children}
    </>
  );
}
