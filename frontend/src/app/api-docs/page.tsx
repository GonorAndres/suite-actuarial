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
        desc_es: "Calcula la prima neta y la prima total de un seguro de vida temporal con la tabla de mortalidad EMSSA-09. La respuesta incluye calculation_metadata con validation_tier y las fuentes de los supuestos.",
        desc_en: "Calculates the net and gross premium for a term life product using the EMSSA-09 mortality table. The response includes calculation_metadata with validation_tier and the assumption sources.",
        params: [
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad del asegurado en años cumplidos (0-120)", description_en: "Age of the insured in completed years (0-120)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: masculino o femenino (se rechaza cualquier otro valor con 422)", description_en: "Sex: masculino or femenino (any other value is rejected with 422)" },
          { name: "suma_asegurada", type: "float", required: true, default_val: "-", description_es: "Suma asegurada en MXN (> 0)", description_en: "Sum insured in MXN (> 0)" },
          { name: "plazo_years", type: "int", required: true, default_val: "-", description_es: "Plazo de la póliza en años (1-99)", description_en: "Policy term in years (1-99)" },
          { name: "tasa_interes", type: "float", required: false, default_val: "0.055", description_es: "Tasa de interés técnico (0-0.15)", description_en: "Technical interest rate (0-0.15)" },
          { name: "frecuencia_pago", type: "string", required: false, default_val: "anual", description_es: "Frecuencia de pago: anual, semestral, trimestral, mensual", description_en: "Payment frequency: anual, semestral, trimestral, mensual" },
          { name: "recargo_gastos_admin", type: "float", required: false, default_val: "0.05", description_es: "Recargo por gastos de administración (0-1)", description_en: "Admin expense loading (0-1)" },
          { name: "recargo_gastos_adq", type: "float", required: false, default_val: "0.10", description_es: "Recargo por gastos de adquisición (0-1)", description_en: "Acquisition expense loading (0-1)" },
          { name: "recargo_utilidad", type: "float", required: false, default_val: "0.03", description_es: "Recargo por utilidad (0-1)", description_en: "Profit loading (0-1)" },
        ],
        example_req: `{
  "edad": 35,
  "sexo": "masculino",
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
    "gastos_admin": 101.20,
    "gastos_adq": 202.41,
    "utilidad": 60.72
  },
  "metadata": {
    "producto": "Vida Temporal 20 anios",
    "tabla_mortalidad": "EMSSA-09",
    "tasa_interes": "0.055",
    ...
  },
  "calculation_metadata": {
    "model_version": "2.2.0",
    "validation_tier": "experimental",
    "sources": ["CNSF / instantanea empaquetada (illustrative)"],
    ...
  }
}`,
        try_link: "/vida",
      },
      {
        method: "POST",
        path: "/api/v1/pricing/ordinario",
        desc_es: "Calcula la prima de un seguro de vida ordinario (vida entera). El campo plazo_years fija el periodo de pago de primas, no la cobertura: la cobertura llega hasta la edad omega de la tabla.",
        desc_en: "Calculates the premium for a whole life product. The plazo_years field sets the premium-paying period, not the coverage: coverage runs to the table's omega age.",
        params: [],
        example_req: `{
  "edad": 35,
  "sexo": "masculino",
  "suma_asegurada": 1000000,
  "plazo_years": 20,
  "tasa_interes": 0.055,
  "frecuencia_pago": "anual"
}`,
        example_res: `{
  "producto": "ordinario",
  "prima_neta": 9394.07,
  "prima_total": 11085.01,
  "moneda": "MXN",
  "desglose_recargos": {
    "gastos_admin": 469.70,
    "gastos_adq": 939.41,
    "utilidad": 281.82
  },
  "metadata": {
    "plazo_cobertura": 66,
    "plazo_pago": "20 anios",
    "edad_omega": 100,
    ...
  },
  "calculation_metadata": { ... }
}`,
        try_link: "/vida",
      },
      {
        method: "POST",
        path: "/api/v1/pricing/dotal",
        desc_es: "Calcula la prima de un seguro dotal (mixto), que paga por muerte durante el plazo o por supervivencia al final del plazo.",
        desc_en: "Calculates the premium for an endowment product that pays on death during the term or on survival at the end of the term.",
        params: [],
        example_req: `{
  "edad": 35,
  "sexo": "femenino",
  "suma_asegurada": 500000,
  "plazo_years": 20,
  "tasa_interes": 0.055
}`,
        example_res: `{
  "producto": "dotal",
  "prima_neta": 13880.46,
  "prima_total": 16378.94,
  "moneda": "MXN",
  "desglose_recargos": {
    "gastos_admin": 694.02,
    "gastos_adq": 1388.05,
    "utilidad": 416.41
  },
  "metadata": { "componentes": "muerte + supervivencia", ... },
  "calculation_metadata": { ... }
}`,
        try_link: "/vida",
      },
      {
        method: "POST",
        path: "/api/v1/pricing/dotal/lab",
        desc_es: "Construye un dotal de pago limitado y expone su interior: valor presente del beneficio por muerte y del beneficio por supervivencia, factor de anualidad de primas, prima neta anual equivalente y la trayectoria de reservas año por año. El bloque verificaciones contrasta el motor contra un camino independiente (columnas de conmutación Dx/Nx/Mx y recursión retrospectiva de Fackler) y publica las diferencias numéricas, no sólo un booleano.",
        desc_en: "Builds a limited-pay endowment and opens it up: present value of the death benefit and of the survival benefit, premium annuity factor, equivalent annual net premium, and the year-by-year reserve path. The verificaciones block contrasts the engine against an independent route (Dx/Nx/Mx commutation columns and the retrospective Fackler recursion) and publishes the numeric gaps, not just a boolean.",
        params: [
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad del asegurado en años cumplidos (0-120)", description_en: "Age of the insured in completed years (0-120)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: masculino o femenino", description_en: "Sex: masculino or femenino" },
          { name: "suma_asegurada", type: "float", required: true, default_val: "-", description_es: "Suma asegurada en MXN (> 0)", description_en: "Sum insured in MXN (> 0)" },
          { name: "plazo_years", type: "int", required: true, default_val: "-", description_es: "Plazo del seguro en años (1-99)", description_en: "Policy term in years (1-99)" },
          { name: "plazo_pago", type: "int", required: true, default_val: "-", description_es: "Plazo de pago de primas en años (1-99); menor que plazo_years para un pago limitado", description_en: "Premium-paying term in years (1-99); shorter than plazo_years for a limited-pay design" },
          { name: "tasa_interes", type: "float", required: false, default_val: "0.055", description_es: "Tasa de interés técnico (0-0.15)", description_en: "Technical interest rate (0-0.15)" },
          { name: "frecuencia_pago", type: "string", required: false, default_val: "anual", description_es: "Frecuencia de pago: anual, semestral, trimestral, mensual", description_en: "Payment frequency: anual, semestral, trimestral, mensual" },
          { name: "recargo_gastos_admin", type: "float", required: false, default_val: "0.05", description_es: "Recargo por gastos de administración (0-1)", description_en: "Admin expense loading (0-1)" },
          { name: "recargo_gastos_adq", type: "float", required: false, default_val: "0.10", description_es: "Recargo por gastos de adquisición (0-1)", description_en: "Acquisition expense loading (0-1)" },
          { name: "recargo_utilidad", type: "float", required: false, default_val: "0.03", description_es: "Recargo por utilidad (0-1)", description_en: "Profit loading (0-1)" },
        ],
        example_req: `{
  "edad": 35,
  "sexo": "femenino",
  "suma_asegurada": 500000,
  "plazo_years": 20,
  "plazo_pago": 10,
  "tasa_interes": 0.055
}`,
        example_res: `{
  "prima": {
    "producto": "dotal",
    "prima_neta": 21914.26,
    "prima_total": 25858.83,
    "metadata": { "producto": "Dotal educativo 20/10", ... },
    "calculation_metadata": { "validation_tier": "experimental", ... }
  },
  "plazo_pago": 10,
  "vp_beneficio_muerte": 6768.66,
  "vp_beneficio_supervivencia": 166968.13,
  "vp_beneficios_total": 173736.79,
  "factor_anualidad_primas": 7.928024,
  "prima_neta_anual_equivalente": 21914.26,
  "reservas": [
    { "anio": 0, "edad_alcanzada": 35, "reserva": 0.0 },
    { "anio": 1, "edad_alcanzada": 36, "reserva": 22804.60 },
    ...
  ],
  "verificaciones": {
    "descomposicion_beneficios": true,
    "principio_equivalencia": true,
    "reserva_inicial_cero": true,
    "reserva_final_igual_beneficio": true,
    "recursion_fackler": true,
    "diferencia_equivalencia": 0.0,
    "diferencia_descomposicion": 6.6e-16,
    "diferencia_recursion": 4e-28
  }
}`,
        try_link: "/vida",
      },
      {
        method: "POST",
        path: "/api/v1/pricing/compare",
        desc_es: "Compara los tres productos de vida (temporal, ordinario, dotal) para el mismo asegurado con parámetros idénticos. Devuelve una respuesta de tarificación completa por producto.",
        desc_en: "Compares all three life products (temporal, ordinario, dotal) for the same insured with identical parameters. Returns a full pricing response per product.",
        params: [],
        example_req: `{
  "edad": 35,
  "sexo": "masculino",
  "suma_asegurada": 1000000,
  "plazo_years": 20
}`,
        example_res: `{
  "temporal":  { "prima_neta": 2024.08,  "prima_total": 2388.42,  ... },
  "ordinario": { "prima_neta": 9394.07,  "prima_total": 11085.01, ... },
  "dotal":     { "prima_neta": 28275.97, "prima_total": 33365.64, ... }
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
        desc_es: "Genera una cotización de seguro de auto: prima por cobertura a partir del grupo del vehículo, zona, edad del conductor, deducible, depreciación y ajuste Bonus-Malus opcional. Las tasas, zonas y factores son ilustrativos: reproducen la estructura de una tarifa de auto, no los valores de ninguna tarifa vigente, y no proceden de la AMIS ni de la experiencia de aseguradora alguna. La respuesta trae los campos disclaimer y validation_tier con ese límite.",
        desc_en: "Generates an auto insurance quotation: premium per coverage from vehicle group, zone, driver age, deductible, depreciation, and an optional Bonus-Malus adjustment. The rates, zones, and factors are illustrative: they reproduce the structure of an auto tariff, not the values of any tariff in force, and they do not come from AMIS or from any insurer's experience. The response carries disclaimer and validation_tier stating that limit.",
        params: [
          { name: "valor_vehiculo", type: "float", required: true, default_val: "-", description_es: "Valor comercial del vehículo en MXN (> 0)", description_en: "Commercial vehicle value in MXN (> 0)" },
          { name: "tipo_vehiculo", type: "string", required: true, default_val: "-", description_es: "Clave del tipo de vehículo (sedan_compacto, suv_mediano, etc.)", description_en: "Vehicle type key (sedan_compacto, suv_mediano, etc.)" },
          { name: "antiguedad_anos", type: "int", required: true, default_val: "-", description_es: "Años de antigüedad del vehículo (>= 0)", description_en: "Vehicle age in years (>= 0)" },
          { name: "zona", type: "string", required: true, default_val: "-", description_es: "Clave de la zona de riesgo (cdmx_sur, guadalajara, monterrey, resto_pais, etc.); una clave desconocida devuelve 400 con la lista de opciones", description_en: "Risk zone key (cdmx_sur, guadalajara, monterrey, resto_pais, etc.); an unknown key returns 400 with the list of options" },
          { name: "edad_conductor", type: "int", required: true, default_val: "-", description_es: "Edad del conductor principal (>= 18)", description_en: "Primary driver age (>= 18)" },
          { name: "deducible_pct", type: "float", required: false, default_val: "0.05", description_es: "Porcentaje de deducible", description_en: "Deductible percentage" },
          { name: "coberturas", type: "list[str] | null", required: false, default_val: "null (todas)", description_es: "Lista de coberturas a cotizar; null cotiza todas", description_en: "List of coverages to quote; null quotes all of them" },
          { name: "historial_siniestros", type: "list[int] | null", required: false, default_val: "null", description_es: "Historial anual de siniestros para el ajuste Bonus-Malus", description_en: "Annual claims history for the Bonus-Malus adjustment" },
        ],
        example_req: `{
  "valor_vehiculo": 350000,
  "tipo_vehiculo": "sedan_compacto",
  "antiguedad_anos": 3,
  "zona": "cdmx_sur",
  "edad_conductor": 30,
  "deducible_pct": 0.05
}`,
        example_res: `{
  "vehiculo": {
    "tipo": "sedan_compacto", "grupo": 1,
    "valor_original": 350000.0, "antiguedad": 3,
    "valor_asegurado": 217000.0
  },
  "conductor": { "edad": 30, "rango_edad": "26-35", "factor_edad": 1.0 },
  "zona": { "nombre": "cdmx_sur", "factor": 1.25 },
  "deducible": { "porcentaje": 0.05, "pesos": 10850.0, "factor": 1.0 },
  "coberturas": {
    "danos_materiales": 6781.25,
    "robo_total": 3255.00,
    "rc_bienes": 1220.63,
    "rc_personas": 1030.75,
    "gastos_medicos": 542.50,
    "asistencia_vial": 406.88
  },
  "subtotal": 13237.01,
  "bonus_malus": { "nivel": 0, "factor": 1.0 },
  "prima_total": 13237.01,
  "validation_tier": "experimental",
  "disclaimer": "AVISO: las tasas, zonas y factores de este modulo son ILUSTRATIVOS ... no proceden de la AMIS ni de la experiencia de aseguradora alguna ..."
}`,
        try_link: "/danos",
      },
      {
        method: "POST",
        path: "/api/v1/danos/incendio/calcular",
        desc_es: "Genera una cotización de seguro de incendio: prima anual = (valor / 1000) x tasa base por tipo de construcción x factor de zona x factor de uso. Las tasas y factores son ilustrativos y la prima no reconoce deducible, infraseguro, regla proporcional ni riesgo catastrófico. La respuesta trae disclaimer y validation_tier.",
        desc_en: "Generates a fire insurance quotation: annual premium = (value / 1000) x base rate by construction type x zone factor x use factor. Rates and factors are illustrative and the premium ignores deductible, underinsurance, average clause, and catastrophe risk. The response carries disclaimer and validation_tier.",
        params: [
          { name: "valor_inmueble", type: "float", required: true, default_val: "-", description_es: "Valor de reposición del inmueble en MXN (> 0)", description_en: "Property replacement value in MXN (> 0)" },
          { name: "tipo_construccion", type: "string", required: true, default_val: "-", description_es: "concreto, acero, ladrillo, mixta, madera, lámina", description_en: "concreto, acero, ladrillo, mixta, madera, lamina" },
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
  "valor_inmueble": 5000000.0,
  "tipo_construccion": "concreto",
  "tasa_base": 0.8,
  "zona": "urbana_baja",
  "factor_zona": 0.85,
  "uso": "habitacional",
  "factor_uso": 1.0,
  "prima_anual": 3400.0,
  "validation_tier": "experimental",
  "disclaimer": "AVISO: las tasas por tipo de construccion y los factores de zona y uso de este modulo son ILUSTRATIVOS ..."
}`,
        try_link: "/danos",
      },
      {
        method: "POST",
        path: "/api/v1/danos/rc/calcular",
        desc_es: "Genera una cotización de responsabilidad civil: prima anual = (límite / 1000) x tasa base por clase de actividad x factor de deducible. Las tasas y factores son ilustrativos; el modelo no usa frecuencia ni severidad, no mide la exposición real y el factor de deducible es escalonado, no interpolado. La respuesta trae disclaimer y validation_tier.",
        desc_en: "Generates a general liability quotation: annual premium = (limit / 1000) x base rate by activity class x deductible factor. Rates and factors are illustrative; the model uses neither frequency nor severity, does not measure real exposure, and the deductible factor is stepwise, not interpolated. The response carries disclaimer and validation_tier.",
        params: [
          { name: "limite_responsabilidad", type: "float", required: true, default_val: "-", description_es: "Límite máximo de cobertura en MXN (> 0)", description_en: "Maximum liability limit in MXN (> 0)" },
          { name: "deducible", type: "float", required: true, default_val: "-", description_es: "Monto del deducible en MXN (>= 0)", description_en: "Deductible amount in MXN (>= 0)" },
          { name: "clase_actividad", type: "string", required: true, default_val: "-", description_es: "oficinas, comercio_minorista, restaurante, manufactura_ligera, manufactura_pesada, construccion, transporte, servicios_profesionales, salud, educacion, hoteleria", description_en: "oficinas, comercio_minorista, restaurante, manufactura_ligera, manufactura_pesada, construccion, transporte, servicios_profesionales, salud, educacion, hoteleria" },
        ],
        example_req: `{
  "limite_responsabilidad": 10000000,
  "deducible": 50000,
  "clase_actividad": "oficinas"
}`,
        example_res: `{
  "limite_responsabilidad": 10000000.0,
  "deducible": 50000.0,
  "clase_actividad": "oficinas",
  "tasa_base": 1.2,
  "factor_deducible": 0.9,
  "prima_anual": 10800.0,
  "validation_tier": "experimental",
  "disclaimer": "AVISO: las tasas por clase de actividad y los factores de deducible de este modulo son ILUSTRATIVOS ..."
}`,
        try_link: "/danos",
      },
      {
        method: "POST",
        path: "/api/v1/danos/bonus-malus",
        desc_es: "Calcula la transición de nivel Bonus-Malus y el factor de prima asociado. Escala ilustrativa: sin siniestros baja 1 nivel (descuento), 1 siniestro sube 2 niveles, 2 o más siniestros suben 3. Los niveles y sus factores no proceden de ninguna tarifa registrada; la respuesta lo declara en disclaimer.",
        desc_en: "Calculates the Bonus-Malus level transition and its premium factor. Illustrative scale: no claims moves down 1 level (discount), 1 claim moves up 2 levels, 2 or more claims move up 3. The levels and their factors do not come from any filed tariff; the response states this in disclaimer.",
        params: [
          { name: "nivel_actual", type: "int", required: false, default_val: "0", description_es: "Nivel BMS actual (-5 a 3; 0 = base)", description_en: "Current BMS level (-5 to 3; 0 = base)" },
          { name: "numero_siniestros", type: "int", required: true, default_val: "-", description_es: "Número de siniestros en el periodo (>= 0)", description_en: "Number of claims in the period (>= 0)" },
        ],
        example_req: `{
  "nivel_actual": 0,
  "numero_siniestros": 1
}`,
        example_res: `{
  "nivel_previo": 0,
  "siniestros": 1,
  "nivel_nuevo": 2,
  "factor": 1.3,
  "validation_tier": "experimental",
  "disclaimer": "AVISO: la escala de Bonus-Malus de este modulo es ILUSTRATIVA..."
}`,
        try_link: "/danos",
      },
      {
        method: "POST",
        path: "/api/v1/danos/frecuencia-severidad",
        desc_es: "Ejecuta un modelo de riesgo colectivo (S = X1 + ... + XN) por simulación Monte Carlo. Devuelve prima pura, momentos de la agregada y medidas de riesgo VaR y TVaR al 95% y 99%. Con seed fija, el resultado es reproducible.",
        desc_en: "Runs a collective risk model (S = X1 + ... + XN) by Monte Carlo simulation. Returns the pure premium, moments of the aggregate, and VaR and TVaR risk measures at 95% and 99%. With a fixed seed the result is reproducible.",
        params: [
          { name: "dist_frecuencia", type: "string", required: true, default_val: "-", description_es: "Distribución de frecuencia: poisson, negbinom, binomial", description_en: "Frequency distribution: poisson, negbinom, binomial" },
          { name: "params_frecuencia", type: "dict", required: true, default_val: "-", description_es: "Parámetros de frecuencia, con estos nombres exactos. poisson: {lambda_}; negbinom: {n, p}; binomial: {n, p}. Un nombre ausente o no reconocido devuelve 422 nombrando el juego válido", description_en: "Frequency params, with these exact names. poisson: {lambda_}; negbinom: {n, p}; binomial: {n, p}. A missing or unrecognised name returns 422 naming the valid set" },
          { name: "dist_severidad", type: "string", required: true, default_val: "-", description_es: "Distribución de severidad: lognormal, pareto, gamma, weibull, exponencial", description_en: "Severity distribution: lognormal, pareto, gamma, weibull, exponencial" },
          { name: "params_severidad", type: "dict", required: true, default_val: "-", description_es: "Parámetros de severidad, con estos nombres exactos. lognormal: {mu, sigma}; pareto: {alpha, scale}; gamma: {alpha, beta}; weibull: {c, scale}; exponencial: {lambda_}. Un nombre ausente o no reconocido devuelve 422 nombrando el juego válido", description_en: "Severity params, with these exact names. lognormal: {mu, sigma}; pareto: {alpha, scale}; gamma: {alpha, beta}; weibull: {c, scale}; exponencial: {lambda_}. A missing or unrecognised name returns 422 naming the valid set" },
          { name: "n_simulaciones", type: "int", required: false, default_val: "100000", description_es: "Número de simulaciones Monte Carlo (1,000-1,000,000)", description_en: "Monte Carlo simulations (1,000-1,000,000)" },
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
  "prima_pura": 339231.46,
  "varianza_agregada": 218365895488.23,
  "desviacion_estandar": 455400.80,
  "asimetria": 7.4063,
  "var_95": 1027754.65,
  "tvar_95": 1733944.41,
  "var_99": 2040510.06,
  "tvar_99": 3216552.16,
  "minimo": 0.0,
  "maximo": 16668524.70,
  "simulaciones": 100000,
  "validation_tier": "experimental",
  "disclaimer": "AVISO: este modulo implementa el modelo colectivo estandar, pero sus cifras son ILUSTRATIVAS..."
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
        desc_es: "Calcula la prima de Gastos Médicos Mayores (GMM): tasa base por banda de edad, factores de zona, nivel hospitalario, deducible y coaseguro, prima ajustada y siniestralidad esperada. Las tasas base son ilustrativas y el modelo no usa frecuencia, severidad ni tendencia médica; la siniestralidad esperada se deriva de la propia prima, así que no es una estimación independiente. El sexo se registra pero no altera la prima. La respuesta trae disclaimer y validation_tier.",
        desc_en: "Calculates the Major Medical Expenses (GMM) premium: base rate by age band, zone, hospital-level, deductible and coinsurance factors, adjusted premium, and expected claims. The base rates are illustrative and the model uses neither frequency, severity, nor medical trend; expected claims are derived from the premium itself, so they are not an independent estimate. Sex is recorded but does not change the premium. The response carries disclaimer and validation_tier.",
        params: [
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad del asegurado (0-110)", description_en: "Insured age (0-110)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: masculino o femenino", description_en: "Sex: masculino or femenino" },
          { name: "suma_asegurada", type: "float", required: true, default_val: "-", description_es: "Suma asegurada en MXN (mínimo 1,000,000)", description_en: "Sum insured in MXN (min 1,000,000)" },
          { name: "deducible", type: "float", required: true, default_val: "-", description_es: "Monto del deducible en MXN (>= 0)", description_en: "Deductible amount in MXN (>= 0)" },
          { name: "coaseguro_pct", type: "float", required: true, default_val: "-", description_es: "Porcentaje de coaseguro (0.10-0.30). Es el rango que tarifa la tabla de factores; fuera de él no hay dato que respalde un precio, y la petición se rechaza con 422", description_en: "Coinsurance percentage (0.10-0.30). That is the range the factor table prices; outside it no data backs a price, and the request is rejected with 422" },
          { name: "tope_coaseguro", type: "float | null", required: false, default_val: "null", description_es: "Tope máximo de coaseguro en MXN; null = sin tope", description_en: "Maximum coinsurance cap in MXN; null = no cap" },
          { name: "zona", type: "string", required: false, default_val: "urbano", description_es: "Zona geográfica: metro, urbano, foraneo", description_en: "Geographic zone: metro, urbano, foraneo" },
          { name: "nivel", type: "string", required: false, default_val: "medio", description_es: "Nivel hospitalario: estandar, medio, alto", description_en: "Hospital level: estandar, medio, alto" },
        ],
        example_req: `{
  "edad": 35,
  "sexo": "masculino",
  "suma_asegurada": 5000000,
  "deducible": 20000,
  "coaseguro_pct": 0.10,
  "zona": "metro",
  "nivel": "alto"
}`,
        example_res: `{
  "asegurado": { "edad": 35, "sexo": "masculino", "banda_edad": "35-39" },
  "producto": {
    "suma_asegurada": 5000000.0,
    "deducible": 20000.0,
    "coaseguro_pct": 0.1,
    "tope_coaseguro": null,
    "zona": "metro",
    "nivel": "alto"
  },
  "tarificacion": {
    "tasa_banda_edad": 9.0,
    "prima_base": 45000.0,
    "factor_zona": 1.2,
    "factor_nivel": 1.3,
    "factor_deducible": 1.2333,
    "factor_coaseguro": 1.0,
    "prima_ajustada": 86577.66
  },
  "siniestralidad_esperada": 66598.20,
  "validation_tier": "experimental",
  "disclaimer": "AVISO: las tasas base por banda de edad de este modulo son ILUSTRATIVAS ..."
}`,
        try_link: "/salud",
      },
      {
        method: "POST",
        path: "/api/v1/salud/accidentes/calcular",
        desc_es: "Calcula la prima de Accidentes y Enfermedades: prima anual = (SA / 1000) x tasa por banda de edad x factor de ocupación. Devuelve además la tabla de indemnización por pérdidas orgánicas, el beneficio diario por hospitalización y los gastos funerarios. Tasas, factores y porcentajes son ilustrativos. La respuesta trae disclaimer y validation_tier.",
        desc_en: "Calculates the Accident & Sickness premium: annual premium = (sum insured / 1000) x age-band rate x occupation factor. It also returns the organic-loss indemnification table, the daily hospitalization benefit, and funeral expenses. Rates, factors, and percentages are illustrative. The response carries disclaimer and validation_tier.",
        params: [
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad del asegurado (18-70)", description_en: "Insured age (18-70)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: masculino o femenino", description_en: "Sex: masculino or femenino" },
          { name: "suma_asegurada", type: "float", required: true, default_val: "-", description_es: "Suma asegurada en MXN (> 0)", description_en: "Sum insured in MXN (> 0)" },
          { name: "ocupacion", type: "string", required: false, default_val: "oficina", description_es: "Clase de riesgo: oficina, comercio, industrial_ligero, industrial_pesado, alto_riesgo", description_en: "Risk class: oficina, comercio, industrial_ligero, industrial_pesado, alto_riesgo" },
          { name: "indemnizacion_diaria", type: "float | null", required: false, default_val: "null (0.1% de la SA)", description_es: "Monto diario por hospitalización; null aplica 0.1% de la suma asegurada", description_en: "Daily hospitalization amount; null applies 0.1% of the sum insured" },
        ],
        example_req: `{
  "edad": 40,
  "sexo": "masculino",
  "suma_asegurada": 1000000,
  "ocupacion": "oficina"
}`,
        example_res: `{
  "suma_asegurada": 1000000.0,
  "prima_anual": 3000.0,
  "perdidas_organicas": {
    "muerte_accidental": { "porcentaje": 1.0, "monto": 1000000.0 },
    "perdida_una_mano": { "porcentaje": 0.6, "monto": 600000.0 },
    ...
  },
  "indemnizacion_diaria": { "monto_diario": 1000.0, "monto_mensual": 30000.0 },
  "gastos_funerarios": 100000.0,
  "validation_tier": "experimental",
  "disclaimer": "AVISO: las tasas base por banda de edad, los factores de ocupacion y los porcentajes de la tabla de perdidas organicas de este modulo son ILUSTRATIVOS ..."
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
        desc_es: "Calcula una pensión IMSS Ley 73 (régimen de beneficio definido). Devuelve el porcentaje de pensión, el factor por edad, la pensión mensual, el aguinaldo anual y el ingreso anual total a partir de las semanas cotizadas, el salario promedio diario y la edad de retiro.",
        desc_en: "Calculates an IMSS Ley 73 pension (defined-benefit regime). Returns the pension percentage, the age factor, the monthly pension, the annual bonus, and total annual income from weeks contributed, average daily salary, and retirement age.",
        params: [
          { name: "semanas_cotizadas", type: "int", required: true, default_val: "-", description_es: "Total de semanas cotizadas al IMSS (mínimo 500)", description_en: "Total weeks contributed to IMSS (min 500)" },
          { name: "salario_promedio_diario", type: "float", required: true, default_val: "-", description_es: "Salario promedio diario de las últimas 250 semanas, en MXN (> 0)", description_en: "Average daily salary over the last 250 weeks, in MXN (> 0)" },
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
  "salario_promedio_diario": 800.0,
  "edad_retiro": 65,
  "porcentaje_pension": 0.7710846153846154,
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
        desc_es: "Calcula una pensión IMSS Ley 97 (contribución definida): computa y compara las dos modalidades, renta vitalicia y retiro programado, a partir del saldo AFORE, la edad, el sexo y las semanas cotizadas. El campo recomendacion sólo nombra la modalidad con mensualidad inicial más alta: es una comparación aritmética del primer año, no un consejo. No pondera el riesgo de longevidad ni el hecho de que el retiro programado puede agotarse. Además, el retiro programado reparte el saldo entre la esperanza de vida sin acreditar el rendimiento del saldo remanente, así que queda subestimado. Las dos modalidades quedan sujetas al piso de la pensión garantizada.",
        desc_en: "Calculates an IMSS Ley 97 pension (defined-contribution regime): it computes and compares the two modalities, life annuity and scheduled withdrawal, from the AFORE balance, age, sex, and weeks contributed. The recomendacion field only names the modality with the higher first-year monthly amount: it is an arithmetic comparison of year one, not advice. It does not weigh longevity risk, nor the fact that a scheduled withdrawal can run out. The scheduled withdrawal divides the balance by life expectancy without crediting the return the remaining balance keeps earning, so it is understated; both modalities are floored at the guaranteed pension.",
        params: [
          { name: "saldo_afore", type: "float", required: true, default_val: "-", description_es: "Saldo actual de la cuenta AFORE en MXN (> 0)", description_en: "Current AFORE account balance in MXN (> 0)" },
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad actual del trabajador (60-70)", description_en: "Current worker age (60-70)" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: masculino o femenino", description_en: "Sex: masculino or femenino" },
          { name: "semanas_cotizadas", type: "int", required: true, default_val: "-", description_es: "Total de semanas cotizadas al IMSS (>= 0)", description_en: "Total weeks contributed to IMSS (>= 0)" },
          { name: "tasa_interes", type: "float", required: false, default_val: "0.035", description_es: "Tasa de interés técnico (0-0.15)", description_en: "Technical interest rate (0-0.15)" },
        ],
        example_req: `{
  "saldo_afore": 2000000,
  "edad": 65,
  "sexo": "masculino",
  "semanas_cotizadas": 1200,
  "tasa_interes": 0.035
}`,
        example_res: `{
  "saldo_afore": 2000000.0,
  "edad": 65,
  "sexo": "masculino",
  "semanas_cotizadas": 1200,
  "renta_vitalicia": {
    "pension_mensual": 13169.67,
    "pension_anual": 158036.04,
    "tipo": "Garantizada de por vida"
  },
  "retiro_programado": {
    "pension_mensual": 9803.92,
    "pension_anual": 117647.04,
    "tipo": "Se recalcula anualmente, puede agotarse"
  },
  "diferencia_mensual": 3365.75,
  "recomendacion": "Renta vitalicia",
  "pension_garantizada": 7467.40
}`,
        try_link: "/pensiones",
      },
      {
        method: "POST",
        path: "/api/v1/pensiones/renta-vitalicia/calcular",
        desc_es: "Calcula el factor de renta y la prima única necesaria para financiar una renta vitalicia del monto mensual indicado, con mortalidad EMSSA-09 y la tasa de interés técnico dada. Admite diferimiento y periodo garantizado.",
        desc_en: "Calculates the annuity factor and the single premium needed to fund a life annuity of the given monthly amount, using EMSSA-09 mortality and the given technical interest rate. Deferral and guaranteed periods are supported.",
        params: [
          { name: "edad", type: "int", required: true, default_val: "-", description_es: "Edad del rentista (18-100). El rango lo acota la tabla EMSSA-09: fuera de él no hay mortalidad tabulada", description_en: "Age of the annuitant (18-100). The EMSSA-09 table bounds the range: outside it there is no tabulated mortality" },
          { name: "sexo", type: "string", required: true, default_val: "-", description_es: "Sexo: masculino o femenino", description_en: "Sex: masculino or femenino" },
          { name: "monto_mensual", type: "float", required: true, default_val: "-", description_es: "Pago mensual de la renta en MXN (> 0)", description_en: "Monthly annuity payment in MXN (> 0)" },
          { name: "tasa_interes", type: "float", required: true, default_val: "-", description_es: "Tasa de interés técnico (0-0.15)", description_en: "Technical interest rate (0-0.15)" },
          { name: "periodo_diferimiento", type: "int", required: false, default_val: "0", description_es: "Periodo de diferimiento en años (0 = inmediata)", description_en: "Deferral period in years (0 = immediate)" },
          { name: "periodo_garantizado", type: "int", required: false, default_val: "0", description_es: "Periodo garantizado de pagos en años", description_en: "Guaranteed payment period in years" },
        ],
        example_req: `{
  "edad": 65,
  "sexo": "masculino",
  "monto_mensual": 15000,
  "tasa_interes": 0.035,
  "periodo_diferimiento": 0,
  "periodo_garantizado": 5
}`,
        example_res: `{
  "edad": 65,
  "sexo": "masculino",
  "monto_mensual": 15000.0,
  "tasa_interes": 0.035,
  "periodo_diferimiento": 0,
  "periodo_garantizado": 5,
  "factor_renta": 12.819393,
  "prima_unica": 2307490.77
}`,
        try_link: "/pensiones",
      },
      {
        method: "GET",
        path: "/api/v1/pensiones/conmutacion/tabla",
        desc_es: "Consulta la tabla de conmutación (Dx, Nx, Mx, ax, Ax) para un rango de edades, con mortalidad EMSSA-09 y la tasa de interés indicada.",
        desc_en: "Looks up commutation table values (Dx, Nx, Mx, ax, Ax) for a range of ages, using EMSSA-09 mortality and the given interest rate.",
        params: [
          { name: "sexo", type: "string (query)", required: true, default_val: "-", description_es: "Sexo: masculino o femenino", description_en: "Sex: masculino or femenino" },
          { name: "tasa_interes", type: "float (query)", required: true, default_val: "-", description_es: "Tasa de interés técnico (0-0.15)", description_en: "Technical interest rate (0-0.15)" },
          { name: "edad_min", type: "int (query)", required: false, default_val: "0", description_es: "Edad mínima a incluir (>= 0)", description_en: "Minimum age to include (>= 0)" },
          { name: "edad_max", type: "int (query)", required: false, default_val: "110", description_es: "Edad máxima a incluir (>= 0)", description_en: "Maximum age to include (>= 0)" },
        ],
        example_req: `GET /api/v1/pensiones/conmutacion/tabla?sexo=masculino&tasa_interes=0.035&edad_min=60&edad_max=62`,
        example_res: `{
  "sexo": "masculino",
  "tasa_interes": 0.035,
  "edad_min": 60,
  "edad_max": 62,
  "filas": [
    { "edad": 60, "Dx": 11521.84, "Nx": 173898.37, "Mx": 5641.22, "ax": 15.0929, "Ax": 0.48961 },
    { "edad": 61, "Dx": 11043.15, "Nx": 162376.53, "Mx": 5552.16, "ax": 14.7038, "Ax": 0.50277 },
    { "edad": 62, "Dx": 10573.69, "Nx": 151333.38, "Mx": 5456.13, "ax": 14.3123, "Ax": 0.51601 }
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
        desc_es: "Calcula reservas con el método Chain Ladder. Acepta un triángulo de desarrollo y devuelve ultimates proyectados, reservas IBNR por año de origen y factores de desarrollo. La forma del triángulo se declara en tipo_triangulo y nunca se infiere: leer un triángulo incremental como acumulado subestima la reserva.",
        desc_en: "Calculates reserves with the Chain Ladder method. Accepts a development triangle and returns projected ultimates, IBNR reserves per origin year, and development factors. The triangle's shape is declared in tipo_triangulo and never inferred: reading an incremental triangle as cumulative understates the reserve.",
        params: [
          { name: "triangle", type: "list[list[float|null]]", required: true, default_val: "-", description_es: "Triángulo de desarrollo como lista de filas (null para celdas vacías)", description_en: "Development triangle as a list of rows (null for missing cells)" },
          { name: "origin_years", type: "list[int]", required: true, default_val: "-", description_es: "Etiquetas de años de origen (una por fila)", description_en: "Origin year labels (one per row)" },
          { name: "tipo_triangulo", type: "string", required: true, default_val: "-", description_es: "Forma del triángulo enviado: acumulado o incremental. Se declara, no se infiere", description_en: "Shape of the submitted triangle: acumulado or incremental. Declared, never inferred" },
          { name: "permitir_desarrollo_negativo", type: "bool", required: false, default_val: "false", description_es: "Permite desarrollo negativo: incrementos negativos o filas acumuladas que decrecen. Es real en triángulos pagados con salvamento y subrogación, y en incurridos con liberación de reservas", description_en: "Allows negative development: negative increments, or cumulative rows that decrease. Real in paid triangles with salvage and subrogation, and in incurred triangles with reserve releases" },
          { name: "metodo_promedio", type: "string", required: false, default_val: "simple", description_es: "Método de promedio: simple, weighted, geometric", description_en: "Averaging method: simple, weighted, geometric" },
          { name: "calcular_tail_factor", type: "bool", required: false, default_val: "false", description_es: "Estima la cola ajustando la curva de potencia inversa de Sherman (1984) y extrapolando el producto. Es extrapolación: revise tail_ajuste_r2 y tail_horizonte en detalles", description_en: "Estimates the tail by fitting Sherman's (1984) inverse power curve and extrapolating the product. This is extrapolation: check tail_ajuste_r2 and tail_horizonte in detalles" },
          { name: "tail_factor", type: "float | null", required: false, default_val: "null", description_es: "Factor de cola manual, si no se calcula automáticamente", description_en: "Manual tail factor, if not auto-calculated" },
          { name: "unidad_monetaria", type: "string", required: false, default_val: "millones_mxn", description_es: "Escala de reporte de todo valor monetario del triángulo; se devuelve en la respuesta", description_en: "Reporting scale for every monetary value in the triangle; echoed in the response" },
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
  "tipo_triangulo": "acumulado",
  "metodo_promedio": "simple"
}`,
        example_res: `{
  "metodo": "chain_ladder",
  "unidad_monetaria": "millones_mxn",
  "reserva_total": 4983.22,
  "ultimate_total": 32883.22,
  "pagado_total": 27900.0,
  "reservas_por_anio": {
    "2019": 0.0, "2020": 103.45, "2021": 322.96,
    "2022": 1025.71, "2023": 3531.10
  },
  "ultimates_por_anio": { "2019": 5900.0, "2020": 6103.45, ... },
  "factores_desarrollo": [1.60393, 1.11483, 1.03510, 1.01724],
  "percentiles": null,
  "detalles": { "metodo_promedio": "simple", "tail_factor_usado": "No", ... },
  "calculation_metadata": { "validation_tier": "supported", ... }
}`,
        try_link: "/reservas",
      },
      {
        method: "POST",
        path: "/api/v1/reserves/bornhuetter-ferguson",
        desc_es: "Calcula reservas con el método Bornhuetter-Ferguson. Combina el desarrollo observado (factores Chain Ladder) con un estimado a priori del loss ratio, lo que da reservas más estables para los años inmaduros. En detalles se reporta el loss ratio implícito, para contrastarlo con el a priori que elegiste.",
        desc_en: "Calculates reserves with the Bornhuetter-Ferguson method. It combines observed development (Chain Ladder factors) with an a-priori loss ratio estimate, giving more stable reserves for immature years. detalles reports the implied loss ratio, so you can contrast it with the a priori you chose.",
        params: [
          { name: "triangle", type: "list[list[float|null]]", required: true, default_val: "-", description_es: "Triángulo de desarrollo (null para celdas vacías)", description_en: "Development triangle (null for missing cells)" },
          { name: "origin_years", type: "list[int]", required: true, default_val: "-", description_es: "Años de origen", description_en: "Origin years" },
          { name: "tipo_triangulo", type: "string", required: true, default_val: "-", description_es: "acumulado o incremental. Se declara, no se infiere", description_en: "acumulado or incremental. Declared, never inferred" },
          { name: "permitir_desarrollo_negativo", type: "bool", required: false, default_val: "false", description_es: "Permite incrementos negativos o filas acumuladas que decrecen", description_en: "Allows negative increments or decreasing cumulative rows" },
          { name: "primas_por_anio", type: "dict[int, float]", required: true, default_val: "-", description_es: "Primas devengadas por año de origen", description_en: "Earned premiums by origin year" },
          { name: "loss_ratio_apriori", type: "float", required: true, default_val: "-", description_es: "Loss ratio a priori esperado (0-2.0; por ejemplo 0.65)", description_en: "A-priori expected loss ratio (0-2.0; e.g. 0.65)" },
          { name: "metodo_promedio", type: "string", required: false, default_val: "simple", description_es: "Método de promedio: simple, weighted, geometric", description_en: "Averaging method: simple, weighted, geometric" },
          { name: "unidad_monetaria", type: "string", required: false, default_val: "millones_mxn", description_es: "Escala de reporte de los valores monetarios", description_en: "Reporting scale for the monetary values" },
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
  "tipo_triangulo": "acumulado",
  "primas_por_anio": {
    "2019": 7000, "2020": 7500,
    "2021": 8000, "2022": 8500, "2023": 9000
  },
  "loss_ratio_apriori": 0.65
}`,
        example_res: `{
  "metodo": "bornhuetter_ferguson",
  "unidad_monetaria": "millones_mxn",
  "reserva_total": 3905.25,
  "ultimate_total": 31805.25,
  "pagado_total": 27900.0,
  "reservas_por_anio": {
    "2019": 0.0, "2020": 82.63, "2021": 261.47,
    "2022": 818.26, "2023": 2742.88
  },
  "factores_desarrollo": [1.60393, 1.11483, 1.03510, 1.01724],
  "detalles": {
    "loss_ratio_apriori": "0.65",
    "loss_ratio_implicito": "79.51%",
    "porcentajes_reportados": { "2023": "53.11%", ... }
  }
}`,
        try_link: "/reservas",
      },
      {
        method: "POST",
        path: "/api/v1/reserves/bootstrap",
        desc_es: "Bootstrap ODP de England-Verrall: distribución predictiva de la reserva, con percentiles. Los residuales de Pearson se calculan sobre incrementales contra valores ajustados hacia atrás desde el ultimate; el parámetro de dispersión phi usa n-p grados de libertad, con la corrección de England (2002), y cada celda futura se simula de una Gamma, así que la dispersión cubre tanto el error de estimación como el de proceso. reserva_total es la media de las réplicas y detalles.error_prediccion su desviación estándar; detalles.conciliacion_cl_relativa mide la distancia contra Chain Ladder, cercana al 1% por la convexidad de la reserva en los factores. Es condicional al modelo: no cubre riesgo de modelo, cambio de mezcla, inflación no observada ni incertidumbre del factor de cola, y no es capital regulatorio.",
        desc_en: "England-Verrall ODP bootstrap: predictive distribution of the reserve, with percentiles. Pearson residuals are computed on incrementals against values fitted backwards from the ultimate; the dispersion parameter phi uses n-p degrees of freedom with England's (2002) adjustment, and each future cell is simulated from a Gamma, so the spread covers both estimation AND process error. reserva_total is the mean of the replicates and detalles.error_prediccion its standard deviation; detalles.conciliacion_cl_relativa measures the gap against Chain Ladder, near 1% from the reserve's convexity in the factors. It is conditional on the model: it does not cover model risk, mix change, unobserved inflation, or tail-factor uncertainty, and it is not regulatory capital.",
        params: [
          { name: "triangle", type: "list[list[float|null]]", required: true, default_val: "-", description_es: "Triángulo de desarrollo (null para celdas vacías)", description_en: "Development triangle (null for missing cells)" },
          { name: "origin_years", type: "list[int]", required: true, default_val: "-", description_es: "Años de origen", description_en: "Origin years" },
          { name: "tipo_triangulo", type: "string", required: true, default_val: "-", description_es: "acumulado o incremental. Se declara, no se infiere", description_en: "acumulado or incremental. Declared, never inferred" },
          { name: "permitir_desarrollo_negativo", type: "bool", required: false, default_val: "false", description_es: "Permite incrementos negativos o filas acumuladas que decrecen", description_en: "Allows negative increments or decreasing cumulative rows" },
          { name: "num_simulaciones", type: "int", required: false, default_val: "1000", description_es: "Número de réplicas bootstrap (100-10,000)", description_en: "Number of bootstrap replicates (100-10,000)" },
          { name: "seed", type: "int | null", required: false, default_val: "null", description_es: "Semilla para reproducibilidad", description_en: "Seed for reproducibility" },
          { name: "percentiles", type: "list[int]", required: false, default_val: "[50, 75, 90, 95, 99]", description_es: "Percentiles a calcular sobre la distribución predictiva", description_en: "Percentiles to compute over the predictive distribution" },
          { name: "unidad_monetaria", type: "string", required: false, default_val: "millones_mxn", description_es: "Escala de reporte de los valores monetarios", description_en: "Reporting scale for the monetary values" },
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
  "tipo_triangulo": "acumulado",
  "num_simulaciones": 5000,
  "seed": 42
}`,
        example_res: `{
  "metodo": "bootstrap",
  "unidad_monetaria": "millones_mxn",
  "reserva_total": 4967.24,
  "ultimate_total": 32867.24,
  "pagado_total": 27900.0,
  "percentiles": {
    "50": 4970.82, "75": 5148.92,
    "90": 5315.29, "95": 5424.76, "99": 5632.00
  },
  "detalles": {
    "metodo": "bootstrap-odp-england-verrall",
    "phi_dispersion": "5.017039466159304",
    "grados_libertad": 6,
    "error_prediccion": "275.1161152333231",
    "reserva_base_cl": "4962.273187911575",
    "conciliacion_cl_relativa": "0.001000437538482507"
  },
  "calculation_metadata": { "validation_tier": "supported", ... }
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
        desc_es: "Calcula un escenario de referencia del Requerimiento de Capital de Solvencia (RCS). Agrega riesgos de suscripción de vida y de daños y riesgos de inversión con una matriz de correlación simplificada; devuelve el desglose por riesgo, la matriz efectivamente aplicada en correlaciones_aplicadas y el año del perfil regulatorio usado. Debe enviarse al menos uno de config_vida, config_danos o config_inversion. Los factores son aproximaciones pedagógicas, no el modelo estocástico completo de la CNSF, y pueden subestimar el requerimiento real: la respuesta lo declara en disclaimer y validation_tier.",
        desc_en: "Calculates a reference Solvency Capital Requirement (RCS) scenario. It aggregates life and P&C underwriting risks and investment risks with a simplified correlation matrix; it returns the breakdown by risk, the matrix actually applied in correlaciones_aplicadas, and the year of the regulatory profile used. At least one of config_vida, config_danos, or config_inversion must be sent. The factors are pedagogical approximations, not the full CNSF stochastic model, and may understate the real requirement: the response states this in disclaimer and validation_tier.",
        params: [
          { name: "config_vida", type: "object | null", required: false, default_val: "null", description_es: "Riesgos de suscripción vida: suma_asegurada_total, reserva_matematica, edad_promedio_asegurados, duracion_promedio_polizas, numero_asegurados", description_en: "Life underwriting risks: suma_asegurada_total, reserva_matematica, edad_promedio_asegurados, duracion_promedio_polizas, numero_asegurados" },
          { name: "config_danos", type: "object | null", required: false, default_val: "null", description_es: "Riesgos de suscripción daños: primas_retenidas_12m, reserva_siniestros, coeficiente_variacion, numero_ramos", description_en: "P&C underwriting risks: primas_retenidas_12m, reserva_siniestros, coeficiente_variacion, numero_ramos" },
          { name: "config_inversion", type: "object | null", required: false, default_val: "null", description_es: "Riesgos de inversión: valor_acciones, valor_bonos_gubernamentales, valor_bonos_corporativos, valor_inmuebles, duracion_promedio_bonos, calificacion_promedio_bonos", description_en: "Investment risks: valor_acciones, valor_bonos_gubernamentales, valor_bonos_corporativos, valor_inmuebles, duracion_promedio_bonos, calificacion_promedio_bonos" },
          { name: "capital_minimo_pagado", type: "float", required: true, default_val: "-", description_es: "Capital mínimo pagado en MXN (> 0)", description_en: "Minimum paid-in capital in MXN (> 0)" },
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
  "rcs_mortalidad": 1950000.0,
  "rcs_longevidad": 315000.0,
  "rcs_invalidez": 772500.0,
  "rcs_gastos": 750000.0,
  "rcs_prima": 79200000.0,
  "rcs_reserva": 61967733.54,
  "rcs_suscripcion_vida": 2633589.52,
  "rcs_suscripcion_danos": 122558086.21,
  "rcs_inversion": 0.0,
  "rcs_total": 122586378.89,
  "capital_minimo_pagado": 100000000.0,
  "excedente_solvencia": -22586378.89,
  "ratio_solvencia": 0.8157513167897116,
  "cumple_regulacion": false,
  "desglose_por_riesgo": { "mortalidad": 1950000.0, ... },
  "anio_regulatorio": 2026,
  "validation_tier": "experimental",
  "disclaimer": "AVISO: Los factores de RCS en este modulo son aproximaciones pedagogicas simplificadas ...",
  "correlaciones_aplicadas": {
    "vida_danos": 0.0,
    "vida_inversion": 0.25,
    "danos_inversion": 0.25
  }
}`,
        try_link: "/regulatorio",
      },
      {
        method: "POST",
        path: "/api/v1/regulatory/sat/deductibility",
        desc_es: "Verifica la deducibilidad de una prima para efectos del ISR conforme al Art. 151 de la LISR. Determina si la prima es deducible y hasta qué monto según el tipo de seguro y la categoría del contribuyente. Para persona física, la prima de gastos médicos (fracc. VI) queda sujeta al tope global del último párrafo: el menor entre cinco UMA anuales y el 15% del total de ingresos. Si no se envía ingresos_totales_anuales, sólo aplica la rama de 5 UMA, tope_global reporta parcial_sin_ingresos y el monto deducible es una cota superior. El campo estado distingue eligible, not_eligible e indeterminate, y factores_faltantes nombra lo que falta para llegar a una respuesta determinada.",
        desc_en: "Checks premium deductibility for ISR purposes under LISR Art. 151. It determines whether a premium is deductible and up to what amount, by insurance type and taxpayer category. For an individual, a medical-expenses premium (fracc. VI) is subject to the global cap of the article's last paragraph: the lesser of five annual UMA and 15% of total income. Without ingresos_totales_anuales only the UMA leg applies, tope_global reports parcial_sin_ingresos, and the deductible amount is an upper bound. The estado field distinguishes eligible, not_eligible, and indeterminate, and factores_faltantes names what is missing to reach a determinate answer.",
        params: [
          { name: "tipo_seguro", type: "string", required: true, default_val: "-", description_es: "Tipo de seguro: vida, gastos_medicos, danos, pensiones, invalidez", description_en: "Insurance type: vida, gastos_medicos, danos, pensiones, invalidez" },
          { name: "monto_prima", type: "float", required: true, default_val: "-", description_es: "Monto de la prima en MXN (> 0)", description_en: "Premium amount in MXN (> 0)" },
          { name: "es_persona_fisica", type: "bool", required: false, default_val: "true", description_es: "true = persona física, false = persona moral", description_en: "true = individual, false = legal entity" },
          { name: "uma_anual", type: "float | null", required: false, default_val: "null (UMA del perfil vigente)", description_es: "Valor de la UMA anual. Si se omite, se usa la del perfil regulatorio vigente hoy y la respuesta indica el año en anio_regulatorio", description_en: "Annual UMA value. If omitted, the UMA of the regulatory profile in force today is used and the response reports the year in anio_regulatorio" },
          { name: "ingreso_anual", type: "float | null", required: false, default_val: "null", description_es: "Ingresos acumulables del ejercicio; base del tope propio de la fracc. V (planes de retiro)", description_en: "Accumulable annual income; base of the fracc. V own cap (retirement plans)" },
          { name: "ingresos_totales_anuales", type: "float | null", required: false, default_val: "null", description_es: "Total de ingresos del contribuyente, incluidos los exentos; base de la rama del 15% del tope global. Sin este dato el tope global no se puede aplicar completo", description_en: "Taxpayer's total income, exempt income included; base of the 15% leg of the global cap. Without it the global cap cannot be fully applied" },
          { name: "metodo_pago", type: "string | null", required: false, default_val: "null", description_es: "Medio de pago; la deducibilidad exige un medio rastreable, distinto del efectivo", description_en: "Payment method; deductibility requires a traceable, non-cash means" },
          { name: "relacion_beneficiario", type: "string | null", required: false, default_val: "null", description_es: "Relación del beneficiario con el contratante (persona moral)", description_en: "Beneficiary's relationship to the policyholder (legal entity)" },
        ],
        example_req: `{
  "tipo_seguro": "gastos_medicos",
  "monto_prima": 25000,
  "es_persona_fisica": true,
  "ingresos_totales_anuales": 300000
}`,
        example_res: `{
  "es_deducible": true,
  "monto_prima": 25000.0,
  "monto_deducible": 25000.0,
  "porcentaje_deducible": 100.0,
  "limite_aplicado": "Menor de 5 UMA anuales ($213,973.20) y 15% del total de ingresos ($45,000.00): $45,000.00",
  "fundamento_legal": "LISR Art. 151, fracc. VI - Primas por seguros de gastos medicos; tope del ultimo parrafo del mismo articulo",
  "estado": "indeterminate",
  "factores_faltantes": ["metodo_pago"],
  "uma_anual_aplicada": 42794.64,
  "anio_regulatorio": 2026,
  "tope_global": "aplicado",
  "nota_tope_global": "Tope global aplicado por la rama de 15% del total de ingresos. ... Aqui se aplica a esta prima como si fuera la unica deduccion personal del contribuyente."
}`,
        try_link: "/regulatorio",
      },
      {
        method: "POST",
        path: "/api/v1/regulatory/sat/withholding",
        desc_es: "Calcula la retención de ISR sobre un pago de seguros. Determina si aplica retención y calcula el monto según el tipo de pago (renta vitalicia, retiro de ahorro, etc.); regla_aplicada nombra la rama del cálculo que produjo el resultado. Las tasas y las citas de artículos no están verificadas contra el texto vigente de la LISR: son ilustrativas, y la respuesta lo declara en disclaimer.",
        desc_en: "Calculates ISR withholding on an insurance payment. It determines whether withholding applies and computes the amount by payment type (life annuity, savings withdrawal, etc.); regla_aplicada names the branch of the calculation that produced the result. The rates and article citations are not verified against the LISR text in force: they are illustrative, and the response states so in disclaimer.",
        params: [
          { name: "tipo_seguro", type: "string", required: true, default_val: "-", description_es: "Tipo de seguro: vida, gastos_medicos, danos, pensiones, invalidez", description_en: "Insurance type: vida, gastos_medicos, danos, pensiones, invalidez" },
          { name: "monto_pago", type: "float", required: true, default_val: "-", description_es: "Monto del pago en MXN (> 0)", description_en: "Payment amount in MXN (> 0)" },
          { name: "monto_gravable", type: "float", required: true, default_val: "-", description_es: "Monto gravable en MXN (>= 0)", description_en: "Taxable amount in MXN (>= 0)" },
          { name: "es_renta_vitalicia", type: "bool", required: false, default_val: "false", description_es: "El pago es de una renta vitalicia", description_en: "The payment is a life annuity" },
          { name: "es_retiro_ahorro", type: "bool", required: false, default_val: "false", description_es: "El pago es un retiro de ahorro", description_en: "The payment is a savings withdrawal" },
          { name: "requiere_retencion_forzosa", type: "bool", required: false, default_val: "false", description_es: "Fuerza la retención. Solo es observable en pensiones sin renta vitalicia: para los demás tipos las ramas de exención devuelven antes", description_en: "Forces withholding. Only observable for pensiones without a life annuity: for every other type the exemption branches return first" },
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
  "monto_pago": 500000.0,
  "base_retencion": 200000.0,
  "tasa_retencion": 0.2,
  "monto_retencion": 40000.0,
  "monto_neto_pagar": 460000.0,
  "regla_aplicada": "Vida + retiro de ahorro: se aplica la tasa de retiros de ahorro.",
  "disclaimer": "AVISO: las tasas de retencion y las citas de articulos de este modulo no estan verificadas contra el texto vigente de la LISR. Son ilustrativas."
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
        desc_es: "Calcula el resultado de un contrato de reaseguro cuota parte (proporcional). Aplica un porcentaje de cesión a primas y siniestros y devuelve montos cedido y retenido, recuperación y comisión. ratio_cesion se reporta en porcentaje, no en fracción.",
        desc_en: "Calculates the outcome of a quota share (proportional) reinsurance treaty. It applies a cession percentage to premiums and claims and returns ceded and retained amounts, recovery, and commission. ratio_cesion is reported as a percentage, not a fraction.",
        params: [
          { name: "porcentaje_cesion", type: "float", required: true, default_val: "-", description_es: "Porcentaje de cesión (0-100)", description_en: "Cession percentage (0-100)" },
          { name: "comision_reaseguro", type: "float", required: true, default_val: "-", description_es: "Comisión de reaseguro en porcentaje (0-50)", description_en: "Reinsurance commission as a percentage (0-50)" },
          { name: "comision_override", type: "float", required: false, default_val: "0.0", description_es: "Comisión override en porcentaje (0-10)", description_en: "Override commission as a percentage (0-10)" },
          { name: "vigencia_inicio", type: "date", required: true, default_val: "-", description_es: "Fecha de inicio de vigencia (YYYY-MM-DD)", description_en: "Inception date (YYYY-MM-DD)" },
          { name: "vigencia_fin", type: "date", required: true, default_val: "-", description_es: "Fecha de fin de vigencia (YYYY-MM-DD)", description_en: "Expiry date (YYYY-MM-DD)" },
          { name: "moneda", type: "string", required: false, default_val: "MXN", description_es: "Moneda del contrato", description_en: "Contract currency" },
          { name: "prima_bruta", type: "float", required: true, default_val: "-", description_es: "Prima bruta total (> 0)", description_en: "Total gross premium (> 0)" },
          { name: "siniestros", type: "list[object]", required: true, default_val: "-", description_es: "Lista de siniestros: id_siniestro, fecha_ocurrencia, monto_bruto", description_en: "Claims list: id_siniestro, fecha_ocurrencia, monto_bruto" },
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
  "monto_cedido": 4000000.0,
  "monto_retenido": 6000000.0,
  "recuperacion_reaseguro": 200000.0,
  "comision_recibida": 1200000.0,
  "prima_reaseguro_pagada": 4000000.0,
  "ratio_cesion": 40.0,
  "resultado_neto_cedente": 6900000.0,
  "detalles": {
    "prima_retenida": "6000000.00",
    "siniestros_cedidos": "200000.00",
    "siniestros_retenidos": "300000.00",
    ...
  }
}`,
        try_link: "/reaseguro",
      },
      {
        method: "POST",
        path: "/api/v1/reinsurance/excess-of-loss",
        desc_es: "Calcula el resultado de un contrato de exceso de pérdida (XL). El reasegurador paga lo que excede la retención, con tope por ocurrencia igual al ancho de la capa (limite). Las reinstalaciones fijan cuántas veces se restituye esa capacidad, así que el agregado del periodo es limite x (1 + numero_reinstatements) y las recuperaciones lo van erosionando. En detalles se reportan limite_agregado, limite_disponible, reinstatements_usados y prima_reinstalacion, esta última cobrada a prorrata de monto al 100%, sin ajuste a prorrata de tiempo.",
        desc_en: "Calculates the outcome of an excess of loss (XL) treaty. The reinsurer pays what exceeds the retention, capped per occurrence at the layer width (limite). Reinstatements set how many times that capacity is restored, so the period aggregate is limite x (1 + numero_reinstatements) and recoveries erode it in order. detalles reports limite_agregado, limite_disponible, reinstatements_usados, and prima_reinstalacion, the latter charged pro rata to amount at 100%, with no pro-rata-to-time adjustment.",
        params: [
          { name: "retencion", type: "float", required: true, default_val: "-", description_es: "Monto de retención (> 0)", description_en: "Retention amount (> 0)" },
          { name: "limite", type: "float", required: true, default_val: "-", description_es: "Ancho de la capa XL (> 0)", description_en: "Width of the XL layer (> 0)" },
          { name: "modalidad", type: "string", required: false, default_val: "por_riesgo", description_es: "Modalidad: por_riesgo o por_evento", description_en: "Modality: por_riesgo or por_evento" },
          { name: "numero_reinstatements", type: "int", required: false, default_val: "0", description_es: "Número de reinstalaciones (0-3)", description_en: "Number of reinstatements (0-3)" },
          { name: "tasa_prima", type: "float", required: true, default_val: "-", description_es: "Tasa de prima en porcentaje (0-100)", description_en: "Premium rate as a percentage (0-100)" },
          { name: "vigencia_inicio", type: "date", required: true, default_val: "-", description_es: "Fecha de inicio (YYYY-MM-DD)", description_en: "Inception date (YYYY-MM-DD)" },
          { name: "vigencia_fin", type: "date", required: true, default_val: "-", description_es: "Fecha de fin (YYYY-MM-DD)", description_en: "Expiry date (YYYY-MM-DD)" },
          { name: "moneda", type: "string", required: false, default_val: "MXN", description_es: "Moneda del contrato", description_en: "Contract currency" },
          { name: "prima_reaseguro_cobrada", type: "float", required: true, default_val: "-", description_es: "Prima de reaseguro cobrada (> 0)", description_en: "Reinsurance premium collected (> 0)" },
          { name: "siniestros", type: "list[object]", required: true, default_val: "-", description_es: "Lista de siniestros: id_siniestro, fecha_ocurrencia, monto_bruto", description_en: "Claims list: id_siniestro, fecha_ocurrencia, monto_bruto" },
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
  "monto_cedido": 0.0,
  "monto_retenido": 1000000.0,
  "recuperacion_reaseguro": 2000000.0,
  "comision_recibida": 0.0,
  "prima_reaseguro_pagada": 2500000.0,
  "ratio_cesion": 66.66666666666667,
  "resultado_neto_cedente": -500000.0,
  "detalles": {
    "limite_por_ocurrencia": "5000000.0",
    "limite_agregado": "5000000.0",
    "limite_disponible": "3000000.0",
    "reinstatements_usados": 0,
    "prima_reinstalacion": "0",
    ...
  }
}`,
        try_link: "/reaseguro",
      },
      {
        method: "POST",
        path: "/api/v1/reinsurance/stop-loss",
        desc_es: "Calcula el resultado de un contrato stop loss (agregado). Protege cuando la siniestralidad agregada excede el punto de retención, hasta el límite de cobertura; ambos se expresan como loss ratio en porcentaje. En detalles se reportan la siniestralidad bruta y la neta y si el contrato se activó.",
        desc_en: "Calculates the outcome of a stop loss (aggregate) treaty. It protects when the aggregate loss ratio exceeds the attachment point, up to the coverage limit; both are expressed as a loss ratio in percent. detalles reports gross and net loss ratios and whether the treaty was triggered.",
        params: [
          { name: "attachment_point", type: "float", required: true, default_val: "-", description_es: "Punto de retención como loss ratio en porcentaje (0-200)", description_en: "Attachment point as a loss ratio in percent (0-200)" },
          { name: "limite_cobertura", type: "float", required: true, default_val: "-", description_es: "Límite de cobertura como loss ratio en porcentaje (0-100)", description_en: "Coverage limit as a loss ratio in percent (0-100)" },
          { name: "primas_sujetas", type: "float", required: true, default_val: "-", description_es: "Primas sujetas al contrato (> 0)", description_en: "Subject premiums (> 0)" },
          { name: "vigencia_inicio", type: "date", required: true, default_val: "-", description_es: "Fecha de inicio (YYYY-MM-DD)", description_en: "Inception date (YYYY-MM-DD)" },
          { name: "vigencia_fin", type: "date", required: true, default_val: "-", description_es: "Fecha de fin (YYYY-MM-DD)", description_en: "Expiry date (YYYY-MM-DD)" },
          { name: "moneda", type: "string", required: false, default_val: "MXN", description_es: "Moneda del contrato", description_en: "Contract currency" },
          { name: "primas_totales", type: "float", required: true, default_val: "-", description_es: "Primas totales del periodo (> 0)", description_en: "Total period premiums (> 0)" },
          { name: "prima_reaseguro_cobrada", type: "float | null", required: false, default_val: "null", description_es: "Prima de reaseguro cobrada; si se omite, el modelo la estima", description_en: "Reinsurance premium collected; if omitted, the model estimates it" },
          { name: "siniestros", type: "list[object]", required: true, default_val: "-", description_es: "Lista de siniestros: id_siniestro, fecha_ocurrencia, monto_bruto", description_en: "Claims list: id_siniestro, fecha_ocurrencia, monto_bruto" },
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
  "monto_cedido": 0.0,
  "monto_retenido": 40000000.0,
  "recuperacion_reaseguro": 5000000.0,
  "comision_recibida": 0.0,
  "prima_reaseguro_pagada": 1500000.0,
  "ratio_cesion": 11.11111111111111,
  "resultado_neto_cedente": 3500000.0,
  "detalles": {
    "siniestralidad_bruta": "90.00%",
    "siniestralidad_neta": "80.00%",
    "contrato_activado": true,
    ...
  }
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
        desc_es: "Devuelve el perfil regulatorio completo de un año fiscal: UMA, tasas SAT, factores CNSF y factores técnicos, más la vigencia (effective_from, effective_to), el validation_tier y el bloque provenance, que cita la fuente, la fecha de publicación y la de consulta de cada dato. Un año sin perfil publicado devuelve 404 con la lista de años disponibles: no se crean perfiles futuros antes de su publicación.",
        desc_en: "Returns the full regulatory profile for a fiscal year: UMA, SAT rates, CNSF factors, and technical factors, plus its period (effective_from, effective_to), the validation_tier, and the provenance block, which cites the source, publication date, and retrieval date of each datum. A year with no published profile returns 404 with the list of available years: future profiles are not created before they are published.",
        params: [
          { name: "anio", type: "int (path)", required: true, default_val: "-", description_es: "Año fiscal. Perfiles empaquetados: 2024, 2025, 2026", description_en: "Fiscal year. Bundled profiles: 2024, 2025, 2026" },
        ],
        example_req: `GET /api/v1/config/2026`,
        example_res: `{
  "anio": 2026,
  "uma": {
    "uma_diaria": 117.31,
    "uma_mensual": 3566.22,
    "uma_anual": 42794.64
  },
  "tasas_sat": {
    "tasa_retencion_rentas_vitalicias": 0.1,
    "tasa_retencion_retiros_ahorro": 0.2,
    "tasa_retencion_otros_ingresos": 0.1,
    "tasa_isr_personas_morales": 0.3,
    "tasa_iva": 0.16,
    "limite_deducciones_pf_umas": 5
  },
  "factores_cnsf": { ... },
  "factores_tecnicos": { ... },
  "effective_from": "2026-02-01",
  "effective_to": "2027-01-31",
  "validation_tier": "experimental",
  "provenance": {
    "uma.diaria": {
      "value": "117.31",
      "unit": "MXN/dia",
      "status": "official",
      "validation_tier": "supported",
      "source": {
        "authority": "INEGI",
        "document_title": "Unidad de Medida y Actualizacion 2026",
        "publication_date": "2026-01-09",
        "retrieval_date": "2026-07-19"
      }
    },
    ...
  }
}`,
        try_link: "/regulatorio",
      },
      {
        method: "GET",
        path: "/api/v1/config/fecha/{fecha}",
        desc_es: "Devuelve el perfil regulatorio vigente en una fecha ISO. Es la vía correcta cuando el corte no coincide con el año calendario: la UMA entra en vigor el 1 de febrero, así que enero pertenece al perfil del año anterior. Una fecha fuera de la cobertura empaquetada devuelve 422 con el rango cubierto en el detalle. La asimetría con /config/{anio}, que devuelve 404, es deliberada: una fecha fuera de rango es una entrada inválida que se valida, mientras que un año sin perfil es un recurso que no existe. Nada se extrapola más allá del último perfil publicado; para escenarios propios, usa un perfil user_supplied.",
        desc_en: "Returns the regulatory profile in force on an ISO date. This is the right route when the cutoff does not match the calendar year: the UMA takes effect on 1 February, so January belongs to the previous year's profile. A date outside the bundled coverage returns 422 with the covered range in the detail. The asymmetry with /config/{anio}, which returns 404, is deliberate: an out-of-range date is an invalid input that gets validated, whereas a year with no profile is a resource that does not exist. Nothing is extrapolated past the last published profile; for your own scenarios, use a user_supplied profile.",
        params: [
          { name: "fecha", type: "date (path)", required: true, default_val: "-", description_es: "Fecha ISO (YYYY-MM-DD). Cobertura empaquetada: 2024-02-01 a 2027-01-31", description_en: "ISO date (YYYY-MM-DD). Bundled coverage: 2024-02-01 to 2027-01-31" },
        ],
        example_req: `GET /api/v1/config/fecha/2026-03-15

# Fuera de cobertura -> 422
GET /api/v1/config/fecha/1990-01-01`,
        example_res: `{
  "anio": 2026,
  "uma": { "uma_diaria": 117.31, "uma_mensual": 3566.22, "uma_anual": 42794.64 },
  "tasas_sat": { ... },
  "factores_cnsf": { ... },
  "factores_tecnicos": { ... },
  "effective_from": "2026-02-01",
  "effective_to": "2027-01-31",
  "validation_tier": "experimental",
  "provenance": { ... }
}

// 422 para 1990-01-01:
{
  "detail": "No existe snapshot oficial para 1990-01-01. Cobertura de perfiles empaquetados: 2024-02-01 a 2027-01-31. No se extrapolan parametros regulatorios: use un perfil user_supplied."
}`,
        try_link: "/regulatorio",
      },
      {
        method: "GET",
        path: "/api/v1/config/validate",
        desc_es: "Revisa los perfiles regulatorios empaquetados: periodos de vigencia contiguos y sin traslapes, unidades declaradas y completitud de las fuentes. Devuelve la lista de hallazgos como cadenas de texto; una lista vacía significa que la revisión no encontró nada. No calcula nada actuarial: es la comprobación de que el paquete de configuración es consistente antes de usarlo.",
        desc_en: "Checks the bundled regulatory profiles: contiguous, non-overlapping effective periods, declared units, and source completeness. It returns the findings as a list of strings; an empty list means the check found nothing. It computes nothing actuarial: it is the verification that the configuration bundle is consistent before you rely on it.",
        params: [],
        example_req: `GET /api/v1/config/validate`,
        example_res: `[]`,
        try_link: "/regulatorio",
      },
      {
        method: "GET",
        path: "/api/v1/config/{anio}/uma",
        desc_es: "Devuelve los valores de la UMA (Unidad de Medida y Actualización) diaria, mensual y anual de un año fiscal. La UMA anual del perfil es la mensual por 12, como la publica el INEGI.",
        desc_en: "Returns the daily, monthly, and annual UMA (Unidad de Medida y Actualizacion) values for a fiscal year. The profile's annual UMA is the monthly figure times 12, as INEGI publishes it.",
        params: [
          { name: "anio", type: "int (path)", required: true, default_val: "-", description_es: "Año fiscal", description_en: "Fiscal year" },
        ],
        example_req: `GET /api/v1/config/2026/uma`,
        example_res: `{
  "uma_diaria": 117.31,
  "uma_mensual": 3566.22,
  "uma_anual": 42794.64
}`,
        try_link: "/regulatorio",
      },
      {
        method: "GET",
        path: "/api/v1/config/{anio}/tasas-sat",
        desc_es: "Devuelve las tasas fiscales del SAT de un año fiscal: retenciones de ISR, tasa de personas morales, IVA y el límite de deducciones personales en UMA (Art. 151 LISR).",
        desc_en: "Returns the SAT tax rates for a fiscal year: ISR withholding rates, the corporate rate, VAT, and the personal deduction limit in UMA (LISR Art. 151).",
        params: [
          { name: "anio", type: "int (path)", required: true, default_val: "-", description_es: "Año fiscal", description_en: "Fiscal year" },
        ],
        example_req: `GET /api/v1/config/2026/tasas-sat`,
        example_res: `{
  "tasa_retencion_rentas_vitalicias": 0.1,
  "tasa_retencion_retiros_ahorro": 0.2,
  "tasa_retencion_otros_ingresos": 0.1,
  "tasa_isr_personas_morales": 0.3,
  "tasa_iva": 0.16,
  "limite_deducciones_pf_umas": 5
}`,
        try_link: "/regulatorio",
      },
      {
        method: "GET",
        path: "/api/v1/config/{anio}/factores-cnsf",
        desc_es: "Devuelve los factores regulatorios CNSF de un año fiscal: shocks de mercado por tipo de activo, shocks de crédito por calificación y las correlaciones que agregan el RCS. El perfil los marca como ilustrativos: son un marco de valuación, no una réplica de la CUSF.",
        desc_en: "Returns the CNSF regulatory factors for a fiscal year: market shocks by asset type, credit shocks by rating, and the correlations that aggregate the RCS. The profile marks them as illustrative: they are a valuation frame, not a replica of the CUSF.",
        params: [
          { name: "anio", type: "int (path)", required: true, default_val: "-", description_es: "Año fiscal", description_en: "Fiscal year" },
        ],
        example_req: `GET /api/v1/config/2026/factores-cnsf`,
        example_res: `{
  "shock_acciones": 0.35,
  "shock_bonos_gubernamentales": 0.05,
  "shock_bonos_corporativos": 0.15,
  "shock_inmuebles": 0.25,
  "shocks_credito": {
    "AAA": 0.002, "AA": 0.005, "A": 0.01,
    "BBB": 0.02, "BB": 0.05, "B": 0.1,
    "CCC": 0.2, "CC": 0.35, "C": 0.5
  },
  "correlacion_vida_danos": 0.0,
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
            ? "Mismos parámetros que /pricing/temporal (ver arriba)."
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
              https://api-suite.gonor.me/api/v1
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
              {lang === "es" ? "Autenticación" : "Authentication"}
            </h3>
            <p className="text-sm text-navy/60">{t("api_docs_auth")}</p>
          </div>
          <div>
            <h3 className="text-sm font-bold text-navy mb-2">Swagger UI</h3>
            <p className="text-sm text-navy/60">
              {t("api_docs_swagger")}{" "}
              <a
                href="https://api-suite.gonor.me/docs"
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
