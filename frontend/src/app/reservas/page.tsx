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
  Badge,
} from "@/components/ui";
import DownloadButton from "@/components/download/DownloadButton";
import { useCalculation } from "@/hooks/useCalculation";
import { reservesApi } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type {
  ChainLadderRequest,
  BornhuetterFergusonRequest,
  BootstrapRequest,
  ReserveResponse,
} from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Types ─────────────────────────────────────────────────────────────── */

type ReserveTab = "chainladder" | "bornhuetter" | "bootstrap";

/* ── Sample data ─────────────────────────────────────────────────────── */

const SAMPLE_TRIANGLE = `[[3000, 5000, 5600, 5900],
 [3200, 5200, 5800, null],
 [3500, 5500, null, null],
 [3800, null, null, null]]`;

const SAMPLE_ORIGIN_YEARS = "2020, 2021, 2022, 2023";

const SAMPLE_PRIMAS: Record<number, number> = {
  2020: 7000,
  2021: 7500,
  2022: 8000,
  2023: 8500,
};

const SAMPLE_SINIESTROS_JSON = JSON.stringify(
  [
    { id_siniestro: "S001", fecha_ocurrencia: "2024-01-15", monto_bruto: 150000 },
    { id_siniestro: "S002", fecha_ocurrencia: "2024-03-22", monto_bruto: 85000 },
    { id_siniestro: "S003", fecha_ocurrencia: "2024-06-10", monto_bruto: 220000 },
  ],
  null,
  2,
);

/* ── Default form values ───────────────────────────────────────────────── */

interface ChainLadderForm {
  triangle: string;
  origin_years: string;
  metodo_promedio: "simple" | "weighted" | "geometric";
  tail_factor: string;
}

interface BornhuetterForm {
  triangle: string;
  origin_years: string;
  primas_por_anio: string;
  loss_ratio_apriori: number;
  metodo_promedio: string;
}

interface BootstrapForm {
  triangle: string;
  origin_years: string;
  num_simulaciones: number;
  seed: string;
  percentiles: string;
}

const DEFAULT_CL: ChainLadderForm = {
  triangle: SAMPLE_TRIANGLE,
  origin_years: SAMPLE_ORIGIN_YEARS,
  metodo_promedio: "weighted",
  tail_factor: "",
};

const DEFAULT_BF: BornhuetterForm = {
  triangle: SAMPLE_TRIANGLE,
  origin_years: SAMPLE_ORIGIN_YEARS,
  primas_por_anio: JSON.stringify(SAMPLE_PRIMAS),
  loss_ratio_apriori: 0.65,
  metodo_promedio: "weighted",
};

const DEFAULT_BS: BootstrapForm = {
  triangle: SAMPLE_TRIANGLE,
  origin_years: SAMPLE_ORIGIN_YEARS,
  num_simulaciones: 1000,
  seed: "42",
  percentiles: "50, 75, 90, 95, 99",
};

/* ── Result display component ──────────────────────────────────────────── */

