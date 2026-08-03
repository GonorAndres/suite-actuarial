import { StructuredData } from "@/components/StructuredData";
import { homeGraph } from "@/lib/structured-data";

/**
 * Route group, so `/` keeps its URL. It exists only to give the home page a
 * Server Component that can carry its own structured data; the page itself is
 * `"use client"`. Title, description and canonical stay on the root layout.
 */
const name = "suite_actuarial · Laboratorio actuarial abierto";
const description =
  "Modelos actuariales explicados y calculadoras reproducibles, con sus fuentes y sus límites, desde el mercado asegurador mexicano.";

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={homeGraph(name, description)} />
      {children}
    </>
  );
}
