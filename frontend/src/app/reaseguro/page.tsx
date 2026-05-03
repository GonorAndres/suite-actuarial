"use client";

import { useCallback, useMemo, useState } from "react";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import {
  Card,
  Button,
  Input,
  Tabs,
  LoadingSpinner,
  Table,
  MetricCard,
  ProgressBar,
} from "@/components/ui";
import DownloadButton from "@/components/download/DownloadButton";
import { useCalculation } from "@/hooks/useCalculation";
import { reinsuranceApi } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type {
  QuotaShareRequest,
  ExcessOfLossRequest,
  StopLossRequest,
  ReinsuranceResponse,
} from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Types ─────────────────────────────────────────────────────────────── */

type ReinsuranceTab = "quotashare" | "xl" | "stoploss";

/* ── Sample claims data ──────────────────────────────────────────────── */

const SAMPLE_CLAIMS = JSON.stringify(
  [
    {
      id_siniestro: "S001",
      fecha_ocurrencia: "2024-01-15",
      monto_bruto: 150000,
    },
    {
      id_siniestro: "S002",
      fecha_ocurrencia: "2024-03-22",
      monto_bruto: 85000,
    },
    {
      id_siniestro: "S003",
      fecha_ocurrencia: "2024-06-10",
      monto_bruto: 220000,
    },
    {
      id_siniestro: "S004",
      fecha_ocurrencia: "2024-08-05",
      monto_bruto: 45000,
    },
    {
      id_siniestro: "S005",
      fecha_ocurrencia: "2024-11-18",
      monto_bruto: 310000,
    },
  ],
  null,
  2,
);

/* ── Default form values ───────────────────────────────────────────────── */

interface QuotaShareForm {
  porcentaje_cesion: number;
  comision_reaseguro: number;
  prima_bruta: number;
  vigencia_inicio: string;
  vigencia_fin: string;
  siniestros: string;
}

interface ExcessOfLossForm {
  retencion: number;
  limite: number;
  tasa_prima: number;
  prima_reaseguro_cobrada: number;
  vigencia_inicio: string;
  vigencia_fin: string;
  siniestros: string;
}

interface StopLossForm {
  attachment_point: number;
  limite_cobertura: number;
  primas_sujetas: number;
  primas_totales: number;
  vigencia_inicio: string;
  vigencia_fin: string;
  siniestros: string;
}

const DEFAULT_QS: QuotaShareForm = {
  porcentaje_cesion: 40,
  comision_reaseguro: 25,
  prima_bruta: 5_000_000,
  vigencia_inicio: "2024-01-01",
  vigencia_fin: "2024-12-31",
  siniestros: SAMPLE_CLAIMS,
};

const DEFAULT_XL: ExcessOfLossForm = {
  retencion: 200000,
  limite: 1_000_000,
  tasa_prima: 0.05,
  prima_reaseguro_cobrada: 250000,
  vigencia_inicio: "2024-01-01",
  vigencia_fin: "2024-12-31",
  siniestros: SAMPLE_CLAIMS,
};

const DEFAULT_SL: StopLossForm = {
  attachment_point: 70,
  limite_cobertura: 30,
  primas_sujetas: 5_000_000,
  primas_totales: 5_000_000,
  vigencia_inicio: "2024-01-01",
  vigencia_fin: "2024-12-31",
  siniestros: SAMPLE_CLAIMS,
};

/* ── Result display component ──────────────────────────────────────────── */

