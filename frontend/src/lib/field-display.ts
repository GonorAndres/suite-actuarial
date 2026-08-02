/**
 * Human presentation of raw API keys and values.
 *
 * Several endpoints answer with open dictionaries (`vehiculo`, `producto`,
 * `tarificacion`, `detalles`, `coberturas`), so the panels that show them were
 * printing the wire key and the wire value: `valor_asegurado: 217000`,
 * `coaseguro_pct: 0.1`, `tope_coaseguro: null`. This module maps a key to a
 * label in the reader's language and to the unit its value is quoted in.
 *
 * Two rules hold everywhere:
 *
 * - **Tolerant.** An unmapped key falls back to the raw key and an unmapped
 *   value to its plain string. A response that grows a field renders it
 *   unstyled; it never crashes and never disappears.
 * - **Absence is visible.** `null`, `undefined`, and the empty string render
 *   as an em dash, never as the word "null".
 */

import type { TranslationKey } from "@/lib/i18n/translations";
import {
  formatCurrency,
  formatNumber,
  formatPerMille,
  formatPercent,
  formatPercentValue,
} from "@/lib/utils";

/** What a missing value looks like on screen. */
export const VALOR_AUSENTE = "—";

/** The unit a value is quoted in, which decides how it is written out. */
export type FormatoCampo =
  /** Pesos. */
  | "moneda"
  /** Fraction of one: 0.10 is ten percent. */
  | "fraccion_pct"
  /** Already in percent points: 40.0 is forty percent. */
  | "valor_pct"
  /** Per thousand of the insured value: 0.8 is 0.80 per mille. */
  | "por_millar"
  /** Multiplicative rating factor, shown to four decimals. */
  | "factor"
  /** Count. */
  | "entero"
  /** Any other number. */
  | "numero"
  /** Enumerated or free text. */
  | "texto";

/* ── Labels ──────────────────────────────────────────────────────────────── */

/** Key -> translation key. Entries may be scoped as `ambito.clave` when the
 *  same wire key means different things in two realms. */
