import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, IBM_Plex_Serif } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { LanguageProvider } from "@/lib/i18n/LanguageContext";
import { DocumentLanguage } from "@/components/layout/DocumentLanguage";
import { LANG_BOOTSTRAP_SCRIPT } from "@/lib/i18n/langBootstrap";
import { StructuredData } from "@/components/StructuredData";
import { SITE_NAME, SITE_URL, SOCIAL_IMAGE } from "@/lib/site-metadata";
import { siteGraph } from "@/lib/structured-data";

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
  metadataBase: new URL(SITE_URL),
  title: "suite_actuarial · Laboratorio actuarial abierto",
  description:
    "Modelos actuariales explicados y calculadoras reproducibles, con sus fuentes y sus límites, desde el mercado asegurador mexicano.",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "es_MX",
    alternateLocale: "en_US",
    siteName: SITE_NAME,
    title: "suite_actuarial · Laboratorio actuarial abierto",
    description: "Entiende el modelo, revisa sus supuestos y calcula escenarios reproducibles.",
    url: "/",
    images: [SOCIAL_IMAGE],
  },
  twitter: {
    card: "summary_large_image",
    title: "suite_actuarial",
    description: "Modelos actuariales explicados y reproducibles, hechos desde México.",
    images: [SOCIAL_IMAGE],
  },
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
        {/* Applies the stored language to <html lang> before hydration. */}
        <script dangerouslySetInnerHTML={{ __html: LANG_BOOTSTRAP_SCRIPT }} />
        <StructuredData graph={siteGraph} />
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
