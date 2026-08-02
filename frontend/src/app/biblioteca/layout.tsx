import type { Metadata } from "next";
export const metadata: Metadata = { title: "Biblioteca de modelos actuariales | suite_actuarial", description: "Casos explicados y calculadoras de vida, daños, salud, pensiones, reservas, reaseguro y referencia regulatoria en México.", alternates: { canonical: "/biblioteca/" } };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) { return children; }