function ReserveResultCard({
  result,
  t,
}: {
  result: ReserveResponse;
  t: (key: TranslationKey) => string;
}) {
  const reservasPorAnio = Object.entries(result.reservas_por_anio).map(
    ([year, val]) => [year, formatCurrency(val)],
  );

  const ultimatesPorAnio = Object.entries(result.ultimates_por_anio).map(
    ([year, val]) => [year, formatCurrency(val)],
  );

  const csvData = {
    metodo: result.metodo,
    reserva_total: result.reserva_total,
    ultimate_total: result.ultimate_total,
    pagado_total: result.pagado_total,
    ...Object.fromEntries(
      Object.entries(result.reservas_por_anio).map(([k, v]) => [`reserva_${k}`, v]),
    ),
  } as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Main totals */}
      <Card className="result-accent">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("reserva_total")}</p>
            <p className="text-3xl font-heading font-bold text-terracotta tabular-nums">
              {formatCurrency(result.reserva_total)}
            </p>
          </div>
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("ultimate_total")}</p>
            <p className="text-3xl font-heading font-bold text-navy tabular-nums">
              {formatCurrency(result.ultimate_total)}
            </p>
          </div>
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("reservas_pagado_total")}</p>
            <p className="text-3xl font-heading font-bold text-navy tabular-nums">
              {formatCurrency(result.pagado_total)}
            </p>
          </div>
        </div>
      </Card>

      {/* Method badge */}
      <Card>
        <div className="flex items-center gap-3">
          <span className="text-sm text-navy/60">{t("reservas_metodo")}:</span>
          <Badge variant="info">{result.metodo}</Badge>
        </div>
      </Card>

      {/* Reserves by year */}
      {reservasPorAnio.length > 0 && (
        <Card title={t("reservas_por_anio_tabla")}>
          <Table
            headers={[t("anios_origen"), t("reserva_total")]}
            rows={reservasPorAnio}
          />
        </Card>
      )}

      {/* Ultimates by year */}
      {ultimatesPorAnio.length > 0 && (
        <Card title={t("reservas_ultimates_por_anio")}>
          <Table
            headers={[t("anios_origen"), t("ultimate_total")]}
            rows={ultimatesPorAnio}
          />
        </Card>
      )}

      {/* Development factors */}
      {result.factores_desarrollo && result.factores_desarrollo.length > 0 && (
        <Card title={t("reservas_factores_desarrollo")}>
          <div className="flex flex-wrap gap-3">
            {result.factores_desarrollo.map((f, i) => (
              <div
                key={i}
                className="bg-navy/5 rounded-lg px-3 py-2 text-center"
              >
                <p className="text-xs text-navy/50">
                  {i + 1} → {i + 2}
                </p>
                <p className="font-heading font-bold text-navy">
                  {formatNumber(f, 4)}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Percentiles (Bootstrap) */}
      {result.percentiles && Object.keys(result.percentiles).length > 0 && (
        <Card title={t("reservas_percentiles")}>
          <Table
            headers={[t("reservas_percentil"), t("reserva_total")]}
            rows={Object.entries(result.percentiles).map(([pct, val]) => [
              `${pct}%`,
              formatCurrency(val),
            ])}
          />
        </Card>
      )}

      <DownloadButton
        data={csvData}
        filename={`reservas_${result.metodo}`}
        label={t("descargar_csv")}
      />
    </div>
  );
}

/* ── Helper: parse triangle text ──────────────────────────────────────── */

function parseTriangle(text: string): (number | null)[][] {
  return JSON.parse(text);
}

function parseOriginYears(text: string): number[] {
  return text.split(",").map((s) => parseInt(s.trim(), 10));
}

/* ── Page component ────────────────────────────────────────────────────── */

export default function ReservasPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<ReserveTab>("chainladder");
  const [clForm, setClForm] = useState<ChainLadderForm>(DEFAULT_CL);
  const [bfForm, setBfForm] = useState<BornhuetterForm>(DEFAULT_BF);
  const [bsForm, setBsForm] = useState<BootstrapForm>(DEFAULT_BS);

  /* ── API hooks ──────────────────────────────────────────────────────── */

  const chainLadder = useCalculation<ChainLadderRequest, ReserveResponse>(
    reservesApi.chainLadder,
  );
  const bornhuetter = useCalculation<BornhuetterFergusonRequest, ReserveResponse>(
    reservesApi.bornhuetterFerguson,
  );
  const bootstrap = useCalculation<BootstrapRequest, ReserveResponse>(
    reservesApi.bootstrap,
  );

  /* ── Tabs definition ────────────────────────────────────────────────── */

  const tabs = useMemo(
    () => [
      { id: "chainladder", label: t("reservas_chain_ladder") },
      { id: "bornhuetter", label: t("reservas_bornhuetter") },
      { id: "bootstrap", label: t("reservas_bootstrap") },
    ],
    [t],
  );

  /* ── Handlers ──────────────────────────────────────────────────────── */

  const handleCalculate = useCallback(async () => {
    try {
      switch (activeTab) {
        case "chainladder": {
          const req: ChainLadderRequest = {
            triangle: parseTriangle(clForm.triangle),
            origin_years: parseOriginYears(clForm.origin_years),
            metodo_promedio: clForm.metodo_promedio,
            tail_factor: clForm.tail_factor ? Number(clForm.tail_factor) : null,
          };
          await chainLadder.calculate(req);
          break;
        }
        case "bornhuetter": {
          const primasObj: Record<number, number> = JSON.parse(bfForm.primas_por_anio);
          const req: BornhuetterFergusonRequest = {
            triangle: parseTriangle(bfForm.triangle),
            origin_years: parseOriginYears(bfForm.origin_years),
            primas_por_anio: primasObj,
            loss_ratio_apriori: bfForm.loss_ratio_apriori,
            metodo_promedio: bfForm.metodo_promedio,
          };
          await bornhuetter.calculate(req);
          break;
        }
        case "bootstrap": {
          const req: BootstrapRequest = {
            triangle: parseTriangle(bsForm.triangle),
            origin_years: parseOriginYears(bsForm.origin_years),
            num_simulaciones: bsForm.num_simulaciones,
            seed: bsForm.seed ? Number(bsForm.seed) : null,
            percentiles: bsForm.percentiles
              .split(",")
              .map((s) => Number(s.trim())),
          };
          await bootstrap.calculate(req);
          break;
        }
      }
    } catch {
      // parsing errors will be caught by useCalculation
    }
  }, [activeTab, clForm, bfForm, bsForm, chainLadder, bornhuetter, bootstrap]);

  /* ── Derive current loading / error ──────────────────────────────── */

  const currentHook = {
    chainladder: chainLadder,
    bornhuetter: bornhuetter,
    bootstrap: bootstrap,
  }[activeTab];

  const isLoading = currentHook.loading;
  const errorMsg = currentHook.error;

  /* ── Select options ────────────────────────────────────────────────── */

  const promedioOptions = useMemo(
    () => [
      { value: "simple", label: t("reservas_promedio_simple") },
      { value: "weighted", label: t("reservas_promedio_ponderado") },
      { value: "geometric", label: t("reservas_promedio_geometrico") },
    ],
    [t],
  );

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-navy mb-2">
          {t("reservas_titulo")}
        </h1>
        <p className="text-navy/60 text-lg">{t("reservas_descripcion")}</p>
        <p className="text-navy/60 text-lg max-w-3xl mt-2">{t("reservas_contexto")}</p>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(id) => setActiveTab(id as ReserveTab)}
      />

      {/* ── Chain Ladder Form ──────��───────────────────────────────── */}
      {activeTab === "chainladder" && (
        <Card className="form-depth">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-navy mb-1">
                {t("triangulo")}
              </label>
              <textarea
                className="w-full rounded-lg border border-navy/20 bg-white px-4 py-3 text-sm text-navy font-mono focus:border-terracotta focus:ring-1 focus:ring-terracotta"
                rows={6}
                value={clForm.triangle}
                onChange={(e) =>
                  setClForm((prev) => ({ ...prev, triangle: e.target.value }))
                }
              />
              <p className="text-xs text-navy/40 mt-1">
                {t("reservas_triangulo_hint")}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label={t("anios_origen")}
                name="origin_years"
                value={clForm.origin_years}
                onChange={(e) =>
                  setClForm((prev) => ({ ...prev, origin_years: e.target.value }))
                }
              />
              <Select
                label={t("metodo_promedio")}
                name="metodo_promedio"
                options={promedioOptions}
                value={clForm.metodo_promedio}
                onChange={(e) =>
                  setClForm((prev) => ({
                    ...prev,
                    metodo_promedio: e.target.value as ChainLadderForm["metodo_promedio"],
                  }))
                }
              />
              <Input
                label={t("tail_factor")}
                name="tail_factor"
                type="number"
                step={0.001}
                min={0}
                value={clForm.tail_factor}
                onChange={(e) =>
                  setClForm((prev) => ({ ...prev, tail_factor: e.target.value }))
                }
              />
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

      {/* ── Bornhuetter-Ferguson Form ─────────────────────────────── */}
      {activeTab === "bornhuetter" && (
        <Card className="form-depth">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-navy mb-1">
                {t("triangulo")}
              </label>
              <textarea
                className="w-full rounded-lg border border-navy/20 bg-white px-4 py-3 text-sm text-navy font-mono focus:border-terracotta focus:ring-1 focus:ring-terracotta"
                rows={6}
                value={bfForm.triangle}
                onChange={(e) =>
                  setBfForm((prev) => ({ ...prev, triangle: e.target.value }))
                }
              />
              <p className="text-xs text-navy/40 mt-1">
                {t("reservas_triangulo_hint")}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label={t("anios_origen")}
                name="origin_years"
                value={bfForm.origin_years}
                onChange={(e) =>
                  setBfForm((prev) => ({ ...prev, origin_years: e.target.value }))
                }
              />
              <Input
                label={t("loss_ratio")}
                name="loss_ratio_apriori"
                type="number"
                step={0.01}
                min={0}
                max={2}
                value={bfForm.loss_ratio_apriori}
                onChange={(e) =>
                  setBfForm((prev) => ({
                    ...prev,
                    loss_ratio_apriori: Number(e.target.value),
                  }))
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1">
                {t("primas_por_anio")}
              </label>
              <textarea
                className="w-full rounded-lg border border-navy/20 bg-white px-4 py-3 text-sm text-navy font-mono focus:border-terracotta focus:ring-1 focus:ring-terracotta"
                rows={3}
                value={bfForm.primas_por_anio}
                onChange={(e) =>
                  setBfForm((prev) => ({ ...prev, primas_por_anio: e.target.value }))
                }
              />
              <p className="text-xs text-navy/40 mt-1">
                {t("reservas_primas_hint")}
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

      {/* ── Bootstrap Form ────────────────────────────────────────── */}
      {activeTab === "bootstrap" && (
        <Card className="form-depth">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-navy mb-1">
                {t("triangulo")}
              </label>
              <textarea
                className="w-full rounded-lg border border-navy/20 bg-white px-4 py-3 text-sm text-navy font-mono focus:border-terracotta focus:ring-1 focus:ring-terracotta"
                rows={6}
                value={bsForm.triangle}
                onChange={(e) =>
                  setBsForm((prev) => ({ ...prev, triangle: e.target.value }))
                }
              />
              <p className="text-xs text-navy/40 mt-1">
                {t("reservas_triangulo_hint")}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Input
                label={t("anios_origen")}
                name="origin_years"
                value={bsForm.origin_years}
                onChange={(e) =>
                  setBsForm((prev) => ({ ...prev, origin_years: e.target.value }))
                }
              />
              <Input
                label={t("num_simulaciones")}
                name="num_simulaciones"
                type="number"
                min={100}
                max={10000}
                value={bsForm.num_simulaciones}
                onChange={(e) =>
                  setBsForm((prev) => ({
                    ...prev,
                    num_simulaciones: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reservas_seed")}
                name="seed"
                type="number"
                value={bsForm.seed}
                onChange={(e) =>
                  setBsForm((prev) => ({ ...prev, seed: e.target.value }))
                }
              />
              <Input
                label={t("reservas_percentiles")}
                name="percentiles"
                value={bsForm.percentiles}
                onChange={(e) =>
                  setBsForm((prev) => ({ ...prev, percentiles: e.target.value }))
                }
              />
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
      {(chainLadder.data || bornhuetter.data || bootstrap.data) && (
        <div className="section-divider" />
      )}

      {activeTab === "chainladder" && chainLadder.data && (
        <ReserveResultCard result={chainLadder.data} t={t} />
      )}
      {activeTab === "bornhuetter" && bornhuetter.data && (
        <ReserveResultCard result={bornhuetter.data} t={t} />
      )}
      {activeTab === "bootstrap" && bootstrap.data && (
        <ReserveResultCard result={bootstrap.data} t={t} />
      )}
    </div>
  );
}
