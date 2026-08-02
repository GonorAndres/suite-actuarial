"use client";

/**
 * Casos ilustrativos por dominio.
 *
 * Cada dominio expone un caso interactivo que se monta al final de su
 * pagina: una situacion concreta, controles que recalculan contra la API
 * en vivo (useLiveCalculation) y una lectura tecnica del resultado.
 */

import { useMemo, useState } from "react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { useLiveCalculation } from "@/hooks/useLiveCalculation";
import {
  danosApi,
  pensionesApi,
  pricingApi,
  regulatoryApi,
  reinsuranceApi,
  reservesApi,
  saludApi,
} from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Formatting helpers ────────────────────────────────────────────────── */

const mxn0 = (v: number) => formatCurrency(v, 0);

function compactMXN(v: number): string {
  if (v >= 1_000_000)
    return `$${(v / 1_000_000).toLocaleString("es-MX", { maximumFractionDigits: 1 })}M`;
  if (v >= 1_000)
    return `$${(v / 1_000).toLocaleString("es-MX", { maximumFractionDigits: 0 })}k`;
  return `$${v.toLocaleString("es-MX")}`;
}

function compactMillionsMXN(v: number): string {
  return `$${v.toLocaleString("es-MX", { maximumFractionDigits: 1 })} M MXN`;
}

/* ── Building blocks ───────────────────────────────────────────────────── */

function Slider({
  label,
  value,
  min,
  max,
  step,
  onChange,
  format,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  format: (v: number) => string;
}) {
  return (
    <label className="block">
      <span className="flex items-baseline justify-between gap-4 mb-1.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-navy/60">
          {label}
        </span>
        <span className="font-heading font-bold text-navy tabular-nums whitespace-nowrap">
          {format(value)}
        </span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 cursor-pointer accent-terracotta"
      />
    </label>
  );
}

function BigFigure({
  label,
  value,
  loading,
  sub,
}: {
  label: string;
  value: string;
  loading: boolean;
  sub?: string;
}) {
  return (
    <div className="border-t-2 border-t-navy bg-white border border-navy/15 rounded-sm px-5 py-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-navy/60 mb-1">
        {label}
      </p>
      <p
        className={[
          "font-heading font-bold text-2xl sm:text-3xl text-navy tabular-nums transition-opacity duration-200",
          loading ? "opacity-40" : "opacity-100",
        ].join(" ")}
      >
        {value}
      </p>
      {sub && <p className="text-sm text-navy/60 mt-1">{sub}</p>}
    </div>
  );
}

