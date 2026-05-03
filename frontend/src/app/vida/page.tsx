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
import { pricingApi } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { PricingRequest, PricingResponse, CompareResponse } from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Types ─────────────────────────────────────────────────────────────── */

type ProductTab = "temporal" | "ordinario" | "dotal" | "comparar";

interface FormState {
  edad: number;
  sexo: "H" | "M";
  suma_asegurada: number;
  plazo_years: number;
  tasa_interes: number;
  frecuencia_pago: "anual" | "semestral" | "trimestral" | "mensual";
  recargo_gastos_admin: number;
  recargo_gastos_adq: number;
  recargo_utilidad: number;
}

/* ── Default form values ───────────────────────────────────────────────── */

const DEFAULT_FORM: FormState = {
  edad: 35,
  sexo: "H",
  suma_asegurada: 1_000_000,
  plazo_years: 20,
  tasa_interes: 0.055,
  frecuencia_pago: "anual",
  recargo_gastos_admin: 0.05,
  recargo_gastos_adq: 0.10,
  recargo_utilidad: 0.03,
};

/* ── Result display component ──────────────────────────────────────────── */

function ResultCard({
  result,
  t,
}: {
  result: PricingResponse;
  t: (key: TranslationKey) => string;
}) {
  const recargosRows = Object.entries(result.desglose_recargos).map(
    ([key, val]) => [key, formatCurrency(val)],
  );

  const metadataRows = Object.entries(result.metadata).map(([key, val]) => [
    key,
    String(val),
  ]);

  const csvData = {
    producto: result.producto,
    prima_neta: result.prima_neta,
    prima_total: result.prima_total,
    moneda: result.moneda,
    ...result.desglose_recargos,
    ...Object.fromEntries(
      Object.entries(result.metadata).map(([k, v]) => [`meta_${k}`, v]),
    ),
  } as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Main premiums */}
      <Card className="result-accent">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("prima_neta")}</p>
            <p className="text-3xl font-heading font-bold text-navy tabular-nums">
              {formatCurrency(result.prima_neta)}
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

      {/* Loading breakdown */}
      {recargosRows.length > 0 && (
        <Card title={t("desglose_recargos")}>
          <Table
            headers={["Concepto", "Monto"]}
            rows={recargosRows}
          />
        </Card>
      )}

      {/* Metadata */}
      {metadataRows.length > 0 && (
        <Card title={t("metadata")}>
          <Table headers={["Campo", "Valor"]} rows={metadataRows} />
        </Card>
      )}

      {/* Download */}
      <DownloadButton
        data={csvData}
        filename={`vida_${result.producto}`}
        label={t("descargar_csv")}
      />
    </div>
  );
}

/* ── Page component ────────────────────────────────────────────────────── */

