"""
Pensiones router -- IMSS pension calculation endpoints.

Wraps PensionLey73, PensionLey97, RentaVitalicia, and TablaConmutacion
for Ley 73 / Ley 97 pension calculations, life annuity pricing, and
commutation table lookups.
"""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.pensiones.conmutacion import TablaConmutacion
from suite_actuarial.pensiones.plan_retiro import PensionLey73, PensionLey97
from suite_actuarial.pensiones.renta_vitalicia import RentaVitalicia

router = APIRouter(prefix="/pensiones", tags=["pensiones"])

# -- Mortality table cache -----------------------------------------------------

_tabla_mortalidad: TablaMortalidad | None = None


def _get_tabla() -> TablaMortalidad:
    """Load and cache the EMSSA-09 mortality table."""
    global _tabla_mortalidad
    if _tabla_mortalidad is None:
        _tabla_mortalidad = TablaMortalidad.cargar_emssa09()
    return _tabla_mortalidad


# -- Request / Response models -------------------------------------------------


class Ley73Request(BaseModel):
    """Request body for Ley 73 pension calculation."""

    semanas_cotizadas: int = Field(
        ..., ge=500, description="Total weeks contributed to IMSS (min 500)"
    )
    salario_promedio_diario: float = Field(
        ..., gt=0, description="Average daily salary over last 250 weeks (5 years)"
    )
    edad_retiro: int = Field(
        ..., ge=60, le=65, description="Retirement age (60-65)"
    )


class Ley73Response(BaseModel):
    """Response for Ley 73 pension calculation."""

    regimen: str
    semanas_cotizadas: int
    salario_promedio_diario: float
    edad_retiro: int
    porcentaje_pension: float
    factor_edad: float
    pension_mensual: float
    aguinaldo_anual: float
    pension_anual_total: float


class Ley97Request(BaseModel):
    """Request body for Ley 97 pension calculation."""

    saldo_afore: float = Field(
        ..., gt=0, description="Current AFORE account balance in MXN"
    )
    edad: int = Field(
        ..., ge=60, le=70, description="Current age of the worker"
    )
    sexo: str = Field(
        ..., pattern="^[HM]$", description="Sex: H (male) or M (female)"
    )
    semanas_cotizadas: int = Field(
        ..., ge=0, description="Total weeks contributed to IMSS"
    )
    tasa_interes: float = Field(
        default=0.035, ge=0, le=0.15,
        description="Technical interest rate (default: 3.5%)",
    )


class ModalidadDetalle(BaseModel):
    """Detail for a single pension modality."""

    pension_mensual: float
    pension_anual: float
    tipo: str


class Ley97Response(BaseModel):
    """Response for Ley 97 pension comparison."""

    saldo_afore: float
    edad: int
    sexo: str
    semanas_cotizadas: int
    renta_vitalicia: ModalidadDetalle
    retiro_programado: ModalidadDetalle
    diferencia_mensual: float
    recomendacion: str
    pension_garantizada: float


class RentaVitaliciaRequest(BaseModel):
    """Request body for life annuity calculation."""

    edad: int = Field(
        ..., ge=0, le=110, description="Age of the annuitant"
    )
    sexo: str = Field(
        ..., pattern="^[HM]$", description="Sex: H (male) or M (female)"
    )
    monto_mensual: float = Field(
        ..., gt=0, description="Monthly annuity payment in MXN"
    )
    tasa_interes: float = Field(
        ..., ge=0, le=0.15, description="Technical interest rate"
    )
    periodo_diferimiento: int = Field(
        default=0, ge=0, description="Deferral period in years (0 = immediate)"
    )
    periodo_garantizado: int = Field(
        default=0, ge=0, description="Guaranteed payment period in years"
    )


class RentaVitaliciaResponse(BaseModel):
    """Response for life annuity calculation."""

    edad: int
    sexo: str
    monto_mensual: float
    tasa_interes: float
    periodo_diferimiento: int
    periodo_garantizado: int
    factor_renta: float
    prima_unica: float


class ConmutacionRow(BaseModel):
    """Single row of a commutation table."""

    edad: int
    Dx: float
    Nx: float
    Mx: float
    ax: float
    Ax: float


class ConmutacionResponse(BaseModel):
    """Response for commutation table lookup."""

    sexo: str
    tasa_interes: float
    edad_min: int
    edad_max: int
    filas: list[ConmutacionRow]


# -- Helpers -------------------------------------------------------------------


def _decimal_dict_to_float(d: dict) -> dict[str, Any]:
    """Recursively convert Decimal values in a dict to float."""
    result = {}
    for k, v in d.items():
        if isinstance(v, Decimal):
            result[k] = float(v)
        elif isinstance(v, dict):
            result[k] = _decimal_dict_to_float(v)
        else:
            result[k] = v
    return result


# -- Endpoints -----------------------------------------------------------------


