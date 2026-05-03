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
import { pensionesApi } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import type {
  Ley73Request,
  Ley73Response,
  Ley97Request,
  Ley97Response,
  RentaVitaliciaRequest,
  RentaVitaliciaResponse,
} from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Types ─────────────────────────────────────────────────────────────── */

type PensionesTab = "ley73" | "ley97" | "renta_vitalicia" | "conmutacion";

interface Ley73FormState {
  semanas_cotizadas: number;
  salario_promedio_diario: number;
  edad_retiro: number;
}

interface Ley97FormState {
  saldo_afore: number;
  edad: number;
  sexo: "H" | "M";
  semanas_cotizadas: number;
  tasa_interes: string;
}

interface RentaVitaliciaFormState {
  edad: number;
  sexo: "H" | "M";
  monto_mensual: number;
  tasa_interes: number;
  periodo_diferimiento: string;
  periodo_garantizado: string;
}

interface ConmutacionFormState {
  edad_min: number;
  edad_max: number;
  sexo: "H" | "M";
  tasa_interes: number;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ConmutacionRow = Record<string, any>;

/* ── Defaults ──────────────────────────────────────────────────────────── */

const DEFAULT_LEY73: Ley73FormState = {
  semanas_cotizadas: 1500,
  salario_promedio_diario: 800,
  edad_retiro: 65,
};

const DEFAULT_LEY97: Ley97FormState = {
  saldo_afore: 1_500_000,
  edad: 65,
  sexo: "H",
  semanas_cotizadas: 1500,
  tasa_interes: "",
};

const DEFAULT_RENTA: RentaVitaliciaFormState = {
  edad: 65,
  sexo: "H",
  monto_mensual: 15_000,
  tasa_interes: 0.035,
  periodo_diferimiento: "",
  periodo_garantizado: "",
};

const DEFAULT_CONMUTACION: ConmutacionFormState = {
  edad_min: 0,
  edad_max: 110,
  sexo: "H",
  tasa_interes: 0.05,
};

/* ── Page component ────────────────────────────────────────────────────── */

export default function PensionesPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<PensionesTab>("ley73");

  /* ── Form state ──────────────────────────────────────────────────────── */

  const [ley73Form, setLey73Form] = useState<Ley73FormState>(DEFAULT_LEY73);
  const [ley97Form, setLey97Form] = useState<Ley97FormState>(DEFAULT_LEY97);
  const [rentaForm, setRentaForm] = useState<RentaVitaliciaFormState>(DEFAULT_RENTA);
  const [conmForm, setConmForm] = useState<ConmutacionFormState>(DEFAULT_CONMUTACION);

  /* ── API hooks ──────────────────────────────────────────────────────── */

  const ley73 = useCalculation<Ley73Request, Ley73Response>(pensionesApi.ley73);
  const ley97 = useCalculation<Ley97Request, Ley97Response>(pensionesApi.ley97);
  const rentaVitalicia = useCalculation<RentaVitaliciaRequest, RentaVitaliciaResponse>(
    pensionesApi.rentaVitalicia,
  );

  /* Conmutacion is a GET endpoint -- handle with dedicated state */
  const [conmData, setConmData] = useState<ConmutacionRow[] | null>(null);
  const [conmLoading, setConmLoading] = useState(false);
  const [conmError, setConmError] = useState<string | null>(null);

  /* ── Tabs definition ────────────────────────────────────────────────── */

  const tabs = useMemo(
    () => [
      { id: "ley73", label: t("pensiones_ley73") },
      { id: "ley97", label: t("pensiones_ley97") },
      { id: "renta_vitalicia", label: t("pensiones_renta_vitalicia") },
      { id: "conmutacion", label: t("pensiones_conmutacion") },
    ],
    [t],
  );

  /* ── Select options ─────────────────────────────────────────────────── */

  const sexoOptions = useMemo(
    () => [
      { value: "H", label: t("masculino") },
      { value: "M", label: t("femenino") },
    ],
    [t],
  );

  /* ── Form field updaters ────────────────────────────────────────────── */