function ReinsuranceResultCard({
  result,
  t,
}: {
  result: ReinsuranceResponse;
  t: (key: TranslationKey) => string;
}) {
  const summaryRows: [string, string][] = [
    [t("monto_cedido"), formatCurrency(result.monto_cedido)],
    [t("monto_retenido"), formatCurrency(result.monto_retenido)],
    [t("recuperacion"), formatCurrency(result.recuperacion_reaseguro)],
    [t("reas_comision_recibida"), formatCurrency(result.comision_recibida)],
    [
      t("reas_prima_reaseguro_pagada"),
      formatCurrency(result.prima_reaseguro_pagada),
    ],
    [t("reas_ratio_cesion"), formatPercent(result.ratio_cesion)],
    [t("reas_resultado_neto"), formatCurrency(result.resultado_neto_cedente)],
  ];

  const detailRows = Object.entries(result.detalles).map(([key, val]) => {
    if (typeof val === "number") {
      return [key, formatCurrency(val)];
    }
    return [key, String(val)];
  });

  const csvData = {
    tipo_contrato: result.tipo_contrato,
    monto_cedido: result.monto_cedido,
    monto_retenido: result.monto_retenido,
    recuperacion_reaseguro: result.recuperacion_reaseguro,
    comision_recibida: result.comision_recibida,
    prima_reaseguro_pagada: result.prima_reaseguro_pagada,
    ratio_cesion: result.ratio_cesion,
    resultado_neto_cedente: result.resultado_neto_cedente,
  } as Record<string, unknown>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Main results -- metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label={t("monto_cedido")}
          value={formatCurrency(result.monto_cedido)}
          variant="accent"
        />
        <MetricCard
          label={t("monto_retenido")}
          value={formatCurrency(result.monto_retenido)}
          variant="primary"
        />
        <MetricCard
          label={t("recuperacion")}
          value={formatCurrency(result.recuperacion_reaseguro)}
          variant="default"
        />
        <MetricCard
          label={t("reas_resultado_neto")}
          value={formatCurrency(result.resultado_neto_cedente)}
          variant="default"
          className={result.resultado_neto_cedente >= 0 ? "ring-2 ring-sage/30" : "ring-2 ring-terracotta/30"}
        />
      </div>

      {/* Cedido vs Retenido stacked bar */}
      {(result.monto_cedido > 0 || result.monto_retenido > 0) && (
        <Card title={t("reas_ratio_cesion")}>
          <ProgressBar
            segments={[
              { label: t("monto_cedido"), value: result.monto_cedido, color: "#C17654" },
              { label: t("monto_retenido"), value: result.monto_retenido, color: "#1B2A4A" },
            ]}
            formatValue={(v) => formatCurrency(v)}
          />
        </Card>
      )}

      {/* Summary table */}
      <Card title={t("reas_resumen_contrato")}>
        <Table
          headers={[t("reas_concepto"), t("reg_valor")]}
          rows={summaryRows}
        />
      </Card>

      {/* Details */}
      {detailRows.length > 0 && (
        <Card title={t("reas_detalles")}>
          <Table
            headers={[t("reas_concepto"), t("reg_valor")]}
            rows={detailRows}
          />
        </Card>
      )}

      <DownloadButton
        data={csvData}
        filename={`reaseguro_${result.tipo_contrato}`}
        label={t("descargar_csv")}
      />
    </div>
  );
}

/* ── Page component ────────────────────────────────────────────────────── */