function SplitBar({
  segments,
  total,
}: {
  segments: { label: string; value: number; color: string }[];
  total: number;
}) {
  if (total <= 0) return null;
  return (
    <div className="space-y-2">
      <div className="h-8 rounded-sm overflow-hidden bg-navy/5 flex gap-[2px]">
        {segments.map(
          (seg) =>
            seg.value > 0 && (
              <div
                key={seg.label}
                className="h-full transition-all duration-300 ease-out"
                style={{
                  width: `${(seg.value / total) * 100}%`,
                  backgroundColor: seg.color,
                }}
              />
            ),
        )}
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-1">
        {segments.map((seg) => (
          <span
            key={seg.label}
            className="flex items-center gap-2 text-sm text-navy/80"
          >
            <span
              className="inline-block w-3 h-3 rounded-[2px]"
              style={{ backgroundColor: seg.color }}
            />
            {seg.label}:{" "}
            <span className="font-semibold tabular-nums">{mxn0(seg.value)}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function StorySection({
  title,
  narrative,
  lesson,
  error,
  t,
  children,
}: {
  title: string;
  narrative: string;
  lesson: string;
  error: string | null;
  t: (key: TranslationKey) => string;
  children: React.ReactNode;
}) {
  return (
    <section className="border-t border-navy/15 mt-14 pt-8">
      <div className="grid lg:grid-cols-[1fr_1.2fr] gap-10">
        <div>
          <p className="kicker mb-2">{t("hist_kicker")}</p>
          <h2 className="font-heading font-bold text-2xl text-navy mb-4">{title}</h2>
          <p className="text-navy/75 leading-relaxed">{narrative}</p>
          <p className="text-sm text-navy/50 mt-4">{t("hist_recalculo")}</p>
        </div>
        <div className="space-y-5">
          {error ? (
            <div className="border border-terracotta/40 bg-terracotta/5 rounded-sm px-5 py-4 text-sm text-terracotta">
              {t("hist_api_error")}
            </div>
          ) : (
            children
          )}
          <div className="bg-white/55 border border-navy/10 rounded-sm px-5 py-4">
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-navy/60 mb-1.5">
              <span className="inline-block w-5 h-px bg-amber" aria-hidden="true" />
              {t("hist_leccion")}
            </p>
            <p className="text-sm text-navy/80 leading-relaxed">{lesson}</p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── Vida ──────────────────────────────────────────────────────────────── */

export function VidaStory() {
  const { t } = useLanguage();
  const [edad, setEdad] = useState(32);
  const [sa, setSa] = useState(1_500_000);
  const [plazo, setPlazo] = useState(20);

  const req = useMemo(
    () => ({
      edad,
      sexo: "masculino" as const,
      suma_asegurada: sa,
      plazo_years: plazo,
      tasa_interes: 0.055,
      frecuencia_pago: "anual" as const,
    }),
    [edad, sa, plazo],
  );
  const { data, loading, error } = useLiveCalculation(pricingApi.temporal, req);

  return (
    <StorySection
      title={t("hist1_title")}
      narrative={t("hist1_narrativa")}
      lesson={t("hist1_leccion")}
      error={error}
      t={t}
    >
      <Slider
        label={t("hist1_edad")}
        value={edad}
        min={25}
        max={60}
        step={1}
        onChange={setEdad}
        format={(v) => `${v} ${t("hist_anios")}`}
      />
      <Slider
        label={t("hist1_sa")}
        value={sa}
        min={500_000}
        max={5_000_000}
        step={250_000}
        onChange={setSa}
        format={compactMXN}
      />
      <Slider
        label={t("hist1_plazo")}
        value={plazo}
        min={10}
        max={30}
        step={5}
        onChange={setPlazo}
        format={(v) => `${v} ${t("hist_anios")}`}
      />
      <BigFigure
        label={t("hist1_prima_anual")}
        value={data ? mxn0(data.prima_total) : "—"}
        loading={loading}
        sub={
          data
            ? `≈ ${formatCurrency(data.prima_total / 365, 2)} ${t("hist1_por_dia")}`
            : undefined
        }
      />
    </StorySection>
  );
}

/* ── Danos ─────────────────────────────────────────────────────────────── */

const DEDUCIBLES = [0.03, 0.05, 0.1, 0.15, 0.2];

export function DanosStory() {
  const { t } = useLanguage();
  const [dedIdx, setDedIdx] = useState(1);
  const deducible = DEDUCIBLES[dedIdx];

  const req = useMemo(
    () => ({
      valor_vehiculo: 420_000,
      tipo_vehiculo: "sedan_mediano",
      antiguedad_anos: 3,
      zona: "cdmx_norte",
      edad_conductor: 40,
      deducible_pct: deducible,
    }),
    [deducible],
  );
  const { data, loading, error } = useLiveCalculation(danosApi.auto, req);

  return (
    <StorySection
      title={t("hist2_title")}
      narrative={t("hist2_narrativa")}
      lesson={t("hist2_leccion")}
      error={error}
      t={t}
    >
      <Slider
        label={t("hist2_deducible")}
        value={dedIdx}
        min={0}
        max={DEDUCIBLES.length - 1}
        step={1}
        onChange={setDedIdx}
        format={(v) =>
          `${(DEDUCIBLES[v] * 100).toFixed(0)}% (${compactMXN(420_000 * DEDUCIBLES[v])})`
        }
      />
      <p className="text-sm text-navy/60 -mt-2">
        {`${(deducible * 100).toFixed(0)}% ${t("hist2_del_valor")}`}
      </p>
      <BigFigure
        label={t("hist2_prima")}
        value={data ? mxn0(data.prima_total) : "—"}
        loading={loading}
      />
    </StorySection>
  );
}

/* ── Salud ─────────────────────────────────────────────────────────────── */

export function SaludStory() {
  const { t } = useLanguage();
  const [edad, setEdad] = useState(45);

  const req = useMemo(
    () => ({
      edad,
      sexo: "femenino" as const,
      suma_asegurada: 5_000_000,
      deducible: 40_000,
      coaseguro_pct: 0.1,
      tope_coaseguro: 50_000,
      zona: "urbano",
      nivel: "medio",
    }),
    [edad],
  );
  const { data, loading, error } = useLiveCalculation(saludApi.gmm, req);
  const prima = data
    ? Number((data.tarificacion as Record<string, unknown>).prima_ajustada)
    : null;

  return (
    <StorySection
      title={t("hist3_title")}
      narrative={t("hist3_narrativa")}
      lesson={t("hist3_leccion")}
      error={error}
      t={t}
    >
      <Slider
        label={t("hist3_edad")}
        value={edad}
        min={25}
        max={64}
        step={1}
        onChange={setEdad}
        format={(v) => `${v} ${t("hist_anios")}`}
      />
      <BigFigure
        label={t("hist3_prima")}
        value={prima != null && !Number.isNaN(prima) ? mxn0(prima) : "—"}
        loading={loading}
      />
    </StorySection>
  );
}

/* ── Pensiones ─────────────────────────────────────────────────────────── */

export function PensionesStory() {
  const { t } = useLanguage();
  const [semanas, setSemanas] = useState(1800);
  const [salario, setSalario] = useState(2930);
  const [saldo, setSaldo] = useState(1_800_000);

  const req73 = useMemo(
    () => ({
      semanas_cotizadas: semanas,
      salario_promedio_diario: salario,
      edad_retiro: 65,
    }),
    [semanas, salario],
  );
  const req97 = useMemo(
    () => ({
      saldo_afore: saldo,
      edad: 65,
      sexo: "masculino" as const,
      semanas_cotizadas: 1300,
      tasa_interes: 0.035,
    }),
    [saldo],
  );

  const ley73 = useLiveCalculation(pensionesApi.ley73, req73);
  const ley97 = useLiveCalculation(pensionesApi.ley97, req97);

  return (
    <StorySection
      title={t("hist4_title")}
      narrative={t("hist4_narrativa")}
      lesson={t("hist4_leccion")}
      error={ley73.error ?? ley97.error}
      t={t}
    >
      <Slider
        label={t("hist4_semanas")}
        value={semanas}
        min={500}
        max={2500}
        step={50}
        onChange={setSemanas}
        format={(v) => v.toLocaleString("es-MX")}
      />
      <Slider
        label={t("hist4_salario")}
        value={salario}
        min={300}
        max={2930}
        step={10}
        onChange={setSalario}
        format={(v) => formatCurrency(v, 0)}
      />
      <BigFigure
        label={t("hist4_pension73")}
        value={ley73.data ? mxn0(ley73.data.pension_mensual) : "—"}
        loading={ley73.loading}
      />
      <Slider
        label={t("hist4_saldo")}
        value={saldo}
        min={500_000}
        max={5_000_000}
        step={100_000}
        onChange={setSaldo}
        format={compactMXN}
      />
      <BigFigure
        label={t("hist4_pension97")}
        value={ley97.data ? mxn0(ley97.data.renta_vitalicia.pension_mensual) : "—"}
        loading={ley97.loading}
      />
    </StorySection>
  );
}

/* ── Reservas ──────────────────────────────────────────────────────────── */

const TRIANGLE: (number | null)[][] = [
  [12.48, 18.72, 21.58, 23.09, 23.78, 24.02],
  [13.65, 20.475, 23.6, 25.25, 26.01, null],
  [14.82, 22.23, 25.64, 27.43, null, null],
  [16.09, 24.135, 27.83, null, null, null],
  [17.51, 26.265, null, null, null, null],
  [18.93, null, null, null, null, null],
];
const ORIGIN_YEARS = [2019, 2020, 2021, 2022, 2023, 2024];

export function ReservasStory() {
  const { t } = useLanguage();
  const [tailPct, setTailPct] = useState(0);

  const req = useMemo(
    () => ({
      triangle: TRIANGLE,
      origin_years: ORIGIN_YEARS,
      // TRIANGLE viene acumulado; se declara, no se deduce.
      tipo_triangulo: "acumulado" as const,
      metodo_promedio: "weighted" as const,
      calcular_tail_factor: false,
      tail_factor: tailPct > 0 ? 1 + tailPct / 100 : null,
      unidad_monetaria: "millones_mxn" as const,
    }),
    [tailPct],
  );
  const { data, loading, error } = useLiveCalculation(reservesApi.chainLadder, req);

  return (
    <StorySection
      title={t("hist5_title")}
      narrative={t("hist5_narrativa")}
      lesson={t("hist5_leccion")}
      error={error}
      t={t}
    >
      <Slider
        label={t("hist5_cola")}
        value={tailPct}
        min={0}
        max={10}
        step={1}
        onChange={setTailPct}
        format={(v) => (v === 0 ? t("hist5_sin_cola") : `+${v}%`)}
      />
      <div className="grid sm:grid-cols-2 gap-4">
        <BigFigure
          label={t("hist5_reserva")}
          value={data ? compactMillionsMXN(data.reserva_total) : "—"}
          loading={loading}
        />
        <BigFigure
          label={t("hist5_ultimate")}
          value={data ? compactMillionsMXN(data.ultimate_total) : "—"}
          loading={loading}
        />
      </div>
    </StorySection>
  );
}

/* ── Regulatorio ───────────────────────────────────────────────────────── */

export function RegulatorioStory() {
  const { t } = useLanguage();
  const [capital, setCapital] = useState(350_000_000);

  const req = useMemo(
    () => ({
      config_vida: {
        suma_asegurada_total: 2_500_000_000,
        reserva_matematica: 180_000_000,
        edad_promedio_asegurados: 38,
        duracion_promedio_polizas: 12,
        numero_asegurados: 25_000,
      },
      config_danos: {
        primas_retenidas_12m: 450_000_000,
        reserva_siniestros: 120_000_000,
        coeficiente_variacion: 0.15,
        numero_ramos: 2,
      },
      config_inversion: {
        valor_acciones: 90_000_000,
        valor_bonos_gubernamentales: 380_000_000,
        valor_bonos_corporativos: 110_000_000,
        valor_inmuebles: 40_000_000,
      },
      capital_minimo_pagado: capital,
    }),
    [capital],
  );
  const { data, loading, error } = useLiveCalculation(regulatoryApi.rcs, req);

  const cobertura = data ? capital / data.rcs_total : null;
  const sumaModulos = data
    ? data.rcs_suscripcion_vida + data.rcs_suscripcion_danos + data.rcs_inversion
    : null;

  return (
    <StorySection
      title={t("hist6_title")}
      narrative={t("hist6_narrativa")}
      lesson={t("hist6_leccion")}
      error={error}
      t={t}
    >
      <Slider
        label={t("hist6_capital")}
        value={capital}
        min={150_000_000}
        max={500_000_000}
        step={10_000_000}
        onChange={setCapital}
        format={compactMXN}
      />
      <div className="grid sm:grid-cols-2 gap-4">
        <BigFigure
          label={t("hist6_rcs")}
          value={data ? compactMXN(data.rcs_total) : "—"}
          loading={loading}
          sub={
            data && sumaModulos
              ? `${t("hist6_diversificacion")}: ${compactMXN(sumaModulos - data.rcs_total)}`
              : undefined
          }
        />
        <BigFigure
          label={t("hist6_cobertura")}
          value={cobertura ? `${cobertura.toFixed(2)}x` : "—"}
          loading={loading}
          sub={
            data
              ? data.cumple_regulacion
                ? t("hist6_cumple")
                : t("hist6_no_cumple")
              : undefined
          }
        />
      </div>
    </StorySection>
  );
}

/* ── Reaseguro ─────────────────────────────────────────────────────────── */

export function ReaseguroStory() {
  const { t } = useLanguage();
  const [perdida, setPerdida] = useState(50_000_000);

  const req = useMemo(
    () => ({
      retencion: 20_000_000,
      limite: 80_000_000,
      tasa_prima: 0.05,
      vigencia_inicio: "2026-01-01",
      vigencia_fin: "2026-12-31",
      prima_reaseguro_cobrada: 4_000_000,
      siniestros: [
        {
          id_siniestro: "CAT-2026-01",
          fecha_ocurrencia: "2026-03-10",
          monto_bruto: perdida,
          tipo: "evento_catastrofico",
        },
      ],
    }),
    [perdida],
  );
  const { data, loading, error } = useLiveCalculation(
    reinsuranceApi.excessOfLoss,
    req,
  );

  const recuperacion = data ? data.recuperacion_reaseguro : 0;
  const cedente = perdida - recuperacion;

  return (
    <StorySection
      title={t("hist7_title")}
      narrative={t("hist7_narrativa")}
      lesson={t("hist7_leccion")}
      error={error}
      t={t}
    >
      <Slider
        label={t("hist7_perdida")}
        value={perdida}
        min={5_000_000}
        max={200_000_000}
        step={5_000_000}
        onChange={setPerdida}
        format={compactMXN}
      />
      <div className={loading ? "opacity-40 transition-opacity" : "transition-opacity"}>
        <SplitBar
          total={perdida}
          segments={[
            { label: t("hist7_cedente"), value: cedente, color: "#2A5FA8" },
            { label: t("hist7_reasegurador"), value: recuperacion, color: "#BC4B3C" },
          ]}
        />
      </div>
    </StorySection>
  );
}