@router.post("/ley73/calcular", response_model=Ley73Response)
def calcular_ley73(req: Ley73Request):
    """Calculate an IMSS Ley 73 pension (defined-benefit regime).

    Computes the monthly pension, annual bonus (aguinaldo), and total
    annual income based on weeks contributed, average salary, and
    retirement age using the Ley del Seguro Social 1973 formula.
    """
    try:
        calc = PensionLey73(
            semanas_cotizadas=req.semanas_cotizadas,
            salario_promedio_5_anos=req.salario_promedio_diario,
            edad_retiro=req.edad_retiro,
        )
        resumen = calc.resumen()

        return Ley73Response(
            regimen=resumen["regimen"],
            semanas_cotizadas=resumen["semanas_cotizadas"],
            salario_promedio_diario=float(resumen["salario_promedio_diario"]),
            edad_retiro=resumen["edad_retiro"],
            porcentaje_pension=float(resumen["porcentaje_pension"]),
            factor_edad=float(resumen["factor_edad"]),
            pension_mensual=float(resumen["pension_mensual"]),
            aguinaldo_anual=float(resumen["aguinaldo_anual"]),
            pension_anual_total=float(resumen["pension_anual_total"]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ley97/calcular", response_model=Ley97Response)
def calcular_ley97(req: Ley97Request):
    """Calculate an IMSS Ley 97 pension (defined-contribution regime).

    Compares renta vitalicia (life annuity) vs retiro programado
    (scheduled withdrawal) modalities and recommends the better option
    based on the worker's AFORE balance, age, and weeks contributed.
    """
    try:
        tabla = _get_tabla()
        calc = PensionLey97(
            saldo_afore=req.saldo_afore,
            edad=req.edad,
            sexo=Sexo(req.sexo),
            semanas_cotizadas=req.semanas_cotizadas,
            tabla_mortalidad=tabla,
            tasa_interes=req.tasa_interes,
        )
        comparacion = calc.comparar_modalidades()

        return Ley97Response(
            saldo_afore=float(comparacion["saldo_afore"]),
            edad=comparacion["edad"],
            sexo=comparacion["sexo"],
            semanas_cotizadas=comparacion["semanas_cotizadas"],
            renta_vitalicia=ModalidadDetalle(
                pension_mensual=float(comparacion["renta_vitalicia"]["pension_mensual"]),
                pension_anual=float(comparacion["renta_vitalicia"]["pension_anual"]),
                tipo=comparacion["renta_vitalicia"]["tipo"],
            ),
            retiro_programado=ModalidadDetalle(
                pension_mensual=float(comparacion["retiro_programado"]["pension_mensual"]),
                pension_anual=float(comparacion["retiro_programado"]["pension_anual"]),
                tipo=comparacion["retiro_programado"]["tipo"],
            ),
            diferencia_mensual=float(comparacion["diferencia_mensual"]),
            recomendacion=comparacion["recomendacion"],
            pension_garantizada=float(comparacion["pension_garantizada"]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/renta-vitalicia/calcular", response_model=RentaVitaliciaResponse)
def calcular_renta_vitalicia(req: RentaVitaliciaRequest):
    """Calculate a life annuity (renta vitalicia) single premium and factor.

    Computes the annuity factor and the single premium needed to fund a
    life annuity of the given monthly amount, using EMSSA-09 mortality
    and the specified technical interest rate.
    """
    try:
        tabla = _get_tabla()
        rv = RentaVitalicia(
            edad=req.edad,
            sexo=Sexo(req.sexo),
            monto_mensual=req.monto_mensual,
            tabla_mortalidad=tabla,
            tasa_interes=req.tasa_interes,
            periodo_diferimiento=req.periodo_diferimiento,
            periodo_garantizado=req.periodo_garantizado,
        )

        factor = rv.calcular_factor_renta()
        prima = rv.calcular_prima_unica()

        return RentaVitaliciaResponse(
            edad=req.edad,
            sexo=req.sexo,
            monto_mensual=req.monto_mensual,
            tasa_interes=req.tasa_interes,
            periodo_diferimiento=req.periodo_diferimiento,
            periodo_garantizado=req.periodo_garantizado,
            factor_renta=float(factor),
            prima_unica=float(prima),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/conmutacion/tabla", response_model=ConmutacionResponse)
def tabla_conmutacion(
    sexo: str = Query(..., pattern="^[HM]$", description="Sex: H (male) or M (female)"),
    tasa_interes: float = Query(..., ge=0, le=0.15, description="Technical interest rate"),
    edad_min: int = Query(default=0, ge=0, description="Minimum age to include"),
    edad_max: int = Query(default=110, ge=0, description="Maximum age to include"),
):
    """Look up commutation table values for a range of ages.

    Loads the EMSSA-09 mortality table, builds a TablaConmutacion for
    the given sex and interest rate, and returns Dx, Nx, Mx, ax, Ax
    for each age in the requested range.
    """
    try:
        tabla = _get_tabla()
        tc = TablaConmutacion(
            tabla_mortalidad=tabla,
            sexo=Sexo(sexo),
            tasa_interes=tasa_interes,
        )

        # Clamp to actual table bounds
        e_min = max(edad_min, tc.edad_min)
        e_max = min(edad_max, tc.edad_max)

        filas = []
        for edad in range(e_min, e_max + 1):
            filas.append(
                ConmutacionRow(
                    edad=edad,
                    Dx=float(tc.Dx(edad)),
                    Nx=float(tc.Nx(edad)),
                    Mx=float(tc.Mx(edad)),
                    ax=float(tc.ax(edad)),
                    Ax=float(tc.Ax(edad)),
                )
            )

        return ConmutacionResponse(
            sexo=sexo,
            tasa_interes=tasa_interes,
            edad_min=e_min,
            edad_max=e_max,
            filas=filas,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
