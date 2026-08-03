import { StructuredData } from "@/components/StructuredData";
import { homeGraph } from "@/lib/structured-data";

/**
 * Route group, so `/en/` keeps its URL. It exists only to give the home page a
 * Server Component that can carry its own structured data; the page itself is
 * `"use client"`. Title, description and canonical stay on the root layout.
 */
const name = "suite_actuarial · Open actuarial laboratory";
const description =
  "Actuarial models explained and reproducible calculators, with their sources and their limits, from the Mexican insurance market.";

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={homeGraph(name, description, "en")} />
      {children}
    </>
  );
}
