import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Property and casualty insurance and rating";
const description =
  "Deductibles, auto, fire, liability, bonus-malus, and frequency-severity explained from the actuarial decision.";
const path = "/en/danos/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("danos", name, description, "en")} />
      {children}
    </>
  );
}
