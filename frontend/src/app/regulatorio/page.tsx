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
  MetricCard,
} from "@/components/ui";
import DownloadButton from "@/components/download/DownloadButton";
import { useCalculation } from "@/hooks/useCalculation";
import { regulatoryApi } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type {
  RCSRequest,
  RCSResponse,
  DeductibilityRequest,
  DeductibilityResponse,
  WithholdingRequest,
  WithholdingResponse,
} from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Types ─────────────────────────────────────────────────────────────── */

type RegTab = "rcs" | "deducibilidad" | "retenciones";

/* ── Default form values ───────────────────────────────────────────────── */

interface RCSFormState {
  // Vida
  vida_suma_asegurada_total: number;
  vida_reserva_matematica: number;
  vida_edad_promedio: number;
  vida_duracion_promedio: number;
  vida_numero_asegurados: number;
  // Danos
  danos_primas_retenidas_12m: number;
  danos_reserva_siniestros: number;
  danos_coeficiente_variacion: number;
  danos_numero_ramos: number;
  // Inversion
  inv_valor_acciones: number;
  inv_valor_bonos_gub: number;
  inv_valor_bonos_corp: number;
  inv_valor_inmuebles: number;
  inv_duracion_promedio_bonos: number;
  inv_calificacion: string;
  // Global
  capital_minimo_pagado: number;
  // Section visibility
  showVida: boolean;
  showDanos: boolean;
  showInversion: boolean;
}

interface DeducibilidadFormState {
  tipo_seguro: string;
  monto_prima: number;
  es_persona_fisica: boolean;
}

interface RetencionesFormState {
  tipo_seguro: string;
  monto_pago: number;
  monto_gravable: number;
  es_renta_vitalicia: boolean;
  es_retiro_ahorro: boolean;
}

const DEFAULT_RCS: RCSFormState = {
  vida_suma_asegurada_total: 500_000_000,
  vida_reserva_matematica: 120_000_000,
  vida_edad_promedio: 42,
  vida_duracion_promedio: 15,
  vida_numero_asegurados: 10000,
  danos_primas_retenidas_12m: 200_000_000,
  danos_reserva_siniestros: 80_000_000,
  danos_coeficiente_variacion: 0.25,
  danos_numero_ramos: 5,
  inv_valor_acciones: 50_000_000,
  inv_valor_bonos_gub: 300_000_000,
  inv_valor_bonos_corp: 100_000_000,
  inv_valor_inmuebles: 80_000_000,
  inv_duracion_promedio_bonos: 5,
  inv_calificacion: "AA",
  capital_minimo_pagado: 150_000_000,
  showVida: true,
  showDanos: true,
  showInversion: true,
};

const DEFAULT_DED: DeducibilidadFormState = {
  tipo_seguro: "vida",
  monto_prima: 35000,
  es_persona_fisica: true,
};

const DEFAULT_RET: RetencionesFormState = {
  tipo_seguro: "vida",
  monto_pago: 500000,
  monto_gravable: 350000,
  es_renta_vitalicia: false,
  es_retiro_ahorro: false,
};

/* ── RCS Result component ──────────────────────────────────────────────── */

