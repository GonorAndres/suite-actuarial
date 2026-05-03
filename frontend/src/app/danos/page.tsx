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
          deducible_pct: autoForm.deducible_pct,
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
        <p className="text-navy/60 text-lg max-w-3xl mt-2">{t("danos_contexto")}</p>
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
  const coverageRows = Object.entries(result.coberturas).map(([key, val]) => [
    key,
    formatCurrency(val),
  ]);

  const vehicleRows = Object.entries(result.vehiculo).map(([key, val]) => [
    key,
    String(val),
  ]);

  const csvData = {
    prima_total: result.prima_total,
    subtotal: result.subtotal,
    ...result.coberturas,
    ...Object.fromEntries(
      Object.entries(result.vehiculo).map(([k, v]) => [`vehiculo_${k}`, v]),
    ),
  } as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="result-accent">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("danos_subtotal")}</p>
            <p className="text-3xl font-heading font-bold text-navy tabular-nums">
              {formatCurrency(result.subtotal)}
            </p>
          </div>
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("prima_total")}</p>
            <p className="text-3xl font-heading font-bold text-terracotta tabular-nums">
              {formatCurrency(result.prima_total)}
            </p>
          </div>
        </div>
      </Card>

      {coverageRows.length > 0 && (
        <Card title={t("coberturas")}>
          <Table headers={[t("danos_concepto"), t("danos_monto")]} rows={coverageRows} />
        </Card>
      )}

      {vehicleRows.length > 0 && (
        <Card title={t("danos_info_vehiculo")}>
          <Table headers={[t("danos_campo"), t("danos_valor")]} rows={vehicleRows} />
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
  const rows: [string, string][] = [
    [t("valor_inmueble"), formatCurrency(result.valor_inmueble)],
    [t("tipo_construccion"), result.tipo_construccion],
    [t("danos_tasa_base"), formatPercent(result.tasa_base)],
    [t("zona"), result.zona],
    [t("danos_factor_zona"), formatNumber(result.factor_zona, 4)],
    [t("uso_inmueble"), result.uso],
    [t("danos_factor_uso"), formatNumber(result.factor_uso, 4)],
  ];

  const csvData = { ...result } as unknown as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="result-accent">
        <div>
          <p className="text-sm text-navy/60 mb-1">{t("danos_prima_anual")}</p>
          <p className="text-3xl font-heading font-bold text-terracotta tabular-nums">
            {formatCurrency(result.prima_anual)}
          </p>
        </div>
      </Card>

      <Card title={t("danos_detalle_calculo")}>
        <Table headers={[t("danos_campo"), t("danos_valor")]} rows={rows} />
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
  const rows: [string, string][] = [
    [t("limite_responsabilidad"), formatCurrency(result.limite_responsabilidad)],
    [t("deducible"), formatCurrency(result.deducible)],
    [t("clase_actividad"), result.clase_actividad],
    [t("danos_tasa_base"), formatPercent(result.tasa_base)],
    [t("danos_factor_deducible"), formatNumber(result.factor_deducible, 4)],
  ];

  const csvData = { ...result } as unknown as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="result-accent">
        <div>
          <p className="text-sm text-navy/60 mb-1">{t("danos_prima_anual")}</p>
          <p className="text-3xl font-heading font-bold text-terracotta tabular-nums">
            {formatCurrency(result.prima_anual)}
          </p>
        </div>
      </Card>

      <Card title={t("danos_detalle_calculo")}>
        <Table headers={[t("danos_campo"), t("danos_valor")]} rows={rows} />
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
  const rows: [string, string][] = [
    [t("danos_nivel_previo"), String(result.nivel_previo)],
    [t("danos_siniestros"), String(result.siniestros)],
    [t("danos_nivel_nuevo"), String(result.nivel_nuevo)],
    [t("danos_factor_bm"), formatNumber(result.factor, 4)],
  ];

  const csvData = { ...result } as unknown as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="result-accent">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("danos_nivel_nuevo")}</p>
            <p className="text-3xl font-heading font-bold text-navy tabular-nums">
              {result.nivel_nuevo}
            </p>
          </div>
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("danos_factor_bm")}</p>
            <p className="text-3xl font-heading font-bold text-terracotta tabular-nums">
              {formatNumber(result.factor, 4)}
            </p>
          </div>
        </div>
      </Card>

      <Card title={t("danos_detalle_calculo")}>
        <Table headers={[t("danos_campo"), t("danos_valor")]} rows={rows} />
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
  const rows: [string, string][] = [
    [t("danos_prima_pura"), formatCurrency(result.prima_pura)],
    [t("danos_varianza_agregada"), formatNumber(result.varianza_agregada)],
    [t("danos_desviacion_estandar"), formatNumber(result.desviacion_estandar)],
    [t("danos_asimetria"), formatNumber(result.asimetria, 4)],
    ["VaR 95%", formatCurrency(result.var_95)],
    ["TVaR 95%", formatCurrency(result.tvar_95)],
    ["VaR 99%", formatCurrency(result.var_99)],
    ["TVaR 99%", formatCurrency(result.tvar_99)],
    [t("danos_minimo"), formatCurrency(result.minimo)],
    [t("danos_maximo"), formatCurrency(result.maximo)],
    [t("num_simulaciones"), formatNumber(result.simulaciones, 0)],
  ];

  const csvData = { ...result } as unknown as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="result-accent">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("danos_prima_pura")}</p>
            <p className="text-3xl font-heading font-bold text-terracotta tabular-nums">
              {formatCurrency(result.prima_pura)}
            </p>
          </div>
          <div>
            <p className="text-sm text-navy/60 mb-1">VaR 99%</p>
            <p className="text-3xl font-heading font-bold text-navy tabular-nums">
              {formatCurrency(result.var_99)}
            </p>
          </div>
        </div>
      </Card>

      <Card title={t("danos_estadisticas")}>
        <Table headers={[t("danos_metrica"), t("danos_valor")]} rows={rows} />
      </Card>

      <DownloadButton data={csvData} filename="danos_frecuencia_severidad" label={t("descargar_csv")} />
    </div>
  );
}
