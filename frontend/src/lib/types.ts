/**
 * TypeScript interfaces matching the FastAPI request/response schemas.
 * Grouped by domain: pricing, danos, salud, pensiones, reserves,
 * regulatory, reinsurance, config.
 */

// ── Pricing (Vida) ──────────────────────────────────────────────────────────

export interface PricingRequest {
  edad: number;
  sexo: "H" | "M";
  suma_asegurada: number;
  plazo_years: number;
  tasa_interes?: number;
  frecuencia_pago?: "anual" | "semestral" | "trimestral" | "mensual";
  recargo_gastos_admin?: number;
  recargo_gastos_adq?: number;
  recargo_utilidad?: number;
}

export interface PricingResponse {
  producto: string;
  prima_neta: number;
  prima_total: number;
  moneda: string;
  desglose_recargos: Record<string, number>;
  metadata: Record<string, unknown>;
}

export interface CompareResponse {
  temporal: PricingResponse;
  ordinario: PricingResponse;
  dotal: PricingResponse;
}

// ── Danos (P&C) ─────────────────────────────────────────────────────────────

export interface AutoRequest {
  valor_vehiculo: number;
  tipo_vehiculo: string;
  antiguedad_anos: number;
  zona: string;
  edad_conductor: number;
  deducible_pct?: number;
  coberturas?: string[];
  historial_siniestros?: number[];
}

export interface AutoResponse {
  vehiculo: Record<string, unknown>;
  conductor: Record<string, unknown>;
  zona: Record<string, unknown>;
  deducible: Record<string, unknown>;
  coberturas: Record<string, number>;
  subtotal: number;
  bonus_malus: Record<string, unknown>;
  prima_total: number;
}

export interface IncendioRequest {
  valor_inmueble: number;
  tipo_construccion: string;
  zona: string;
  uso: string;
}

export interface IncendioResponse {
  valor_inmueble: number;
  tipo_construccion: string;
  tasa_base: number;
  zona: string;
  factor_zona: number;
  uso: string;
  factor_uso: number;
  prima_anual: number;
}

export interface RCRequest {
  limite_responsabilidad: number;
  deducible: number;
  clase_actividad: string;
}

export interface RCResponse {
  limite_responsabilidad: number;
  deducible: number;
  clase_actividad: string;
  tasa_base: number;
  factor_deducible: number;
  prima_anual: number;
}

export interface BonusMalusRequest {
  nivel_actual?: number;
  numero_siniestros: number;
}

export interface BonusMalusResponse {
  nivel_previo: number;
  siniestros: number;
  nivel_nuevo: number;
  factor: number;
}

export interface FrecuenciaSeveridadRequest {
  dist_frecuencia: string;
  params_frecuencia: Record<string, number>;
  dist_severidad: string;
  params_severidad: Record<string, number>;
  n_simulaciones?: number;
  seed?: number | null;
}

export interface FrecuenciaSeveridadResponse {
  prima_pura: number;
  varianza_agregada: number;
  desviacion_estandar: number;
  asimetria: number;
  var_95: number;
  tvar_95: number;
  var_99: number;
  tvar_99: number;
  minimo: number;
  maximo: number;
  simulaciones: number;
}

// ── Salud (Health) ──────────────────────────────────────────────────────────

export interface GMMRequest {
  edad: number;
  sexo: "M" | "F";
  suma_asegurada: number;
  deducible: number;
  coaseguro_pct: number;
  tope_coaseguro?: number | null;
  zona?: string;
  nivel?: string;
}

export interface GMMResponse {
  asegurado: Record<string, unknown>;
  producto: Record<string, unknown>;
  tarificacion: Record<string, unknown>;
  siniestralidad_esperada: number;
}

export interface AccidentesRequest {
  edad: number;
  sexo: "M" | "F";
  suma_asegurada: number;
  ocupacion?: string;
  indemnizacion_diaria?: number | null;
}

export interface AccidentesResponse {
  suma_asegurada: number;
  prima_anual: number;
  perdidas_organicas: Record<string, unknown>;
  indemnizacion_diaria: Record<string, number>;
  gastos_funerarios: number;
}

