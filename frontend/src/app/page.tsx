"use client";

import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { Card } from "@/components/ui";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Domain card data ──────────────────────────────────────────────────── */

interface DomainCard {
  href: string;
  titleKey: TranslationKey;
  descKey: TranslationKey;
  icon: string; // unicode symbol
}

const DOMAINS: DomainCard[] = [
  { href: "/vida", titleKey: "nav_vida", descKey: "home_vida_desc", icon: "❤" },
  { href: "/danos", titleKey: "nav_danos", descKey: "home_danos_desc", icon: "⚠" },
  { href: "/salud", titleKey: "nav_salud", descKey: "home_salud_desc", icon: "⚕" },
  { href: "/pensiones", titleKey: "nav_pensiones", descKey: "home_pensiones_desc", icon: "⏳" },
  { href: "/reservas", titleKey: "nav_reservas", descKey: "home_reservas_desc", icon: "Δ" },
  { href: "/regulatorio", titleKey: "nav_regulatorio", descKey: "home_regulatorio_desc", icon: "⚖" },
  { href: "/reaseguro", titleKey: "nav_reaseguro", descKey: "home_reaseguro_desc", icon: "⇄" },
];

/* ── Feature highlights data ───────────────────────────────────────────── */

interface Feature {
  titleKey: TranslationKey;
  descKey: TranslationKey;
  svg: string; // SVG path for geometric icon
}

const FEATURES: Feature[] = [
  {
    titleKey: "feature_regulatory_title",
    descKey: "feature_regulatory_desc",
    svg: "M3 6l9-4 9 4v6c0 5.6-3.8 10.7-9 12-5.2-1.3-9-6.4-9-12V6z",
  },
  {
    titleKey: "feature_opensource_title",
    descKey: "feature_opensource_desc",
    svg: "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.4 0-8-3.6-8-8s3.6-8 8-8 8 3.6 8 8-3.6 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z",
  },
  {
    titleKey: "feature_domains_title",
    descKey: "feature_domains_desc",
    svg: "M4 4h16v16H4V4zm2 2v5h5V6H6zm7 0v5h5V6h-5zM6 13v5h5v-5H6zm7 0v5h5v-5h-5z",
  },
  {
    titleKey: "feature_bilingual_title",
    descKey: "feature_bilingual_desc",
    svg: "M12.87 15.07l-2.54-2.51.03-.03A17.52 17.52 0 0014.07 6H17V4h-7V2H8v2H1v2h11.17C11.5 7.92 10.44 9.75 9 11.35 8.07 10.32 7.3 9.19 6.69 8h-2c.73 1.63 1.73 3.17 2.98 4.56l-5.09 5.02L4 19l5-5 3.11 3.11.76-2.04M18.5 10h-2L12 22h2l1.12-3h4.75L21 22h2l-4.5-12zm-2.62 7l1.62-4.33L19.12 17h-3.24z",
  },
];

const GITHUB_URL = "https://github.com/GonorAndres/suite-actuarial";

/* ── Page component ────────────────────────────────────────────────────── */

export default function Home() {
  const { t } = useLanguage();

  const scrollToGrid = () => {
    const el = document.getElementById("calculators-grid");
    el?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="space-y-24">
      {/* ── Hero section ──────────────────────────────────────────────── */}
      <section className="relative max-w-6xl mx-auto px-6 pt-20 pb-16 text-center overflow-hidden">
        {/* Decorative geometric accent */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          {/* Top-right decorative circle */}
          <div
            className="absolute -top-20 -right-20 w-80 h-80 rounded-full opacity-[0.04]"
            style={{ background: "radial-gradient(circle, #C17654, transparent 70%)" }}
          />
          {/* Bottom-left decorative circle */}
          <div
            className="absolute -bottom-16 -left-16 w-64 h-64 rounded-full opacity-[0.03]"
            style={{ background: "radial-gradient(circle, #D4A574, transparent 70%)" }}
          />
          {/* Thin horizontal accent line */}
          <div
            className="absolute top-1/2 left-1/2 -translate-x-1/2 w-96 h-px"
            style={{ background: "linear-gradient(90deg, transparent, rgba(212,165,116,0.2), transparent)" }}
          />
        </div>

        <div className="relative z-10">
          <h1 className="font-heading text-4xl md:text-5xl lg:text-6xl font-bold text-navy mb-5 animate-fade-in">
            {t("hero_titulo")}
          </h1>
          <p className="text-lg md:text-xl text-navy/70 max-w-2xl mx-auto mb-4 animate-fade-in" style={{ animationDelay: "0.1s" }}>
            {t("hero_subtitulo")}
          </p>
          <p className="text-base text-navy/55 max-w-3xl mx-auto mb-10 animate-fade-in" style={{ animationDelay: "0.2s" }}>
            {t("hero_descripcion")}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in" style={{ animationDelay: "0.3s" }}>
            <button
              type="button"
              onClick={scrollToGrid}
              className="px-8 py-3.5 bg-terracotta text-cream rounded-full font-medium hover:bg-terracotta/90 hover:shadow-lg hover:shadow-terracotta/20 transition-all duration-200"
            >
              {t("hero_cta")}
            </button>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-3.5 border border-amber/40 text-navy/70 rounded-full font-medium hover:bg-amber/10 hover:text-terracotta transition-all duration-200"
            >
              {t("hero_docs")}
            </a>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="mt-14 flex justify-center animate-bounce-down">
          <svg
            className="w-6 h-6 text-amber/60"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </section>

      {/* ── "What is suite_actuarial?" section ─────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6">
        <Card>
          <h2 className="font-heading text-xl font-bold text-navy mb-3">
            {t("home_what_title")}
          </h2>
          <p className="text-navy/60 text-base leading-relaxed">
            {t("home_what_text")}
          </p>
        </Card>
      </section>

      {/* ── Domain cards grid ─────────────────────────────────────────── */}
      <section id="calculators-grid" className="max-w-6xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {DOMAINS.map((domain, i) => (
            <Link
              key={domain.href}
              href={domain.href}
              className="block animate-fade-in-up"
              style={{ animationDelay: `${i * 0.07}s` }}
            >
              <Card hoverable className="h-full">
                <div className="text-3xl mb-3" aria-hidden="true">
                  {domain.icon}
                </div>
                <h3 className="font-heading text-lg font-bold text-navy mb-2">
                  {t(domain.titleKey)}
                </h3>
                <p className="text-sm text-navy/60 leading-relaxed">
                  {t(domain.descKey)}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* ── Features section ──────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        {/* Section divider */}
        <div className="section-divider mb-16" />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {FEATURES.map((feature, i) => (
            <div
              key={feature.titleKey}
              style={{ animationDelay: `${i * 0.1}s` }}
              className="text-center animate-fade-in-up"
            >
              <Card className="h-full">
                {/* SVG geometric icon */}
                <div className="flex justify-center mb-4">
                  <div className="w-12 h-12 rounded-xl bg-terracotta/10 flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-terracotta"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path d={feature.svg} />
                    </svg>
                  </div>
                </div>
                <h3 className="font-heading text-base font-bold text-navy mb-2">
                  {t(feature.titleKey)}
                </h3>
                <p className="text-sm text-navy/60 leading-relaxed">
                  {t(feature.descKey)}
                </p>
              </Card>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