  const updateLey73 = useCallback(
    <K extends keyof Ley73FormState>(field: K, value: Ley73FormState[K]) => {
      setLey73Form((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const updateLey97 = useCallback(
    <K extends keyof Ley97FormState>(field: K, value: Ley97FormState[K]) => {
      setLey97Form((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const updateRenta = useCallback(
    <K extends keyof RentaVitaliciaFormState>(field: K, value: RentaVitaliciaFormState[K]) => {
      setRentaForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  const updateConm = useCallback(
    <K extends keyof ConmutacionFormState>(field: K, value: ConmutacionFormState[K]) => {
      setConmForm((prev) => ({ ...prev, [field]: value }));
    },
    [],
  );

  /* ── Calculate handler ──────────────────────────────────────────────── */

  const handleCalculate = useCallback(async () => {
    switch (activeTab) {
      case "ley73":
        await ley73.calculate({
          semanas_cotizadas: ley73Form.semanas_cotizadas,
          salario_promedio_diario: ley73Form.salario_promedio_diario,
          edad_retiro: ley73Form.edad_retiro,
        });
        break;
      case "ley97":
        await ley97.calculate({
          saldo_afore: ley97Form.saldo_afore,
          edad: ley97Form.edad,
          sexo: ley97Form.sexo,
          semanas_cotizadas: ley97Form.semanas_cotizadas,
          tasa_interes: ley97Form.tasa_interes ? Number(ley97Form.tasa_interes) : undefined,
        });
        break;
      case "renta_vitalicia":
        await rentaVitalicia.calculate({
          edad: rentaForm.edad,
          sexo: rentaForm.sexo,
          monto_mensual: rentaForm.monto_mensual,
          tasa_interes: rentaForm.tasa_interes,
          periodo_diferimiento: rentaForm.periodo_diferimiento
            ? Number(rentaForm.periodo_diferimiento)
            : undefined,
          periodo_garantizado: rentaForm.periodo_garantizado
            ? Number(rentaForm.periodo_garantizado)
            : undefined,
        });
        break;
      case "conmutacion":
        setConmLoading(true);
        setConmError(null);
        setConmData(null);
        try {
          const result = await pensionesApi.conmutacion({
            sexo: conmForm.sexo,
            tasa_interes: String(conmForm.tasa_interes),
            edad_min: String(conmForm.edad_min),
            edad_max: String(conmForm.edad_max),
          });
          setConmData(result as ConmutacionRow[]);
        } catch (err) {
          setConmError(err instanceof Error ? err.message : "Unknown error");
        } finally {
          setConmLoading(false);
        }
        break;
    }
  }, [activeTab, ley73Form, ley97Form, rentaForm, conmForm, ley73, ley97, rentaVitalicia]);

  /* ── Derive current loading / error ─────────────────────────────────── */

  const isLoading =
    activeTab === "conmutacion"
      ? conmLoading
      : { ley73, ley97, renta_vitalicia: rentaVitalicia, conmutacion: null }[activeTab]?.loading ??
        false;

  const errorMsg =
    activeTab === "conmutacion"
      ? conmError
      : { ley73, ley97, renta_vitalicia: rentaVitalicia, conmutacion: null }[activeTab]?.error ??
        null;

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-navy mb-2">
          {t("pensiones_titulo")}
        </h1>
        <p className="text-navy/60 text-lg">{t("pensiones_descripcion")}</p>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(id) => setActiveTab(id as PensionesTab)}
      />

      {/* Calculator form */}
      <Card className="form-depth">
        <div className="space-y-6">
          {/* Ley 73 form */}
          {activeTab === "ley73" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("semanas_cotizadas")}
                name="semanas_cotizadas"
                type="number"
                min={500}
                max={2600}
                value={ley73Form.semanas_cotizadas}
                onChange={(e) => updateLey73("semanas_cotizadas", Number(e.target.value))}
              />
              <Input
                label={t("salario_promedio")}
                name="salario_promedio_diario"
                type="number"
                min={1}
                value={ley73Form.salario_promedio_diario}
                onChange={(e) =>
                  updateLey73("salario_promedio_diario", Number(e.target.value))
                }
              />
              <Input
                label={t("edad_retiro")}
                name="edad_retiro"
                type="number"
                min={60}
                max={65}
                value={ley73Form.edad_retiro}
                onChange={(e) => updateLey73("edad_retiro", Number(e.target.value))}
              />
            </div>
          )}

          {/* Ley 97 form */}
          {activeTab === "ley97" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("saldo_afore")}
                name="saldo_afore"
                type="number"
                min={1}
                value={ley97Form.saldo_afore}
                onChange={(e) => updateLey97("saldo_afore", Number(e.target.value))}
              />
              <Input
                label={t("edad")}
                name="edad_97"
                type="number"
                min={60}
                max={75}
                value={ley97Form.edad}
                onChange={(e) => updateLey97("edad", Number(e.target.value))}
              />
              <Select
                label={t("sexo")}
                name="sexo_97"
                options={sexoOptions}
                value={ley97Form.sexo}
                onChange={(e) => updateLey97("sexo", e.target.value as "H" | "M")}
              />
              <Input
                label={t("semanas_cotizadas")}
                name="semanas_cotizadas_97"
                type="number"
                min={500}
                max={2600}
                value={ley97Form.semanas_cotizadas}
                onChange={(e) => updateLey97("semanas_cotizadas", Number(e.target.value))}
              />
              <Input
                label={t("tasa_interes")}
                name="tasa_interes_97"
                type="number"
                step={0.001}
                min={0}
                max={1}
                value={ley97Form.tasa_interes}
                onChange={(e) => updateLey97("tasa_interes", e.target.value)}
              />
            </div>
          )}

          {/* Renta Vitalicia form */}
          {activeTab === "renta_vitalicia" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("edad")}
                name="edad_rv"
                type="number"
                min={0}
                max={110}
                value={rentaForm.edad}
                onChange={(e) => updateRenta("edad", Number(e.target.value))}
              />
              <Select
                label={t("sexo")}
                name="sexo_rv"
                options={sexoOptions}
                value={rentaForm.sexo}
                onChange={(e) => updateRenta("sexo", e.target.value as "H" | "M")}
              />
              <Input
                label={t("monto_mensual")}
                name="monto_mensual"
                type="number"
                min={1}
                value={rentaForm.monto_mensual}
                onChange={(e) => updateRenta("monto_mensual", Number(e.target.value))}
              />
              <Input
                label={t("tasa_interes")}
                name="tasa_interes_rv"
                type="number"
                step={0.001}
                min={0}
                max={1}
                value={rentaForm.tasa_interes}
                onChange={(e) => updateRenta("tasa_interes", Number(e.target.value))}
              />
              <Input
                label={t("periodo_diferimiento")}
                name="periodo_diferimiento"
                type="number"
                min={0}
                value={rentaForm.periodo_diferimiento}
                onChange={(e) => updateRenta("periodo_diferimiento", e.target.value)}
              />
              <Input
                label={t("periodo_garantizado")}
                name="periodo_garantizado"
                type="number"
                min={0}
                value={rentaForm.periodo_garantizado}
                onChange={(e) => updateRenta("periodo_garantizado", e.target.value)}
              />
            </div>
          )}

          {/* Conmutacion form */}
          {activeTab === "conmutacion" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label={t("pensiones_edad_min")}
                name="edad_min"
                type="number"
                min={0}
                max={110}
                value={conmForm.edad_min}
                onChange={(e) => updateConm("edad_min", Number(e.target.value))}
              />
              <Input
                label={t("pensiones_edad_max")}
                name="edad_max"
                type="number"
                min={0}
                max={110}
                value={conmForm.edad_max}
                onChange={(e) => updateConm("edad_max", Number(e.target.value))}
              />
              <Select
                label={t("sexo")}
                name="sexo_conm"
                options={sexoOptions}
                value={conmForm.sexo}
                onChange={(e) => updateConm("sexo", e.target.value as "H" | "M")}
              />
              <Input
                label={t("tasa_interes")}
                name="tasa_interes_conm"
                type="number"
                step={0.001}
                min={0}
                max={1}
                value={conmForm.tasa_interes}
                onChange={(e) => updateConm("tasa_interes", Number(e.target.value))}
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
      {(ley73.data || ley97.data || rentaVitalicia.data || conmData) && (
        <div className="section-divider" />
      )}

      {/* ── Ley 73 results ────────────────────────────────────────────── */}
      {activeTab === "ley73" && ley73.data && (
        <Ley73Results result={ley73.data} t={t} />
      )}

      {/* ── Ley 97 results ────────────────────────────────────────────── */}
      {activeTab === "ley97" && ley97.data && (
        <Ley97Results result={ley97.data} t={t} />
      )}

      {/* ── Renta Vitalicia results ───────────────────────────────────── */}
      {activeTab === "renta_vitalicia" && rentaVitalicia.data && (
        <RentaVitaliciaResults result={rentaVitalicia.data} t={t} />
      )}

      {/* ── Conmutacion results ───────────────────────────────────────── */}
      {activeTab === "conmutacion" && conmData && (
        <ConmutacionResults data={conmData} t={t} />
      )}
    </div>
  );
}

/* ── Result components ──────────────────────────────────────────────────── */

function Ley73Results({
  result,
  t,
}: {
  result: Ley73Response;
  t: (key: TranslationKey) => string;
}) {
  const rows: [string, string][] = [
    [t("pensiones_regimen"), result.regimen],
    [t("semanas_cotizadas"), formatNumber(result.semanas_cotizadas, 0)],
    [t("salario_promedio"), formatCurrency(result.salario_promedio_diario)],
    [t("edad_retiro"), String(result.edad_retiro)],
    [t("pensiones_porcentaje_pension"), formatPercent(result.porcentaje_pension)],
    [t("pensiones_factor_edad"), formatNumber(result.factor_edad, 4)],
    [t("pension_mensual"), formatCurrency(result.pension_mensual)],
    [t("pensiones_aguinaldo_anual"), formatCurrency(result.aguinaldo_anual)],
    [t("pension_anual"), formatCurrency(result.pension_anual_total)],
  ];

  const csvData = { ...result } as unknown as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="result-accent">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("pension_mensual")}</p>
            <p className="text-3xl font-heading font-bold text-terracotta tabular-nums">
              {formatCurrency(result.pension_mensual)}
            </p>
          </div>
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("pension_anual")}</p>
            <p className="text-3xl font-heading font-bold text-navy tabular-nums">
              {formatCurrency(result.pension_anual_total)}
            </p>
          </div>
        </div>
      </Card>

      <Card title={t("danos_detalle_calculo")}>
        <Table headers={[t("danos_campo"), t("danos_valor")]} rows={rows} />
      </Card>

      <DownloadButton data={csvData} filename="pensiones_ley73" label={t("descargar_csv")} />
    </div>
  );
}