const ETIQUETAS: Record<string, TranslationKey> = {
  // Auto: vehicle, driver, zone, deductible
  tipo: "campo_tipo",
  grupo: "campo_grupo",
  valor_original: "campo_valor_original",
  valor_asegurado: "campo_valor_asegurado",
  antiguedad: "antiguedad",
  nombre: "campo_nombre",
  rango_edad: "campo_rango_edad",
  factor_edad: "campo_factor_edad",
  factor: "campo_factor",
  porcentaje: "campo_porcentaje",
  pesos: "campo_pesos",

  // Auto coverages
  danos_materiales: "cobertura_danos_materiales",
  robo_total: "cobertura_robo_total",
  rc_bienes: "cobertura_rc_bienes",
  rc_personas: "cobertura_rc_personas",
  gastos_medicos: "cobertura_gastos_medicos",
  asistencia_vial: "cobertura_asistencia_vial",

  // Health: insured, product, rating
  edad: "edad",
  sexo: "sexo",
  banda_edad: "campo_banda_edad",
  suma_asegurada: "suma_asegurada",
  deducible: "deducible",
  coaseguro_pct: "coaseguro",
  tope_coaseguro: "tope_coaseguro",
  zona: "campo_zona",
  "salud.zona": "zona_geografica",
  nivel: "campo_nivel",
  "salud.nivel": "nivel_hospitalario",
  tasa_banda_edad: "campo_tasa_banda_edad",
  tasa_base: "danos_tasa_base",
  prima_base: "campo_prima_base",
  prima_ajustada: "campo_prima_ajustada",
  factor_zona: "danos_factor_zona",
  factor_uso: "danos_factor_uso",
  factor_nivel: "campo_factor_nivel",
  factor_deducible: "danos_factor_deducible",
  factor_coaseguro: "campo_factor_coaseguro",
  monto_diario: "campo_monto_diario",
  monto_mensual: "monto_mensual",

  // Personal accident: scheduled organic losses
  muerte_accidental: "perdida_muerte_accidental",
  perdida_ambas_manos: "perdida_ambas_manos",
  perdida_ambos_pies: "perdida_ambos_pies",
  perdida_vista_ambos_ojos: "perdida_vista_ambos_ojos",
  perdida_una_mano_un_pie: "perdida_una_mano_un_pie",
  perdida_una_mano: "perdida_una_mano",
  perdida_un_pie: "perdida_un_pie",
  perdida_vista_un_ojo: "perdida_vista_un_ojo",
  perdida_pulgar: "perdida_pulgar",
  perdida_indice: "perdida_indice",
  perdida_oido_ambos: "perdida_oido_ambos",
  perdida_oido_uno: "perdida_oido_uno",

  // Life: premium loadings
  gastos_admin: "recargo_admin_corto",
  gastos_adq: "recargo_adq_corto",
  utilidad: "recargo_utilidad_corto",

  // Reinsurance: treaty details
  porcentaje_cesion: "porcentaje_cesion",
  comision_pct: "comision_reaseguro",
  prima_bruta: "reas_prima_bruta",
  prima_cedida: "reas_prima_cedida",
  prima_retenida: "reas_prima_retenida",
  comision_recibida: "reas_comision_recibida",
  siniestros_totales: "reas_siniestros_totales",
  siniestros_cedidos: "reas_siniestros_cedidos",
  siniestros_retenidos: "reas_siniestros_retenidos",
  numero_siniestros: "danos_numero_siniestros",
  detalle_siniestros: "reas_detalle_siniestros",
  retencion: "reas_retencion",
  limite_original: "reas_limite_original",
  limite_por_ocurrencia: "reas_limite_por_ocurrencia",
  limite_agregado: "reas_limite_agregado",
  limite_disponible: "reas_limite_disponible",
  modalidad: "reas_modalidad",
  numero_reinstatements: "reas_numero_reinstatements",
  reinstatements_usados: "reas_reinstatements_usados",
  prima_reinstalacion: "reas_prima_reinstalacion",
  attachment_point: "reas_attachment_point",
  limite_cobertura: "reas_limite_cobertura",
  primas_sujetas: "reas_primas_sujetas",
  primas_totales: "reas_primas_totales",
  siniestralidad_bruta: "reas_siniestralidad_bruta",
  siniestralidad_neta: "reas_siniestralidad_neta",
  contrato_activado: "reas_contrato_activado",
  id: "reas_id_siniestro",
  monto: "reas_monto_siniestro",
  recuperacion: "reas_recuperacion_siniestro",

  // Reserves
  metodo: "reservas_metodo",

  // SAT deductibility: inputs the validator reports as missing
  metodo_pago: "reg_metodo_pago",
  ingreso_anual: "reg_ingreso_anual",
  ingresos_totales_anuales: "reg_ingresos_totales",
  relacion_beneficiario: "reg_relacion_beneficiario",
};

/* ── Units ───────────────────────────────────────────────────────────────── */

