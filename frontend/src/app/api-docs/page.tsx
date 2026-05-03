"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { Card, Tabs, Table } from "@/components/ui";
import type { TranslationKey } from "@/lib/i18n/translations";

/* ── Types ─────────────────────────────────────────────────────────────── */

interface Param {
  name: string;
  type: string;
  required: boolean;
  default_val: string;
  description_es: string;
  description_en: string;
}

interface Endpoint {
  method: "POST" | "GET";
  path: string;
  desc_es: string;
  desc_en: string;
  params: Param[];
  example_req: string;
  example_res: string;
  try_link: string;
}

interface DomainGroup {
  id: string;
  labelKey: TranslationKey;
  endpoints: Endpoint[];
}

/* ── Endpoint data ─────────────────────────────────────────────────────── */

const DOMAINS: DomainGroup[] = [
  {
    id: "vida",
    labelKey: "nav_vida",
    endpoints: [
      {
        method: "POST",
        path: "/api/v1/pricing/temporal",
        desc_es: "Calcula la prima neta y bruta para un seguro de vida temporal usando la tabla de mortalidad EMSSA-09.",
        desc_en: "Calculates the net and gross premium for a term life insurance product using the EMSSA-09 mortality table.",
        params: [
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad del asegurado (0-120)", description_en: "Age of the insured (0-120)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: H (hombre) o M (mujer)", description_en: "Sex: H (male) or M (female)" },
          { name: "suma_asegurada", type: "float", required: true, default_val: "-", description_es: "Suma asegurada (> 0)", description_en: "Sum insured (> 0)" },
          { name: "plazo_years", type: "int", required: true, default_val: "-", description_es: "Plazo de la poliza en anos (1-99)", description_en: "Policy term in years (1-99)" },
          { name: "tasa_interes", type: "float", required: false, default_val: "0.055", description_es: "Tasa de interes tecnico (0-0.15)", description_en: "Technical interest rate (0-0.15)" },
          { name: "frecuencia_pago", type: "string", required: false, default_val: "anual", description_es: "Frecuencia: anual, semestral, trimestral, mensual", description_en: "Frequency: anual, semestral, trimestral, mensual" },
          { name: "recargo_gastos_admin", type: "float", required: false, default_val: "0.05", description_es: "Recargo por gastos de administracion (0-1)", description_en: "Admin expense loading (0-1)" },
          { name: "recargo_gastos_adq", type: "float", required: false, default_val: "0.10", description_es: "Recargo por gastos de adquisicion (0-1)", description_en: "Acquisition expense loading (0-1)" },
          { name: "recargo_utilidad", type: "float", required: false, default_val: "0.03", description_es: "Recargo por utilidad (0-1)", description_en: "Profit loading (0-1)" },
        ],
        example_req: `{
  "edad": 35,
  "sexo": "H",
  "suma_asegurada": 1000000,
  "plazo_years": 20,
  "tasa_interes": 0.055,
  "frecuencia_pago": "anual"
}`,
        example_res: `{
  "producto": "temporal",
  "prima_neta": 2024.08,
  "prima_total": 2388.42,
  "moneda": "MXN",
  "desglose_recargos": {
    "admin": 101.20,
    "adquisicion": 202.41,
    "utilidad": 60.72
  },
  "metadata": { ... }
}`,
        try_link: "/vida",
      },
      {
        method: "POST",
        path: "/api/v1/pricing/ordinario",
        desc_es: "Calcula la prima para un seguro de vida ordinario (vida entera). El campo plazo_years controla el periodo de pago de primas.",
        desc_en: "Calculates the premium for a whole life insurance product. The plazo_years field controls the premium payment period (limited pay).",
        params: [],
        example_req: `{
  "edad": 35,
  "sexo": "H",
  "suma_asegurada": 1000000,
  "plazo_years": 20,
  "tasa_interes": 0.055,
  "frecuencia_pago": "anual"
}`,
        example_res: `{
  "producto": "ordinario",
  "prima_neta": 5842.31,
  "prima_total": 6894.92,
  "moneda": "MXN",
  "desglose_recargos": { ... },
  "metadata": { ... }
}`,
        try_link: "/vida",
      },
      {
        method: "POST",
        path: "/api/v1/pricing/dotal",
        desc_es: "Calcula la prima para un seguro dotal (mixto) que paga por muerte o supervivencia al final del plazo.",
        desc_en: "Calculates the premium for an endowment product that pays on death or survival at the end of the term.",
        params: [],
        example_req: `{
  "edad": 35,
  "sexo": "M",
  "suma_asegurada": 500000,
  "plazo_years": 20,
  "tasa_interes": 0.055
}`,
        example_res: `{
  "producto": "dotal",
  "prima_neta": 14210.55,
  "prima_total": 16768.45,
  "moneda": "MXN",
  "desglose_recargos": { ... },
  "metadata": { ... }
}`,
        try_link: "/vida",
      },
      {
        method: "POST",
        path: "/api/v1/pricing/compare",
        desc_es: "Compara los tres productos de vida (temporal, ordinario, dotal) para el mismo asegurado con parametros identicos.",
        desc_en: "Compares all three life products (temporal, ordinario, dotal) for the same insured with identical parameters.",
        params: [],
        example_req: `{
  "edad": 35,
  "sexo": "H",
  "suma_asegurada": 1000000,
  "plazo_years": 20
}`,
        example_res: `{
  "temporal": { "prima_neta": 2024.08, ... },
  "ordinario": { "prima_neta": 5842.31, ... },
  "dotal": { "prima_neta": 28421.10, ... }
}`,
        try_link: "/vida",
      },
    ],
  },
  {
    id: "danos",
    labelKey: "nav_danos",
    endpoints: [
      {
        method: "POST",
        path: "/api/v1/danos/auto/calcular",
        desc_es: "Genera una cotizacion completa de seguro de auto usando tablas AMIS, factores de zona, edad del conductor, deducible, depreciacion y ajuste Bonus-Malus opcional.",
        desc_en: "Generates a complete auto insurance quotation using AMIS reference tables, zone factors, driver age, deductible, depreciation, and optional Bonus-Malus adjustment.",
        params: [
          { name: "valor_vehiculo", type: "float", required: true, default_val: "-", description_es: "Valor comercial del vehiculo en MXN", description_en: "Commercial vehicle value in MXN" },
          { name: "tipo_vehiculo", type: "string", required: true, default_val: "-", description_es: "Clave del tipo de vehiculo (sedan_compacto, suv_mediano, etc.)", description_en: "Vehicle type key (sedan_compacto, suv_mediano, etc.)" },
          { name: "antiguedad_anos", type: "int", required: true, default_val: "-", description_es: "Anos de antiguedad del vehiculo", description_en: "Vehicle age in years" },
          { name: "zona", type: "string", required: true, default_val: "-", description_es: "Clave de la zona de riesgo", description_en: "Risk zone key" },
          { name: "edad_conductor", type: "int", required: true, default_val: "-", description_es: "Edad del conductor principal (>= 18)", description_en: "Primary driver age (>= 18)" },
          { name: "deducible_pct", type: "float", required: false, default_val: "0.05", description_es: "Porcentaje de deducible", description_en: "Deductible percentage" },
          { name: "coberturas", type: "list[str] | null", required: false, default_val: "null (todas)", description_es: "Lista de coberturas a cotizar", description_en: "List of coverages to quote" },
          { name: "historial_siniestros", type: "list[int] | null", required: false, default_val: "null", description_es: "Historial anual de siniestros para Bonus-Malus", description_en: "Annual claims history for Bonus-Malus" },
        ],
        example_req: `{
  "valor_vehiculo": 350000,
  "tipo_vehiculo": "sedan_compacto",
  "antiguedad_anos": 3,
  "zona": "ciudad_mexico",
  "edad_conductor": 30,
  "deducible_pct": 0.05
}`,
        example_res: `{
  "vehiculo": { "tipo": "sedan_compacto", ... },
  "conductor": { "edad": 30, ... },
  "coberturas": { "danos_materiales": 4500.00, ... },
  "subtotal": 12350.00,
  "bonus_malus": { "factor": 1.0 },
  "prima_total": 12350.00
}`,
        try_link: "/danos",
      },
      {
        method: "POST",
        path: "/api/v1/danos/incendio/calcular",
        desc_es: "Genera una cotizacion de seguro de incendio basada en valor del inmueble, tipo de construccion, zona de riesgo y uso.",
        desc_en: "Generates a fire insurance quotation based on property value, construction type, risk zone, and property use.",
        params: [
          { name: "valor_inmueble", type: "float", required: true, default_val: "-", description_es: "Valor de reposicion del inmueble en MXN", description_en: "Property replacement value in MXN" },
          { name: "tipo_construccion", type: "string", required: true, default_val: "-", description_es: "concreto, acero, ladrillo, mixta, madera, lamina", description_en: "concreto, acero, ladrillo, mixta, madera, lamina" },
          { name: "zona", type: "string", required: true, default_val: "-", description_es: "urbana_baja, urbana_media, urbana_alta, industrial, rural, forestal", description_en: "urbana_baja, urbana_media, urbana_alta, industrial, rural, forestal" },
          { name: "uso", type: "string", required: true, default_val: "-", description_es: "habitacional, comercial, oficinas, industrial, bodega, restaurante", description_en: "habitacional, comercial, oficinas, industrial, bodega, restaurante" },
        ],
        example_req: `{
  "valor_inmueble": 5000000,
  "tipo_construccion": "concreto",
  "zona": "urbana_baja",
  "uso": "habitacional"
}`,
        example_res: `{
  "valor_inmueble": 5000000,
  "tipo_construccion": "concreto",
  "tasa_base": 0.0008,
  "zona": "urbana_baja",
  "factor_zona": 0.85,
  "uso": "habitacional",
  "factor_uso": 0.90,
  "prima_anual": 3060.00
}`,
        try_link: "/danos",
      },
      {
        method: "POST",
        path: "/api/v1/danos/rc/calcular",
        desc_es: "Genera una cotizacion de seguro de responsabilidad civil basada en limite de cobertura, deducible y clase de actividad.",
        desc_en: "Generates a general liability insurance quotation based on liability limit, deductible, and business activity class.",
        params: [
          { name: "limite_responsabilidad", type: "float", required: true, default_val: "-", description_es: "Limite maximo de cobertura en MXN", description_en: "Maximum liability limit in MXN" },
          { name: "deducible", type: "float", required: true, default_val: "-", description_es: "Monto del deducible en MXN", description_en: "Deductible amount in MXN" },
          { name: "clase_actividad", type: "string", required: true, default_val: "-", description_es: "Tipo de actividad (oficinas, comercio_minorista, restaurante, manufactura_ligera, etc.)", description_en: "Activity type (oficinas, comercio_minorista, restaurante, manufactura_ligera, etc.)" },
        ],
        example_req: `{
  "limite_responsabilidad": 10000000,
  "deducible": 50000,
  "clase_actividad": "oficinas"
}`,
        example_res: `{
  "limite_responsabilidad": 10000000,
  "deducible": 50000,
  "clase_actividad": "oficinas",
  "tasa_base": 0.002,
  "factor_deducible": 0.92,
  "prima_anual": 18400.00
}`,
        try_link: "/danos",
      },
      {
        method: "POST",
        path: "/api/v1/danos/bonus-malus",
        desc_es: "Calcula la transicion de nivel Bonus-Malus. Escala BMS mexicana: sin siniestros = -1 nivel (descuento), 1 siniestro = +2, 2+ siniestros = +3.",
        desc_en: "Calculates the Bonus-Malus level transition. Mexican BMS scale: no claims = -1 level (discount), 1 claim = +2, 2+ claims = +3.",
        params: [
          { name: "nivel_actual", type: "int", required: false, default_val: "0", description_es: "Nivel BMS actual (-5 a 3, 0 = base)", description_en: "Current BMS level (-5 to 3, 0 = base)" },
          { name: "numero_siniestros", type: "int", required: true, default_val: "-", description_es: "Numero de siniestros en el periodo (>= 0)", description_en: "Number of claims in the period (>= 0)" },
        ],
        example_req: `{
  "nivel_actual": 0,
  "numero_siniestros": 1
}`,
        example_res: `{
  "nivel_previo": 0,
  "siniestros": 1,
  "nivel_nuevo": 2,
  "factor": 1.30
}`,
        try_link: "/danos",
      },
      {
        method: "POST",
        path: "/api/v1/danos/frecuencia-severidad",
        desc_es: "Ejecuta un modelo de riesgo colectivo (S = X1 + ... + XN) con simulacion Monte Carlo. Retorna medidas de riesgo como VaR, TVaR y prima pura.",
        desc_en: "Runs a collective risk model simulation (S = X1 + ... + XN) with Monte Carlo. Returns risk measures including VaR, TVaR, and pure premium.",
        params: [
          { name: "dist_frecuencia", type: "string", required: true, default_val: "-", description_es: "Distribucion de frecuencia: poisson, negbinom, binomial", description_en: "Frequency distribution: poisson, negbinom, binomial" },
          { name: "params_frecuencia", type: "dict", required: true, default_val: "-", description_es: "Parametros de frecuencia (ej: {lambda_: 5})", description_en: "Frequency params (e.g.: {lambda_: 5})" },
          { name: "dist_severidad", type: "string", required: true, default_val: "-", description_es: "Distribucion de severidad: lognormal, pareto, gamma, weibull, exponencial", description_en: "Severity distribution: lognormal, pareto, gamma, weibull, exponencial" },
          { name: "params_severidad", type: "dict", required: true, default_val: "-", description_es: "Parametros de severidad (ej: {mu: 10, sigma: 1.5})", description_en: "Severity params (e.g.: {mu: 10, sigma: 1.5})" },
          { name: "n_simulaciones", type: "int", required: false, default_val: "100000", description_es: "Numero de simulaciones Monte Carlo (1,000-1,000,000)", description_en: "Monte Carlo simulations (1,000-1,000,000)" },
          { name: "seed", type: "int | null", required: false, default_val: "null", description_es: "Semilla para reproducibilidad", description_en: "Seed for reproducibility" },
        ],
        example_req: `{
  "dist_frecuencia": "poisson",
  "params_frecuencia": { "lambda_": 5 },
  "dist_severidad": "lognormal",
  "params_severidad": { "mu": 10, "sigma": 1.5 },
  "n_simulaciones": 100000,
  "seed": 42
}`,
        example_res: `{
  "prima_pura": 182340.50,
  "varianza_agregada": 1.2e+11,
  "desviacion_estandar": 346410.00,
  "asimetria": 3.42,
  "var_95": 650000.00,
  "tvar_95": 920000.00,
  "var_99": 1450000.00,
  "tvar_99": 1980000.00,
  "minimo": 0.0,
  "maximo": 12500000.00,
  "simulaciones": 100000
}`,
        try_link: "/danos",
      },
    ],
  },
  {
    id: "salud",
    labelKey: "nav_salud",
    endpoints: [
      {
        method: "POST",
        path: "/api/v1/salud/gmm/calcular",
        desc_es: "Calcula la prima de Gastos Medicos Mayores (GMM). Retorna un desglose detallado con tasa base, factores de ajuste, prima ajustada y siniestralidad esperada.",
        desc_en: "Calculates the Major Medical Expenses (GMM) premium. Returns a detailed breakdown with base rate, adjustment factors, adjusted premium, and expected claims.",
        params: [
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad del asegurado (0-110)", description_en: "Insured age (0-110)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: M (masculino) o F (femenino)", description_en: "Sex: M (male) or F (female)" },
          { name: "suma_asegurada", type: "float", required: true, default_val: "-", description_es: "Suma asegurada en MXN (min 1,000,000)", description_en: "Sum insured in MXN (min 1,000,000)" },
          { name: "deducible", type: "float", required: true, default_val: "-", description_es: "Monto del deducible en MXN", description_en: "Deductible amount in MXN" },
          { name: "coaseguro_pct", type: "float", required: true, default_val: "-", description_es: "Porcentaje de coaseguro (ej: 0.10 = 10%)", description_en: "Coinsurance percentage (e.g.: 0.10 = 10%)" },
          { name: "tope_coaseguro", type: "float | null", required: false, default_val: "null", description_es: "Tope maximo de coaseguro en MXN", description_en: "Maximum coinsurance cap in MXN" },
          { name: "zona", type: "string", required: false, default_val: "urbano", description_es: "Zona geografica: metro, urbano, foraneo", description_en: "Geographic zone: metro, urbano, foraneo" },
          { name: "nivel", type: "string", required: false, default_val: "medio", description_es: "Nivel hospitalario: estandar, medio, alto", description_en: "Hospital level: estandar, medio, alto" },
        ],
        example_req: `{
  "edad": 35,
  "sexo": "M",
  "suma_asegurada": 5000000,
  "deducible": 20000,
  "coaseguro_pct": 0.10,
  "zona": "metro",
  "nivel": "alto"
}`,
        example_res: `{
  "asegurado": { "edad": 35, "sexo": "M" },
  "producto": { "suma_asegurada": 5000000, ... },
  "tarificacion": {
    "tasa_base": 0.012,
    "prima_ajustada": 42000.00,
    ...
  },
  "siniestralidad_esperada": 35000.00
}`,
        try_link: "/salud",
      },
      {
        method: "POST",
        path: "/api/v1/salud/accidentes/calcular",
        desc_es: "Calcula la prima de Accidentes y Enfermedades. Retorna prima anual, tabla de indemnizacion por perdidas organicas, beneficio diario por hospitalizacion y gastos funerarios.",
        desc_en: "Calculates the Accident & Sickness premium. Returns annual premium, organic-loss indemnification table, daily hospitalization benefit, and funeral expenses.",
        params: [
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad del asegurado (18-70)", description_en: "Insured age (18-70)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: M (masculino) o F (femenino)", description_en: "Sex: M (male) or F (female)" },
          { name: "suma_asegurada", type: "float", required: true, default_val: "-", description_es: "Suma asegurada en MXN", description_en: "Sum insured in MXN" },
          { name: "ocupacion", type: "string", required: false, default_val: "oficina", description_es: "Clase de riesgo: oficina, comercio, industrial_ligero, industrial_pesado, alto_riesgo", description_en: "Risk class: oficina, comercio, industrial_ligero, industrial_pesado, alto_riesgo" },
          { name: "indemnizacion_diaria", type: "float | null", required: false, default_val: "null (0.1% SA)", description_es: "Monto diario por hospitalizacion", description_en: "Daily hospitalization amount" },
        ],
        example_req: `{
  "edad": 40,
  "sexo": "M",
  "suma_asegurada": 1000000,
  "ocupacion": "oficina"
}`,
        example_res: `{
  "suma_asegurada": 1000000,
  "prima_anual": 4500.00,
  "perdidas_organicas": { "muerte": 1000000, ... },
  "indemnizacion_diaria": { "monto": 1000, ... },
  "gastos_funerarios": 50000
}`,
        try_link: "/salud",
      },
    ],
  },
  {
    id: "pensiones",
    labelKey: "nav_pensiones",
    endpoints: [
      {
        method: "POST",
        path: "/api/v1/pensiones/ley73/calcular",
        desc_es: "Calcula una pension IMSS Ley 73 (regimen de beneficio definido). Retorna pension mensual, aguinaldo anual e ingreso total basado en semanas cotizadas, salario promedio y edad de retiro.",
        desc_en: "Calculates an IMSS Ley 73 pension (defined-benefit regime). Returns monthly pension, annual bonus, and total income based on weeks contributed, average salary, and retirement age.",
        params: [
          { name: "semanas_cotizadas", type: "int", required: true, default_val: "-", description_es: "Total de semanas cotizadas al IMSS (min 500)", description_en: "Total weeks contributed to IMSS (min 500)" },
          { name: "salario_promedio_diario", type: "float", required: true, default_val: "-", description_es: "Salario promedio diario de ultimas 250 semanas", description_en: "Average daily salary over last 250 weeks" },
          { name: "edad_retiro", type: "int", required: true, default_val: "-", description_es: "Edad de retiro (60-65)", description_en: "Retirement age (60-65)" },
        ],
        example_req: `{
  "semanas_cotizadas": 1500,
  "salario_promedio_diario": 800,
  "edad_retiro": 65
}`,
        example_res: `{
  "regimen": "Ley 73",
  "semanas_cotizadas": 1500,
  "salario_promedio_diario": 800,
  "edad_retiro": 65,
  "porcentaje_pension": 0.771,
  "factor_edad": 1.0,
  "pension_mensual": 18506.03,
  "aguinaldo_anual": 18506.03,
  "pension_anual_total": 240578.39
}`,
        try_link: "/pensiones",
      },
      {
        method: "POST",
        path: "/api/v1/pensiones/ley97/calcular",
        desc_es: "Calcula una pension IMSS Ley 97 (contribucion definida). Compara renta vitalicia vs retiro programado y recomienda la mejor opcion segun saldo AFORE, edad y semanas cotizadas.",
        desc_en: "Calculates an IMSS Ley 97 pension (defined contribution). Compares life annuity vs scheduled withdrawal and recommends the best option based on AFORE balance, age, and weeks contributed.",
        params: [
          { name: "saldo_afore", type: "float", required: true, default_val: "-", description_es: "Saldo actual de la cuenta AFORE en MXN", description_en: "Current AFORE account balance in MXN" },
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad actual del trabajador (60-70)", description_en: "Current worker age (60-70)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: H (hombre) o M (mujer)", description_en: "Sex: H (male) or M (female)" },
          { name: "semanas_cotizadas", type: "int", required: true, default_val: "-", description_es: "Total de semanas cotizadas al IMSS", description_en: "Total weeks contributed to IMSS" },
          { name: "tasa_interes", type: "float", required: false, default_val: "0.035", description_es: "Tasa de interes tecnico (0-0.15)", description_en: "Technical interest rate (0-0.15)" },
        ],
        example_req: `{
  "saldo_afore": 2000000,
  "edad": 65,
  "sexo": "H",
  "semanas_cotizadas": 1200,
  "tasa_interes": 0.035
}`,
        example_res: `{
  "saldo_afore": 2000000,
  "edad": 65,
  "sexo": "H",
  "renta_vitalicia": {
    "pension_mensual": 12500.00,
    "pension_anual": 150000.00,
    "tipo": "renta_vitalicia"
  },
  "retiro_programado": {
    "pension_mensual": 14200.00,
    ...
  },
  "diferencia_mensual": 1700.00,
  "recomendacion": "retiro_programado",
  "pension_garantizada": 7468.00
}`,
        try_link: "/pensiones",
      },
      {
        method: "POST",
        path: "/api/v1/pensiones/renta-vitalicia/calcular",
        desc_es: "Calcula el factor de renta y la prima unica necesaria para financiar una renta vitalicia del monto mensual indicado, usando mortalidad EMSSA-09.",
        desc_en: "Calculates the annuity factor and single premium needed to fund a life annuity of the given monthly amount, using EMSSA-09 mortality.",
        params: [
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad del rentista (0-110)", description_en: "Age of annuitant (0-110)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: H o M", description_en: "Sex: H or M" },
          { name: "monto_mensual", type: "float", required: true, default_val: "-", description_es: "Pago mensual de la renta en MXN", description_en: "Monthly annuity payment in MXN" },
          { name: "tasa_interes", type: "float", required: true, default_val: "-", description_es: "Tasa de interes tecnico (0-0.15)", description_en: "Technical interest rate (0-0.15)" },
          { name: "periodo_diferimiento", type: "int", required: false, default_val: "0", description_es: "Periodo de diferimiento en anos (0 = inmediata)", description_en: "Deferral period in years (0 = immediate)" },
          { name: "periodo_garantizado", type: "int", required: false, default_val: "0", description_es: "Periodo garantizado de pagos en anos", description_en: "Guaranteed payment period in years" },
        ],
        example_req: `{
  "edad": 65,
  "sexo": "H",
  "monto_mensual": 15000,
  "tasa_interes": 0.035,
  "periodo_diferimiento": 0,
  "periodo_garantizado": 5
}`,
        example_res: `{
  "edad": 65,
  "sexo": "H",
  "monto_mensual": 15000,
  "tasa_interes": 0.035,
  "periodo_diferimiento": 0,
  "periodo_garantizado": 5,
  "factor_renta": 11.234,
  "prima_unica": 2022120.00
}`,
        try_link: "/pensiones",
      },
      {
        method: "GET",
        path: "/api/v1/pensiones/conmutacion/tabla",
        desc_es: "Consulta la tabla de conmutacion (Dx, Nx, Mx, ax, Ax) para un rango de edades, usando mortalidad EMSSA-09 y la tasa de interes especificada.",
        desc_en: "Looks up commutation table values (Dx, Nx, Mx, ax, Ax) for a range of ages, using EMSSA-09 mortality and the specified interest rate.",
        params: [
          { name: "sexo", type: "string (query)", required: true, default_val: "-", description_es: "Sexo: H o M", description_en: "Sex: H or M" },
          { name: "tasa_interes", type: "float (query)", required: true, default_val: "-", description_es: "Tasa de interes tecnico (0-0.15)", description_en: "Technical interest rate (0-0.15)" },
          { name: "edad_min", type: "int (query)", required: false, default_val: "0", description_es: "Edad minima a incluir", description_en: "Minimum age to include" },
          { name: "edad_max", type: "int (query)", required: false, default_val: "110", description_es: "Edad maxima a incluir", description_en: "Maximum age to include" },
        ],
        example_req: `GET /api/v1/pensiones/conmutacion/tabla?sexo=H&tasa_interes=0.035&edad_min=60&edad_max=65`,
        example_res: `{
  "sexo": "H",
  "tasa_interes": 0.035,
  "edad_min": 60,
  "edad_max": 65,
  "filas": [
    { "edad": 60, "Dx": 5234.12, "Nx": 52341.20, "Mx": 1234.56, "ax": 10.00, "Ax": 0.236 },
    ...
  ]
}`,
        try_link: "/pensiones",
      },
    ],
  },
  {
    id: "reservas",
    labelKey: "nav_reservas",
    endpoints: [
      {
        method: "POST",
        path: "/api/v1/reserves/chain-ladder",
        desc_es: "Calcula reservas usando el metodo Chain Ladder. Acepta un triangulo de desarrollo acumulado y retorna ultimates proyectados, reservas IBNR por ano de origen y factores de desarrollo.",
        desc_en: "Calculates reserves using the Chain Ladder method. Accepts a cumulative development triangle and returns projected ultimates, IBNR reserves per origin year, and development factors.",
        params: [
          { name: "triangle", type: "list[list[float|null]]", required: true, default_val: "-", description_es: "Triangulo acumulado (null para celdas vacias)", description_en: "Cumulative triangle (null for missing cells)" },
          { name: "origin_years", type: "list[int]", required: true, default_val: "-", description_es: "Etiquetas de anos de origen (una por fila)", description_en: "Origin year labels (one per row)" },
          { name: "metodo_promedio", type: "string", required: false, default_val: "simple", description_es: "Metodo de promedio: simple, weighted, geometric", description_en: "Averaging method: simple, weighted, geometric" },
          { name: "calcular_tail_factor", type: "bool", required: false, default_val: "false", description_es: "Estimar factor de cola automaticamente", description_en: "Auto-estimate tail factor" },
          { name: "tail_factor", type: "float | null", required: false, default_val: "null", description_es: "Factor de cola manual (1.0-2.0)", description_en: "Manual tail factor (1.0-2.0)" },
        ],
        example_req: `{
  "triangle": [
    [3000, 5000, 5600, 5800, 5900],
    [3200, 5200, 5800, 6000, null],
    [3500, 5500, 6100, null, null],
    [3800, 5900, null, null, null],
    [4000, null, null, null, null]
  ],
  "origin_years": [2019, 2020, 2021, 2022, 2023],
  "metodo_promedio": "simple"
}`,
        example_res: `{
  "metodo": "chain_ladder",
  "reserva_total": 4983.22,
  "ultimate_total": 32883.22,
  "pagado_total": 27900.00,
  "reservas_por_anio": { "2020": 102.5, "2021": 480.3, ... },
  "ultimates_por_anio": { "2019": 5900, ... },
  "factores_desarrollo": [1.581, 1.108, 1.036, 1.017]
}`,
        try_link: "/reservas",
      },
      {
        method: "POST",
        path: "/api/v1/reserves/bornhuetter-ferguson",
        desc_es: "Calcula reservas con el metodo Bornhuetter-Ferguson. Combina el desarrollo observado (factores Chain Ladder) con un estimado a priori del loss ratio, proporcionando reservas mas estables para anos inmaduros.",
        desc_en: "Calculates reserves using Bornhuetter-Ferguson. Combines observed development (Chain Ladder factors) with an a-priori loss ratio estimate, providing more stable reserves for immature years.",
        params: [
          { name: "triangle", type: "list[list[float|null]]", required: true, default_val: "-", description_es: "Triangulo acumulado", description_en: "Cumulative triangle" },
          { name: "origin_years", type: "list[int]", required: true, default_val: "-", description_es: "Anos de origen", description_en: "Origin years" },
          { name: "primas_por_anio", type: "dict[int, float]", required: true, default_val: "-", description_es: "Primas devengadas por ano de origen", description_en: "Earned premiums by origin year" },
          { name: "loss_ratio_apriori", type: "float", required: true, default_val: "-", description_es: "Loss ratio a priori esperado (0-2.0, ej: 0.65)", description_en: "A-priori expected loss ratio (0-2.0, e.g.: 0.65)" },
          { name: "metodo_promedio", type: "string", required: false, default_val: "simple", description_es: "Metodo de promedio: simple, weighted, geometric", description_en: "Averaging: simple, weighted, geometric" },
        ],
        example_req: `{
  "triangle": [
    [3000, 5000, 5600, 5800, 5900],
    [3200, 5200, 5800, 6000, null],
    [3500, 5500, 6100, null, null],
    [3800, 5900, null, null, null],
    [4000, null, null, null, null]
  ],
  "origin_years": [2019, 2020, 2021, 2022, 2023],
  "primas_por_anio": {
    "2019": 7000, "2020": 7500,
    "2021": 8000, "2022": 8500, "2023": 9000
  },
  "loss_ratio_apriori": 0.65
}`,
        example_res: `{
  "metodo": "bornhuetter_ferguson",
  "reserva_total": 5120.40,
  "ultimate_total": 33020.40,
  "pagado_total": 27900.00,
  "reservas_por_anio": { "2020": 95.2, ... },
  "factores_desarrollo": [1.581, 1.108, 1.036, 1.017]
}`,
        try_link: "/reservas",
      },
      {
        method: "POST",
        path: "/api/v1/reserves/bootstrap",
        desc_es: "Calcula reservas con el metodo Bootstrap. Ejecuta simulaciones Monte Carlo sobre triangulos re-muestreados para producir una distribucion completa de estimados de reserva, incluyendo percentiles.",
        desc_en: "Calculates reserves using Bootstrap simulation. Runs Monte Carlo on re-sampled triangles to produce a full distribution of reserve estimates including percentiles.",
        params: [
          { name: "triangle", type: "list[list[float|null]]", required: true, default_val: "-", description_es: "Triangulo acumulado", description_en: "Cumulative triangle" },
          { name: "origin_years", type: "list[int]", required: true, default_val: "-", description_es: "Anos de origen", description_en: "Origin years" },
          { name: "num_simulaciones", type: "int", required: false, default_val: "1000", description_es: "Numero de simulaciones (100-10,000)", description_en: "Number of simulations (100-10,000)" },
          { name: "seed", type: "int | null", required: false, default_val: "null", description_es: "Semilla para reproducibilidad", description_en: "Seed for reproducibility" },
          { name: "percentiles", type: "list[int]", required: false, default_val: "[50,75,90,95,99]", description_es: "Percentiles a calcular", description_en: "Percentiles to calculate" },
        ],
        example_req: `{
  "triangle": [
    [3000, 5000, 5600, 5800, 5900],
    [3200, 5200, 5800, 6000, null],
    [3500, 5500, 6100, null, null]
  ],
  "origin_years": [2020, 2021, 2022],
  "num_simulaciones": 5000,
  "seed": 42
}`,
        example_res: `{
  "metodo": "bootstrap",
  "reserva_total": 4850.00,
  "ultimate_total": 17750.00,
  "pagado_total": 12900.00,
  "percentiles": {
    "50": 4720, "75": 5100,
    "90": 5800, "95": 6200, "99": 7100
  }
}`,
        try_link: "/reservas",
      },
    ],
  },
  {
    id: "regulatorio",
    labelKey: "nav_regulatorio",
    endpoints: [
      {
        method: "POST",
        path: "/api/v1/regulatory/rcs",
        desc_es: "Calcula el Requerimiento de Capital de Solvencia (RCS) completo. Agrega riesgos de suscripcion (vida y danos) e inversion usando una matriz de correlacion conforme a la CNSF. Se requiere al menos uno de config_vida, config_danos o config_inversion.",
        desc_en: "Calculates the full Solvency Capital Requirement (RCS). Aggregates subscription risks (life and P&C) and investment risks using a correlation matrix per CNSF regulations. At least one of config_vida, config_danos, or config_inversion must be provided.",
        params: [
          { name: "config_vida", type: "object | null", required: false, default_val: "null", description_es: "Riesgos de suscripcion vida (suma_asegurada_total, reserva_matematica, edad_promedio_asegurados, duracion_promedio_polizas, numero_asegurados)", description_en: "Life subscription risks (suma_asegurada_total, reserva_matematica, edad_promedio_asegurados, duracion_promedio_polizas, numero_asegurados)" },
          { name: "config_danos", type: "object | null", required: false, default_val: "null", description_es: "Riesgos de suscripcion danos (primas_retenidas_12m, reserva_siniestros, coeficiente_variacion, numero_ramos)", description_en: "P&C subscription risks (primas_retenidas_12m, reserva_siniestros, coeficiente_variacion, numero_ramos)" },
          { name: "config_inversion", type: "object | null", required: false, default_val: "null", description_es: "Riesgos de inversion (valor_acciones, valor_bonos_gubernamentales, valor_bonos_corporativos, valor_inmuebles, duracion_promedio_bonos, calificacion_promedio_bonos)", description_en: "Investment risks (valor_acciones, valor_bonos_gubernamentales, valor_bonos_corporativos, valor_inmuebles, duracion_promedio_bonos, calificacion_promedio_bonos)" },
          { name: "capital_minimo_pagado", type: "float", required: true, default_val: "-", description_es: "Capital minimo pagado (> 0)", description_en: "Minimum paid-in capital (> 0)" },
        ],
        example_req: `{
  "config_vida": {
    "suma_asegurada_total": 500000000,
    "reserva_matematica": 150000000,
    "edad_promedio_asegurados": 42,
    "duracion_promedio_polizas": 15,
    "numero_asegurados": 1000
  },
  "config_danos": {
    "primas_retenidas_12m": 200000000,
    "reserva_siniestros": 80000000,
    "coeficiente_variacion": 0.15,
    "numero_ramos": 5
  },
  "capital_minimo_pagado": 100000000
}`,
        example_res: `{
  "rcs_total": 85000000,
  "rcs_suscripcion_vida": 45000000,
  "rcs_suscripcion_danos": 32000000,
  "rcs_inversion": 0,
  "ratio_solvencia": 1.176,
  "cumple_regulacion": true,
  "desglose_por_riesgo": { ... }
}`,
        try_link: "/regulatorio",
      },
      {
        method: "POST",
        path: "/api/v1/regulatory/sat/deductibility",
        desc_es: "Verifica la deducibilidad de una prima de seguros para efectos del ISR segun reglas del SAT. Determina si la prima es deducible y hasta que monto, segun tipo de seguro y categoria de contribuyente.",
        desc_en: "Checks premium deductibility for ISR purposes per SAT rules. Determines whether an insurance premium is tax-deductible and up to what amount, based on insurance type and taxpayer category.",
        params: [
          { name: "tipo_seguro", type: "string", required: true, default_val: "-", description_es: "Tipo de seguro: vida, gastos_medicos, danos, pensiones, invalidez", description_en: "Insurance type: vida, gastos_medicos, danos, pensiones, invalidez" },
          { name: "monto_prima", type: "float", required: true, default_val: "-", description_es: "Monto de la prima (> 0)", description_en: "Premium amount (> 0)" },
          { name: "es_persona_fisica", type: "bool", required: false, default_val: "true", description_es: "true = persona fisica, false = persona moral", description_en: "true = individual, false = legal entity" },
          { name: "uma_anual", type: "float", required: false, default_val: "39960.60", description_es: "Valor UMA anual (UMA diaria x 365)", description_en: "Annual UMA value (daily UMA x 365)" },
        ],
        example_req: `{
  "tipo_seguro": "gastos_medicos",
  "monto_prima": 25000,
  "es_persona_fisica": true
}`,
        example_res: `{
  "es_deducible": true,
  "monto_prima": 25000,
  "monto_deducible": 25000,
  "porcentaje_deducible": 1.0,
  "limite_aplicado": null,
  "fundamento_legal": "Art. 151 fraccion VI LISR"
}`,
        try_link: "/regulatorio",
      },
      {
        method: "POST",
        path: "/api/v1/regulatory/sat/withholding",
        desc_es: "Calcula la retencion de ISR sobre un pago de seguros. Determina si aplica retencion y calcula el monto segun tipo de pago (rentas vitalicias, retiros de ahorro, etc.) conforme a la Ley del ISR.",
        desc_en: "Calculates ISR withholding on an insurance payment. Determines whether withholding applies and computes the retention amount based on payment type (annuities, savings withdrawals, etc.) per Ley del ISR.",
        params: [
          { name: "tipo_seguro", type: "string", required: true, default_val: "-", description_es: "Tipo de seguro: vida, gastos_medicos, danos, pensiones, invalidez", description_en: "Insurance type: vida, gastos_medicos, danos, pensiones, invalidez" },
          { name: "monto_pago", type: "float", required: true, default_val: "-", description_es: "Monto del pago (> 0)", description_en: "Payment amount (> 0)" },
          { name: "monto_gravable", type: "float", required: true, default_val: "-", description_es: "Monto gravable (>= 0)", description_en: "Taxable amount (>= 0)" },
          { name: "es_renta_vitalicia", type: "bool", required: false, default_val: "false", description_es: "Es pago de renta vitalicia", description_en: "Is a life annuity payment" },
          { name: "es_retiro_ahorro", type: "bool", required: false, default_val: "false", description_es: "Es retiro de ahorro", description_en: "Is a savings withdrawal" },
          { name: "requiere_retencion_forzosa", type: "bool", required: false, default_val: "false", description_es: "Requiere retencion forzosa", description_en: "Requires forced withholding" },
        ],
        example_req: `{
  "tipo_seguro": "vida",
  "monto_pago": 500000,
  "monto_gravable": 200000,
  "es_renta_vitalicia": false,
  "es_retiro_ahorro": true
}`,
        example_res: `{
  "requiere_retencion": true,
  "monto_pago": 500000,
  "base_retencion": 200000,
  "tasa_retencion": 0.20,
  "monto_retencion": 40000,
  "monto_neto_pagar": 460000
}`,
        try_link: "/regulatorio",
      },
    ],
  },
  {
    id: "reaseguro",
    labelKey: "nav_reaseguro",
    endpoints: [
      {
        method: "POST",
        path: "/api/v1/reinsurance/quota-share",
        desc_es: "Calcula los resultados de un contrato de reaseguro cuota parte (proporcional). Aplica un porcentaje de cesion a primas y siniestros, retornando montos retenidos, recuperaciones y comisiones.",
        desc_en: "Calculates quota share reinsurance results. Applies a proportional cession percentage to premiums and claims, returning retained amounts, recoveries, and commissions.",
        params: [
          { name: "porcentaje_cesion", type: "float", required: true, default_val: "-", description_es: "Porcentaje de cesion (0-100)", description_en: "Cession percentage (0-100)" },
          { name: "comision_reaseguro", type: "float", required: true, default_val: "-", description_es: "Comision de reaseguro (0-50%)", description_en: "Reinsurance commission (0-50%)" },
          { name: "comision_override", type: "float", required: false, default_val: "0.0", description_es: "Comision override (0-10%)", description_en: "Override commission (0-10%)" },
          { name: "vigencia_inicio", type: "date", required: true, default_val: "-", description_es: "Fecha de inicio de vigencia (YYYY-MM-DD)", description_en: "Inception date (YYYY-MM-DD)" },
          { name: "vigencia_fin", type: "date", required: true, default_val: "-", description_es: "Fecha de fin de vigencia (YYYY-MM-DD)", description_en: "Expiry date (YYYY-MM-DD)" },
          { name: "moneda", type: "string", required: false, default_val: "MXN", description_es: "Moneda del contrato", description_en: "Contract currency" },
          { name: "prima_bruta", type: "float", required: true, default_val: "-", description_es: "Prima bruta total (> 0)", description_en: "Total gross premium (> 0)" },
          { name: "siniestros", type: "list[object]", required: true, default_val: "-", description_es: "Lista de siniestros ({id_siniestro, fecha_ocurrencia, monto_bruto})", description_en: "Claims list ({id_siniestro, fecha_ocurrencia, monto_bruto})" },
        ],
        example_req: `{
  "porcentaje_cesion": 40,
  "comision_reaseguro": 30,
  "vigencia_inicio": "2025-01-01",
  "vigencia_fin": "2025-12-31",
  "prima_bruta": 10000000,
  "siniestros": [
    {
      "id_siniestro": "S001",
      "fecha_ocurrencia": "2025-03-15",
      "monto_bruto": 500000
    }
  ]
}`,
        example_res: `{
  "tipo_contrato": "quota_share",
  "monto_cedido": 4000000,
  "monto_retenido": 6000000,
  "recuperacion_reaseguro": 200000,
  "comision_recibida": 1200000,
  "prima_reaseguro_pagada": 4000000,
  "ratio_cesion": 0.40,
  "resultado_neto_cedente": -2600000,
  "detalles": { ... }
}`,
        try_link: "/reaseguro",
      },
      {
        method: "POST",
        path: "/api/v1/reinsurance/excess-of-loss",
        desc_es: "Calcula los resultados de un contrato de reaseguro exceso de perdida (XL). El reasegurador paga cuando un siniestro excede la retencion, hasta el limite del contrato.",
        desc_en: "Calculates excess of loss (XL) reinsurance results. The reinsurer pays when a claim exceeds the retention, up to the contract limit.",
        params: [
          { name: "retencion", type: "float", required: true, default_val: "-", description_es: "Monto de retencion (> 0)", description_en: "Retention amount (> 0)" },
          { name: "limite", type: "float", required: true, default_val: "-", description_es: "Limite del contrato (> 0)", description_en: "Contract limit (> 0)" },
          { name: "modalidad", type: "string", required: false, default_val: "por_riesgo", description_es: "Modalidad: por_riesgo o por_evento", description_en: "Modality: por_riesgo or por_evento" },
          { name: "numero_reinstatements", type: "int", required: false, default_val: "0", description_es: "Numero de reinstalaciones (0-3)", description_en: "Number of reinstatements (0-3)" },
          { name: "tasa_prima", type: "float", required: true, default_val: "-", description_es: "Tasa de prima (0-100%)", description_en: "Premium rate (0-100%)" },
          { name: "vigencia_inicio", type: "date", required: true, default_val: "-", description_es: "Fecha de inicio (YYYY-MM-DD)", description_en: "Inception date (YYYY-MM-DD)" },
          { name: "vigencia_fin", type: "date", required: true, default_val: "-", description_es: "Fecha de fin (YYYY-MM-DD)", description_en: "Expiry date (YYYY-MM-DD)" },
          { name: "moneda", type: "string", required: false, default_val: "MXN", description_es: "Moneda", description_en: "Currency" },
          { name: "prima_reaseguro_cobrada", type: "float", required: true, default_val: "-", description_es: "Prima de reaseguro cobrada (> 0)", description_en: "Reinsurance premium collected (> 0)" },
          { name: "siniestros", type: "list[object]", required: true, default_val: "-", description_es: "Lista de siniestros", description_en: "Claims list" },
        ],
        example_req: `{
  "retencion": 1000000,
  "limite": 5000000,
  "modalidad": "por_riesgo",
  "tasa_prima": 5.0,
  "vigencia_inicio": "2025-01-01",
  "vigencia_fin": "2025-12-31",
  "prima_reaseguro_cobrada": 2500000,
  "siniestros": [
    {
      "id_siniestro": "S001",
      "fecha_ocurrencia": "2025-06-01",
      "monto_bruto": 3000000
    }
  ]
}`,
        example_res: `{
  "tipo_contrato": "excess_of_loss",
  "monto_cedido": 2000000,
  "monto_retenido": 1000000,
  "recuperacion_reaseguro": 2000000,
  "comision_recibida": 0,
  "prima_reaseguro_pagada": 2500000,
  "ratio_cesion": 0.667,
  "resultado_neto_cedente": -500000,
  "detalles": { ... }
}`,
        try_link: "/reaseguro",
      },
      {
        method: "POST",
        path: "/api/v1/reinsurance/stop-loss",
        desc_es: "Calcula los resultados de un contrato stop loss (agregado). Protege cuando el loss ratio agregado excede el punto de retencion (attachment point).",
        desc_en: "Calculates stop loss reinsurance results. Protects when the aggregate loss ratio exceeds the attachment point.",
        params: [
          { name: "attachment_point", type: "float", required: true, default_val: "-", description_es: "Punto de retencion en loss ratio (0-200%)", description_en: "Attachment point as loss ratio (0-200%)" },
          { name: "limite_cobertura", type: "float", required: true, default_val: "-", description_es: "Limite de cobertura en loss ratio (0-100%)", description_en: "Coverage limit as loss ratio (0-100%)" },
          { name: "primas_sujetas", type: "float", required: true, default_val: "-", description_es: "Primas sujetas al contrato (> 0)", description_en: "Subject premiums (> 0)" },
          { name: "vigencia_inicio", type: "date", required: true, default_val: "-", description_es: "Fecha de inicio (YYYY-MM-DD)", description_en: "Inception date (YYYY-MM-DD)" },
          { name: "vigencia_fin", type: "date", required: true, default_val: "-", description_es: "Fecha de fin (YYYY-MM-DD)", description_en: "Expiry date (YYYY-MM-DD)" },
          { name: "moneda", type: "string", required: false, default_val: "MXN", description_es: "Moneda", description_en: "Currency" },
          { name: "primas_totales", type: "float", required: true, default_val: "-", description_es: "Primas totales del periodo (> 0)", description_en: "Total period premiums (> 0)" },
          { name: "prima_reaseguro_cobrada", type: "float | null", required: false, default_val: "null", description_es: "Prima de reaseguro cobrada", description_en: "Reinsurance premium collected" },
          { name: "siniestros", type: "list[object]", required: true, default_val: "-", description_es: "Lista de siniestros", description_en: "Claims list" },
        ],
        example_req: `{
  "attachment_point": 80,
  "limite_cobertura": 40,
  "primas_sujetas": 50000000,
  "vigencia_inicio": "2025-01-01",
  "vigencia_fin": "2025-12-31",
  "primas_totales": 50000000,
  "siniestros": [
    {
      "id_siniestro": "S001",
      "fecha_ocurrencia": "2025-04-10",
      "monto_bruto": 45000000
    }
  ]
}`,
        example_res: `{
  "tipo_contrato": "stop_loss",
  "monto_cedido": 5000000,
  "monto_retenido": 40000000,
  "recuperacion_reaseguro": 5000000,
  "prima_reaseguro_pagada": 0,
  "ratio_cesion": 0.111,
  "resultado_neto_cedente": 5000000,
  "detalles": { ... }
}`,
        try_link: "/reaseguro",
      },
    ],
  },
  {
    id: "config",
    labelKey: "api_docs_tab_config",
    endpoints: [
      {
        method: "GET",
        path: "/api/v1/config/{anio}",
        desc_es: "Retorna la configuracion regulatoria completa para un ano fiscal: UMA, tasas SAT, factores CNSF y parametros tecnicos.",
        desc_en: "Returns the full regulatory configuration for a fiscal year: UMA, SAT rates, CNSF factors, and technical parameters.",
        params: [
          { name: "anio", type: "int (path)", required: true, default_val: "-", description_es: "Ano fiscal (ej: 2025)", description_en: "Fiscal year (e.g.: 2025)" },
        ],
        example_req: `GET /api/v1/config/2025`,
        example_res: `{
  "anio": 2025,
  "uma": {
    "uma_diaria": 113.14,
    "uma_mensual": 3439.46,
    "uma_anual": 41296.10
  },
  "tasas_sat": {
    "tasa_retencion_rentas_vitalicias": 0.20,
    "tasa_isr_personas_morales": 0.30,
    "tasa_iva": 0.16,
    ...
  },
  "factores_cnsf": { ... },
  "factores_tecnicos": { ... }
}`,
        try_link: "/regulatorio",
      },
      {
        method: "GET",
        path: "/api/v1/config/{anio}/uma",
        desc_es: "Retorna los valores de la UMA (Unidad de Medida y Actualizacion) diaria, mensual y anual para un ano fiscal.",
        desc_en: "Returns the daily, monthly, and annual UMA (Unidad de Medida y Actualizacion) values for a fiscal year.",
        params: [
          { name: "anio", type: "int (path)", required: true, default_val: "-", description_es: "Ano fiscal", description_en: "Fiscal year" },
        ],
        example_req: `GET /api/v1/config/2025/uma`,
        example_res: `{
  "uma_diaria": 113.14,
  "uma_mensual": 3439.46,
  "uma_anual": 41296.10
}`,
        try_link: "/regulatorio",
      },
      {
        method: "GET",
        path: "/api/v1/config/{anio}/tasas-sat",
        desc_es: "Retorna las tasas fiscales del SAT para un ano fiscal: retenciones ISR, tasa corporativa, IVA y limite de deducciones personales en UMAs.",
        desc_en: "Returns SAT tax rates for a fiscal year: ISR withholding rates, corporate tax rate, VAT rate, and personal deduction limit in UMAs.",
        params: [
          { name: "anio", type: "int (path)", required: true, default_val: "-", description_es: "Ano fiscal", description_en: "Fiscal year" },
        ],
        example_req: `GET /api/v1/config/2025/tasas-sat`,
        example_res: `{
  "tasa_retencion_rentas_vitalicias": 0.20,
  "tasa_retencion_retiros_ahorro": 0.20,
  "tasa_isr_personas_morales": 0.30,
  "tasa_iva": 0.16,
  "limite_deducciones_pf_umas": 5
}`,
        try_link: "/regulatorio",
      },
      {
        method: "GET",
        path: "/api/v1/config/{anio}/factores-cnsf",
        desc_es: "Retorna los factores regulatorios CNSF para un ano fiscal: shocks de mercado por tipo de activo, shocks de credito por calificacion y la matriz de correlacion para el calculo del RCS.",
        desc_en: "Returns CNSF regulatory factors for a fiscal year: market shocks by asset type, credit shocks by rating, and the correlation matrix for RCS calculation.",
        params: [
          { name: "anio", type: "int (path)", required: true, default_val: "-", description_es: "Ano fiscal", description_en: "Fiscal year" },
        ],
        example_req: `GET /api/v1/config/2025/factores-cnsf`,
        example_res: `{
  "shock_acciones": 0.25,
  "shock_bonos_gubernamentales": 0.02,
  "shock_bonos_corporativos": 0.08,
  "shock_inmuebles": 0.15,
  "shocks_credito": {
    "AAA": 0.004, "AA": 0.008, ...
  },
  "correlacion_vida_danos": 0.25,
  "correlacion_vida_inversion": 0.25,
  "correlacion_danos_inversion": 0.25
}`,
        try_link: "/regulatorio",
      },
    ],
  },
];