function Ley97Results({
  result,
  t,
}: {
  result: Ley97Response;
  t: (key: TranslationKey) => string;
}) {
  const compareRows: [string, string, string][] = [
    [
      t("pension_mensual"),
      formatCurrency(result.renta_vitalicia.pension_mensual),
      formatCurrency(result.retiro_programado.pension_mensual),
    ],
    [
      t("pension_anual"),
      formatCurrency(result.renta_vitalicia.pension_anual),
      formatCurrency(result.retiro_programado.pension_anual),
    ],
    [
      t("pensiones_tipo"),
      result.renta_vitalicia.tipo,
      result.retiro_programado.tipo,
    ],
  ];

  const infoRows: [string, string][] = [
    [t("saldo_afore"), formatCurrency(result.saldo_afore)],
    [t("edad"), String(result.edad)],
    [t("sexo"), result.sexo],
    [t("semanas_cotizadas"), formatNumber(result.semanas_cotizadas, 0)],
    [t("pensiones_diferencia_mensual"), formatCurrency(result.diferencia_mensual)],
    [t("pensiones_pension_garantizada"), formatCurrency(result.pension_garantizada)],
    [t("pensiones_recomendacion"), result.recomendacion],
  ];

  const csvData = {
    saldo_afore: result.saldo_afore,
    edad: result.edad,
    sexo: result.sexo,
    semanas_cotizadas: result.semanas_cotizadas,
    renta_vitalicia_mensual: result.renta_vitalicia.pension_mensual,
    renta_vitalicia_anual: result.renta_vitalicia.pension_anual,
    retiro_programado_mensual: result.retiro_programado.pension_mensual,
    retiro_programado_anual: result.retiro_programado.pension_anual,
    diferencia_mensual: result.diferencia_mensual,
    pension_garantizada: result.pension_garantizada,
    recomendacion: result.recomendacion,
  } as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card title={t("pensiones_comparacion_modalidades")} className="result-accent">
        <Table
          headers={[
            t("danos_concepto"),
            t("pensiones_renta_vitalicia"),
            t("pensiones_retiro_programado"),
          ]}
          rows={compareRows}
        />
      </Card>

      <Card title={t("pensiones_info_general")}>
        <Table headers={[t("danos_campo"), t("danos_valor")]} rows={infoRows} />
      </Card>

      <DownloadButton data={csvData} filename="pensiones_ley97" label={t("descargar_csv")} />
    </div>
  );
}