export default function ReaseguroPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<ReinsuranceTab>("quotashare");
  const [qsForm, setQsForm] = useState<QuotaShareForm>(DEFAULT_QS);
  const [xlForm, setXlForm] = useState<ExcessOfLossForm>(DEFAULT_XL);
  const [slForm, setSlForm] = useState<StopLossForm>(DEFAULT_SL);

  /* ── API hooks ──────────────────────────────────────────────────────── */

  const quotaShare = useCalculation<QuotaShareRequest, ReinsuranceResponse>(
    reinsuranceApi.quotaShare,
  );
  const excessOfLoss = useCalculation<ExcessOfLossRequest, ReinsuranceResponse>(
    reinsuranceApi.excessOfLoss,
  );
  const stopLoss = useCalculation<StopLossRequest, ReinsuranceResponse>(
    reinsuranceApi.stopLoss,
  );

  /* ── Tabs definition ────────────────────────────────────────────────── */

  const tabs = useMemo(
    () => [
      { id: "quotashare", label: t("reaseguro_quota_share") },
      { id: "xl", label: t("reaseguro_xl") },
      { id: "stoploss", label: t("reaseguro_stop_loss") },
    ],
    [t],
  );

  /* ── Handlers ──────────────────────────────────────────────────────── */

  const handleCalculate = useCallback(async () => {
    try {
      switch (activeTab) {
        case "quotashare": {
          const siniestros = JSON.parse(qsForm.siniestros);
          const req: QuotaShareRequest = {
            porcentaje_cesion: qsForm.porcentaje_cesion / 100,
            comision_reaseguro: qsForm.comision_reaseguro / 100,
            prima_bruta: qsForm.prima_bruta,
            vigencia_inicio: qsForm.vigencia_inicio,
            vigencia_fin: qsForm.vigencia_fin,
            siniestros,
          };
          await quotaShare.calculate(req);
          break;
        }
        case "xl": {
          const siniestros = JSON.parse(xlForm.siniestros);
          const req: ExcessOfLossRequest = {
            retencion: xlForm.retencion,
            limite: xlForm.limite,
            tasa_prima: xlForm.tasa_prima,
            prima_reaseguro_cobrada: xlForm.prima_reaseguro_cobrada,
            vigencia_inicio: xlForm.vigencia_inicio,
            vigencia_fin: xlForm.vigencia_fin,
            siniestros,
          };
          await excessOfLoss.calculate(req);
          break;
        }
        case "stoploss": {
          const siniestros = JSON.parse(slForm.siniestros);
          const req: StopLossRequest = {
            attachment_point: slForm.attachment_point,
            limite_cobertura: slForm.limite_cobertura,
            primas_sujetas: slForm.primas_sujetas,
            primas_totales: slForm.primas_totales,
            vigencia_inicio: slForm.vigencia_inicio,
            vigencia_fin: slForm.vigencia_fin,
            siniestros,
          };
          await stopLoss.calculate(req);
          break;
        }
      }
    } catch {
      // parsing errors will be caught by useCalculation
    }
  }, [activeTab, qsForm, xlForm, slForm, quotaShare, excessOfLoss, stopLoss]);

  /* ── Derive current loading / error ──────────────────────────────── */

  const currentHook = {
    quotashare: quotaShare,
    xl: excessOfLoss,
    stoploss: stopLoss,
  }[activeTab];

  const isLoading = currentHook.loading;
  const errorMsg = currentHook.error;

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-navy mb-2">
          {t("reaseguro_titulo")}
        </h1>
        <p className="text-navy/60 text-lg">{t("reaseguro_descripcion")}</p>
        <p className="text-navy/50 text-lg leading-relaxed mt-3">{t("reaseguro_contexto")}</p>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(id) => setActiveTab(id as ReinsuranceTab)}
      />

      {/* ── Quota Share Form ──────────────────────────────────────── */}
      {activeTab === "quotashare" && (
        <Card className="form-depth">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("porcentaje_cesion") + " (%)"}
                name="porcentaje_cesion"
                type="number"
                min={0}
                max={100}
                value={qsForm.porcentaje_cesion}
                onChange={(e) =>
                  setQsForm((prev) => ({
                    ...prev,
                    porcentaje_cesion: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("comision_reaseguro") + " (%)"}
                name="comision_reaseguro"
                type="number"
                min={0}
                max={50}
                value={qsForm.comision_reaseguro}
                onChange={(e) =>
                  setQsForm((prev) => ({
                    ...prev,
                    comision_reaseguro: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_prima_bruta")}
                name="prima_bruta"
                type="number"
                min={0}
                value={qsForm.prima_bruta}
                onChange={(e) =>
                  setQsForm((prev) => ({
                    ...prev,
                    prima_bruta: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_vigencia_inicio")}
                name="vigencia_inicio"
                type="date"
                value={qsForm.vigencia_inicio}
                onChange={(e) =>
                  setQsForm((prev) => ({
                    ...prev,
                    vigencia_inicio: e.target.value,
                  }))
                }
              />
              <Input
                label={t("reas_vigencia_fin")}
                name="vigencia_fin"
                type="date"
                value={qsForm.vigencia_fin}
                onChange={(e) =>
                  setQsForm((prev) => ({
                    ...prev,
                    vigencia_fin: e.target.value,
                  }))
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1">
                {t("reas_siniestros")}
              </label>
              <textarea
                className="w-full rounded-lg border border-navy/20 bg-white px-4 py-3 text-sm text-navy font-mono focus:border-terracotta focus:ring-1 focus:ring-terracotta"
                rows={8}
                value={qsForm.siniestros}
                onChange={(e) =>
                  setQsForm((prev) => ({
                    ...prev,
                    siniestros: e.target.value,
                  }))
                }
              />
              <p className="text-xs text-navy/40 mt-1">
                {t("reas_siniestros_hint")}
              </p>
            </div>
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
      )}

      {/* ── Excess of Loss Form ───────────────────────────────────── */}
      {activeTab === "xl" && (
        <Card className="form-depth">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("reas_retencion")}
                name="retencion"
                type="number"
                min={0}
                value={xlForm.retencion}
                onChange={(e) =>
                  setXlForm((prev) => ({
                    ...prev,
                    retencion: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_limite")}
                name="limite"
                type="number"
                min={0}
                value={xlForm.limite}
                onChange={(e) =>
                  setXlForm((prev) => ({
                    ...prev,
                    limite: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_tasa_prima")}
                name="tasa_prima"
                type="number"
                step={0.01}
                min={0}
                max={1}
                value={xlForm.tasa_prima}
                onChange={(e) =>
                  setXlForm((prev) => ({
                    ...prev,
                    tasa_prima: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_prima_reaseguro_cobrada")}
                name="prima_reaseguro_cobrada"
                type="number"
                min={0}
                value={xlForm.prima_reaseguro_cobrada}
                onChange={(e) =>
                  setXlForm((prev) => ({
                    ...prev,
                    prima_reaseguro_cobrada: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_vigencia_inicio")}
                name="vigencia_inicio_xl"
                type="date"
                value={xlForm.vigencia_inicio}
                onChange={(e) =>
                  setXlForm((prev) => ({
                    ...prev,
                    vigencia_inicio: e.target.value,
                  }))
                }
              />
              <Input
                label={t("reas_vigencia_fin")}
                name="vigencia_fin_xl"
                type="date"
                value={xlForm.vigencia_fin}
                onChange={(e) =>
                  setXlForm((prev) => ({
                    ...prev,
                    vigencia_fin: e.target.value,
                  }))
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1">
                {t("reas_siniestros")}
              </label>
              <textarea
                className="w-full rounded-lg border border-navy/20 bg-white px-4 py-3 text-sm text-navy font-mono focus:border-terracotta focus:ring-1 focus:ring-terracotta"
                rows={8}
                value={xlForm.siniestros}
                onChange={(e) =>
                  setXlForm((prev) => ({
                    ...prev,
                    siniestros: e.target.value,
                  }))
                }
              />
              <p className="text-xs text-navy/40 mt-1">
                {t("reas_siniestros_hint")}
              </p>
            </div>
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
      )}

      {/* ── Stop Loss Form ────────────────────────────────────────── */}
      {activeTab === "stoploss" && (
        <Card className="form-depth">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("reas_attachment_point") + " (%)"}
                name="attachment_point"
                type="number"
                step={1}
                min={60}
                max={100}
                value={slForm.attachment_point}
                onChange={(e) =>
                  setSlForm((prev) => ({
                    ...prev,
                    attachment_point: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_limite_cobertura") + " (%)"}
                name="limite_cobertura"
                type="number"
                step={1}
                min={1}
                max={100}
                value={slForm.limite_cobertura}
                onChange={(e) =>
                  setSlForm((prev) => ({
                    ...prev,
                    limite_cobertura: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_primas_sujetas")}
                name="primas_sujetas"
                type="number"
                min={0}
                value={slForm.primas_sujetas}
                onChange={(e) =>
                  setSlForm((prev) => ({
                    ...prev,
                    primas_sujetas: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_primas_totales")}
                name="primas_totales"
                type="number"
                min={0}
                value={slForm.primas_totales}
                onChange={(e) =>
                  setSlForm((prev) => ({
                    ...prev,
                    primas_totales: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reas_vigencia_inicio")}
                name="vigencia_inicio_sl"
                type="date"
                value={slForm.vigencia_inicio}
                onChange={(e) =>
                  setSlForm((prev) => ({
                    ...prev,
                    vigencia_inicio: e.target.value,
                  }))
                }
              />
              <Input
                label={t("reas_vigencia_fin")}
                name="vigencia_fin_sl"
                type="date"
                value={slForm.vigencia_fin}
                onChange={(e) =>
                  setSlForm((prev) => ({
                    ...prev,
                    vigencia_fin: e.target.value,
                  }))
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1">
                {t("reas_siniestros")}
              </label>
              <textarea
                className="w-full rounded-lg border border-navy/20 bg-white px-4 py-3 text-sm text-navy font-mono focus:border-terracotta focus:ring-1 focus:ring-terracotta"
                rows={8}
                value={slForm.siniestros}
                onChange={(e) =>
                  setSlForm((prev) => ({
                    ...prev,
                    siniestros: e.target.value,
                  }))
                }
              />
              <p className="text-xs text-navy/40 mt-1">
                {t("reas_siniestros_hint")}
              </p>
            </div>
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
      )}

      {/* Error display */}
      {errorMsg && (
        <Card className="border-red-300 bg-red-50">
          <p className="text-red-700 font-medium">
            {t("error")}: {errorMsg}
          </p>
        </Card>
      )}

      {/* ── Results ──────────────────────────────────────────────── */}
      {/* ── Section divider ─────────────────────────────────────────── */}
      {(quotaShare.data || excessOfLoss.data || stopLoss.data) && (
        <div className="section-divider" />
      )}

      {activeTab === "quotashare" && quotaShare.data && (
        <ReinsuranceResultCard result={quotaShare.data} t={t} />
      )}
      {activeTab === "xl" && excessOfLoss.data && (
        <ReinsuranceResultCard result={excessOfLoss.data} t={t} />
      )}
      {activeTab === "stoploss" && stopLoss.data && (
        <ReinsuranceResultCard result={stopLoss.data} t={t} />
      )}
    </div>
  );
}