const FORMATOS: Record<string, FormatoCampo> = {
  // Money
  valor_original: "moneda",
  valor_asegurado: "moneda",
  suma_asegurada: "moneda",
  deducible: "moneda",
  tope_coaseguro: "moneda",
  pesos: "moneda",
  prima_base: "moneda",
  prima_ajustada: "moneda",
  prima_anual: "moneda",
  prima_total: "moneda",
  subtotal: "moneda",
  monto_diario: "moneda",
  monto_mensual: "moneda",
  gastos_funerarios: "moneda",
  danos_materiales: "moneda",
  robo_total: "moneda",
  rc_bienes: "moneda",
  rc_personas: "moneda",
  gastos_medicos: "moneda",
  asistencia_vial: "moneda",
  gastos_admin: "moneda",
  gastos_adq: "moneda",
  utilidad: "moneda",
  prima_bruta: "moneda",
  prima_cedida: "moneda",
  prima_retenida: "moneda",
  comision_recibida: "moneda",
  siniestros_totales: "moneda",
  siniestros_cedidos: "moneda",
  siniestros_retenidos: "moneda",
  retencion: "moneda",
  limite_original: "moneda",
  limite_por_ocurrencia: "moneda",
  limite_agregado: "moneda",
  limite_disponible: "moneda",
  prima_reinstalacion: "moneda",
  primas_sujetas: "moneda",
  primas_totales: "moneda",
  monto: "moneda",
  recuperacion: "moneda",

  // Fractions of one
  coaseguro_pct: "fraccion_pct",
  porcentaje: "fraccion_pct",

  // Rates quoted per thousand of the insured value
  tasa_banda_edad: "por_millar",
  tasa_base: "por_millar",

  // Rating factors
  factor: "factor",
  factor_edad: "factor",
  factor_zona: "factor",
  factor_uso: "factor",
  factor_nivel: "factor",
  factor_deducible: "factor",
  factor_coaseguro: "factor",

  // Counts
  grupo: "entero",
  antiguedad: "entero",
  edad: "entero",
  numero_siniestros: "entero",
  numero_reinstatements: "entero",
  reinstatements_usados: "entero",
  simulaciones: "entero",

  // Text
  tipo: "texto",
  sexo: "texto",
  banda_edad: "texto",
  rango_edad: "texto",
  nombre: "texto",
  zona: "texto",
  nivel: "texto",
  uso: "texto",
  ocupacion: "texto",
  tipo_construccion: "texto",
  clase_actividad: "texto",
  modalidad: "texto",
  metodo: "texto",
  id: "texto",
};

/* ── Enumerated values ───────────────────────────────────────────────────── */

/** Wire value -> translation key, optionally scoped as `clave:valor`. */
const VALORES: Record<string, TranslationKey> = {
  // Sex
  masculino: "masculino",
  femenino: "femenino",

  // Vehicle types
  sedan_compacto: "vehiculo_sedan_compacto",
  sedan_mediano: "vehiculo_sedan_mediano",
  sedan_lujo: "vehiculo_sedan_lujo",
  suv_compacto: "vehiculo_suv_compacto",
  suv_mediano: "vehiculo_suv_mediano",
  suv_lujo: "vehiculo_suv_lujo",
  pickup: "vehiculo_pickup",
  deportivo: "vehiculo_deportivo",
  electrico: "vehiculo_electrico",
  motocicleta: "vehiculo_motocicleta",
  van: "vehiculo_van",
  camion_ligero: "vehiculo_camion_ligero",

  // Fire: construction, zone, and use of the building
  concreto: "construccion_concreto",
  acero: "construccion_acero",
  ladrillo: "construccion_ladrillo",
  mixta: "construccion_mixta",
  madera: "construccion_madera",
  lamina: "construccion_lamina",
  "zona:urbana_baja": "zona_incendio_urbana_baja",
  "zona:urbana_media": "zona_incendio_urbana_media",
  "zona:urbana_alta": "zona_incendio_urbana_alta",
  "zona:industrial": "zona_incendio_industrial",
  "zona:rural": "zona_incendio_rural",
  "zona:forestal": "zona_incendio_forestal",
  "uso:habitacional": "uso_habitacional",
  "uso:comercial": "uso_comercial",
  "uso:oficinas": "uso_oficinas",
  "uso:industrial": "uso_industrial",
  "uso:bodega": "uso_bodega",
  "uso:restaurante": "uso_restaurante",

  // Liability: activity class
  "clase_actividad:oficinas": "actividad_oficinas",
  "clase_actividad:comercio_minorista": "actividad_comercio_minorista",
  "clase_actividad:restaurante": "actividad_restaurante",
  "clase_actividad:manufactura_ligera": "actividad_manufactura_ligera",
  "clase_actividad:manufactura_pesada": "actividad_manufactura_pesada",
  "clase_actividad:construccion": "actividad_construccion",
  "clase_actividad:transporte": "actividad_transporte",
  "clase_actividad:servicios_profesionales": "actividad_servicios_profesionales",
  "clase_actividad:salud": "actividad_salud",
  "clase_actividad:educacion": "actividad_educacion",
  "clase_actividad:hoteleria": "actividad_hoteleria",
  "clase_actividad:inmobiliaria": "actividad_inmobiliaria",

  // Occupation class for personal accident
  "ocupacion:oficina": "salud_ocup_oficina",
  "ocupacion:comercio": "salud_ocup_comercio",
  "ocupacion:industrial_ligero": "salud_ocup_industrial_ligero",
  "ocupacion:industrial_pesado": "salud_ocup_industrial_pesado",
  "ocupacion:alto_riesgo": "salud_ocup_alto_riesgo",

  // Health zone and hospital level
  "zona:metro": "salud_zona_metro",
  "zona:urbano": "salud_zona_urbano",
  "zona:foraneo": "salud_zona_foraneo",
  "nivel:estandar": "salud_nivel_estandar",
  "nivel:medio": "salud_nivel_medio",
  "nivel:alto": "salud_nivel_alto",

  // Excess-of-loss basis
  por_riesgo: "reas_modalidad_por_riesgo",
  por_evento: "reas_modalidad_por_evento",

  // Reserving methods
  chain_ladder: "reservas_chain_ladder",
  bornhuetter_ferguson: "reservas_bornhuetter",
  bootstrap: "reservas_bootstrap",
};

