import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Regulatory reference and solvency capital (RCS)";
const description =
  "Pedagogical scenarios of the RCS, capital, deductibility, and retentions with visible scope.";
const path = "/en/regulatorio/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("regulatorio", name, description, "en")} />
      {children}
    </>
  );
}