/* ── Collapsible code block component ──────────────────────────────────── */

function CodeBlock({ label, code, lang: codeLang }: { label: string; code: string; lang: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm font-medium text-navy/70 hover:text-terracotta transition-colors"
      >
        <svg
          className={`w-4 h-4 transition-transform duration-200 ${open ? "rotate-90" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        {label}
      </button>
      {open && (
        <div className="relative rounded-xl overflow-hidden mt-2">
          <div className="absolute top-0 left-0 right-0 h-8 bg-[#1e1e2e] flex items-center px-4 gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-red-400/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-amber/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-sage/80" />
            <span className="ml-3 text-xs text-white/40 font-mono">{codeLang}</span>
          </div>
          <pre className="bg-[#1e1e2e] text-[#cdd6f4] p-4 pt-11 overflow-x-auto text-xs leading-relaxed font-mono">
            <code>{code}</code>
          </pre>
        </div>
      )}
    </div>
  );
}

/* ── Method badge component ────────────────────────────────────────────── */

function MethodBadge({ method }: { method: "POST" | "GET" }) {
  const styles =
    method === "POST"
      ? "bg-terracotta/15 text-terracotta border-terracotta/30"
      : "bg-sage/15 text-sage border-sage/30";

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-widest border ${styles}`}
    >
      {method}
    </span>
  );
}

