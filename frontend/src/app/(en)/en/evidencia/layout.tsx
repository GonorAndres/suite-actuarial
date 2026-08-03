import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { evidenceGraph } from "@/lib/structured-data";

const name = "Evidence, validation, and limits";
const description =
  "Sources, identities, actuarial audit, and professional limits of suite_actuarial's open models.";
const path = "/en/evidencia/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={evidenceGraph(name, description, "en")} />
      {children}
    </>
  );
}
