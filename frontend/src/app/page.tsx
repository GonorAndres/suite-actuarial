"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { Card, Tabs } from "@/components/ui";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Domain index data ─────────────────────────────────────────────────── */

interface DomainEntry {
  href: string;
  titleKey: TranslationKey;
  descKey: TranslationKey;
}

const DOMAINS: DomainEntry[] = [
  { href: "/vida", titleKey: "nav_vida", descKey: "home_vida_desc" },
  { href: "/danos", titleKey: "nav_danos", descKey: "home_danos_desc" },
  { href: "/salud", titleKey: "nav_salud", descKey: "home_salud_desc" },
  { href: "/pensiones", titleKey: "nav_pensiones", descKey: "home_pensiones_desc" },
  { href: "/reservas", titleKey: "nav_reservas", descKey: "home_reservas_desc" },
  { href: "/regulatorio", titleKey: "nav_regulatorio", descKey: "home_regulatorio_desc" },
  { href: "/reaseguro", titleKey: "nav_reaseguro", descKey: "home_reaseguro_desc" },
];

/* ── Feature highlights data ───────────────────────────────────────────── */

interface Feature {
  titleKey: TranslationKey;
  descKey: TranslationKey;
}

const FEATURES: Feature[] = [
  { titleKey: "feature_regulatory_title", descKey: "feature_regulatory_desc" },
  { titleKey: "feature_opensource_title", descKey: "feature_opensource_desc" },
  { titleKey: "feature_domains_title", descKey: "feature_domains_desc" },
  { titleKey: "feature_bilingual_title", descKey: "feature_bilingual_desc" },
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
    <div className="space-y-20">
      {/* ── Hero: editorial front page ─────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-4">
        <div className="max-w-3xl">
          <p className="kicker mb-4 animate-fade-in">
            {t("nav_regulatorio")} · CNSF · IMSS · SAT
          </p>
          <h1 className="font-heading text-4xl md:text-5xl lg:text-6xl font-bold text-navy leading-[1.08] mb-6 animate-fade-in">
            {t("hero_titulo")}
          </h1>
          <p
            className="text-xl md:text-2xl text-navy/75 font-heading leading-snug mb-4 animate-fade-in"
            style={{ animationDelay: "0.1s" }}
          >
            {t("hero_subtitulo")}
          </p>
          <p
            className="text-base text-navy/60 leading-relaxed mb-10 animate-fade-in"
            style={{ animationDelay: "0.2s" }}
          >
            {t("hero_descripcion")}
          </p>
          <div
            className="flex flex-col sm:flex-row items-start sm:items-center gap-4 animate-fade-in"
            style={{ animationDelay: "0.3s" }}
          >
            <button
              type="button"
              onClick={scrollToGrid}
              className="px-7 py-3 bg-navy text-offwhite rounded-sm text-sm font-semibold uppercase tracking-wider hover:bg-navy/90 transition-colors duration-150"
            >
              {t("hero_cta")}
            </button>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="px-7 py-3 border border-navy/30 text-navy rounded-sm text-sm font-semibold uppercase tracking-wider hover:border-navy hover:bg-navy/5 transition-colors duration-150"
            >
              {t("hero_docs")}
            </a>
          </div>
        </div>
      </section>

      {/* ── "What is suite_actuarial?" ─────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6">
        <hr className="rule-double mb-10" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <h2 className="font-heading text-2xl font-bold text-navy">
            {t("home_what_title")}
          </h2>
          <p className="md:col-span-2 text-navy/65 text-base leading-relaxed">
            {t("home_what_text")}
          </p>
        </div>
      </section>

      {/* ── Domain index: numbered editorial entries ───────────────────── */}
      <section id="calculators-grid" className="max-w-6xl mx-auto px-6 scroll-mt-24">
        <hr className="rule-double mb-10" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-10 gap-y-2">
          {DOMAINS.map((domain, i) => (
            <Link
              key={domain.href}
              href={domain.href}
              className="group block border-t border-navy/15 py-5 animate-fade-in-up"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="flex items-baseline gap-4">
                <span className="font-heading text-sm text-terracotta tabular-nums shrink-0">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3 className="font-heading text-xl font-bold text-navy mb-1.5 group-hover:text-terracotta transition-colors duration-150">
                    {t(domain.titleKey)}
                    <span
                      aria-hidden="true"
                      className="inline-block ml-2 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-150"
                    >
                      →
                    </span>
                  </h3>
                  <p className="text-sm text-navy/60 leading-relaxed">
                    {t(domain.descKey)}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── Quick Start Python tutorial ─────────────────────────────────── */}
      <QuickStartSection />

      {/* ── Features: ruled editorial columns ──────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6">
        <hr className="rule-double mb-10" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">
          {FEATURES.map((feature, i) => (
            <div
              key={feature.titleKey}
              style={{ animationDelay: `${i * 0.07}s` }}
              className="animate-fade-in-up"
            >
              <p className="kicker mb-3">
                {String(i + 1).padStart(2, "0")}
              </p>
              <h3 className="font-heading text-lg font-bold text-navy mb-2">
                {t(feature.titleKey)}
              </h3>
              <p className="text-sm text-navy/60 leading-relaxed">
                {t(feature.descKey)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Community / Contribute ─────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        <hr className="rule-double mb-10" />
        <div className="max-w-2xl">
          <h2 className="font-heading text-2xl font-bold text-navy mb-3">
            {t("community_title")}
          </h2>
          <p className="text-navy/60 leading-relaxed mb-6">
            {t("community_text")}
          </p>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-2.5 bg-terracotta text-offwhite rounded-sm text-sm font-semibold uppercase tracking-wider hover:bg-terracotta/90 transition-colors duration-150"
            >
              {t("community_cta")}
            </a>
            <a
              href={`${GITHUB_URL}/issues`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-2.5 border border-navy/30 text-navy rounded-sm text-sm font-semibold uppercase tracking-wider hover:border-navy hover:bg-navy/5 transition-colors duration-150"
            >
              {t("community_discuss")}
            </a>
          </div>
        </div>
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
      <hr className="rule-double mb-10" />
      <Card>
        <div className="mb-6">
          <h2 className="font-heading text-2xl font-bold text-navy mb-2">
            {t("quickstart_title")}
          </h2>
          <p className="text-navy/60">{t("quickstart_subtitle")}</p>
        </div>

        <Tabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          className="mb-6"
        />

        <div className="relative rounded-sm overflow-hidden border border-navy/20">
          <div className="absolute top-0 left-0 right-0 h-9 bg-[#131722] border-b border-white/10 flex items-center px-4">
            <span className="text-xs text-white/50 font-mono">python</span>
          </div>
          <pre className="bg-[#1A2028] text-[#D5DBE3] p-6 pt-13 overflow-x-auto text-sm leading-relaxed font-mono">
            <code>{code}</code>
          </pre>
        </div>

        {activeTab === "install" && (
          <div className="mt-4 space-y-3">
            <p className="text-sm text-navy/55">{t("quickstart_pip_note")}</p>
            <div className="rounded-sm bg-cream px-4 py-3 border border-navy/10">
              <p className="text-xs text-navy/55 mb-1">
                {t("quickstart_api_note")}
              </p>
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
