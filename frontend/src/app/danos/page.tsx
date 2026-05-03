"use client";

import { useCallback, useMemo, useState } from "react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import {
  Card,
  Button,
  Input,
  Select,
  Tabs,
  LoadingSpinner,
  Table,
  MetricCard,
  ProgressBar,
} from "@/components/ui";
import DownloadButton from "@/components/download/DownloadButton";
import { useCalculation } from "@/hooks/useCalculation";
import { danosApi } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import type {
  AutoRequest,
  AutoResponse,
  IncendioRequest,
  IncendioResponse,
  RCRequest,
  RCResponse,
  BonusMalusRequest,
  BonusMalusResponse,
  FrecuenciaSeveridadRequest,
  FrecuenciaSeveridadResponse,
} from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n/translations";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

/* ── Types ─────────────────────────────────────────────────────────────── */

type DanosTab = "auto" | "incendio" | "rc" | "bonus_malus" | "freq_sev";

interface AutoFormState {
  valor_vehiculo: number;
  tipo_vehiculo: string;
  antiguedad_anos: number;
  zona: string;
  edad_conductor: number;
  deducible_pct: number;
}

interface IncendioFormState {
  valor_inmueble: number;
  tipo_construccion: string;
  zona: string;
  uso: string;
}

interface RCFormState {
  limite_responsabilidad: number;
  deducible: number;
  clase_actividad: string;
}

interface BonusMalusFormState {
  nivel_actual: number;
  numero_siniestros: number;
}

interface FreqSevFormState {
  dist_frecuencia: string;
  param_freq_lambda: number;
  dist_severidad: string;
  param_sev_mu: number;
  param_sev_sigma: number;
  n_simulaciones: number;
  seed: number;
}

/* ── Chart colors ────────────────────────────────────────────────────── */

const CHART_COLORS = {
  navy: "#1B2A4A",
  terracotta: "#C17654",
  sage: "#7A9E7E",
  amber: "#D4A853",
  cream: "#F5F0EA",
};

const COVERAGE_COLORS = [
  CHART_COLORS.terracotta,
  CHART_COLORS.navy,
  CHART_COLORS.sage,
  CHART_COLORS.amber,
  "#8B5A6B",
  "#4A7C8B",
  "#9B8B6B",
  "#6B4A8B",
];

/* ── Defaults ──────────────────────────────────────────────────────────── */

const DEFAULT_AUTO: AutoFormState = {
  valor_vehiculo: 350_000,
  tipo_vehiculo: "sedan_compacto",
  antiguedad_anos: 3,
  zona: "ciudad_mexico",
  edad_conductor: 35,
  deducible_pct: 5,
};

const DEFAULT_INCENDIO: IncendioFormState = {
  valor_inmueble: 2_000_000,
  tipo_construccion: "concreto",
  zona: "ciudad_mexico",
  uso: "habitacional",
};

const DEFAULT_RC: RCFormState = {
  limite_responsabilidad: 5_000_000,
  deducible: 50_000,
  clase_actividad: "oficinas",
};

const DEFAULT_BM: BonusMalusFormState = {
  nivel_actual: 0,
  numero_siniestros: 0,
};

const DEFAULT_FS: FreqSevFormState = {
  dist_frecuencia: "poisson",
  param_freq_lambda: 2.5,
  dist_severidad: "lognormal",
  param_sev_mu: 10.0,
  param_sev_sigma: 1.5,
  n_simulaciones: 10_000,
  seed: 42,
};

/* ── Page component ────────────────────────────────────────────────────── */

