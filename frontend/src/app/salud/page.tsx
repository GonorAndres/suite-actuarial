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
} from "@/components/ui";
import DownloadButton from "@/components/download/DownloadButton";
import { useCalculation } from "@/hooks/useCalculation";
import { saludApi } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import type {
  GMMRequest,
  GMMResponse,
  AccidentesRequest,
  AccidentesResponse,
} from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Types ─────────────────────────────────────────────────────────────── */

type SaludTab = "gmm" | "accidentes";

interface GMMFormState {
  edad: number;
  sexo: "M" | "F";
  suma_asegurada: number;
  deducible: number;
  coaseguro_pct: number;
  tope_coaseguro: string;
  zona: string;
  nivel: string;
}

interface AccidentesFormState {
  edad: number;
  sexo: "M" | "F";
  suma_asegurada: number;
  ocupacion: string;
  indemnizacion_diaria: string;
}

/* ── Defaults ──────────────────────────────────────────────────────────── */

const DEFAULT_GMM: GMMFormState = {
  edad: 35,
  sexo: "M",
  suma_asegurada: 5_000_000,
  deducible: 50_000,
  coaseguro_pct: 0.10,
  tope_coaseguro: "",
  zona: "urbano",
  nivel: "medio",
};

const DEFAULT_ACCIDENTES: AccidentesFormState = {
  edad: 35,
  sexo: "M",
  suma_asegurada: 500_000,
  ocupacion: "oficina",
  indemnizacion_diaria: "",
};

/* ── Page component ────────────────────────────────────────────────────── */