function RCSResultCard({
  result,
  t,
}: {
  result: RCSResponse;
  t: (key: TranslationKey) => string;
}) {
  const riskRows = Object.entries(result.desglose_por_riesgo).map(
    ([key, val]) => [key, formatCurrency(val)],
  );

  const mainRows: [string, string][] = [
    [t("reg_rcs_suscripcion_vida"), formatCurrency(result.rcs_suscripcion_vida)],
    [t("reg_rcs_suscripcion_danos"), formatCurrency(result.rcs_suscripcion_danos)],
    [t("reg_rcs_inversion"), formatCurrency(result.rcs_inversion)],
    [t("reg_rcs_total"), formatCurrency(result.rcs_total)],
  ];

  const csvData = {
    rcs_total: result.rcs_total,
    rcs_suscripcion_vida: result.rcs_suscripcion_vida,
    rcs_suscripcion_danos: result.rcs_suscripcion_danos,
    rcs_inversion: result.rcs_inversion,
    capital_minimo_pagado: result.capital_minimo_pagado,
    excedente_solvencia: result.excedente_solvencia,
    ratio_solvencia: result.ratio_solvencia,
    cumple_regulacion: result.cumple_regulacion,
    ...result.desglose_por_riesgo,
  } as Record<string, unknown>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Main summary -- metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label={t("reg_rcs_total")}
          value={formatCurrency(result.rcs_total)}
          variant="accent"
        />
        <MetricCard
          label={t("ratio_solvencia")}
          value={formatPercent(result.ratio_solvencia)}
          variant="primary"
        />
        <MetricCard
          label={t("reg_excedente")}
          value={formatCurrency(result.excedente_solvencia)}
          variant="default"
        />
        <div className="rounded-xl p-5 shadow-sm border border-navy/8 bg-offwhite flex flex-col justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-navy/50 mb-2">
            {t("cumple_regulacion")}
          </p>
          <Badge variant={result.cumple_regulacion ? "success" : "error"}>
            {result.cumple_regulacion ? t("reg_si_cumple") : t("reg_no_cumple")}
          </Badge>
        </div>
      </div>

      {/* RCS breakdown */}
      <Card title={t("reg_desglose_rcs")}>
        <Table
          headers={[t("reg_componente"), t("reg_monto")]}
          rows={mainRows}
        />
      </Card>

      {/* Risk details */}
      {riskRows.length > 0 && (
        <Card title={t("reg_desglose_riesgos")}>
          <Table
            headers={[t("reg_tipo_riesgo"), t("reg_monto")]}
            rows={riskRows}
          />
        </Card>
      )}

      <DownloadButton
        data={csvData}
        filename="regulatorio_rcs"
        label={t("descargar_csv")}
      />
    </div>
  );
}

/* ── Deductibility Result ──────────────────────────────────────────────── */

function DeductibilityResultCard({
  result,
  t,
}: {
  result: DeductibilityResponse;
  t: (key: TranslationKey) => string;
}) {
  const rows: [string, string][] = [
    [
      t("reg_es_deducible"),
      result.es_deducible ? t("reg_si") : t("reg_no"),
    ],
    [t("reg_monto_prima"), formatCurrency(result.monto_prima)],
    [t("reg_monto_deducible"), formatCurrency(result.monto_deducible)],
    [
      t("reg_porcentaje_deducible"),
      formatPercent(result.porcentaje_deducible),
    ],
    [t("reg_limite_aplicado"), result.limite_aplicado ?? "-"],
    [t("reg_fundamento_legal"), result.fundamento_legal],
  ];

  const csvData = {
    es_deducible: result.es_deducible,
    monto_prima: result.monto_prima,
    monto_deducible: result.monto_deducible,
    porcentaje_deducible: result.porcentaje_deducible,
    limite_aplicado: result.limite_aplicado,
    fundamento_legal: result.fundamento_legal,
  } as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="result-accent">
        <div className="flex items-center gap-4 mb-4">
          <Badge variant={result.es_deducible ? "success" : "warning"}>
            {result.es_deducible ? t("reg_deducible") : t("reg_no_deducible")}
          </Badge>
          <span className="text-lg font-heading font-bold text-navy">
            {formatCurrency(result.monto_deducible)}
          </span>
        </div>
        <Table headers={[t("reg_concepto"), t("reg_valor")]} rows={rows} />
      </Card>

      <DownloadButton
        data={csvData}
        filename="regulatorio_deducibilidad"
        label={t("descargar_csv")}
      />
    </div>
  );
}

/* ── Withholding Result ────────────────────────────────────────────────── */