/* ── Single endpoint card ──────────────────────────────────────────────── */

function EndpointCard({ endpoint, lang }: { endpoint: Endpoint; lang: "es" | "en" }) {
  const { t } = useLanguage();
  const desc = lang === "es" ? endpoint.desc_es : endpoint.desc_en;
  const params = endpoint.params;
  const isGet = endpoint.method === "GET";

  return (
    <Card className="mb-6">
      {/* Header row */}
      <div className="flex flex-wrap items-center gap-3 mb-3">
        <MethodBadge method={endpoint.method} />
        <code className="text-sm font-mono font-semibold text-navy break-all">
          {endpoint.path}
        </code>
      </div>

      {/* Description */}
      <p className="text-sm text-navy/65 mb-4 leading-relaxed">{desc}</p>

      {/* Parameters table */}
      {params.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-bold text-navy mb-2">{t("api_docs_params")}</h4>
          <Table
            headers={[
              t("api_docs_param_name"),
              t("api_docs_param_type"),
              t("api_docs_required"),
              t("api_docs_default"),
              t("api_docs_param_desc"),
            ]}
            rows={params.map((p) => [
              p.name,
              p.type,
              p.required ? t("api_docs_required") : t("api_docs_optional"),
              p.default_val,
              lang === "es" ? p.description_es : p.description_en,
            ])}
          />
        </div>
      )}

      {/* Same params note for shared-schema endpoints */}
      {params.length === 0 && (
        <p className="text-xs text-navy/40 italic mb-4">
          {lang === "es"
            ? "Mismos parametros que /pricing/temporal (ver arriba)."
            : "Same parameters as /pricing/temporal (see above)."}
        </p>
      )}

      {/* Collapsible examples */}
      <CodeBlock
        label={t("api_docs_example_req")}
        code={endpoint.example_req}
        lang={isGet ? "http" : "json"}
      />
      <CodeBlock
        label={t("api_docs_example_res")}
        code={endpoint.example_res}
        lang="json"
      />

      {/* Try it link */}
      <div className="mt-4 pt-3 border-t border-navy/5">
        <Link
          href={endpoint.try_link}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-terracotta hover:text-terracotta/80 transition-colors"
        >
          {t("api_docs_try_it")}
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </Link>
      </div>
    </Card>
  );
}