export default function SaludPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<SaludTab>("gmm");

  /* ── Form state ──────────────────────────────────────────────────────── */

  const [gmmForm, setGMMForm] = useState<GMMFormState>(DEFAULT_GMM);
  const [accForm, setAccForm] = useState<AccidentesFormState>(DEFAULT_ACCIDENTES);

  /* ── API hooks ──────────────────────────────────────────────────────── */

  const gmm = useCalculation<GMMRequest, GMMResponse>(saludApi.gmm);
  const accidentes = useCalculation<AccidentesRequest, AccidentesResponse>(saludApi.accidentes);

  /* ── Tabs definition ────────────────────────────────────────────────── */

  const tabs = useMemo(
    () => [
      { id: "gmm", label: t("salud_gmm") },
      { id: "accidentes", label: t("salud_accidentes") },
    ],
    [t],
  );

  /* ── Select options ─────────────────────────────────────────────────── */

  const sexoGMMOptions = useMemo(
    () => [
      { value: "M", label: t("masculino") },
      { value: "F", label: t("femenino") },
    ],
    [t],
  );

  const zonaGMMOptions = useMemo(
    () => [
      { value: "metro", label: t("salud_zona_metro") },
      { value: "urbano", label: t("salud_zona_urbano") },
      { value: "foraneo", label: t("salud_zona_foraneo") },
    ],
    [t],
  );

  const nivelOptions = useMemo(
    () => [
      { value: "estandar", label: t("salud_nivel_estandar") },
      { value: "medio", label: t("salud_nivel_medio") },
      { value: "alto", label: t("salud_nivel_alto") },
    ],
    [t],
  );

  const ocupacionOptions = useMemo(
    () => [
      { value: "oficina", label: t("salud_ocup_oficina") },
      { value: "comercio", label: t("salud_ocup_comercio") },
      { value: "industrial_ligero", label: t("salud_ocup_industrial_ligero") },
      { value: "industrial_pesado", label: t("salud_ocup_industrial_pesado") },
      { value: "alto_riesgo", label: t("salud_ocup_alto_riesgo") },
    ],
    [t],
  );

  /* ── Form field updaters ────────────────────────────────────────────── */

  const updateGMM = useCallback(
    <K extends keyof GMMFormState>(field: K, value: GMMFormState[K]) => {
      setGMMForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const updateAcc = useCallback(
    <K extends keyof AccidentesFormState>(field: K, value: AccidentesFormState[K]) => {
      setAccForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  /* ── Calculate handler ──────────────────────────────────────────────── */

  const handleCalculate = useCallback(async () => {
    switch (activeTab) {
      case "gmm":
        await gmm.calculate({
          edad: gmmForm.edad,
          sexo: gmmForm.sexo,
          suma_asegurada: gmmForm.suma_asegurada,
          deducible: gmmForm.deducible,
          coaseguro_pct: gmmForm.coaseguro_pct,
          tope_coaseguro: gmmForm.tope_coaseguro ? Number(gmmForm.tope_coaseguro) : undefined,
          zona: gmmForm.zona,
          nivel: gmmForm.nivel,
        });
        break;
      case "accidentes":
        await accidentes.calculate({
          edad: accForm.edad,
          sexo: accForm.sexo,
          suma_asegurada: accForm.suma_asegurada,
          ocupacion: accForm.ocupacion,
          indemnizacion_diaria: accForm.indemnizacion_diaria
            ? Number(accForm.indemnizacion_diaria)
            : undefined,
        });
        break;
    }
  }, [activeTab, gmmForm, accForm, gmm, accidentes]);

  /* ── Derive current loading / error ─────────────────────────────────── */

  const currentHook = {
    gmm,
    accidentes,
  }[activeTab];

  const isLoading = currentHook.loading;
  const errorMsg = currentHook.error;

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-navy mb-2">
          {t("salud_titulo")}
        </h1>
        <p className="text-navy/60 text-lg">{t("salud_descripcion")}</p>
        <p className="text-navy/50 text-lg leading-relaxed mt-3">{t("salud_contexto")}</p>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(id) => setActiveTab(id as SaludTab)}
      />

      {/* Calculator form */}
      <Card className="form-depth">
        <div className="space-y-6">
          {/* GMM form */}
          {activeTab === "gmm" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("edad")}
                name="edad"
                type="number"
                min={0}
                max={99}
                value={gmmForm.edad}
                onChange={(e) => updateGMM("edad", Number(e.target.value))}
              />
              <Select
                label={t("sexo")}
                name="sexo"
                options={sexoGMMOptions}
                value={gmmForm.sexo}
                onChange={(e) => updateGMM("sexo", e.target.value as "M" | "F")}
              />
              <Input
                label={t("suma_asegurada")}
                name="suma_asegurada"
                type="number"
                min={1}
                value={gmmForm.suma_asegurada}
                onChange={(e) => updateGMM("suma_asegurada", Number(e.target.value))}
              />
              <Input
                label={t("deducible")}
                name="deducible"
                type="number"
                min={0}
                value={gmmForm.deducible}
                onChange={(e) => updateGMM("deducible", Number(e.target.value))}
              />
              <Input
                label={t("coaseguro")}
                name="coaseguro_pct"
                type="number"
                step={0.01}
                min={0}
                max={1}
                value={gmmForm.coaseguro_pct}
                onChange={(e) => updateGMM("coaseguro_pct", Number(e.target.value))}
              />
              <Input
                label={t("tope_coaseguro")}
                name="tope_coaseguro"
                type="number"
                min={0}
                value={gmmForm.tope_coaseguro}
                onChange={(e) => updateGMM("tope_coaseguro", e.target.value)}
              />
              <Select
                label={t("zona_geografica")}
                name="zona"
                options={zonaGMMOptions}
                value={gmmForm.zona}
                onChange={(e) => updateGMM("zona", e.target.value)}
              />
              <Select
                label={t("nivel_hospitalario")}
                name="nivel"
                options={nivelOptions}
                value={gmmForm.nivel}
                onChange={(e) => updateGMM("nivel", e.target.value)}
              />
            </div>
          )}

          {/* Accidentes form */}
          {activeTab === "accidentes" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("edad")}
                name="edad_acc"
                type="number"
                min={0}
                max={99}
                value={accForm.edad}
                onChange={(e) => updateAcc("edad", Number(e.target.value))}
              />
              <Select
                label={t("sexo")}
                name="sexo_acc"
                options={sexoGMMOptions}
                value={accForm.sexo}
                onChange={(e) => updateAcc("sexo", e.target.value as "M" | "F")}
              />
              <Input
                label={t("suma_asegurada")}
                name="suma_asegurada_acc"
                type="number"
                min={1}
                value={accForm.suma_asegurada}
                onChange={(e) => updateAcc("suma_asegurada", Number(e.target.value))}
              />
              <Select
                label={t("ocupacion")}
                name="ocupacion"
                options={ocupacionOptions}
                value={accForm.ocupacion}
                onChange={(e) => updateAcc("ocupacion", e.target.value)}
              />
              <Input
                label={t("indemnizacion_diaria")}
                name="indemnizacion_diaria"
                type="number"
                min={0}
                value={accForm.indemnizacion_diaria}
                onChange={(e) => updateAcc("indemnizacion_diaria", e.target.value)}
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
      {(gmm.data || accidentes.data) && (
        <div className="section-divider" />
      )}

      {/* ── GMM results ───────────────────────────────────────────────── */}
      {activeTab === "gmm" && gmm.data && (
        <GMMResults result={gmm.data} t={t} />
      )}

      {/* ── Accidentes results ────────────────────────────────────────── */}
      {activeTab === "accidentes" && accidentes.data && (
        <AccidentesResults result={accidentes.data} t={t} />
      )}
    </div>
  );
}

/* ── Result components ──────────────────────────────────────────────────── */

