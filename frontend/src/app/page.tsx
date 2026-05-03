"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { Card, Tabs } from "@/components/ui";
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

      {/* ── Quick Start Python tutorial ─────────────────────────────── */}
      <QuickStartSection />

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

      {/* ── Community / Contribute section ────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <Card className="text-center">
          <div className="max-w-2xl mx-auto">
            <div className="flex justify-center mb-4">
              <div className="w-14 h-14 rounded-full bg-sage/15 flex items-center justify-center">
                <svg className="w-7 h-7 text-sage" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" />
                </svg>
              </div>
            </div>
            <h2 className="font-heading text-2xl font-bold text-navy mb-3">
              {t("community_title")}
            </h2>
            <p className="text-navy/55 leading-relaxed mb-6">
              {t("community_text")}
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <a
                href="https://github.com/GonorAndres/suite-actuarial"
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-2.5 bg-sage text-cream rounded-full font-medium hover:bg-sage/90 transition-all duration-200"
              >
                {t("community_cta")}
              </a>
              <a
                href="https://github.com/GonorAndres/suite-actuarial/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-2.5 border border-sage/40 text-navy/60 rounded-full font-medium hover:bg-sage/10 hover:text-sage transition-all duration-200"
              >
                {t("community_discuss")}
              </a>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}

/* ── Quick Start Python Tutorial ──────────────────────────────────────── */

const CODE_SNIPPETS = {
  install: `# Instalar desde GitHub
pip install git+https://github.com/GonorAndres/suite-actuarial.git

# O clonar y desarrollar localmente
git clone https://github.com/GonorAndres/suite-actuarial.git
cd suite-actuarial
pip install -e ".[dev]"`,

  vida: `from suite_actuarial import VidaTemporal, TablaMortalidad
from suite_actuarial import Asegurado, ConfiguracionProducto
from decimal import Decimal

# Cargar tabla de mortalidad EMSSA-09
tabla = TablaMortalidad.cargar_emssa09()

# Configurar producto: temporal 20 años, tasa 5.5%
config = ConfiguracionProducto(
    nombre_producto="Temporal 20",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),
)

# Crear asegurado: hombre, 35 años, $1M de suma asegurada
asegurado = Asegurado(
    edad=35, sexo="H",
    suma_asegurada=Decimal("1000000"),
)

# Calcular prima
producto = VidaTemporal(tabla_mortalidad=tabla, config=config)
resultado = producto.calcular_prima(asegurado)

print(f"Prima neta:  \${float(resultado.prima_neta):,.2f} MXN")
print(f"Prima total: \${float(resultado.prima_total):,.2f} MXN")
# -> Prima neta:  $2,024.08 MXN
# -> Prima total: $2,388.42 MXN`,

  pension: `from suite_actuarial import PensionLey73
from decimal import Decimal

# Calcular pensión IMSS Ley 73
pension = PensionLey73(
    semanas_cotizadas=1500,
    salario_promedio_diario=Decimal("800"),
    edad_retiro=65,
)

resumen = pension.resumen()
print(f"Pensión mensual: \${resumen['pension_mensual']:,.2f} MXN")
print(f"Porcentaje:      {resumen['porcentaje_pension']:.1%}")
print(f"Aguinaldo anual: \${resumen['aguinaldo_anual']:,.2f} MXN")
# -> Pensión mensual: $18,506.03 MXN
# -> Porcentaje:      77.1%
# -> Aguinaldo anual: $18,506.03 MXN`,

  reservas: `from suite_actuarial.reservas.chain_ladder import ChainLadder
from suite_actuarial.core.validators import ConfiguracionChainLadder

# Triángulo de desarrollo acumulado
triangle = [
    [3000, 5000, 5600, 5800, 5900],
    [3200, 5200, 5800, 6000, None],
    [3500, 5500, 6100, None, None],
    [3800, 5900, None, None, None],
    [4000, None, None, None, None],
]

config = ConfiguracionChainLadder(
    triangulo=triangle,
    anios_origen=[2019, 2020, 2021, 2022, 2023],
)

resultado = ChainLadder(config).calcular()
print(f"Reserva IBNR total: \${float(resultado.reserva_total):,.2f}")
print(f"Ultimate total:     \${float(resultado.ultimate_total):,.2f}")
# -> Reserva IBNR total: $4,983.22
# -> Ultimate total:     $32,883.22`,
};

const QUICKSTART_TABS = [
  { id: "install", labelKey: "quickstart_tab_install" as TranslationKey },
  { id: "vida", labelKey: "quickstart_tab_vida" as TranslationKey },
  { id: "pension", labelKey: "quickstart_tab_pension" as TranslationKey },
  { id: "reservas", labelKey: "quickstart_tab_reservas" as TranslationKey },
];

function QuickStartSection() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState("install");

  const tabs = QUICKSTART_TABS.map((tab) => ({
    id: tab.id,
    label: t(tab.labelKey),
  }));

  const code = CODE_SNIPPETS[activeTab as keyof typeof CODE_SNIPPETS];

  return (
    <section className="max-w-6xl mx-auto px-6">
      <Card>
        <div className="mb-6">
          <h2 className="font-heading text-2xl font-bold text-navy mb-2">
            {t("quickstart_title")}
          </h2>
          <p className="text-navy/60">
            {t("quickstart_subtitle")}
          </p>
        </div>

        <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} className="mb-6" />

        <div className="relative rounded-xl overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-10 bg-[#1e1e2e] flex items-center px-4 gap-2">
            <div className="w-3 h-3 rounded-full bg-red-400/80" />
            <div className="w-3 h-3 rounded-full bg-amber/80" />
            <div className="w-3 h-3 rounded-full bg-sage/80" />
            <span className="ml-3 text-xs text-white/40 font-mono">python</span>
          </div>
          <pre className="bg-[#1e1e2e] text-[#cdd6f4] p-6 pt-14 overflow-x-auto text-sm leading-relaxed font-mono">
            <code>{code}</code>
          </pre>
        </div>

        {activeTab === "install" && (
          <div className="mt-4 space-y-3">
            <p className="text-sm text-navy/50">
              {t("quickstart_pip_note")}
            </p>
            <div className="rounded-lg bg-navy/5 px-4 py-3">
              <p className="text-xs text-navy/50 mb-1">{t("quickstart_api_note")}</p>
              <code className="text-sm text-terracotta font-mono">
                python -m uvicorn suite_actuarial.api.main:app --port 8000
              </code>
            </div>
          </div>
        )}
      </Card>
    </section>
  );
}
