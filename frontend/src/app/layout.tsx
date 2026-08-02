import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, IBM_Plex_Serif } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { LanguageProvider } from "@/lib/i18n/LanguageContext";
import { DocumentLanguage } from "@/components/layout/DocumentLanguage";

const plexSans = IBM_Plex_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const plexSerif = IBM_Plex_Serif({
  variable: "--font-serif",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://suite.gonor.me"),
  title: "suite_actuarial — Laboratorio actuarial abierto",
  description:
    "Modelos actuariales explicados, calculadoras reproducibles, fuentes y límites desde el contexto asegurador mexicano.",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "es_MX",
    alternateLocale: "en_US",
    siteName: "suite_actuarial",
    title: "suite_actuarial — Laboratorio actuarial abierto",
    description: "Entienda el modelo, revise sus supuestos y calcule escenarios reproducibles.",
    url: "/",
  },
  twitter: { card: "summary", title: "suite_actuarial", description: "Modelos actuariales explicados y reproducibles desde México." },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${plexSans.variable} ${plexSerif.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <LanguageProvider>
          <DocumentLanguage />
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </LanguageProvider>
      </body>
    </html>
  );
}
