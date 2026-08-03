import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Medical expenses and cost sharing";
const description =
  "Case and calculators for major medical, deductible, coinsurance, and personal accidents with explicit limitations.";
const path = "/en/salud/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("salud", name, description, "en")} />
      {children}
    </>
  );
}