function RentaVitaliciaResults({
  result,
  t,
}: {
  result: RentaVitaliciaResponse;
  t: (key: TranslationKey) => string;
}) {
  const rows: [string, string][] = [
    [t("edad"), String(result.edad)],
    [t("sexo"), result.sexo],
    [t("monto_mensual"), formatCurrency(result.monto_mensual)],
    [t("tasa_interes"), formatPercent(result.tasa_interes)],
    [t("periodo_diferimiento"), String(result.periodo_diferimiento)],
    [t("periodo_garantizado"), String(result.periodo_garantizado)],
    [t("pensiones_factor_renta"), formatNumber(result.factor_renta, 6)],
    [t("pensiones_prima_unica"), formatCurrency(result.prima_unica)],
  ];

  const csvData = { ...result } as unknown as Record<string, unknown>;

  return (
    <div className="space-y-4 animate-fade-in">
      <Card className="result-accent">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("pensiones_prima_unica")}</p>
            <p className="text-3xl font-heading font-bold text-terracotta tabular-nums">
              {formatCurrency(result.prima_unica)}
            </p>
          </div>
          <div>
            <p className="text-sm text-navy/60 mb-1">{t("pensiones_factor_renta")}</p>
            <p className="text-3xl font-heading font-bold text-navy tabular-nums">
              {formatNumber(result.factor_renta, 6)}
            </p>
          </div>
        </div>
      </Card>

      <Card title={t("danos_detalle_calculo")}>
        <Table headers={[t("danos_campo"), t("danos_valor")]} rows={rows} />
      </Card>

      <DownloadButton data={csvData} filename="pensiones_renta_vitalicia" label={t("descargar_csv")} />
    </div>
  );
}

