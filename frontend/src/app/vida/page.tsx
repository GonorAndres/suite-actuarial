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
import { pricingApi } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { PricingRequest, PricingResponse, CompareResponse } from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n/translations";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from "recharts";

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

/* ── Chart color palette ──────────────────────────────────────────────── */

const CHART_COLORS = {
  navy: "#1B2A4A",
  terracotta: "#C17654",
  sage: "#7A9E7E",
  amber: "#D4A853",
  cream: "#F5F0EA",
};

/* ── Result display component ──────────────────────────────────────────── */

function ResultCard({
  result,
  t,
}: {
  result: PricingResponse;
  t: (key: TranslationKey) => string;
}) {
  const [showMetadata, setShowMetadata] = useState(false);

  const recargosEntries = Object.entries(result.desglose_recargos);
  const totalRecargos = recargosEntries.reduce((sum, [, val]) => sum + val, 0);

  const recargosSegments = recargosEntries.map(([key, val], i) => ({
    label: key,
    value: val,
    color: [CHART_COLORS.navy, CHART_COLORS.terracotta, CHART_COLORS.sage, CHART_COLORS.amber][
      i % 4
    ],
  }));

  const pieData = recargosEntries.map(([key, val], i) => ({
    name: key,
    value: val,
    color: [CHART_COLORS.navy, CHART_COLORS.terracotta, CHART_COLORS.sage, CHART_COLORS.amber][
      i % 4
    ],
  }));

  const metadataEntries = Object.entries(result.metadata);

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
    <div className="space-y-6 animate-fade-in">
      {/* Hero metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MetricCard
          label={t("prima_neta")}
          value={formatCurrency(result.prima_neta)}
          variant="primary"
        />
        <MetricCard
          label={t("prima_total")}
          value={formatCurrency(result.prima_total)}
          variant="accent"
          sublabel={`${t("desglose_recargos")}: +${formatCurrency(totalRecargos)}`}
        />
      </div>

      {/* Recargos breakdown -- donut + progress bar */}
      {recargosEntries.length > 0 && (
        <Card title={t("desglose_recargos")}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
            {/* Donut chart */}
            <div className="flex justify-center">
              <ResponsiveContainer width={220} height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    formatter={(value) => formatCurrency(Number(value))}
                    contentStyle={{
                      background: CHART_COLORS.navy,
                      border: "none",
                      borderRadius: "8px",
                      color: CHART_COLORS.cream,
                      fontSize: "13px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Progress bar breakdown */}
            <ProgressBar
              segments={recargosSegments}
              formatValue={(v) => formatCurrency(v)}
            />
          </div>
        </Card>
      )}

      {/* Metadata -- collapsible info grid */}
      {metadataEntries.length > 0 && (
        <div>
          <button
            type="button"
            onClick={() => setShowMetadata(!showMetadata)}
            className="flex items-center gap-2 text-sm font-medium text-navy/60 hover:text-terracotta transition-colors mb-3"
          >
            <svg
              className={`w-4 h-4 transition-transform ${showMetadata ? "rotate-90" : ""}`}
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
            {t("metadata")}
          </button>
          {showMetadata && (
            <Card className="animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
                {metadataEntries.map(([key, val]) => (
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
        </div>
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

  // Find cheapest product
  const cheapestKey = products.reduce(
    (min, p) => (p.result.prima_total < min.result.prima_total ? p : min),
    products[0],
  ).key;

  // Grouped bar chart data
  const chartData = products.map((p) => ({
    name: p.label,
    prima_neta: p.result.prima_neta,
    prima_total: p.result.prima_total,
  }));

  const csvData = products.map((p) => ({
    producto: p.label,
    prima_neta: p.result.prima_neta,
    prima_total: p.result.prima_total,
    moneda: p.result.moneda,
    ...p.result.desglose_recargos,
  })) as Record<string, unknown>[];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Product comparison cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {products.map((p) => (
          <Card
            key={p.key}
            className={`relative ${p.key === cheapestKey ? "ring-2 ring-sage/60" : ""}`}
          >
            {/* Cheapest badge */}
            {p.key === cheapestKey && (
              <span className="absolute -top-3 left-4 bg-sage text-white text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full">
                {t("vida_temporal") === p.label ? t("vida_temporal") : ""}{" "}
                {/* fallback */}
                Mas economico
              </span>
            )}
            <div className="pt-2 space-y-4">
              <h4 className="font-heading text-lg font-bold text-navy">
                {p.label}
              </h4>
              <div>
                <p className="text-xs text-navy/50 uppercase tracking-wide">
                  {t("prima_neta")}
                </p>
                <p className="text-2xl font-heading font-bold text-navy tabular-nums">
                  {formatCurrency(p.result.prima_neta)}
                </p>
              </div>
              <div>
                <p className="text-xs text-navy/50 uppercase tracking-wide">
                  {t("prima_total")}
                </p>
                <p className="text-2xl font-heading font-bold text-terracotta tabular-nums">
                  {formatCurrency(p.result.prima_total)}
                </p>
              </div>
              {/* Metadata mini */}
              <div className="pt-2 border-t border-navy/5 space-y-1">
                {Object.entries(p.result.metadata).map(([mk, mv]) => (
                  <div
                    key={mk}
                    className="flex justify-between items-baseline text-xs"
                  >
                    <span className="text-navy/40">{mk}</span>
                    <span className="text-navy/70 tabular-nums">
                      {String(mv)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Grouped bar chart */}
      <Card title={t("vida_compare_desc")}>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 10, right: 10, left: 10, bottom: 10 }}
              barGap={4}
            >
              <XAxis
                dataKey="name"
                tick={{ fill: CHART_COLORS.navy, fontSize: 13 }}
                axisLine={{ stroke: CHART_COLORS.navy, strokeOpacity: 0.15 }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: CHART_COLORS.navy, fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v: number) =>
                  `$${(v / 1000).toLocaleString("es-MX")}k`
                }
              />
              <RechartsTooltip
                formatter={(value, name) => [
                  formatCurrency(Number(value)),
                  name === "prima_neta" ? t("prima_neta") : t("prima_total"),
                ]}
                contentStyle={{
                  background: CHART_COLORS.navy,
                  border: "none",
                  borderRadius: "8px",
                  color: CHART_COLORS.cream,
                  fontSize: "13px",
                }}
              />
              <Bar
                dataKey="prima_neta"
                name={t("prima_neta")}
                fill={CHART_COLORS.navy}
                radius={[6, 6, 0, 0]}
              />
              <Bar
                dataKey="prima_total"
                name={t("prima_total")}
                fill={CHART_COLORS.terracotta}
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <DownloadButton
        data={csvData}
        filename="vida_comparacion"
        label={t("descargar_csv")}
      />
    </div>
  );
}