// ── Pensiones ───────────────────────────────────────────────────────────────

export interface Ley73Request {
  semanas_cotizadas: number;
  salario_promedio_diario: number;
  edad_retiro: number;
}

export interface Ley73Response {
  regimen: string;
  semanas_cotizadas: number;
  salario_promedio_diario: number;
  edad_retiro: number;
  porcentaje_pension: number;
  factor_edad: number;
  pension_mensual: number;
  aguinaldo_anual: number;
  pension_anual_total: number;
}

export interface Ley97Request {
  saldo_afore: number;
  edad: number;
  sexo: "H" | "M";
  semanas_cotizadas: number;
  tasa_interes?: number;
}

export interface ModalidadDetalle {
  pension_mensual: number;
  pension_anual: number;
  tipo: string;
}

export interface Ley97Response {
  saldo_afore: number;
  edad: number;
  sexo: string;
  semanas_cotizadas: number;
  renta_vitalicia: ModalidadDetalle;
  retiro_programado: ModalidadDetalle;
  diferencia_mensual: number;
  recomendacion: string;
  pension_garantizada: number;
}

export interface RentaVitaliciaRequest {
  edad: number;
  sexo: "H" | "M";
  monto_mensual: number;
  tasa_interes: number;
  periodo_diferimiento?: number;
  periodo_garantizado?: number;
}

export interface RentaVitaliciaResponse {
  edad: number;
  sexo: string;
  monto_mensual: number;
  tasa_interes: number;
  periodo_diferimiento: number;
  periodo_garantizado: number;
  factor_renta: number;
  prima_unica: number;
}

// ── Reserves ────────────────────────────────────────────────────────────────

export interface ChainLadderRequest {
  triangle: (number | null)[][];
  origin_years: number[];
  metodo_promedio?: "simple" | "weighted" | "geometric";
  calcular_tail_factor?: boolean;
  tail_factor?: number | null;
}

export interface BornhuetterFergusonRequest {
  triangle: (number | null)[][];
  origin_years: number[];
  primas_por_anio: Record<number, number>;
  loss_ratio_apriori: number;
  metodo_promedio?: string;
}

export interface BootstrapRequest {
  triangle: (number | null)[][];
  origin_years: number[];
  num_simulaciones?: number;
  seed?: number | null;
  percentiles?: number[];
}

export interface ReserveResponse {
  metodo: string;
  reserva_total: number;
  ultimate_total: number;
  pagado_total: number;
  reservas_por_anio: Record<number, number>;
  ultimates_por_anio: Record<number, number>;
  factores_desarrollo?: number[] | null;
  percentiles?: Record<number, number> | null;
  detalles: Record<string, unknown>;
}

// ── Regulatory ──────────────────────────────────────────────────────────────

export interface RCSVidaIn {
  suma_asegurada_total: number;
  reserva_matematica: number;
  edad_promedio_asegurados: number;
  duracion_promedio_polizas: number;
  numero_asegurados?: number;
}

export interface RCSDanosIn {
  primas_retenidas_12m: number;
  reserva_siniestros: number;
  coeficiente_variacion?: number;
  numero_ramos?: number;
}

export interface RCSInversionIn {
  valor_acciones?: number;
  valor_bonos_gubernamentales?: number;
  valor_bonos_corporativos?: number;
  valor_inmuebles?: number;
  duracion_promedio_bonos?: number;
  calificacion_promedio_bonos?: string;
}

export interface RCSRequest {
  config_vida?: RCSVidaIn | null;
  config_danos?: RCSDanosIn | null;
  config_inversion?: RCSInversionIn | null;
  capital_minimo_pagado: number;
}

export interface RCSResponse {
  rcs_mortalidad: number;
  rcs_longevidad: number;
  rcs_invalidez: number;
  rcs_gastos: number;
  rcs_prima: number;
  rcs_reserva: number;
  rcs_mercado: number;
  rcs_credito: number;
  rcs_concentracion: number;
  rcs_suscripcion_vida: number;
  rcs_suscripcion_danos: number;
  rcs_inversion: number;
  rcs_total: number;
  capital_minimo_pagado: number;
  excedente_solvencia: number;
  ratio_solvencia: number;
  cumple_regulacion: boolean;
  desglose_por_riesgo: Record<string, number>;
}