export default function VidaPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<ProductTab>("temporal");
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [showRecargos, setShowRecargos] = useState(false);

  /* ── API hooks ──────────────────────────────────────────────────────── */

  const temporal = useCalculation<PricingRequest, PricingResponse>(
    pricingApi.temporal,
  );
  const ordinario = useCalculation<PricingRequest, PricingResponse>(
    pricingApi.ordinario,
  );
  const dotal = useCalculation<PricingRequest, PricingResponse>(
    pricingApi.dotal,
  );
  const compare = useCalculation<PricingRequest, CompareResponse>(
    pricingApi.compare,
  );

  /* ── Tabs definition ────────────────────────────────────────────────── */

  const tabs = useMemo(
    () => [
      { id: "temporal", label: t("vida_temporal") },
      { id: "ordinario", label: t("vida_ordinario") },
      { id: "dotal", label: t("vida_dotal") },
      { id: "comparar", label: t("vida_comparar") },
    ],
    [t],
  );

  /* ── Form handlers ──────────────────────────────────────────────────── */

  const updateField = useCallback(
    <K extends keyof FormState>(field: K, value: FormState[K]) => {
      setForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const buildRequest = useCallback((): PricingRequest => {
    return {
      edad: form.edad,
      sexo: form.sexo,
      suma_asegurada: form.suma_asegurada,
      plazo_years: form.plazo_years,
      tasa_interes: form.tasa_interes,
      frecuencia_pago: form.frecuencia_pago,
      recargo_gastos_admin: form.recargo_gastos_admin,
      recargo_gastos_adq: form.recargo_gastos_adq,
      recargo_utilidad: form.recargo_utilidad,
    };
  }, [form]);

  const handleCalculate = useCallback(async () => {
    const req = buildRequest();
    switch (activeTab) {
      case "temporal":
        await temporal.calculate(req);
        break;
      case "ordinario":
        await ordinario.calculate(req);
        break;
      case "dotal":
        await dotal.calculate(req);
        break;
      case "comparar":
        await compare.calculate(req);
        break;
    }
  }, [activeTab, buildRequest, temporal, ordinario, dotal, compare]);

  /* ── Derive current loading / error / data ──────────────────────────── */

  const currentHook = {
    temporal,
    ordinario,
    dotal,
    comparar: compare,
  }[activeTab];

  const isLoading = currentHook.loading;
  const errorMsg = currentHook.error;

  /* ── Frequency and sex options ──────────────────────────────────────── */

  const sexOptions = useMemo(
    () => [
      { value: "H", label: t("masculino") },
      { value: "M", label: t("femenino") },
    ],
    [t],
  );

  const freqOptions = useMemo(
    () => [
      { value: "anual", label: t("anual") },
      { value: "semestral", label: t("semestral") },
      { value: "trimestral", label: t("trimestral") },
      { value: "mensual", label: t("mensual") },
    ],
    [t],
  );

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-navy mb-2">
          {t("vida_titulo")}
        </h1>
        <p className="text-navy/60 text-lg">{t("vida_descripcion")}</p>
        <p className="text-navy/60 text-lg max-w-3xl mt-2">{t("vida_contexto")}</p>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(id) => setActiveTab(id as ProductTab)}
      />

      {/* Calculator form */}
      <Card className="form-depth">
        <div className="space-y-6">
          {/* Main inputs */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Input
              label={t("edad")}
              name="edad"
              type="number"
              min={18}
              max={99}
              value={form.edad}
              onChange={(e) => updateField("edad", Number(e.target.value))}
            />
            <Select
              label={t("sexo")}
              name="sexo"
              options={sexOptions}
              value={form.sexo}
              onChange={(e) =>
                updateField("sexo", e.target.value as "H" | "M")
              }
            />
            <Input
              label={t("suma_asegurada")}
              name="suma_asegurada"
              type="number"
              min={1}
              value={form.suma_asegurada}
              onChange={(e) =>
                updateField("suma_asegurada", Number(e.target.value))
              }
            />
            <Input
              label={t("plazo")}
              name="plazo_years"
              type="number"
              min={1}
              max={50}
              value={form.plazo_years}
              onChange={(e) =>
                updateField("plazo_years", Number(e.target.value))
              }
            />
            <Input
              label={t("tasa_interes")}
              name="tasa_interes"
              type="number"
              step={0.001}
              min={0}
              max={1}
              value={form.tasa_interes}
              onChange={(e) =>
                updateField("tasa_interes", Number(e.target.value))
              }
            />
            <Select
              label={t("frecuencia_pago")}
              name="frecuencia_pago"
              options={freqOptions}
              value={form.frecuencia_pago}
              onChange={(e) =>
                updateField(
                  "frecuencia_pago",
                  e.target.value as FormState["frecuencia_pago"],
                )
              }
            />
          </div>

          {/* Recargos (collapsible) */}
          <div>
            <button
              type="button"
              onClick={() => setShowRecargos(!showRecargos)}
              className="flex items-center gap-2 text-sm font-medium text-navy/70 hover:text-terracotta transition-colors"
            >
              <svg
                className={`w-4 h-4 transition-transform ${showRecargos ? "rotate-90" : ""}`}
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
              {t("desglose_recargos")}
            </button>
            {showRecargos && (
              <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label={t("recargo_gastos_admin")}
                  name="recargo_gastos_admin"
                  type="number"
                  step={0.01}
                  min={0}
                  max={1}
                  value={form.recargo_gastos_admin}
                  onChange={(e) =>
                    updateField(
                      "recargo_gastos_admin",
                      Number(e.target.value),
                    )
                  }
                />
                <Input
                  label={t("recargo_gastos_adq")}
                  name="recargo_gastos_adq"
                  type="number"
                  step={0.01}
                  min={0}
                  max={1}
                  value={form.recargo_gastos_adq}
                  onChange={(e) =>
                    updateField(
                      "recargo_gastos_adq",
                      Number(e.target.value),
                    )
                  }
                />
                <Input
                  label={t("recargo_utilidad")}
                  name="recargo_utilidad"
                  type="number"
                  step={0.01}
                  min={0}
                  max={1}
                  value={form.recargo_utilidad}
                  onChange={(e) =>
                    updateField("recargo_utilidad", Number(e.target.value))
                  }
                />
              </div>
            )}
          </div>

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
      {(temporal.data || ordinario.data || dotal.data || compare.data) && (
        <div className="section-divider" />
      )}

      {/* ── Results for single product tabs ──────────────────────────── */}
      {activeTab === "temporal" && temporal.data && (
        <ResultCard result={temporal.data} t={t} />
      )}
      {activeTab === "ordinario" && ordinario.data && (
        <ResultCard result={ordinario.data} t={t} />
      )}
      {activeTab === "dotal" && dotal.data && (
        <ResultCard result={dotal.data} t={t} />
      )}

      {/* ── Compare tab results ──────────────────────────────────────── */}
      {activeTab === "comparar" && compare.data && (
        <CompareResults data={compare.data} t={t} />
      )}
    </div>
  );
}

