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
  DotalLabRequest,
  DotalLabResponse,
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
  Sexo,
  StopLossRequest,
  UMAResponse,
  WithholdingRequest,
  WithholdingResponse,
} from "./types";

// ── Base URL ────────────────────────────────────────────────────────────────

// Same-origin by default: production is served by FastAPI and development is
// forwarded by Next.js. This also works through remote preview proxies.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

// ── Error class ─────────────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** One entry of FastAPI's 422 validation array. */
interface ValidationIssue {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
}

function describeIssue(issue: ValidationIssue): string {
  // `loc` starts with the request part ("body", "query", ...); the reader
  // cares about the field, not about where FastAPI found it.
  const path = (issue.loc ?? [])
    .slice(1)
    .map((part) => String(part))
    .join(".");
  const msg = issue.msg ?? "";
  if (path && msg) return `${path}: ${msg}`;
  return path || msg;
}

/**
 * Reduce an error response body to a sentence a reader can act on.
 *
 * The API answers a rejected input with `{"detail": "..."}` or, for a schema
 * violation, with `{"detail": [ ...issues ]}`. Neither should reach the screen
 * as JSON.
 */
export function parseErrorBody(
  body: string,
  status: number,
  statusText?: string,
): string {
  const trimmed = body.trim();
  if (trimmed) {
    try {
      const parsed: unknown = JSON.parse(trimmed);
      const detail =
        typeof parsed === "object" && parsed !== null && "detail" in parsed
          ? (parsed as { detail: unknown }).detail
          : undefined;

      if (typeof detail === "string" && detail.trim()) return detail.trim();

      if (Array.isArray(detail)) {
        const described = detail
          .map((issue) => describeIssue(issue as ValidationIssue))
          .filter(Boolean);
        if (described.length > 0) return described.join("; ");
      }

      if (detail && typeof detail === "object") {
        const described = describeIssue(detail as ValidationIssue);
        if (described) return described;
      }
    } catch {
      // Not JSON: the body is already plain text.
      return trimmed;
    }
  }
  return statusText?.trim() ? statusText.trim() : `HTTP ${status}`;
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
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, parseErrorBody(body, res.status, res.statusText));
  }

  return res.json() as Promise<TRes>;
}

async function apiGet<TRes>(
  path: string,
  params?: Record<string, string>,
): Promise<TRes> {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value);
    }
  }

  const res = await fetch(url.toString());

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, parseErrorBody(body, res.status, res.statusText));
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

  dotalLab: (req: DotalLabRequest) =>
    apiPost<DotalLabRequest, DotalLabResponse>("/pricing/dotal/lab", req),

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
    sexo: Sexo;
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