export default function DanosPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<DanosTab>("auto");

  /* ── Form state ──────────────────────────────────────────────────────── */

  const [autoForm, setAutoForm] = useState<AutoFormState>(DEFAULT_AUTO);
  const [incendioForm, setIncendioForm] = useState<IncendioFormState>(DEFAULT_INCENDIO);
  const [rcForm, setRCForm] = useState<RCFormState>(DEFAULT_RC);
  const [bmForm, setBMForm] = useState<BonusMalusFormState>(DEFAULT_BM);
  const [fsForm, setFSForm] = useState<FreqSevFormState>(DEFAULT_FS);

  /* ── API hooks ──────────────────────────────────────────────────────── */

  const auto = useCalculation<AutoRequest, AutoResponse>(danosApi.auto);
  const incendio = useCalculation<IncendioRequest, IncendioResponse>(danosApi.incendio);
  const rc = useCalculation<RCRequest, RCResponse>(danosApi.rc);
  const bonusMalus = useCalculation<BonusMalusRequest, BonusMalusResponse>(danosApi.bonusMalus);
  const freqSev = useCalculation<FrecuenciaSeveridadRequest, FrecuenciaSeveridadResponse>(
    danosApi.frecuenciaSeveridad,
  );

  /* ── Tabs definition ────────────────────────────────────────────────── */

  const tabs = useMemo(
    () => [
      { id: "auto", label: t("danos_auto") },
      { id: "incendio", label: t("danos_incendio") },
      { id: "rc", label: t("danos_rc") },
      { id: "bonus_malus", label: t("danos_bonus_malus") },
      { id: "freq_sev", label: t("danos_frecuencia_severidad") },
    ],
    [t],
  );

  /* ── Select options ─────────────────────────────────────────────────── */

  const tipoVehiculoOptions = useMemo(
    () => [
      { value: "sedan_compacto", label: t("vehiculo_sedan_compacto") },
      { value: "sedan_mediano", label: t("vehiculo_sedan_mediano") },
      { value: "sedan_lujo", label: t("vehiculo_sedan_lujo") },
      { value: "suv_compacto", label: t("vehiculo_suv_compacto") },
      { value: "suv_mediano", label: t("vehiculo_suv_mediano") },
      { value: "suv_lujo", label: t("vehiculo_suv_lujo") },
      { value: "pickup", label: t("vehiculo_pickup") },
      { value: "deportivo", label: t("vehiculo_deportivo") },
      { value: "van", label: t("vehiculo_van") },
      { value: "camion_ligero", label: t("vehiculo_camion_ligero") },
    ],
    [t],
  );

  const zonaOptions = useMemo(
    () => [
      { value: "ciudad_mexico", label: t("zona_ciudad_mexico") },
      { value: "guadalajara", label: t("zona_guadalajara") },
      { value: "monterrey", label: t("zona_monterrey") },
      { value: "puebla", label: t("zona_puebla") },
      { value: "queretaro", label: t("zona_queretaro") },
      { value: "merida", label: t("zona_merida") },
      { value: "tijuana", label: t("zona_tijuana") },
      { value: "leon", label: t("zona_leon") },
      { value: "resto_republica", label: t("zona_resto_republica") },
    ],
    [t],
  );

  const tipoConstruccionOptions = useMemo(
    () => [
      { value: "concreto", label: t("construccion_concreto") },
      { value: "mixta", label: t("construccion_mixta") },
      { value: "madera", label: t("construccion_madera") },
      { value: "lamina", label: t("construccion_lamina") },
      { value: "adobe", label: t("construccion_adobe") },
      { value: "prefabricada", label: t("construccion_prefabricada") },
    ],
    [t],
  );

  const usoInmuebleOptions = useMemo(
    () => [
      { value: "habitacional", label: t("uso_habitacional") },
      { value: "comercial", label: t("uso_comercial") },
      { value: "industrial", label: t("uso_industrial") },
      { value: "oficinas", label: t("uso_oficinas") },
    ],
    [t],
  );

  const claseActividadOptions = useMemo(
    () => [
      { value: "oficinas", label: t("actividad_oficinas") },
      { value: "comercio", label: t("actividad_comercio") },
      { value: "manufactura_ligera", label: t("actividad_manufactura_ligera") },
      { value: "manufactura_pesada", label: t("actividad_manufactura_pesada") },
      { value: "construccion", label: t("actividad_construccion") },
      { value: "alimentos", label: t("actividad_alimentos") },
    ],
    [t],
  );

  const distFrecuenciaOptions = useMemo(
    () => [
      { value: "poisson", label: "Poisson" },
      { value: "binomial_negativa", label: t("dist_binomial_negativa") },
    ],
    [t],
  );

  const distSeveridadOptions = useMemo(
    () => [
      { value: "lognormal", label: "Lognormal" },
      { value: "gamma", label: "Gamma" },
      { value: "pareto", label: "Pareto" },
      { value: "weibull", label: "Weibull" },
    ],
    [],
  );

  /* ── Form field updaters ────────────────────────────────────────────── */

  const updateAuto = useCallback(
    <K extends keyof AutoFormState>(field: K, value: AutoFormState[K]) => {
      setAutoForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const updateIncendio = useCallback(
    <K extends keyof IncendioFormState>(field: K, value: IncendioFormState[K]) => {
      setIncendioForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const updateRC = useCallback(
    <K extends keyof RCFormState>(field: K, value: RCFormState[K]) => {
      setRCForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const updateBM = useCallback(
    <K extends keyof BonusMalusFormState>(field: K, value: BonusMalusFormState[K]) => {
      setBMForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const updateFS = useCallback(
    <K extends keyof FreqSevFormState>(field: K, value: FreqSevFormState[K]) => {
      setFSForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  /* ── Calculate handler ──────────────────────────────────────────────── */

  const handleCalculate = useCallback(async () => {
    switch (activeTab) {
      case "auto":
        await auto.calculate({
          valor_vehiculo: autoForm.valor_vehiculo,
          tipo_vehiculo: autoForm.tipo_vehiculo,
          antiguedad_anos: autoForm.antiguedad_anos,
          zona: autoForm.zona,
          edad_conductor: autoForm.edad_conductor,
          deducible_pct: autoForm.deducible_pct / 100,
        });
        break;
      case "incendio":
        await incendio.calculate({
          valor_inmueble: incendioForm.valor_inmueble,
          tipo_construccion: incendioForm.tipo_construccion,
          zona: incendioForm.zona,
          uso: incendioForm.uso,
        });
        break;
      case "rc":
        await rc.calculate({
          limite_responsabilidad: rcForm.limite_responsabilidad,
          deducible: rcForm.deducible,
          clase_actividad: rcForm.clase_actividad,
        });
        break;
      case "bonus_malus":
        await bonusMalus.calculate({
          nivel_actual: bmForm.nivel_actual,
          numero_siniestros: bmForm.numero_siniestros,
        });
        break;
      case "freq_sev": {
        const paramsFrecuencia: Record<string, number> = { lambda: fsForm.param_freq_lambda };
        const paramsSeveridad: Record<string, number> =
          fsForm.dist_severidad === "lognormal"
            ? { mu: fsForm.param_sev_mu, sigma: fsForm.param_sev_sigma }
            : fsForm.dist_severidad === "gamma"
              ? { alpha: fsForm.param_sev_mu, beta: fsForm.param_sev_sigma }
              : fsForm.dist_severidad === "pareto"
                ? { alpha: fsForm.param_sev_mu, xm: fsForm.param_sev_sigma }
                : { k: fsForm.param_sev_mu, lambda: fsForm.param_sev_sigma };
        await freqSev.calculate({
          dist_frecuencia: fsForm.dist_frecuencia,
          params_frecuencia: paramsFrecuencia,
          dist_severidad: fsForm.dist_severidad,
          params_severidad: paramsSeveridad,
          n_simulaciones: fsForm.n_simulaciones,
          seed: fsForm.seed,
        });
        break;
      }
    }
  }, [activeTab, autoForm, incendioForm, rcForm, bmForm, fsForm, auto, incendio, rc, bonusMalus, freqSev]);

  /* ── Derive current loading / error ─────────────────────────────────── */

  const currentHook = {
    auto,
    incendio,
    rc,
    bonus_malus: bonusMalus,
    freq_sev: freqSev,
  }[activeTab];

  const isLoading = currentHook.loading;
  const errorMsg = currentHook.error;

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-navy mb-2">
          {t("danos_titulo")}
        </h1>
        <p className="text-navy/60 text-lg">{t("danos_descripcion")}</p>
        <p className="text-navy/50 text-lg leading-relaxed mt-3">{t("danos_contexto")}</p>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(id) => setActiveTab(id as DanosTab)}
      />

      {/* Calculator form */}
      <Card className="form-depth">
        <div className="space-y-6">
          {/* Auto form */}
          {activeTab === "auto" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("valor_vehiculo")}
                name="valor_vehiculo"
                type="number"
                min={1}
                value={autoForm.valor_vehiculo}
                onChange={(e) => updateAuto("valor_vehiculo", Number(e.target.value))}
              />
              <Select
                label={t("tipo_vehiculo")}
                name="tipo_vehiculo"
                options={tipoVehiculoOptions}
                value={autoForm.tipo_vehiculo}
                onChange={(e) => updateAuto("tipo_vehiculo", e.target.value)}
              />
              <Input
                label={t("antiguedad")}
                name="antiguedad_anos"
                type="number"
                min={0}
                max={30}
                value={autoForm.antiguedad_anos}
                onChange={(e) => updateAuto("antiguedad_anos", Number(e.target.value))}
              />
              <Select
                label={t("zona")}
                name="zona"
                options={zonaOptions}
                value={autoForm.zona}
                onChange={(e) => updateAuto("zona", e.target.value)}
              />
              <Input
                label={t("edad_conductor")}
                name="edad_conductor"
                type="number"
                min={18}
                max={99}
                value={autoForm.edad_conductor}
                onChange={(e) => updateAuto("edad_conductor", Number(e.target.value))}
              />
              <Input
                label={t("danos_deducible_pct")}
                name="deducible_pct"
                type="number"
                step={1}
                min={0}
                max={100}
                value={autoForm.deducible_pct}
                onChange={(e) => updateAuto("deducible_pct", Number(e.target.value))}
              />
            </div>
          )}

          {/* Incendio form */}
          {activeTab === "incendio" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("valor_inmueble")}
                name="valor_inmueble"
                type="number"
                min={1}
                value={incendioForm.valor_inmueble}
                onChange={(e) => updateIncendio("valor_inmueble", Number(e.target.value))}
              />
              <Select
                label={t("tipo_construccion")}
                name="tipo_construccion"
                options={tipoConstruccionOptions}
                value={incendioForm.tipo_construccion}
                onChange={(e) => updateIncendio("tipo_construccion", e.target.value)}
              />
              <Select
                label={t("zona")}
                name="zona_incendio"
                options={zonaOptions}
                value={incendioForm.zona}
                onChange={(e) => updateIncendio("zona", e.target.value)}
              />
              <Select
                label={t("uso_inmueble")}
                name="uso"
                options={usoInmuebleOptions}
                value={incendioForm.uso}
                onChange={(e) => updateIncendio("uso", e.target.value)}
              />
            </div>
          )}

          {/* RC form */}
          {activeTab === "rc" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("limite_responsabilidad")}
                name="limite_responsabilidad"
                type="number"
                min={1}
                value={rcForm.limite_responsabilidad}
                onChange={(e) => updateRC("limite_responsabilidad", Number(e.target.value))}
              />
              <Input
                label={t("deducible")}
                name="deducible"
                type="number"
                min={0}
                value={rcForm.deducible}
                onChange={(e) => updateRC("deducible", Number(e.target.value))}
              />
              <Select
                label={t("clase_actividad")}
                name="clase_actividad"
                options={claseActividadOptions}
                value={rcForm.clase_actividad}
                onChange={(e) => updateRC("clase_actividad", e.target.value)}
              />
            </div>
          )}

          {/* Bonus-Malus form */}
          {activeTab === "bonus_malus" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("danos_nivel_actual")}
                name="nivel_actual"
                type="number"
                min={-5}
                max={10}
                value={bmForm.nivel_actual}
                onChange={(e) => updateBM("nivel_actual", Number(e.target.value))}
              />
              <Input
                label={t("danos_numero_siniestros")}
                name="numero_siniestros"
                type="number"
                min={0}
                value={bmForm.numero_siniestros}
                onChange={(e) => updateBM("numero_siniestros", Number(e.target.value))}
              />
            </div>
          )}

          {/* Frecuencia-Severidad form */}
          {activeTab === "freq_sev" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Select
                label={t("danos_dist_frecuencia")}
                name="dist_frecuencia"
                options={distFrecuenciaOptions}
                value={fsForm.dist_frecuencia}
                onChange={(e) => updateFS("dist_frecuencia", e.target.value)}
              />
              <Input
                label={t("danos_param_lambda")}
                name="param_freq_lambda"
                type="number"
                step={0.1}
                min={0}
                value={fsForm.param_freq_lambda}
                onChange={(e) => updateFS("param_freq_lambda", Number(e.target.value))}
              />
              <Select
                label={t("danos_dist_severidad")}
                name="dist_severidad"
                options={distSeveridadOptions}
                value={fsForm.dist_severidad}
                onChange={(e) => updateFS("dist_severidad", e.target.value)}
              />
              <Input
                label={t("danos_param_1")}
                name="param_sev_mu"
                type="number"
                step={0.1}
                value={fsForm.param_sev_mu}
                onChange={(e) => updateFS("param_sev_mu", Number(e.target.value))}
              />
              <Input
                label={t("danos_param_2")}
                name="param_sev_sigma"
                type="number"
                step={0.1}
                min={0}
                value={fsForm.param_sev_sigma}
                onChange={(e) => updateFS("param_sev_sigma", Number(e.target.value))}
              />
              <Input
                label={t("num_simulaciones")}
                name="n_simulaciones"
                type="number"
                min={100}
                max={100_000}
                value={fsForm.n_simulaciones}
                onChange={(e) => updateFS("n_simulaciones", Number(e.target.value))}
              />
              <Input
                label={t("danos_seed")}
                name="seed"
                type="number"
                min={0}
                value={fsForm.seed}
                onChange={(e) => updateFS("seed", Number(e.target.value))}
              />
            </div>
          )}

          {/* Calculate button */}
          <div className="flex items-center gap-4">
            <Button
              variant="primary"
              size="lg"
              onClick={handleCalculate}
              disabled={isLoading}
            >
              {isLoading ? t("cargando") : t("calcular")}
            </Button>
            {isLoading && <LoadingSpinner size="sm" />}
          </div>
        </div>
      </Card>

      {/* Error display */}
      {errorMsg && (
        <Card className="border-red-300 bg-red-50">
          <p className="text-red-700 font-medium">
            {t("error")}: {errorMsg}
          </p>
        </Card>
      )}

      {/* ── Section divider ─────────────────────────────────────────── */}
      {(auto.data || incendio.data || rc.data || bonusMalus.data || freqSev.data) && (
        <div className="section-divider" />
      )}

      {/* ── Auto results ──────────────────────────────────────────────── */}
      {activeTab === "auto" && auto.data && (
        <AutoResults result={auto.data} t={t} />
      )}

      {/* ── Incendio results ──────────────────────────────────────────── */}
      {activeTab === "incendio" && incendio.data && (
        <IncendioResults result={incendio.data} t={t} />
      )}

      {/* ── RC results ────────────────────────────────────────────────── */}
      {activeTab === "rc" && rc.data && (
        <RCResults result={rc.data} t={t} />
      )}

      {/* ── Bonus-Malus results ───────────────────────────────────────── */}
      {activeTab === "bonus_malus" && bonusMalus.data && (
        <BonusMalusResults result={bonusMalus.data} t={t} />
      )}

      {/* ── Freq-Sev results ──────────────────────────────────────────── */}
      {activeTab === "freq_sev" && freqSev.data && (
        <FreqSevResults result={freqSev.data} t={t} />
      )}
    </div>
  );
}