/* ── Compare results component ─────────────────────────────────────────── */

function CompareResults({
  data,
  t,
}: {
  data: CompareResponse;
  t: (key: TranslationKey) => string;
}) {
  const products = [
    { key: "temporal", label: t("vida_temporal"), result: data.temporal },
    { key: "ordinario", label: t("vida_ordinario"), result: data.ordinario },
    { key: "dotal", label: t("vida_dotal"), result: data.dotal },
  ];

  const comparisonRows: [string, string, string, string][] = [
    [
      t("prima_neta"),
      formatCurrency(data.temporal.prima_neta),
      formatCurrency(data.ordinario.prima_neta),
      formatCurrency(data.dotal.prima_neta),
    ],
    [
      t("prima_total"),
      formatCurrency(data.temporal.prima_total),
      formatCurrency(data.ordinario.prima_total),
      formatCurrency(data.dotal.prima_total),
    ],
  ];

  // Add recargos rows
  const allRecargosKeys = new Set<string>();
  products.forEach((p) => {
    Object.keys(p.result.desglose_recargos).forEach((k) =>
      allRecargosKeys.add(k),
    );
  });
  allRecargosKeys.forEach((key) => {
    comparisonRows.push([
      key,
      formatCurrency(data.temporal.desglose_recargos[key] ?? 0),
      formatCurrency(data.ordinario.desglose_recargos[key] ?? 0),
      formatCurrency(data.dotal.desglose_recargos[key] ?? 0),
    ]);
  });

  const csvData = products.map((p) => ({
    producto: p.label,
    prima_neta: p.result.prima_neta,
    prima_total: p.result.prima_total,
    moneda: p.result.moneda,
    ...p.result.desglose_recargos,
  })) as Record<string, unknown>[];

  return (
    <div className="space-y-4 animate-fade-in">
      <Card title={t("vida_compare_desc")} className="result-accent">
        <Table
          headers={[
            "Concepto",
            t("vida_temporal"),
            t("vida_ordinario"),
            t("vida_dotal"),
          ]}
          rows={comparisonRows}
        />
      </Card>

      {/* Individual cards row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {products.map((p) => (
          <Card key={p.key} title={p.label}>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-navy/60">{t("prima_neta")}</p>
                <p className="text-xl font-heading font-bold text-navy">
                  {formatCurrency(p.result.prima_neta)}
                </p>
              </div>
              <div>
                <p className="text-sm text-navy/60">{t("prima_total")}</p>
                <p className="text-xl font-heading font-bold text-terracotta">
                  {formatCurrency(p.result.prima_total)}
                </p>
              </div>
              {Object.entries(p.result.metadata).map(([mk, mv]) => (
                <div key={mk}>
                  <p className="text-xs text-navy/50">{mk}</p>
                  <p className="text-sm text-navy/80">{String(mv)}</p>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>

      <DownloadButton
        data={csvData}
        filename="vida_comparacion"
        label={t("descargar_csv")}
      />
    </div>
  );
}