export interface DeductibilityRequest {
  tipo_seguro: string;
  monto_prima: number;
  es_persona_fisica?: boolean;
  uma_anual?: number;
}

export interface DeductibilityResponse {
  es_deducible: boolean;
  monto_prima: number;
  monto_deducible: number;
  porcentaje_deducible: number;
  limite_aplicado: string | null;
  fundamento_legal: string;
}

export interface WithholdingRequest {
  tipo_seguro: string;
  monto_pago: number;
  monto_gravable: number;
  es_renta_vitalicia?: boolean;
  es_retiro_ahorro?: boolean;
  requiere_retencion_forzosa?: boolean;
}

export interface WithholdingResponse {
  requiere_retencion: boolean;
  monto_pago: number;
  base_retencion: number;
  tasa_retencion: number;
  monto_retencion: number;
  monto_neto_pagar: number;
}

// ── Reinsurance ─────────────────────────────────────────────────────────────

export interface SiniestroIn {
  id_siniestro: string;
  fecha_ocurrencia: string; // ISO date string
  monto_bruto: number;
  tipo?: string;
  id_poliza?: string | null;
  descripcion?: string | null;
}

export interface QuotaShareRequest {
  porcentaje_cesion: number;
  comision_reaseguro: number;
  comision_override?: number;
  vigencia_inicio: string; // ISO date
  vigencia_fin: string;
  moneda?: string;
  prima_bruta: number;
  siniestros: SiniestroIn[];
}

export interface ExcessOfLossRequest {
  retencion: number;
  limite: number;
  modalidad?: string;
  numero_reinstatements?: number;
  tasa_prima: number;
  vigencia_inicio: string;
  vigencia_fin: string;
  moneda?: string;
  prima_reaseguro_cobrada: number;
  siniestros: SiniestroIn[];
}

export interface StopLossRequest {
  attachment_point: number;
  limite_cobertura: number;
  primas_sujetas: number;
  vigencia_inicio: string;
  vigencia_fin: string;
  moneda?: string;
  primas_totales: number;
  prima_reaseguro_cobrada?: number | null;
  siniestros: SiniestroIn[];
}

export interface ReinsuranceResponse {
  tipo_contrato: string;
  monto_cedido: number;
  monto_retenido: number;
  recuperacion_reaseguro: number;
  comision_recibida: number;
  prima_reaseguro_pagada: number;
  ratio_cesion: number;
  resultado_neto_cedente: number;
  detalles: Record<string, unknown>;
}

// ── Config ──────────────────────────────────────────────────────────────────

export interface UMAResponse {
  uma_diaria: number;
  uma_mensual: number;
  uma_anual: number;
}

export interface TasasSATResponse {
  tasa_retencion_rentas_vitalicias: number;
  tasa_retencion_retiros_ahorro: number;
  tasa_isr_personas_morales: number;
  tasa_iva: number;
  limite_deducciones_pf_umas: number;
}

export interface FactoresCNSFResponse {
  shock_acciones: number;
  shock_bonos_gubernamentales: number;
  shock_bonos_corporativos: number;
  shock_inmuebles: number;
  shocks_credito: Record<string, number>;
  correlacion_vida_danos: number;
  correlacion_vida_inversion: number;
  correlacion_danos_inversion: number;
}

export interface FactoresTecnicosResponse {
  tasa_interes_tecnico_vida: number;
  tasa_interes_tecnico_pensiones: number;
  edad_omega: number;
  margen_seguridad_s114: number;
}

export interface ConfigAnualResponse {
  anio: number;
  uma: UMAResponse;
  tasas_sat: TasasSATResponse;
  factores_cnsf: FactoresCNSFResponse;
  factores_tecnicos: FactoresTecnicosResponse;
}