/* ── Result components ──────────────────────────────────────────────────── */

function AutoResults({
  result,
  t,
}: {
  result: AutoResponse;
  t: (key: TranslationKey) => string;
}) {
  const coverageEntries = Object.entries(result.coberturas);

  const chartData = coverageEntries.map(([key, val]) => ({
    name: key,
    value: val,
  }));

  const vehicleEntries = Object.entries(result.vehiculo);

  const csvData = {
    prima_total: result.prima_total,
    subtotal: result.subtotal,
    ...result.coberturas,
    ...Object.fromEntries(
      Object.entries(result.vehiculo).map(([k, v]) => [`vehiculo_${k}`, v]),
    ),
  } as Record<string, unknown>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MetricCard
          label={t("danos_subtotal")}
          value={formatCurrency(result.subtotal)}
          variant="primary"
        />
        <MetricCard
          label={t("prima_total")}
          value={formatCurrency(result.prima_total)}
          variant="accent"
        />
      </div>

      {/* Coverage breakdown -- horizontal bar chart */}
      {coverageEntries.length > 0 && (
        <Card title={t("coberturas")}>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
              >
                <XAxis
                  type="number"
                  tick={{ fill: CHART_COLORS.navy, fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v: number) =>
                    `$${(v / 1000).toLocaleString("es-MX")}k`
                  }
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fill: CHART_COLORS.navy, fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                  width={120}
                />
                <RechartsTooltip
                  formatter={(value) => [formatCurrency(Number(value)), ""]}
                  contentStyle={{
                    background: CHART_COLORS.navy,
                    border: "none",
                    borderRadius: "8px",
                    color: CHART_COLORS.cream,
                    fontSize: "13px",
                  }}
                />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={24}>
                  {chartData.map((_, i) => (
                    <Cell key={i} fill={COVERAGE_COLORS[i % COVERAGE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      {/* Vehicle info card */}
      {vehicleEntries.length > 0 && (
        <Card title={t("danos_info_vehiculo")}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
            {vehicleEntries.map(([key, val]) => (
              <div key={key} className="flex items-baseline justify-between gap-3 py-1.5 border-b border-navy/5 last:border-0">
                <span className="text-sm text-navy/50 shrink-0">{key}</span>
                <span className="text-sm font-medium text-navy tabular-nums text-right">
                  {String(val)}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <DownloadButton data={csvData} filename="danos_auto" label={t("descargar_csv")} />
    </div>
  );
}

function IncendioResults({
  result,
  t,
}: {
  result: IncendioResponse;
  t: (key: TranslationKey) => string;
}) {
  const csvData = { ...result } as unknown as Record<string, unknown>;

  // Factor pipeline data
  const pipelineSteps = [
    { label: t("danos_tasa_base"), value: formatPercent(result.tasa_base), sublabel: result.tipo_construccion },
    { label: t("danos_factor_zona"), value: formatNumber(result.factor_zona, 4), sublabel: result.zona },
    { label: t("danos_factor_uso"), value: formatNumber(result.factor_uso, 4), sublabel: result.uso },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero metric */}
      <MetricCard
        label={t("danos_prima_anual")}
        value={formatCurrency(result.prima_anual)}
        variant="accent"
        sublabel={`${t("valor_inmueble")}: ${formatCurrency(result.valor_inmueble)}`}
      />

      {/* Factor pipeline */}
      <Card title={t("danos_detalle_calculo")}>
        <div className="flex flex-col sm:flex-row items-stretch gap-3">
          {pipelineSteps.map((step, i) => (
            <div key={i} className="flex items-center gap-3 flex-1">
              <div className="flex-1 bg-navy/[0.03] rounded-lg p-4 text-center">
                <p className="text-xs text-navy/50 uppercase tracking-wide mb-1">
                  {step.label}
                </p>
                <p className="text-xl font-heading font-bold text-navy tabular-nums">
                  {step.value}
                </p>
                <p className="text-xs text-navy/40 mt-1">{step.sublabel}</p>
              </div>
              {i < pipelineSteps.length - 1 && (
                <svg
                  className="w-5 h-5 text-terracotta/40 shrink-0 hidden sm:block"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              )}
            </div>
          ))}
        </div>
      </Card>

      <DownloadButton data={csvData} filename="danos_incendio" label={t("descargar_csv")} />
    </div>
  );
}

function RCResults({
  result,
  t,
}: {
  result: RCResponse;
  t: (key: TranslationKey) => string;
}) {
  const csvData = { ...result } as unknown as Record<string, unknown>;

  const pipelineSteps = [
    { label: t("danos_tasa_base"), value: formatPercent(result.tasa_base), sublabel: result.clase_actividad },
    { label: t("danos_factor_deducible"), value: formatNumber(result.factor_deducible, 4), sublabel: formatCurrency(result.deducible) },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero metric */}
      <MetricCard
        label={t("danos_prima_anual")}
        value={formatCurrency(result.prima_anual)}
        variant="accent"
        sublabel={`${t("limite_responsabilidad")}: ${formatCurrency(result.limite_responsabilidad)}`}
      />

      {/* Factor pipeline */}
      <Card title={t("danos_detalle_calculo")}>
        <div className="flex flex-col sm:flex-row items-stretch gap-3">
          {pipelineSteps.map((step, i) => (
            <div key={i} className="flex items-center gap-3 flex-1">
              <div className="flex-1 bg-navy/[0.03] rounded-lg p-4 text-center">
                <p className="text-xs text-navy/50 uppercase tracking-wide mb-1">
                  {step.label}
                </p>
                <p className="text-xl font-heading font-bold text-navy tabular-nums">
                  {step.value}
                </p>
                <p className="text-xs text-navy/40 mt-1">{step.sublabel}</p>
              </div>
              {i < pipelineSteps.length - 1 && (
                <svg
                  className="w-5 h-5 text-terracotta/40 shrink-0 hidden sm:block"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              )}
            </div>
          ))}
        </div>
      </Card>

      <DownloadButton data={csvData} filename="danos_rc" label={t("descargar_csv")} />
    </div>
  );
}

function BonusMalusResults({
  result,
  t,
}: {
  result: BonusMalusResponse;
  t: (key: TranslationKey) => string;
}) {
  const csvData = { ...result } as unknown as Record<string, unknown>;

  // Gauge scale from -5 to +3 (typical BM range)
  const minLevel = -5;
  const maxLevel = 3;
  const range = maxLevel - minLevel;
  const clampedLevel = Math.max(minLevel, Math.min(maxLevel, result.nivel_nuevo));
  const pctPosition = ((clampedLevel - minLevel) / range) * 100;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MetricCard
          label={t("danos_nivel_nuevo")}
          value={String(result.nivel_nuevo)}
          variant="primary"
          sublabel={`${t("danos_nivel_previo")}: ${result.nivel_previo}`}
        />
        <MetricCard
          label={t("danos_factor_bm")}
          value={formatNumber(result.factor, 4)}
          variant={result.factor > 1 ? "accent" : "default"}
          sublabel={`${t("danos_siniestros")}: ${result.siniestros}`}
        />
      </div>

      {/* Visual gauge */}
      <Card title="Bonus-Malus">
        <div className="space-y-3">
          <div className="relative h-6 rounded-full overflow-hidden">
            {/* Background gradient */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-sage via-amber to-terracotta" />
            {/* Position marker */}
            <div
              className="absolute top-0 h-full w-1.5 bg-navy rounded-full shadow-lg transition-all duration-500 -translate-x-1/2"
              style={{ left: `${pctPosition}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-navy/50">
            <span>{minLevel} (Bonus)</span>
            <span>0</span>
            <span>+{maxLevel} (Malus)</span>
          </div>
        </div>
      </Card>

      <DownloadButton data={csvData} filename="danos_bonus_malus" label={t("descargar_csv")} />
    </div>
  );
}

function FreqSevResults({
  result,
  t,
}: {
  result: FrecuenciaSeveridadResponse;
  t: (key: TranslationKey) => string;
}) {
  const csvData = { ...result } as unknown as Record<string, unknown>;

  const riskMetrics = [
    { label: "VaR 95%", value: formatCurrency(result.var_95) },
    { label: "TVaR 95%", value: formatCurrency(result.tvar_95) },
    { label: "VaR 99%", value: formatCurrency(result.var_99) },
    { label: "TVaR 99%", value: formatCurrency(result.tvar_99) },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MetricCard
          label={t("danos_prima_pura")}
          value={formatCurrency(result.prima_pura)}
          variant="accent"
        />
        <MetricCard
          label="VaR 99%"
          value={formatCurrency(result.var_99)}
          variant="primary"
        />
      </div>

      {/* Risk metrics grid */}
      <Card title={t("danos_estadisticas")}>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {riskMetrics.map((m) => (
            <div key={m.label} className="bg-navy/[0.03] rounded-lg p-4 text-center">
              <p className="text-xs text-navy/50 uppercase tracking-wide mb-1">
                {m.label}
              </p>
              <p className="text-lg font-heading font-bold text-navy tabular-nums">
                {m.value}
              </p>
            </div>
          ))}
        </div>

        {/* Additional stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3 mt-6 pt-4 border-t border-navy/5">
          <div className="flex items-baseline justify-between gap-3 py-1.5 border-b border-navy/5">
            <span className="text-sm text-navy/50">{t("danos_varianza_agregada")}</span>
            <span className="text-sm font-medium text-navy tabular-nums">{formatNumber(result.varianza_agregada)}</span>
          </div>
          <div className="flex items-baseline justify-between gap-3 py-1.5 border-b border-navy/5">
            <span className="text-sm text-navy/50">{t("danos_desviacion_estandar")}</span>
            <span className="text-sm font-medium text-navy tabular-nums">{formatNumber(result.desviacion_estandar)}</span>
          </div>
          <div className="flex items-baseline justify-between gap-3 py-1.5 border-b border-navy/5">
            <span className="text-sm text-navy/50">{t("danos_asimetria")}</span>
            <span className="text-sm font-medium text-navy tabular-nums">{formatNumber(result.asimetria, 4)}</span>
          </div>
          <div className="flex items-baseline justify-between gap-3 py-1.5 border-b border-navy/5">
            <span className="text-sm text-navy/50">{t("num_simulaciones")}</span>
            <span className="text-sm font-medium text-navy tabular-nums">{formatNumber(result.simulaciones, 0)}</span>
          </div>
          <div className="flex items-baseline justify-between gap-3 py-1.5 border-b border-navy/5">
            <span className="text-sm text-navy/50">{t("danos_minimo")}</span>
            <span className="text-sm font-medium text-navy tabular-nums">{formatCurrency(result.minimo)}</span>
          </div>
          <div className="flex items-baseline justify-between gap-3 py-1.5 border-b border-navy/5">
            <span className="text-sm text-navy/50">{t("danos_maximo")}</span>
            <span className="text-sm font-medium text-navy tabular-nums">{formatCurrency(result.maximo)}</span>
          </div>
        </div>
      </Card>

      <DownloadButton data={csvData} filename="danos_frecuencia_severidad" label={t("descargar_csv")} />
    </div>
  );
}
