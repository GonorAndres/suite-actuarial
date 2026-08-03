import type { Metadata } from "next";
import "../globals.css";
import { RootDocument } from "@/components/layout/RootDocument";
import { languageAlternates, SITE_NAME, SITE_URL, socialImage } from "@/lib/site-metadata";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "suite_actuarial · Laboratorio actuarial abierto",
  description:
    "Modelos actuariales explicados y calculadoras reproducibles, con sus fuentes y sus límites, desde el mercado asegurador mexicano.",
  alternates: { canonical: "/", languages: languageAlternates("/") },
  openGraph: {
    type: "website",
    locale: "es_MX",
    alternateLocale: "en_US",
    siteName: SITE_NAME,
    title: "suite_actuarial · Laboratorio actuarial abierto",
    description: "Entiende el modelo, revisa sus supuestos y calcula escenarios reproducibles.",
    url: "/",
    images: [socialImage("es")],
  },
  twitter: {
    card: "summary_large_image",
    title: "suite_actuarial",
    description: "Modelos actuariales explicados y reproducibles, hechos desde México.",
    images: [socialImage("es")],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <RootDocument lang="es">{children}</RootDocument>;
}
