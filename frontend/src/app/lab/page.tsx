"use client";

import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useLiveCalculation } from "@/hooks/useLiveCalculation";
import { pricingApi } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { labCopy } from "@/lib/i18n/labCopy";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { DotalLabChecks, DotalLabRequest } from "@/lib/types";

const STEP_KEYS = ["step1", "step2", "step3", "step4", "step5", "step6"] as const;
type DotalBooleanCheck = {
  [K in keyof DotalLabChecks]: DotalLabChecks[K] extends boolean ? K : never;
}[keyof DotalLabChecks];

const PYTHON_EXAMPLE = `from decimal import Decimal
from suite_actuarial import Asegurado, ConfiguracionProducto, TablaMortalidad
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.vida import VidaDotal

tabla = TablaMortalidad.cargar_emssa09()
config = ConfiguracionProducto(
    nombre_producto="Dotal educativo 20/10",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),
)
asegurado = Asegurado(
    edad=35,
    sexo=Sexo.HOMBRE,
    suma_asegurada=Decimal("1000000"),
)
producto = VidaDotal(config, tabla, plazo_pago=10)
analisis = producto.analizar_producto(asegurado)`;

function RangeControl({
  label,
  value,
  min,
  max,
  step,
  onChange,
  display,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  display: string;
}) {
  return (
    <label className="lab-control">
      <span>
        {label}
        <strong>{display}</strong>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function CheckRow({ label, passed, copy }: { label: string; passed?: boolean; copy: Record<string, string> }) {
  return (
    <div className="check-row">
      <span className={passed === undefined ? "check-mark pending" : passed ? "check-mark passed" : "check-mark failed"} aria-hidden="true">
        {passed === undefined ? "·" : passed ? "✓" : "×"}
      </span>
      <span>{label}</span>
      <strong>{passed === undefined ? copy.pending : passed ? copy.passed : copy.failed}</strong>
    </div>
  );
}

export default function LaboratoryPage() {
  const { lang } = useLanguage();
  const copy = labCopy[lang];
  const [activeStep, setActiveStep] = useState(0);
  const [age, setAge] = useState(35);
  const [sumAssured, setSumAssured] = useState(1_000_000);
  const [term, setTerm] = useState(20);
  const [payTerm, setPayTerm] = useState(10);
  const [rate, setRate] = useState(0.055);

  const request = useMemo<DotalLabRequest>(
    () => ({
      edad: age,
      sexo: "H",
      suma_asegurada: sumAssured,
      plazo_years: term,
      plazo_pago: Math.min(payTerm, term),
      tasa_interes: rate,
      frecuencia_pago: "anual",
      recargo_gastos_admin: 0.05,
      recargo_gastos_adq: 0.1,
      recargo_utilidad: 0.03,
    }),
    [age, sumAssured, term, payTerm, rate],
  );
  const { data, loading, error } = useLiveCalculation(pricingApi.dotalLab, request, 250);

  const checks: Array<[string, DotalBooleanCheck]> = [
    [copy.checkDecomp, "descomposicion_beneficios"],
    [copy.checkEquivalence, "principio_equivalencia"],
    [copy.checkInitial, "reserva_inicial_cero"],
    [copy.checkFinal, "reserva_final_igual_beneficio"],
    [copy.checkFackler, "recursion_fackler"],
  ];

  const renderStep = () => {
    if (activeStep === 0) {
      return (
        <div className="lab-prose">
          <p className="eyebrow">01 · {copy.purposeQuestion}</p>
          <h2>{copy.purposeTitle}</h2>
          <p>{copy.purposeText}</p>
          <blockquote>{copy.purposeQuestionText}</blockquote>
        </div>
      );
    }
    if (activeStep === 1) {
      return (
        <div className="lab-prose">
          <p className="eyebrow">02 · {copy.benefitsKicker}</p>
          <h2>{copy.benefitsTitle}</h2>
          <div className="benefit-grid">
            <article><span>01</span><h3>{copy.death}</h3><p>{copy.deathText}</p></article>
            <article><span>02</span><h3>{copy.survival}</h3><p>{copy.survivalText}</p></article>
          </div>
          <div className="equation">{copy.decomposition}</div>
        </div>
      );
    }
    if (activeStep === 2) {
      return (
        <div className="lab-prose">
          <p className="eyebrow">03 · {copy.assumptionsKicker}</p>
          <h2>{copy.assumptionsTitle}</h2>
          <div className="control-grid">
            <RangeControl label={copy.age} value={age} min={25} max={60} step={1} onChange={setAge} display={`${age} ${copy.years}`} />
            <RangeControl label={copy.sumAssured} value={sumAssured} min={500_000} max={5_000_000} step={250_000} onChange={setSumAssured} display={formatCurrency(sumAssured, 0)} />
            <RangeControl label={copy.term} value={term} min={10} max={30} step={5} onChange={(value) => { setTerm(value); setPayTerm((current) => Math.min(current, value)); }} display={`${term} ${copy.years}`} />
            <RangeControl label={copy.payTerm} value={Math.min(payTerm, term)} min={5} max={term} step={5} onChange={setPayTerm} display={`${Math.min(payTerm, term)} ${copy.years}`} />
            <RangeControl label={copy.rate} value={rate} min={0.02} max={0.09} step={0.005} onChange={setRate} display={formatPercent(rate, 1)} />
          </div>
          <div className="assumption-note"><span>{copy.mortality}</span><strong>{copy.mortalityValue}</strong></div>
        </div>
      );
    }
    if (activeStep === 3) {
      const deathShare = data ? (data.vp_beneficio_muerte / data.vp_beneficios_total) * 100 : 0;
      return (
        <div className="lab-prose">
          <p className="eyebrow">04 · {copy.premiumKicker}</p>
          <h2>{copy.premiumTitle}</h2>
          <div className="metric-grid">
            <article><span>{copy.netPremium}</span><strong>{data ? formatCurrency(data.prima_neta_anual_equivalente) : "—"}</strong></article>
            <article><span>{copy.totalPremium}</span><strong>{data ? formatCurrency(data.prima.prima_total) : "—"}</strong></article>
            <article><span>{copy.annuity}</span><strong>{data ? data.factor_anualidad_primas.toFixed(5) : "—"}</strong></article>
          </div>
          <div className="decomposition-bar" aria-label={copy.decomposition}>
            <div className="death" style={{ width: `${deathShare}%` }} />
            <div className="survival" style={{ width: `${100 - deathShare}%` }} />
          </div>
          <div className="bar-legend"><span>{copy.deathPV}: {data ? formatCurrency(data.vp_beneficio_muerte) : "—"}</span><span>{copy.survivalPV}: {data ? formatCurrency(data.vp_beneficio_supervivencia) : "—"}</span></div>
        </div>
      );
    }
    if (activeStep === 4) {
      return (
        <div className="lab-prose">
          <p className="eyebrow">05 · {copy.reserveKicker}</p>
          <h2>{copy.reserveTitle}</h2>
          <p>{copy.reserveText}</p>
          <div className="reserve-chart">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data?.reservas ?? []} margin={{ top: 12, right: 12, left: 8, bottom: 4 }}>
                <defs><linearGradient id="reserveFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#176B74" stopOpacity={0.35}/><stop offset="100%" stopColor="#176B74" stopOpacity={0.03}/></linearGradient></defs>
                <CartesianGrid stroke="#CBD5D1" strokeDasharray="3 5" vertical={false} />
                <XAxis dataKey="anio" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => `$${Math.round(value / 1000)}k`} />
                <Tooltip formatter={(value) => formatCurrency(Number(value))} labelFormatter={(value) => `${copy.years}: ${value}`} />
                <Area type="monotone" dataKey="reserva" stroke="#176B74" strokeWidth={2.5} fill="url(#reserveFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    }
    return (
      <div className="lab-prose">
        <p className="eyebrow">06 · {copy.validationKicker}</p>
        <h2>{copy.validationTitle}</h2>
        <p>{copy.validationText}</p>
        <div className="checks">
          {checks.map(([label, key]) => <CheckRow key={key} label={label} passed={data?.verificaciones[key]} copy={copy} />)}
        </div>
        <div className="evidence-note"><h3>{copy.evidence}</h3><p>{copy.evidenceText}</p></div>
      </div>
    );
  };

  return (
    <div className="lab-page">
      <header className="lab-hero">
        <p className="eyebrow">{copy.kicker}</p>
        <h1>{copy.title}</h1>
        <p className="lab-subtitle">{copy.subtitle}</p>
        <p className="scope-note">{copy.scope}</p>
      </header>

      <nav className="lab-steps" aria-label={copy.stepsLabel}>
        {STEP_KEYS.map((key, index) => (
          <button key={key} type="button" onClick={() => setActiveStep(index)} className={activeStep === index ? "active" : ""}>
            <span>{String(index + 1).padStart(2, "0")}</span>{copy[key]}
          </button>
        ))}
      </nav>

      <section className="lab-workspace">
        <div className="workspace-main">
          {error && <div className="lab-error"><strong>{copy.unavailable}</strong><span>{copy.error}</span></div>}
          {renderStep()}
          <div className="step-actions">
            <button type="button" disabled={activeStep === 0} onClick={() => setActiveStep((value) => value - 1)}>← {copy.previous}</button>
            <span>{loading ? copy.loading : copy.live}</span>
            <button type="button" disabled={activeStep === STEP_KEYS.length - 1} onClick={() => setActiveStep((value) => value + 1)}>{copy.next} →</button>
          </div>
        </div>
        <aside className="model-sheet">
          <div className="sheet-heading">
            <div><p className="eyebrow">{copy.modelSheet}</p><h2>Dotal {term}/{Math.min(payTerm, term)}</h2></div>
            <div className="sheet-step"><span>{copy.currentStage}</span><strong>{String(activeStep + 1).padStart(2, "0")} / 06</strong></div>
          </div>
          <div className="sheet-progress" aria-hidden="true">{STEP_KEYS.map((key, index) => <i key={key} className={index <= activeStep ? "active" : ""} />)}</div>
          <div className="contract-mini">
            <p>{copy.contractStructure}</p>
            <div><span>{copy.coverageBand}</span><b style={{ width: "100%" }} /></div>
            <div><span>{copy.premiumBand}</span><b className="premium" style={{ width: `${(Math.min(payTerm, term) / term) * 100}%` }} /></div>
            <footer><span>0</span><span>{Math.min(payTerm, term)}</span><span>{term}</span></footer>
          </div>
          <dl>
            <div><dt>{copy.age}</dt><dd>{age}</dd></div>
            <div><dt>{copy.sumAssured}</dt><dd>{formatCurrency(sumAssured, 0)}</dd></div>
            <div><dt>{copy.rate}</dt><dd>{formatPercent(rate, 1)}</dd></div>
            <div><dt>{copy.netPremium}</dt><dd>{data ? formatCurrency(data.prima_neta_anual_equivalente) : "—"}</dd></div>
          </dl>
          <div className={`model-status ${error ? "error" : loading ? "loading" : "ready"}`}>
            <i /><div><span>{copy.modelStatus}</span><strong>{error ? copy.unavailable : loading ? copy.connecting : copy.ready}</strong></div>
          </div>
        </aside>
      </section>
      <section className="lab-code">
        <details>
          <summary><span><small>PYTHON / 01</small><strong>{copy.codeTitle}</strong></span><b>{copy.showCode} ↓</b></summary>
          <div><p>{copy.codeText}</p><pre><code>{PYTHON_EXAMPLE}</code></pre></div>
        </details>
      </section>
    </div>
  );
}
