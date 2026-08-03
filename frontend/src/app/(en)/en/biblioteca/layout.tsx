import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { libraryGraph } from "@/lib/structured-data";

const name = "Library of actuarial models";
const description =
  "Explained cases and calculators for life, P&C, health, pensions, reserves, reinsurance, and Mexican regulatory reference.";
const path = "/en/biblioteca/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={libraryGraph(name, description, "en")} />
      {children}
    </>
  );
}
