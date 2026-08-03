import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { apiDocsGraph } from "@/lib/structured-data";

const name = "API reference";
const description =
  "REST contracts of the suite_actuarial technical interface.";
const path = "/en/api-docs/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={apiDocsGraph(name, description, "en")} />
      {children}
    </>
  );
}