/* ── Page component ────────────────────────────────────────────────────── */

export default function ApiDocsPage() {
  const { t, lang } = useLanguage();
  const [activeDomain, setActiveDomain] = useState("vida");

  const tabs = DOMAINS.map((d) => ({
    id: d.id,
    label: t(d.labelKey),
  }));

  const currentDomain = DOMAINS.find((d) => d.id === activeDomain) ?? DOMAINS[0];

  const endpointCount = DOMAINS.reduce((sum, d) => sum + d.endpoints.length, 0);

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 space-y-10">
      {/* ── Page header ─────────────────────────────────────────────── */}
      <section>
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-navy mb-3">
          {t("api_docs_title")}
        </h1>
        <p className="text-navy/60 text-lg mb-6">
          {lang === "es"
            ? `Referencia completa de los ${endpointCount} endpoints REST disponibles.`
            : `Complete reference for all ${endpointCount} available REST endpoints.`}
        </p>
      </section>

      {/* ── Base URL / info section ─────────────────────────────────── */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-bold text-navy mb-2">{t("api_docs_base_url")}</h3>
            <code className="text-sm font-mono bg-navy/5 px-3 py-1.5 rounded-lg text-terracotta">
              http://localhost:8000/api/v1
            </code>
          </div>
          <div>
            <h3 className="text-sm font-bold text-navy mb-2">Content-Type</h3>
            <code className="text-sm font-mono bg-navy/5 px-3 py-1.5 rounded-lg text-navy/70">
              application/json
            </code>
          </div>
          <div>
            <h3 className="text-sm font-bold text-navy mb-2">
              {lang === "es" ? "Autenticacion" : "Authentication"}
            </h3>
            <p className="text-sm text-navy/60">{t("api_docs_auth")}</p>
          </div>
          <div>
            <h3 className="text-sm font-bold text-navy mb-2">Swagger UI</h3>
            <p className="text-sm text-navy/60">
              {t("api_docs_swagger")}{" "}
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-terracotta hover:underline font-mono"
              >
                /docs
              </a>
            </p>
          </div>
        </div>
      </Card>

      {/* ── Domain tabs ─────────────────────────────────────────────── */}
      <div>
        <Tabs tabs={tabs} activeTab={activeDomain} onTabChange={setActiveDomain} className="mb-8" />

        {/* Endpoint count for active domain */}
        <p className="text-sm text-navy/40 mb-6">
          {currentDomain.endpoints.length} endpoint{currentDomain.endpoints.length !== 1 ? "s" : ""}
        </p>

        {/* ── Endpoint cards ──────────────────────────────────────── */}
        <div
          role="tabpanel"
          id={`tabpanel-${activeDomain}`}
          aria-labelledby={`tab-${activeDomain}`}
        >
          {currentDomain.endpoints.map((ep) => (
            <EndpointCard key={ep.path} endpoint={ep} lang={lang} />
          ))}
        </div>
      </div>
    </div>
  );
}
