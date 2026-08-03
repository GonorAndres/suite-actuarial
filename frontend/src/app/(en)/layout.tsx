import type { Metadata } from "next";
import "../globals.css";
import { RootDocument } from "@/components/layout/RootDocument";
import { languageAlternates, SITE_NAME, SITE_URL, socialImage } from "@/lib/site-metadata";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "suite_actuarial · Open actuarial laboratory",
  description:
    "Actuarial models explained and reproducible calculators, with their sources and their limits, from the Mexican insurance market.",
  alternates: { canonical: "/en/", languages: languageAlternates("/en/") },
  openGraph: {
    type: "website",
    locale: "en_US",
    alternateLocale: "es_MX",
    siteName: SITE_NAME,
    title: "suite_actuarial · Open actuarial laboratory",
    description: "Understand the model, check its assumptions, and compute reproducible scenarios.",
    url: "/en/",
    images: [socialImage("en")],
  },
  twitter: {
    card: "summary_large_image",
    title: "suite_actuarial",
    description: "Actuarial models explained and reproducible, built from Mexico.",
    images: [socialImage("en")],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <RootDocument lang="en">{children}</RootDocument>;
}