/* ── Public helpers ──────────────────────────────────────────────────────── */

type Traducir = (key: TranslationKey) => string;

/**
 * Label for a raw API key, in the reader's language.
 *
 * `ambito` disambiguates a key that two realms use differently, e.g. `zona`
 * is a risk zone in auto and a geographic band in health. Unknown keys come
 * back unchanged.
 */
export function etiquetaCampo(
  clave: string,
  t: Traducir,
  ambito?: string,
): string {
  const key = ambito ? ETIQUETAS[`${ambito}.${clave}`] : undefined;
  const resuelta = key ?? ETIQUETAS[clave];
  return resuelta ? t(resuelta) : clave;
}

/** The unit registered for a key, or `undefined` when the key is unknown. */
export function formatoCampo(clave: string): FormatoCampo | undefined {
  return FORMATOS[clave];
}

function aplicarFormato(valor: number, formato: FormatoCampo): string {
  switch (formato) {
    case "moneda":
      return formatCurrency(valor);
    case "fraccion_pct":
      return formatPercent(valor);
    case "valor_pct":
      return formatPercentValue(valor);
    case "por_millar":
      return formatPerMille(valor);
    case "factor":
      return formatNumber(valor, 4);
    case "entero":
      return formatNumber(valor, 0);
    default:
      return formatNumber(valor);
  }
}

/**
 * Write a raw API value out for a reader.
 *
 * Numbers take the unit registered for their key; strings that already carry
 * a percent sign are left alone (several reinsurance details arrive
 * preformatted); booleans read as yes/no; absent values read as an em dash.
 */
export function valorCampo(
  clave: string,
  valor: unknown,
  t: Traducir,
  formatoExplicito?: FormatoCampo,
): string {
  if (valor === null || valor === undefined) return VALOR_AUSENTE;
  if (typeof valor === "boolean") return valor ? t("reg_si") : t("reg_no");

  const formato = formatoExplicito ?? FORMATOS[clave];

  if (typeof valor === "number") {
    if (!Number.isFinite(valor)) return VALOR_AUSENTE;
    return aplicarFormato(valor, formato ?? "numero");
  }

  if (typeof valor === "string") {
    const texto = valor.trim();
    if (texto === "") return VALOR_AUSENTE;

    // Already written out by the package, e.g. "40.0%" or "89.20%".
    if (texto.endsWith("%")) return texto;

    const enumerada = VALORES[`${clave}:${texto}`] ?? VALORES[texto];
    if (enumerada) return t(enumerada);

    // Decimals cross the wire as strings in the reinsurance details.
    if (formato && formato !== "texto") {
      const numero = Number(texto);
      if (texto !== "" && Number.isFinite(numero)) {
        return aplicarFormato(numero, formato);
      }
    }
    return texto;
  }

  return String(valor);
}