function WithholdingResultCard({
  result,
  t,
}: {
  result: WithholdingResponse;
  t: (key: TranslationKey) => string;
}) {
  const rows: [string, string][] = [
    [
      t("reg_requiere_retencion"),
      result.requiere_retencion ? t("reg_si") : t("reg_no"),
    ],
    [t("reg_monto_pago"), formatCurrency(result.monto_pago)],
    [t("reg_base_retencion"), formatCurrency(result.base_retencion)],
    [t("reg_tasa_retencion"), formatPercent(result.tasa_retencion)],
    [t("reg_monto_retencion"), formatCurrency(result.monto_retencion)],
    [t("reg_monto_neto"), formatCurrency(result.monto_neto_pagar)],
  ];

  const csvData = {
    requiere_retencion: result.requiere_retencion,
    monto_pago: result.monto_pago,
    base_retencion: result.base_retencion,
    tasa_retencion: result.tasa_retencion,
    monto_retencion: result.monto_retencion,
    monto_neto_pagar: result.monto_neto_pagar,
  } as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="result-accent">
        <div className="flex items-center gap-4 mb-4">
          <Badge variant={result.requiere_retencion ? "warning" : "success"}>
            {result.requiere_retencion
              ? t("reg_con_retencion")
              : t("reg_sin_retencion")}
          </Badge>
          <span className="text-lg font-heading font-bold text-terracotta">
            {t("reg_monto_neto")}: {formatCurrency(result.monto_neto_pagar)}
          </span>
        </div>
        <Table headers={[t("reg_concepto"), t("reg_valor")]} rows={rows} />
      </Card>

      <DownloadButton
        data={csvData}
        filename="regulatorio_retenciones"
        label={t("descargar_csv")}
      />
    </div>
  );
}

/* ── Page component ────────────────────────────────────────────────────── */

