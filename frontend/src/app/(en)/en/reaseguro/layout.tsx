import { StructuredData } from "@/components/StructuredData";
import { routeMetadata } from "@/lib/site-metadata";
import { domainGraph } from "@/lib/structured-data";

const name = "Proportional and excess-of-loss reinsurance";
const description =
  "Quota share, excess of loss, stop loss, retention, and recovery through reproducible cases.";
const path = "/en/reaseguro/";

export const metadata = routeMetadata({ name, description, path, lang: "en" });

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <StructuredData graph={domainGraph("reaseguro", name, description, "en")} />
      {children}
    </>
  );
}
