/**
 * Typed API client for the suite_actuarial FastAPI backend.
 */

import type {
  AutoRequest,
  AutoResponse,
  AccidentesRequest,
  AccidentesResponse,
  BonusMalusRequest,
  BonusMalusResponse,
  BootstrapRequest,
  BornhuetterFergusonRequest,
  ChainLadderRequest,
  CompareResponse,
  ConfigAnualResponse,
  DeductibilityRequest,
  DeductibilityResponse,
  ExcessOfLossRequest,
  FrecuenciaSeveridadRequest,
  FrecuenciaSeveridadResponse,
  GMMRequest,
  GMMResponse,
  IncendioRequest,
  IncendioResponse,
  Ley73Request,
  Ley73Response,
  Ley97Request,
  Ley97Response,
  PricingRequest,
  PricingResponse,
  QuotaShareRequest,
  RCRequest,
  RCResponse,
  RCSRequest,
  RCSResponse,
  ReinsuranceResponse,
  RentaVitaliciaRequest,
  RentaVitaliciaResponse,
  ReserveResponse,
  StopLossRequest,
  UMAResponse,
  WithholdingRequest,
  WithholdingResponse,
} from "./types";

// ── Base URL ────────────────────────────────────────────────────────────────

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ── Error class ─────────────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// ── Generic helpers ─────────────────────────────────────────────────────────

async function apiPost<TReq, TRes>(
  path: string,
  body: TReq,
): Promise<TRes> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<TRes>;
}

async function apiGet<TRes>(
  path: string,
  params?: Record<string, string>,
): Promise<TRes> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value);
    }
  }

  const res = await fetch(url.toString());

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<TRes>;
}

// ── Pricing (Vida) ──────────────────────────────────────────────────────────

export const pricingApi = {
  temporal: (req: PricingRequest) =>
    apiPost<PricingRequest, PricingResponse>("/pricing/temporal", req),

  ordinario: (req: PricingRequest) =>
    apiPost<PricingRequest, PricingResponse>("/pricing/ordinario", req),

  dotal: (req: PricingRequest) =>
    apiPost<PricingRequest, PricingResponse>("/pricing/dotal", req),

  compare: (req: PricingRequest) =>
    apiPost<PricingRequest, CompareResponse>("/pricing/compare", req),
};

// ── Danos (P&C) ─────────────────────────────────────────────────────────────

export const danosApi = {
  auto: (req: AutoRequest) =>
    apiPost<AutoRequest, AutoResponse>("/danos/auto/calcular", req),

  incendio: (req: IncendioRequest) =>
    apiPost<IncendioRequest, IncendioResponse>("/danos/incendio/calcular", req),

  rc: (req: RCRequest) =>
    apiPost<RCRequest, RCResponse>("/danos/rc/calcular", req),

  bonusMalus: (req: BonusMalusRequest) =>
    apiPost<BonusMalusRequest, BonusMalusResponse>("/danos/bonus-malus", req),

  frecuenciaSeveridad: (req: FrecuenciaSeveridadRequest) =>
    apiPost<FrecuenciaSeveridadRequest, FrecuenciaSeveridadResponse>(
      "/danos/frecuencia-severidad",
      req,
    ),
};

// ── Salud (Health) ──────────────────────────────────────────────────────────

export const saludApi = {
  gmm: (req: GMMRequest) =>
    apiPost<GMMRequest, GMMResponse>("/salud/gmm/calcular", req),

  accidentes: (req: AccidentesRequest) =>
    apiPost<AccidentesRequest, AccidentesResponse>(
      "/salud/accidentes/calcular",
      req,
    ),
};

// ── Pensiones ───────────────────────────────────────────────────────────────

export const pensionesApi = {
  ley73: (req: Ley73Request) =>
    apiPost<Ley73Request, Ley73Response>("/pensiones/ley73/calcular", req),

  ley97: (req: Ley97Request) =>
    apiPost<Ley97Request, Ley97Response>("/pensiones/ley97/calcular", req),

  rentaVitalicia: (req: RentaVitaliciaRequest) =>
    apiPost<RentaVitaliciaRequest, RentaVitaliciaResponse>(
      "/pensiones/renta-vitalicia/calcular",
      req,
    ),

  conmutacion: (params: {
    sexo: string;
    tasa_interes: string;
    edad_min?: string;
    edad_max?: string;
  }) => apiGet<unknown>("/pensiones/conmutacion/tabla", params),
};

// ── Reserves ────────────────────────────────────────────────────────────────

export const reservesApi = {
  chainLadder: (req: ChainLadderRequest) =>
    apiPost<ChainLadderRequest, ReserveResponse>("/reserves/chain-ladder", req),

  bornhuetterFerguson: (req: BornhuetterFergusonRequest) =>
    apiPost<BornhuetterFergusonRequest, ReserveResponse>(
      "/reserves/bornhuetter-ferguson",
      req,
    ),

  bootstrap: (req: BootstrapRequest) =>
    apiPost<BootstrapRequest, ReserveResponse>("/reserves/bootstrap", req),
};

// ── Regulatory ──────────────────────────────────────────────────────────────

export const regulatoryApi = {
  rcs: (req: RCSRequest) =>
    apiPost<RCSRequest, RCSResponse>("/regulatory/rcs", req),

  deductibility: (req: DeductibilityRequest) =>
    apiPost<DeductibilityRequest, DeductibilityResponse>(
      "/regulatory/sat/deductibility",
      req,
    ),

  withholding: (req: WithholdingRequest) =>
    apiPost<WithholdingRequest, WithholdingResponse>(
      "/regulatory/sat/withholding",
      req,
    ),
};

// ── Reinsurance ─────────────────────────────────────────────────────────────

export const reinsuranceApi = {
  quotaShare: (req: QuotaShareRequest) =>
    apiPost<QuotaShareRequest, ReinsuranceResponse>(
      "/reinsurance/quota-share",
      req,
    ),

  excessOfLoss: (req: ExcessOfLossRequest) =>
    apiPost<ExcessOfLossRequest, ReinsuranceResponse>(
      "/reinsurance/excess-of-loss",
      req,
    ),

  stopLoss: (req: StopLossRequest) =>
    apiPost<StopLossRequest, ReinsuranceResponse>(
      "/reinsurance/stop-loss",
      req,
    ),
};

// ── Config ──────────────────────────────────────────────────────────────────

export const configApi = {
  getConfig: (year: number) =>
    apiGet<ConfigAnualResponse>(`/config/${year}`),

  getUma: (year: number) =>
    apiGet<UMAResponse>(`/config/${year}/uma`),

  getTasasSat: (year: number) =>
    apiGet<unknown>(`/config/${year}/tasas-sat`),

  getFactoresCnsf: (year: number) =>
    apiGet<unknown>(`/config/${year}/factores-cnsf`),
};
