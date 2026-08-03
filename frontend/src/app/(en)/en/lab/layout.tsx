import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { labGraph } from "@/lib/structured-data";

const name = "Guided case: 20/10 educational endowment insurance";
const description =
  "From the contractual promise to the premium, reserve, and independent validation of an endowment insurance.";
const path = "/en/lab/";

export const metadata = routeMetadata({ name, description, path, title: name, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={labGraph(name, description, "en")} />
      {children}
    </>
  );
}