export default function RegulatorioPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<RegTab>("rcs");
  const [rcsForm, setRcsForm] = useState<RCSFormState>(DEFAULT_RCS);
  const [dedForm, setDedForm] = useState<DeducibilidadFormState>(DEFAULT_DED);
  const [retForm, setRetForm] = useState<RetencionesFormState>(DEFAULT_RET);

  /* ── API hooks ──────────────────────────────────────────────────────── */

  const rcs = useCalculation<RCSRequest, RCSResponse>(regulatoryApi.rcs);
  const deductibility = useCalculation<DeductibilityRequest, DeductibilityResponse>(
    regulatoryApi.deductibility,
  );
  const withholding = useCalculation<WithholdingRequest, WithholdingResponse>(
    regulatoryApi.withholding,
  );

  /* ── Tabs definition ────────────────────────────────────────────────── */

  const tabs = useMemo(
    () => [
      { id: "rcs", label: t("regulatorio_rcs") },
      { id: "deducibilidad", label: t("regulatorio_deducibilidad") },
      { id: "retenciones", label: t("regulatorio_retenciones") },
    ],
    [t],
  );

  /* ── Handlers ──────────────────────────────────────────────────────── */

  const handleCalculate = useCallback(async () => {
    switch (activeTab) {
      case "rcs": {
        const req: RCSRequest = {
          config_vida: rcsForm.showVida
            ? {
                suma_asegurada_total: rcsForm.vida_suma_asegurada_total,
                reserva_matematica: rcsForm.vida_reserva_matematica,
                edad_promedio_asegurados: rcsForm.vida_edad_promedio,
                duracion_promedio_polizas: rcsForm.vida_duracion_promedio,
                numero_asegurados: rcsForm.vida_numero_asegurados,
              }
            : null,
          config_danos: rcsForm.showDanos
            ? {
                primas_retenidas_12m: rcsForm.danos_primas_retenidas_12m,
                reserva_siniestros: rcsForm.danos_reserva_siniestros,
                coeficiente_variacion: rcsForm.danos_coeficiente_variacion,
                numero_ramos: rcsForm.danos_numero_ramos,
              }
            : null,
          config_inversion: rcsForm.showInversion
            ? {
                valor_acciones: rcsForm.inv_valor_acciones,
                valor_bonos_gubernamentales: rcsForm.inv_valor_bonos_gub,
                valor_bonos_corporativos: rcsForm.inv_valor_bonos_corp,
                valor_inmuebles: rcsForm.inv_valor_inmuebles,
                duracion_promedio_bonos: rcsForm.inv_duracion_promedio_bonos,
                calificacion_promedio_bonos: rcsForm.inv_calificacion,
              }
            : null,
          capital_minimo_pagado: rcsForm.capital_minimo_pagado,
        };
        await rcs.calculate(req);
        break;
      }
      case "deducibilidad": {
        const req: DeductibilityRequest = {
          tipo_seguro: dedForm.tipo_seguro,
          monto_prima: dedForm.monto_prima,
          es_persona_fisica: dedForm.es_persona_fisica,
        };
        await deductibility.calculate(req);
        break;
      }
      case "retenciones": {
        const req: WithholdingRequest = {
          tipo_seguro: retForm.tipo_seguro,
          monto_pago: retForm.monto_pago,
          monto_gravable: retForm.monto_gravable,
          es_renta_vitalicia: retForm.es_renta_vitalicia,
          es_retiro_ahorro: retForm.es_retiro_ahorro,
        };
        await withholding.calculate(req);
        break;
      }
    }
  }, [activeTab, rcsForm, dedForm, retForm, rcs, deductibility, withholding]);

  /* ── Derive current loading / error ──────────────────────────────── */

  const currentHook = {
    rcs,
    deducibilidad: deductibility,
    retenciones: withholding,
  }[activeTab];

  const isLoading = currentHook.loading;
  const errorMsg = currentHook.error;

  /* ── Options ─────────────────────────────────────────────────────── */

  const tipoSeguroOptions = useMemo(
    () => [
      { value: "vida", label: t("reg_tipo_vida") },
      { value: "gastos_medicos", label: t("reg_tipo_gastos_medicos") },
      { value: "danos", label: t("reg_tipo_danos") },
      { value: "pensiones", label: t("reg_tipo_pensiones") },
      { value: "invalidez", label: t("reg_tipo_invalidez") },
    ],
    [t],
  );

  const calificacionOptions = useMemo(
    () => [
      { value: "AAA", label: "AAA" },
      { value: "AA", label: "AA" },
      { value: "A", label: "A" },
      { value: "BBB", label: "BBB" },
      { value: "BB", label: "BB" },
      { value: "B", label: "B" },
    ],
    [],
  );

  /* ── Toggle section helper ──────────────────────────────────────── */

  const SectionToggle = ({
    label,
    isOpen,
    onToggle,
    children,
  }: {
    label: string;
    isOpen: boolean;
    onToggle: () => void;
    children: React.ReactNode;
  }) => (
    <div className="border border-navy/10 rounded-lg">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 text-left text-sm font-medium text-navy/80 hover:text-terracotta transition-colors"
      >
        <span>{label}</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? "rotate-90" : ""}`}
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
      </button>
      {isOpen && <div className="px-4 pb-4">{children}</div>}
    </div>
  );

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-navy mb-2">
          {t("regulatorio_titulo")}
        </h1>
        <p className="text-navy/60 text-lg">{t("regulatorio_descripcion")}</p>
        <p className="text-navy/60 text-lg max-w-3xl mt-2">{t("regulatorio_contexto")}</p>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(id) => setActiveTab(id as RegTab)}
      />

      {/* ── RCS Form ──────────────────────────────────────────────── */}
      {activeTab === "rcs" && (
        <Card className="form-depth">
          <div className="space-y-4">
            {/* Capital minimo */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label={t("capital_minimo")}
                name="capital_minimo_pagado"
                type="number"
                min={0}
                value={rcsForm.capital_minimo_pagado}
                onChange={(e) =>
                  setRcsForm((prev) => ({
                    ...prev,
                    capital_minimo_pagado: Number(e.target.value),
                  }))
                }
              />
            </div>

            {/* Vida section */}
            <SectionToggle
              label={t("reg_config_vida")}
              isOpen={rcsForm.showVida}
              onToggle={() =>
                setRcsForm((prev) => ({ ...prev, showVida: !prev.showVida }))
              }
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-3">
                <Input
                  label={t("suma_asegurada") + " (" + t("reg_total") + ")"}
                  name="vida_sa"
                  type="number"
                  min={0}
                  value={rcsForm.vida_suma_asegurada_total}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      vida_suma_asegurada_total: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_reserva_matematica")}
                  name="vida_rm"
                  type="number"
                  min={0}
                  value={rcsForm.vida_reserva_matematica}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      vida_reserva_matematica: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_edad_promedio")}
                  name="vida_edad"
                  type="number"
                  min={18}
                  max={99}
                  value={rcsForm.vida_edad_promedio}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      vida_edad_promedio: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_duracion_promedio")}
                  name="vida_dur"
                  type="number"
                  min={1}
                  value={rcsForm.vida_duracion_promedio}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      vida_duracion_promedio: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_numero_asegurados")}
                  name="vida_num"
                  type="number"
                  min={1}
                  value={rcsForm.vida_numero_asegurados}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      vida_numero_asegurados: Number(e.target.value),
                    }))
                  }
                />
              </div>
            </SectionToggle>

            {/* Danos section */}
            <SectionToggle
              label={t("reg_config_danos")}
              isOpen={rcsForm.showDanos}
              onToggle={() =>
                setRcsForm((prev) => ({ ...prev, showDanos: !prev.showDanos }))
              }
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                <Input
                  label={t("reg_primas_retenidas")}
                  name="danos_pr"
                  type="number"
                  min={0}
                  value={rcsForm.danos_primas_retenidas_12m}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      danos_primas_retenidas_12m: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_reserva_siniestros")}
                  name="danos_rs"
                  type="number"
                  min={0}
                  value={rcsForm.danos_reserva_siniestros}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      danos_reserva_siniestros: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_coeficiente_variacion")}
                  name="danos_cv"
                  type="number"
                  step={0.01}
                  min={0}
                  max={1}
                  value={rcsForm.danos_coeficiente_variacion}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      danos_coeficiente_variacion: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_numero_ramos")}
                  name="danos_nr"
                  type="number"
                  min={1}
                  value={rcsForm.danos_numero_ramos}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      danos_numero_ramos: Number(e.target.value),
                    }))
                  }
                />
              </div>
            </SectionToggle>

            {/* Inversion section */}
            <SectionToggle
              label={t("reg_config_inversion")}
              isOpen={rcsForm.showInversion}
              onToggle={() =>
                setRcsForm((prev) => ({
                  ...prev,
                  showInversion: !prev.showInversion,
                }))
              }
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-3">
                <Input
                  label={t("reg_valor_acciones")}
                  name="inv_acc"
                  type="number"
                  min={0}
                  value={rcsForm.inv_valor_acciones}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      inv_valor_acciones: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_valor_bonos_gub")}
                  name="inv_bg"
                  type="number"
                  min={0}
                  value={rcsForm.inv_valor_bonos_gub}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      inv_valor_bonos_gub: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_valor_bonos_corp")}
                  name="inv_bc"
                  type="number"
                  min={0}
                  value={rcsForm.inv_valor_bonos_corp}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      inv_valor_bonos_corp: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_valor_inmuebles")}
                  name="inv_inm"
                  type="number"
                  min={0}
                  value={rcsForm.inv_valor_inmuebles}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      inv_valor_inmuebles: Number(e.target.value),
                    }))
                  }
                />
                <Input
                  label={t("reg_duracion_bonos")}
                  name="inv_dur"
                  type="number"
                  min={0}
                  value={rcsForm.inv_duracion_promedio_bonos}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      inv_duracion_promedio_bonos: Number(e.target.value),
                    }))
                  }
                />
                <Select
                  label={t("reg_calificacion")}
                  name="inv_cal"
                  options={calificacionOptions}
                  value={rcsForm.inv_calificacion}
                  onChange={(e) =>
                    setRcsForm((prev) => ({
                      ...prev,
                      inv_calificacion: e.target.value,
                    }))
                  }
                />
              </div>
            </SectionToggle>

            <div className="flex items-center gap-4 pt-2">
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

      {/* ── Deducibilidad Form ────────────────────────────────────── */}
      {activeTab === "deducibilidad" && (
        <Card className="form-depth">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Select
                label={t("reg_tipo_seguro")}
                name="tipo_seguro"
                options={tipoSeguroOptions}
                value={dedForm.tipo_seguro}
                onChange={(e) =>
                  setDedForm((prev) => ({
                    ...prev,
                    tipo_seguro: e.target.value,
                  }))
                }
              />
              <Input
                label={t("reg_monto_prima")}
                name="monto_prima"
                type="number"
                min={0}
                value={dedForm.monto_prima}
                onChange={(e) =>
                  setDedForm((prev) => ({
                    ...prev,
                    monto_prima: Number(e.target.value),
                  }))
                }
              />
              <div className="flex items-end pb-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={dedForm.es_persona_fisica}
                    onChange={(e) =>
                      setDedForm((prev) => ({
                        ...prev,
                        es_persona_fisica: e.target.checked,
                      }))
                    }
                    className="w-4 h-4 rounded border-navy/30 text-terracotta focus:ring-terracotta"
                  />
                  <span className="text-sm text-navy">
                    {t("reg_persona_fisica")}
                  </span>
                </label>
              </div>
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

      {/* ── Retenciones Form ──────────────────────────────────────── */}
      {activeTab === "retenciones" && (
        <Card className="form-depth">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Select
                label={t("reg_tipo_seguro")}
                name="tipo_seguro_ret"
                options={tipoSeguroOptions}
                value={retForm.tipo_seguro}
                onChange={(e) =>
                  setRetForm((prev) => ({
                    ...prev,
                    tipo_seguro: e.target.value,
                  }))
                }
              />
              <Input
                label={t("reg_monto_pago")}
                name="monto_pago"
                type="number"
                min={0}
                value={retForm.monto_pago}
                onChange={(e) =>
                  setRetForm((prev) => ({
                    ...prev,
                    monto_pago: Number(e.target.value),
                  }))
                }
              />
              <Input
                label={t("reg_monto_gravable")}
                name="monto_gravable"
                type="number"
                min={0}
                value={retForm.monto_gravable}
                onChange={(e) =>
                  setRetForm((prev) => ({
                    ...prev,
                    monto_gravable: Number(e.target.value),
                  }))
                }
              />
            </div>
            <div className="flex gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={retForm.es_renta_vitalicia}
                  onChange={(e) =>
                    setRetForm((prev) => ({
                      ...prev,
                      es_renta_vitalicia: e.target.checked,
                    }))
                  }
                  className="w-4 h-4 rounded border-navy/30 text-terracotta focus:ring-terracotta"
                />
                <span className="text-sm text-navy">
                  {t("reg_es_renta_vitalicia")}
                </span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={retForm.es_retiro_ahorro}
                  onChange={(e) =>
                    setRetForm((prev) => ({
                      ...prev,
                      es_retiro_ahorro: e.target.checked,
                    }))
                  }
                  className="w-4 h-4 rounded border-navy/30 text-terracotta focus:ring-terracotta"
                />
                <span className="text-sm text-navy">
                  {t("reg_es_retiro_ahorro")}
                </span>
              </label>
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
      {(rcs.data || deductibility.data || withholding.data) && (
        <div className="section-divider" />
      )}

      {activeTab === "rcs" && rcs.data && (
        <RCSResultCard result={rcs.data} t={t} />
      )}
      {activeTab === "deducibilidad" && deductibility.data && (
        <DeductibilityResultCard result={deductibility.data} t={t} />
      )}
      {activeTab === "retenciones" && withholding.data && (
        <WithholdingResultCard result={withholding.data} t={t} />
      )}
    </div>
  );
}