function ConmutacionResults({
  data,
  t,
}: {
  data: ConmutacionRow[];
  t: (key: TranslationKey) => string;
}) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <Card>
        <p className="text-navy/60">{t("pensiones_sin_datos")}</p>
      </Card>
    );
  }

  const headers = [t("edad"), "Dx", "Nx", "Mx", "ax", "Ax"];

  const rows = data.map((row) => [
    String(row.edad ?? row.x ?? ""),
    formatNumber(row.Dx ?? 0, 4),
    formatNumber(row.Nx ?? 0, 4),
    formatNumber(row.Mx ?? 0, 6),
    formatNumber(row.ax ?? 0, 6),
    formatNumber(row.Ax ?? 0, 6),
  ]);

  const csvData = data.map((row) => ({
    edad: row.edad ?? row.x ?? "",
    Dx: row.Dx ?? 0,
    Nx: row.Nx ?? 0,
    Mx: row.Mx ?? 0,
    ax: row.ax ?? 0,
    Ax: row.Ax ?? 0,
  })) as Record<string, unknown>[];

  return (
    <div className="space-y-4">
      <Card title={t("pensiones_tabla_conmutacion")}>
        <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
          <Table headers={headers} rows={rows} />
        </div>
      </Card>

      <DownloadButton data={csvData} filename="pensiones_conmutacion" label={t("descargar_csv")} />
    </div>
  );
}