function GMMResults({
  result,
  t,
}: {
  result: GMMResponse;
  t: (key: TranslationKey) => string;
}) {
  const aseguradoRows = Object.entries(result.asegurado).map(([key, val]) => [
    key,
    String(val),
  ]);

  const productoRows = Object.entries(result.producto).map(([key, val]) => [
    key,
    String(val),
  ]);

  const CURRENCY_KEYS = new Set(["prima_base", "prima_ajustada", "siniestralidad_esperada"]);
  const RATE_KEYS = new Set(["tasa_banda_edad"]);
  const tarificacionRows = Object.entries(result.tarificacion).map(([key, val]) => [
    key,
    typeof val !== "number"
      ? String(val)
      : CURRENCY_KEYS.has(key)
        ? formatCurrency(val)
        : RATE_KEYS.has(key)
          ? `${val.toFixed(2)} ‰`
          : key.startsWith("factor_")
            ? val.toFixed(4)
            : formatNumber(val),
  ]);

  const csvData = {
    siniestralidad_esperada: result.siniestralidad_esperada,
    ...Object.fromEntries(
      Object.entries(result.asegurado).map(([k, v]) => [`asegurado_${k}`, v]),
    ),
    ...Object.fromEntries(
      Object.entries(result.producto).map(([k, v]) => [`producto_${k}`, v]),
    ),
    ...Object.fromEntries(
      Object.entries(result.tarificacion).map(([k, v]) => [`tarificacion_${k}`, v]),
    ),
  } as Record<string, unknown>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero metrics -- premium is the main output */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricCard
          label={t("prima_total")}
          value={formatCurrency(Number(result.tarificacion?.prima_ajustada ?? 0))}
          variant="accent"
        />
        <MetricCard
          label={t("salud_siniestralidad_esperada")}
          value={formatCurrency(result.siniestralidad_esperada)}
          sublabel={t("salud_descripcion")}
          variant="default"
        />
      </div>

      {tarificacionRows.length > 0 && (
        <Card title={t("salud_tarificacion")}>
          <Table headers={[t("danos_concepto"), t("danos_valor")]} rows={tarificacionRows} />
        </Card>
      )}

      {/* Asegurado and Producto as info grids */}
      {(aseguradoRows.length > 0 || productoRows.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {aseguradoRows.length > 0 && (
            <Card title={t("salud_datos_asegurado")}>
              <div className="space-y-2">
                {aseguradoRows.map(([key, val]) => (
                  <div key={String(key)} className="flex items-baseline justify-between gap-3 py-1.5 border-b border-navy/5 last:border-0">
                    <span className="text-sm text-navy/50">{key}</span>
                    <span className="text-sm font-medium text-navy tabular-nums text-right">{val}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
          {productoRows.length > 0 && (
            <Card title={t("salud_datos_producto")}>
              <div className="space-y-2">
                {productoRows.map(([key, val]) => (
                  <div key={String(key)} className="flex items-baseline justify-between gap-3 py-1.5 border-b border-navy/5 last:border-0">
                    <span className="text-sm text-navy/50">{key}</span>
                    <span className="text-sm font-medium text-navy tabular-nums text-right">{val}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      <DownloadButton data={csvData} filename="salud_gmm" label={t("descargar_csv")} />
    </div>
  );
}

function AccidentesResults({
  result,
  t,
}: {
  result: AccidentesResponse;
  t: (key: TranslationKey) => string;
}) {
  const perdidasRows = Object.entries(result.perdidas_organicas).map(([key, val]) => {
    const entry = val as { porcentaje?: number; monto?: number } | number;
    if (typeof entry === "object" && entry !== null && "monto" in entry) {
      return [key, formatPercent(entry.porcentaje ?? 0), formatCurrency(entry.monto ?? 0)];
    }
    return [key, "", typeof entry === "number" ? formatCurrency(entry) : String(entry)];
  });

  const indemnizacionRows = Object.entries(result.indemnizacion_diaria).map(([key, val]) => [
    key,
    formatCurrency(val),
  ]);

  const csvData = {
    suma_asegurada: result.suma_asegurada,
    prima_anual: result.prima_anual,
    gastos_funerarios: result.gastos_funerarios,
    ...Object.fromEntries(
      Object.entries(result.perdidas_organicas).map(([k, v]) => {
        const entry = v as { monto?: number } | number;
        return [`perdida_${k}`, typeof entry === "object" && entry !== null ? entry.monto : entry];
      }),
    ),
    ...Object.fromEntries(
      Object.entries(result.indemnizacion_diaria).map(([k, v]) => [`indemnizacion_${k}`, v]),
    ),
  } as Record<string, unknown>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MetricCard
          label={t("danos_prima_anual")}
          value={formatCurrency(result.prima_anual)}
          variant="accent"
        />
        <MetricCard
          label={t("salud_gastos_funerarios")}
          value={formatCurrency(result.gastos_funerarios)}
          variant="primary"
        />
      </div>

      {perdidasRows.length > 0 && (
        <Card title={t("salud_perdidas_organicas")}>
          <Table headers={[t("danos_concepto"), "%", t("danos_valor")]} rows={perdidasRows} />
        </Card>
      )}

      {indemnizacionRows.length > 0 && (
        <Card title={t("indemnizacion_diaria")}>
          <Table headers={[t("danos_concepto"), t("danos_valor")]} rows={indemnizacionRows} />
        </Card>
      )}

      <DownloadButton data={csvData} filename="salud_accidentes" label={t("descargar_csv")} />
    </div>
  );
}
