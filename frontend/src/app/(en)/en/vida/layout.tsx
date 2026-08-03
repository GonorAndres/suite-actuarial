import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Life insurance: premiums and reserves";
const description =
  "Explained case and calculators for term, whole life, and endowment insurance with visible assumptions and validation.";
const path = "/en/vida/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("vida", name, description, "en")} />
      {children}
    </>
  );
}
