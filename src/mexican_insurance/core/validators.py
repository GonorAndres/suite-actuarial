"""
Validadores con Pydantic para datos de seguros

Aquí van todas las validaciones de entrada/salida para asegurar
que los datos cumplen con las reglas de negocio y de la CNSF.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Sexo(StrEnum):
    """Sexo del asegurado según tablas actuariales"""

    HOMBRE = "H"
    MUJER = "M"


class Fumador(StrEnum):
    """Estatus de fumador (usado en algunas tablas de mortalidad)"""

    SI = "fumador"
    NO = "no_fumador"
    NO_ESPECIFICADO = "no_especificado"


class Moneda(StrEnum):
    """Monedas soportadas en el sistema"""

    MXN = "MXN"
    USD = "USD"


class Asegurado(BaseModel):
    """
    Representa a una persona asegurada.

    Esta clase valida que los datos estén en el rango correcto
    según las regulaciones de la CNSF y la práctica actuarial.
    """

    edad: int = Field(
        ...,
        ge=0,
        le=120,
        description="Edad del asegurado en años cumplidos",
    )
    sexo: Sexo = Field(
        ...,
        description="Sexo del asegurado para selección de tabla",
    )
    fumador: Fumador = Field(
        default=Fumador.NO_ESPECIFICADO,
        description="Estatus de fumador (algunas tablas lo requieren)",
    )
    fecha_nacimiento: date | None = Field(
        default=None,
        description="Fecha de nacimiento (opcional, para cálculos exactos)",
    )
    suma_asegurada: Decimal = Field(
        ...,
        gt=0,
        description="Suma asegurada en la moneda especificada",
    )

    @field_validator("suma_asegurada")
    @classmethod
    def validar_suma_asegurada(cls, v: Decimal) -> Decimal:
        """La suma asegurada debe ser positiva y razonable"""
        if v <= 0:
            raise ValueError("La suma asegurada debe ser mayor a cero")
        if v > Decimal("1e12"):  # 1 billón - límite razonable
            raise ValueError("La suma asegurada es excesivamente alta")
        return v

    @field_validator("edad")
    @classmethod
    def validar_edad(cls, v: int) -> int:
        """Validar que la edad esté en un rango asegurable típico"""
        if v < 0:
            raise ValueError("La edad no puede ser negativa")
        if v > 100:
            # Warning: edades muy altas pueden no tener datos en tablas
            pass
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "edad": 35,
                    "sexo": "H",
                    "fumador": "no_fumador",
                    "suma_asegurada": "1000000.00",
                }
            ]
        }
    }


class ConfiguracionProducto(BaseModel):
    """
    Configuración de un producto de seguros.

    Aquí van los parámetros que definen cómo funciona el producto:
    tasas, plazos, recargos, etc.
    """

    nombre_producto: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nombre del producto",
    )
    plazo_years: int = Field(
        ...,
        ge=1,
        le=99,
        description="Plazo del seguro en años",
    )
    tasa_interes_tecnico: Decimal = Field(
        default=Decimal("0.055"),
        ge=0,
        le=1,
        description="Tasa de interés técnico (típicamente 5.5% en México)",
    )
    recargo_gastos_admin: Decimal = Field(
        default=Decimal("0.05"),
        ge=0,
        le=1,
        description="Recargo por gastos de administración (% de prima)",
    )
    recargo_gastos_adq: Decimal = Field(
        default=Decimal("0.10"),
        ge=0,
        le=1,
        description="Recargo por gastos de adquisición (% de prima)",
    )
    recargo_utilidad: Decimal = Field(
        default=Decimal("0.03"),
        ge=0,
        le=1,
        description="Recargo por utilidad esperada (% de prima)",
    )
    moneda: Moneda = Field(
        default=Moneda.MXN,
        description="Moneda del producto",
    )

    @field_validator("tasa_interes_tecnico")
    @classmethod
    def validar_tasa_interes(cls, v: Decimal) -> Decimal:
        """
        La tasa de interés técnico debe estar en rangos razonables.
        CNSF típicamente permite hasta 5.5% para ciertos productos.
        """
        if v < 0:
            raise ValueError("La tasa de interés no puede ser negativa")
        if v > Decimal("0.15"):
            raise ValueError(
                "Tasa de interés muy alta (típicamente máx 15% anual)"
            )
        return v

    @model_validator(mode="after")
    def validar_recargos_totales(self) -> "ConfiguracionProducto":
        """Los recargos totales no deberían ser mayores al 100%"""
        total_recargos = (
            self.recargo_gastos_admin
            + self.recargo_gastos_adq
            + self.recargo_utilidad
        )
        if total_recargos > Decimal("1.0"):
            raise ValueError(
                f"Recargos totales ({total_recargos:.2%}) superan el 100%"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nombre_producto": "Vida Temporal 20 Años",
                    "plazo_years": 20,
                    "tasa_interes_tecnico": "0.055",
                    "recargo_gastos_admin": "0.05",
                    "recargo_gastos_adq": "0.10",
                    "recargo_utilidad": "0.03",
                    "moneda": "MXN",
                }
            ]
        }
    }


class ResultadoCalculo(BaseModel):
    """
    Resultado de un cálculo actuarial.

    Almacena los resultados de primas, reservas, etc.
    con metadatos sobre cómo se calculó.
    """

    prima_neta: Decimal = Field(
        ...,
        ge=0,
        description="Prima neta (sin recargos)",
    )
    prima_total: Decimal = Field(
        ...,
        ge=0,
        description="Prima total (con todos los recargos)",
    )
    moneda: Moneda = Field(
        ...,
        description="Moneda del cálculo",
    )
    desglose_recargos: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Desglose detallado de cada recargo aplicado",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Información adicional sobre el cálculo",
    )

    @model_validator(mode="after")
    def validar_prima_total(self) -> "ResultadoCalculo":
        """La prima total debe ser >= prima neta"""
        if self.prima_total < self.prima_neta:
            raise ValueError(
                "La prima total no puede ser menor a la prima neta"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prima_neta": "5000.00",
                    "prima_total": "5900.00",
                    "moneda": "MXN",
                    "desglose_recargos": {
                        "gastos_admin": "250.00",
                        "gastos_adq": "500.00",
                        "utilidad": "150.00",
                    },
                    "metadata": {
                        "tabla_mortalidad": "EMSSA-09",
                        "metodo": "prima_nivelada",
                    },
                }
            ]
        }
    }


# Validador para tablas de mortalidad
class RegistroMortalidad(BaseModel):
    """
    Un registro en una tabla de mortalidad.

    Representa la probabilidad de muerte (qx) para una edad y sexo dados.
    """

    edad: int = Field(..., ge=0, le=120)
    sexo: Sexo
    qx: Decimal = Field(
        ...,
        ge=0,
        le=1,
        description="Probabilidad de muerte entre edad x y x+1",
    )
    lx: int | None = Field(
        default=None,
        ge=0,
        description="Número de sobrevivientes a edad x (opcional)",
    )

    @field_validator("qx")
    @classmethod
    def validar_qx(cls, v: Decimal) -> Decimal:
        """qx debe estar entre 0 y 1"""
        if not (0 <= v <= 1):
            raise ValueError(f"qx debe estar entre 0 y 1, se recibió {v}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "edad": 35,
                    "sexo": "H",
                    "qx": "0.001234",
                    "lx": 98765,
                }
            ]
        }
    }


# ============================================================================
# MODELOS PARA REASEGURO (Fase 3)
# ============================================================================


class TipoContrato(StrEnum):
    """Tipos de contratos de reaseguro soportados"""

    QUOTA_SHARE = "quota_share"
    EXCESS_OF_LOSS = "excess_of_loss"
    STOP_LOSS = "stop_loss"


class TipoSiniestro(StrEnum):
    """Tipo de siniestro para efectos de reaseguro"""

    INDIVIDUAL = "individual"
    EVENTO_CATASTROFICO = "evento_catastrofico"


class ModalidadXL(StrEnum):
    """Modalidades de Excess of Loss"""

    POR_RIESGO = "por_riesgo"
    POR_EVENTO = "por_evento"


class Siniestro(BaseModel):
    """
    Representa un siniestro individual o agregado.

    Se usa para calcular recuperaciones de reaseguro.
    """

    id_siniestro: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identificador único del siniestro",
    )
    fecha_ocurrencia: date = Field(
        ...,
        description="Fecha en que ocurrió el siniestro",
    )
    monto_bruto: Decimal = Field(
        ...,
        gt=0,
        description="Monto del siniestro antes de reaseguro",
    )
    tipo: TipoSiniestro = Field(
        default=TipoSiniestro.INDIVIDUAL,
        description="Tipo de siniestro (individual o catastrófico)",
    )
    id_poliza: str | None = Field(
        default=None,
        description="ID de la póliza asociada (si aplica)",
    )
    descripcion: str | None = Field(
        default=None,
        max_length=500,
        description="Descripción del siniestro",
    )

    @field_validator("monto_bruto")
    @classmethod
    def validar_monto_razonable(cls, v: Decimal) -> Decimal:
        """El monto debe ser positivo y razonable"""
        if v <= 0:
            raise ValueError("El monto del siniestro debe ser mayor a cero")
        if v > Decimal("1e9"):  # 1,000 millones - límite razonable
            raise ValueError("Monto de siniestro excesivamente alto")
        return v

    @field_validator("fecha_ocurrencia")
    @classmethod
    def validar_fecha_no_futura(cls, v: date) -> date:
        """La fecha del siniestro no puede ser futura"""
        from datetime import date as dt_date

        hoy = dt_date.today()
        if v > hoy:
            raise ValueError(
                f"La fecha del siniestro ({v}) no puede ser futura"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id_siniestro": "SIN-2024-001",
                    "fecha_ocurrencia": "2024-03-15",
                    "monto_bruto": "350000.00",
                    "tipo": "individual",
                    "id_poliza": "POL-12345",
                    "descripcion": "Fallecimiento del asegurado",
                }
            ]
        }
    }


class ConfiguracionReaseguro(BaseModel):
    """
    Configuración base para contratos de reaseguro.

    Clase base que comparten todos los tipos de contratos.
    """

    tipo_contrato: TipoContrato = Field(
        ...,
        description="Tipo de contrato de reaseguro",
    )
    vigencia_inicio: date = Field(
        ...,
        description="Fecha de inicio de vigencia del contrato",
    )
    vigencia_fin: date = Field(
        ...,
        description="Fecha de fin de vigencia del contrato",
    )
    moneda: Moneda = Field(
        default=Moneda.MXN,
        description="Moneda del contrato",
    )

    @model_validator(mode="after")
    def validar_vigencia(self) -> "ConfiguracionReaseguro":
        """La fecha de fin debe ser posterior a la de inicio"""
        if self.vigencia_fin <= self.vigencia_inicio:
            raise ValueError(
                "La fecha de fin debe ser posterior a la de inicio"
            )

        # Validar que el periodo no sea mayor a 5 años
        dias_vigencia = (self.vigencia_fin - self.vigencia_inicio).days
        if dias_vigencia > 365 * 5:
            raise ValueError(
                "El periodo de vigencia no puede exceder 5 años"
            )

        return self


class QuotaShareConfig(ConfiguracionReaseguro):
    """
    Configuración para contrato Quota Share (Cuota Parte).

    El reasegurador acepta un % fijo de cada riesgo y paga
    una comisión a la cedente.
    """

    porcentaje_cesion: Decimal = Field(
        ...,
        gt=0,
        le=100,
        description="Porcentaje cedido al reasegurador (0-100%)",
    )
    comision_reaseguro: Decimal = Field(
        ...,
        ge=0,
        le=50,
        description="Comisión que el reasegurador paga a la cedente (%)",
    )
    comision_override: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=10,
        description="Comisión adicional (override) si aplica (%)",
    )

    @field_validator("porcentaje_cesion")
    @classmethod
    def validar_porcentaje(cls, v: Decimal) -> Decimal:
        """Porcentaje debe estar entre 0 y 100"""
        if not (0 < v <= 100):
            raise ValueError(
                f"Porcentaje de cesión debe estar entre 0 y 100, recibido: {v}"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_contrato": "quota_share",
                    "vigencia_inicio": "2024-01-01",
                    "vigencia_fin": "2024-12-31",
                    "moneda": "MXN",
                    "porcentaje_cesion": "30.00",
                    "comision_reaseguro": "25.00",
                    "comision_override": "2.50",
                }
            ]
        }
    }


class ExcessOfLossConfig(ConfiguracionReaseguro):
    """
    Configuración para contrato Excess of Loss (Exceso de Pérdida).

    El reasegurador paga cuando un siniestro excede la retención,
    hasta un límite máximo.
    """

    retencion: Decimal = Field(
        ...,
        gt=0,
        description="Retención de la cedente (prioridad)",
    )
    limite: Decimal = Field(
        ...,
        gt=0,
        description="Límite de cobertura del reasegurador",
    )
    modalidad: ModalidadXL = Field(
        default=ModalidadXL.POR_RIESGO,
        description="Modalidad del XL (por riesgo o por evento)",
    )
    numero_reinstatements: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Número de reinstalaciones permitidas",
    )
    tasa_prima: Decimal = Field(
        ...,
        gt=0,
        le=100,
        description="Tasa de prima (% sobre el límite)",
    )

    @model_validator(mode="after")
    def validar_limite_mayor_retencion(self) -> "ExcessOfLossConfig":
        """El límite debe ser mayor que la retención"""
        if self.limite <= self.retencion:
            raise ValueError(
                f"El límite ({self.limite}) debe ser mayor que "
                f"la retención ({self.retencion})"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_contrato": "excess_of_loss",
                    "vigencia_inicio": "2024-01-01",
                    "vigencia_fin": "2024-12-31",
                    "moneda": "MXN",
                    "retencion": "200000.00",
                    "limite": "500000.00",
                    "modalidad": "por_riesgo",
                    "numero_reinstatements": 2,
                    "tasa_prima": "5.00",
                }
            ]
        }
    }


class StopLossConfig(ConfiguracionReaseguro):
    """
    Configuración para contrato Stop Loss.

    Protege cuando la siniestralidad agregada excede un porcentaje
    (attachment point) hasta un límite.
    """

    attachment_point: Decimal = Field(
        ...,
        gt=0,
        le=200,
        description="Punto de activación (% de siniestralidad)",
    )
    limite_cobertura: Decimal = Field(
        ...,
        gt=0,
        le=100,
        description="Límite de cobertura adicional (%)",
    )
    primas_sujetas: Decimal = Field(
        ...,
        gt=0,
        description="Primas sujetas al contrato (base de cálculo)",
    )

    @field_validator("attachment_point")
    @classmethod
    def validar_attachment(cls, v: Decimal) -> Decimal:
        """El attachment debe ser razonable (típicamente 60-150%)"""
        if v < 50:
            raise ValueError(
                "Attachment point muy bajo (típicamente >= 60%)"
            )
        if v > 200:
            raise ValueError(
                "Attachment point muy alto (típicamente <= 150%)"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_contrato": "stop_loss",
                    "vigencia_inicio": "2024-01-01",
                    "vigencia_fin": "2024-12-31",
                    "moneda": "MXN",
                    "attachment_point": "80.00",
                    "limite_cobertura": "20.00",
                    "primas_sujetas": "10000000.00",
                }
            ]
        }
    }


class ResultadoReaseguro(BaseModel):
    """
    Resultado de aplicar un contrato de reaseguro.

    Contiene los montos cedidos, retenidos y recuperados,
    así como las comisiones y primas pagadas.
    """

    tipo_contrato: TipoContrato = Field(
        ...,
        description="Tipo de contrato aplicado",
    )
    monto_cedido: Decimal = Field(
        ...,
        ge=0,
        description="Monto cedido al reasegurador",
    )
    monto_retenido: Decimal = Field(
        ...,
        ge=0,
        description="Monto retenido por la cedente",
    )
    recuperacion_reaseguro: Decimal = Field(
        ...,
        ge=0,
        description="Monto recuperado del reasegurador",
    )
    comision_recibida: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Comisión recibida del reasegurador",
    )
    prima_reaseguro_pagada: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Prima pagada al reasegurador",
    )
    ratio_cesion: Decimal = Field(
        ...,
        ge=0,
        le=100,
        description="% de cesión efectivo",
    )
    resultado_neto_cedente: Decimal = Field(
        ...,
        description="Resultado neto para la cedente (puede ser negativo)",
    )
    detalles: dict[str, Any] = Field(
        default_factory=dict,
        description="Detalles adicionales del cálculo",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_contrato": "quota_share",
                    "monto_cedido": "300000.00",
                    "monto_retenido": "700000.00",
                    "recuperacion_reaseguro": "150000.00",
                    "comision_recibida": "82500.00",
                    "prima_reaseguro_pagada": "300000.00",
                    "ratio_cesion": "30.00",
                    "resultado_neto_cedente": "532500.00",
                    "detalles": {
                        "porcentaje_cesion": "30%",
                        "comision_total": "27.5%",
                    },
                }
            ]
        }
    }


# ============================================================================
# MODELOS PARA RESERVAS (Fase 4)
# ============================================================================


class TipoTriangulo(StrEnum):
    """Tipo de triángulo de desarrollo"""

    ACUMULADO = "acumulado"
    INCREMENTAL = "incremental"


class MetodoReserva(StrEnum):
    """Métodos de cálculo de reservas soportados"""

    CHAIN_LADDER = "chain_ladder"
    BORNHUETTER_FERGUSON = "bornhuetter_ferguson"
    BOOTSTRAP = "bootstrap"


class MetodoPromedio(StrEnum):
    """Métodos para calcular promedio de factores de desarrollo"""

    SIMPLE = "simple"
    PONDERADO = "weighted"
    GEOMETRICO = "geometric"


class ConfiguracionChainLadder(BaseModel):
    """
    Configuración para método Chain Ladder.

    El Chain Ladder es el método más usado en la industria
    para proyectar desarrollo de siniestros.
    """

    metodo_promedio: MetodoPromedio = Field(
        default=MetodoPromedio.SIMPLE,
        description="Método para calcular factores de desarrollo",
    )
    calcular_tail_factor: bool = Field(
        default=False,
        description="Si se debe calcular factor de cola (tail)",
    )
    tail_factor: Decimal | None = Field(
        default=None,
        ge=Decimal("1.0"),
        le=Decimal("2.0"),
        description="Factor de cola manual (si no se calcula)",
    )


class ConfiguracionBornhuetterFerguson(BaseModel):
    """
    Configuración para método Bornhuetter-Ferguson.

    Combina siniestros observados con expectativa a priori.
    Más estable para años con poco desarrollo.
    """

    loss_ratio_apriori: Decimal = Field(
        ...,
        gt=0,
        le=Decimal("2.0"),
        description="Loss ratio esperado (típicamente 0.60-0.75)",
    )
    metodo_promedio: MetodoPromedio = Field(
        default=MetodoPromedio.SIMPLE,
        description="Método para factores de desarrollo",
    )

    @field_validator("loss_ratio_apriori")
    @classmethod
    def validar_loss_ratio(cls, v: Decimal) -> Decimal:
        """Loss ratio debe ser razonable"""
        if v < Decimal("0.3"):
            raise ValueError("Loss ratio muy bajo (típicamente >= 30%)")
        if v > Decimal("1.5"):
            raise ValueError("Loss ratio muy alto (típicamente <= 150%)")
        return v


class ConfiguracionBootstrap(BaseModel):
    """
    Configuración para método Bootstrap.

    Usa simulación Monte Carlo para estimar distribución
    completa de reservas.
    """

    num_simulaciones: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Número de simulaciones a ejecutar",
    )
    seed: int | None = Field(
        default=None,
        description="Semilla para reproducibilidad",
    )
    metodo_residuales: str = Field(
        default="pearson",
        description="Método para calcular residuales",
    )
    percentiles: list[int] = Field(
        default=[50, 75, 90, 95, 99],
        description="Percentiles a calcular",
    )

    @field_validator("percentiles")
    @classmethod
    def validar_percentiles(cls, v: list[int]) -> list[int]:
        """Percentiles deben estar entre 1 y 99"""
        for p in v:
            if not (1 <= p <= 99):
                raise ValueError(f"Percentil {p} fuera de rango [1, 99]")
        return sorted(set(v))  # Ordenar y eliminar duplicados


class ResultadoReserva(BaseModel):
    """
    Resultado de cálculo de reservas.

    Contiene estimaciones de ultimate y reservas por año de origen.
    """

    metodo: MetodoReserva = Field(
        ...,
        description="Método utilizado para el cálculo",
    )
    reserva_total: Decimal = Field(
        ...,
        ge=0,
        description="Reserva total estimada",
    )
    ultimate_total: Decimal = Field(
        ...,
        ge=0,
        description="Estimación final total de siniestros",
    )
    pagado_total: Decimal = Field(
        ...,
        ge=0,
        description="Total pagado a la fecha",
    )

    # Por año de origen
    reservas_por_anio: dict[int, Decimal] = Field(
        default_factory=dict,
        description="Reservas estimadas por año de origen",
    )
    ultimates_por_anio: dict[int, Decimal] = Field(
        default_factory=dict,
        description="Ultimate estimado por año de origen",
    )

    # Factores de desarrollo (solo Chain Ladder y BF)
    factores_desarrollo: list[Decimal] | None = Field(
        default=None,
        description="Factores age-to-age calculados",
    )

    # Distribución (solo Bootstrap)
    percentiles: dict[int, Decimal] | None = Field(
        default=None,
        description="Percentiles de la distribución (solo Bootstrap)",
    )

    detalles: dict[str, Any] = Field(
        default_factory=dict,
        description="Detalles adicionales del cálculo",
    )

    @model_validator(mode="after")
    def validar_consistencia(self) -> "ResultadoReserva":
        """Validar que ultimate = pagado + reserva"""
        expected_ultimate = self.pagado_total + self.reserva_total
        # Permitir pequeña diferencia por redondeo
        if abs(self.ultimate_total - expected_ultimate) > Decimal("0.01"):
            raise ValueError(
                f"Inconsistencia: ultimate ({self.ultimate_total}) != "
                f"pagado ({self.pagado_total}) + reserva ({self.reserva_total})"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "metodo": "chain_ladder",
                    "reserva_total": "2500000.00",
                    "ultimate_total": "12500000.00",
                    "pagado_total": "10000000.00",
                    "reservas_por_anio": {
                        "2020": "100000.00",
                        "2021": "500000.00",
                        "2022": "900000.00",
                        "2023": "1000000.00",
                    },
                    "factores_desarrollo": ["1.20", "1.10", "1.05"],
                }
            ]
        }
    }


# ============================================================================
# MODELOS PARA RCS - REQUERIMIENTO DE CAPITAL DE SOLVENCIA (Fase 5A)
# ============================================================================


class TipoRiesgoRCS(StrEnum):
    """Tipos de riesgo para cálculo de RCS"""

    MORTALIDAD = "mortalidad"
    LONGEVIDAD = "longevidad"
    INVALIDEZ = "invalidez"
    GASTOS = "gastos"
    PRIMA = "prima"
    RESERVA = "reserva"
    MERCADO = "mercado"
    CREDITO = "credito"
    CONCENTRACION = "concentracion"


class TipoRamo(StrEnum):
    """Tipo de ramo para clasificación"""

    VIDA = "vida"
    DANOS = "danos"
    ACCIDENTES_SALUD = "accidentes_salud"


class ConfiguracionRCSVida(BaseModel):
    """
    Configuración para cálculo de RCS de suscripción en ramos de vida.

    El RCS de vida considera riesgos de:
    - Mortalidad: Muerte antes de lo esperado
    - Longevidad: Supervivencia mayor a la esperada
    - Invalidez: Incapacidad del asegurado
    - Gastos: Gastos de administración mayores a proyectados
    """

    suma_asegurada_total: Decimal = Field(
        ...,
        gt=0,
        description="Suma asegurada total de la cartera de vida",
    )
    reserva_matematica: Decimal = Field(
        ...,
        ge=0,
        description="Reserva matemática total (pasivo actuarial)",
    )
    edad_promedio_asegurados: int = Field(
        ...,
        ge=18,
        le=100,
        description="Edad promedio ponderada de asegurados",
    )
    duracion_promedio_polizas: int = Field(
        ...,
        ge=1,
        le=50,
        description="Duración promedio de pólizas en años",
    )
    numero_asegurados: int = Field(
        default=1000,
        ge=1,
        description="Número total de asegurados",
    )

    @field_validator("reserva_matematica")
    @classmethod
    def validar_reserva_vs_suma_asegurada(cls, v: Decimal, info) -> Decimal:
        """La reserva no debería exceder la suma asegurada"""
        if "suma_asegurada_total" in info.data:
            suma = info.data["suma_asegurada_total"]
            if v > suma * Decimal("2"):
                raise ValueError(
                    f"Reserva matemática ({v}) parece muy alta vs suma asegurada ({suma})"
                )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "suma_asegurada_total": "500000000.00",
                    "reserva_matematica": "350000000.00",
                    "edad_promedio_asegurados": 45,
                    "duracion_promedio_polizas": 15,
                    "numero_asegurados": 10000,
                }
            ]
        }
    }


class ConfiguracionRCSDanos(BaseModel):
    """
    Configuración para cálculo de RCS de suscripción en ramos de daños.

    El RCS de daños considera:
    - Riesgo de prima: Insuficiencia de primas vs siniestralidad
    - Riesgo de reserva: Insuficiencia de reservas de siniestros
    """

    primas_retenidas_12m: Decimal = Field(
        ...,
        gt=0,
        description="Primas retenidas (netas de reaseguro) últimos 12 meses",
    )
    reserva_siniestros: Decimal = Field(
        ...,
        ge=0,
        description="Reserva de siniestros pendientes",
    )
    coeficiente_variacion: Decimal = Field(
        default=Decimal("0.15"),
        ge=Decimal("0.05"),
        le=Decimal("0.50"),
        description="Coeficiente de variación histórico de siniestralidad",
    )
    numero_ramos: int = Field(
        default=1,
        ge=1,
        le=20,
        description="Número de ramos diferentes en cartera",
    )

    @field_validator("coeficiente_variacion")
    @classmethod
    def validar_coeficiente(cls, v: Decimal) -> Decimal:
        """CV típicamente entre 5% y 50%"""
        if v < Decimal("0.05"):
            raise ValueError(
                "Coeficiente de variación muy bajo (típicamente >= 5%)"
            )
        if v > Decimal("0.50"):
            raise ValueError(
                "Coeficiente de variación muy alto (típicamente <= 50%)"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "primas_retenidas_12m": "250000000.00",
                    "reserva_siniestros": "180000000.00",
                    "coeficiente_variacion": "0.15",
                    "numero_ramos": 5,
                }
            ]
        }
    }


class ConfiguracionRCSInversion(BaseModel):
    """
    Configuración para cálculo de RCS de inversión (riesgos de mercado).

    Considera riesgos de:
    - Mercado: Caída en valor de acciones, bonos, etc.
    - Crédito: Incumplimiento de emisores
    - Concentración: Exceso de exposición a un solo emisor
    """

    valor_acciones: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Valor de mercado de acciones",
    )
    valor_bonos_gubernamentales: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Valor de bonos gubernamentales",
    )
    valor_bonos_corporativos: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Valor de bonos corporativos",
    )
    valor_inmuebles: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Valor de bienes raíces",
    )
    duracion_promedio_bonos: Decimal = Field(
        default=Decimal("5.0"),
        ge=Decimal("0.5"),
        le=Decimal("30.0"),
        description="Duración promedio de cartera de bonos (años)",
    )
    calificacion_promedio_bonos: str = Field(
        default="AAA",
        description="Calificación crediticia promedio (AAA, AA, A, BBB, etc.)",
    )

    @field_validator("calificacion_promedio_bonos")
    @classmethod
    def validar_calificacion(cls, v: str) -> str:
        """Calificación debe ser válida"""
        calificaciones_validas = [
            "AAA",
            "AA",
            "A",
            "BBB",
            "BB",
            "B",
            "CCC",
            "CC",
            "C",
        ]
        if v not in calificaciones_validas:
            raise ValueError(
                f"Calificación '{v}' no válida. Debe ser una de: {calificaciones_validas}"
            )
        return v

    @model_validator(mode="after")
    def validar_total_inversiones(self) -> "ConfiguracionRCSInversion":
        """Debe haber al menos algunas inversiones"""
        total = (
            self.valor_acciones
            + self.valor_bonos_gubernamentales
            + self.valor_bonos_corporativos
            + self.valor_inmuebles
        )
        if total == 0:
            raise ValueError(
                "Debe especificar al menos un tipo de inversión con valor > 0"
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "valor_acciones": "50000000.00",
                    "valor_bonos_gubernamentales": "300000000.00",
                    "valor_bonos_corporativos": "150000000.00",
                    "valor_inmuebles": "100000000.00",
                    "duracion_promedio_bonos": "7.5",
                    "calificacion_promedio_bonos": "AA",
                }
            ]
        }
    }


class ResultadoRCS(BaseModel):
    """
    Resultado del cálculo completo de RCS.

    El RCS total se calcula agregando diferentes tipos de riesgo
    con una matriz de correlación para evitar doble conteo.
    """

    # RCS por tipo de riesgo (vida)
    rcs_mortalidad: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de mortalidad"
    )
    rcs_longevidad: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de longevidad"
    )
    rcs_invalidez: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de invalidez"
    )
    rcs_gastos: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de gastos"
    )

    # RCS por tipo de riesgo (daños)
    rcs_prima: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de prima"
    )
    rcs_reserva: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de reserva"
    )

    # RCS por tipo de riesgo (inversión)
    rcs_mercado: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de mercado"
    )
    rcs_credito: Decimal = Field(
        default=Decimal("0"), ge=0, description="RCS por riesgo de crédito"
    )
    rcs_concentracion: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="RCS por riesgo de concentración",
    )

    # Agregados por categoría
    rcs_suscripcion_vida: Decimal = Field(
        ..., ge=0, description="RCS total de suscripción vida"
    )
    rcs_suscripcion_danos: Decimal = Field(
        ..., ge=0, description="RCS total de suscripción daños"
    )
    rcs_inversion: Decimal = Field(
        ..., ge=0, description="RCS total de inversión"
    )

    # RCS total agregado
    rcs_total: Decimal = Field(
        ..., gt=0, description="RCS total (con correlaciones aplicadas)"
    )

    # Capital y solvencia
    capital_minimo_pagado: Decimal = Field(
        ..., gt=0, description="Capital mínimo pagado de la aseguradora"
    )
    excedente_solvencia: Decimal = Field(
        ..., description="Excedente o déficit de capital (puede ser negativo)"
    )
    ratio_solvencia: Decimal = Field(
        ..., gt=0, description="Ratio RCS/Capital (debe ser <= 1.0 para cumplir)"
    )
    cumple_regulacion: bool = Field(
        ..., description="True si cumple con RCS (capital >= RCS)"
    )

    # Desglose detallado
    desglose_por_riesgo: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Desglose detallado de RCS por cada tipo de riesgo",
    )

    @model_validator(mode="after")
    def validar_agregacion(self) -> "ResultadoRCS":
        """Validar que los agregados sean consistentes"""
        # Validar que RCS total >= cada componente
        if self.rcs_total < self.rcs_suscripcion_vida:
            raise ValueError(
                "RCS total no puede ser menor que RCS suscripción vida"
            )
        if self.rcs_total < self.rcs_suscripcion_danos:
            raise ValueError(
                "RCS total no puede ser menor que RCS suscripción daños"
            )
        if self.rcs_total < self.rcs_inversion:
            raise ValueError("RCS total no puede ser menor que RCS inversión")

        # Validar ratio de solvencia
        ratio_calculado = (
            self.rcs_total / self.capital_minimo_pagado
            if self.capital_minimo_pagado > 0
            else Decimal("999")
        )
        if abs(ratio_calculado - self.ratio_solvencia) > Decimal("0.01"):
            raise ValueError(
                f"Ratio de solvencia inconsistente: "
                f"calculado={ratio_calculado}, proporcionado={self.ratio_solvencia}"
            )

        # Validar cumplimiento
        cumple_esperado = self.capital_minimo_pagado >= self.rcs_total
        if cumple_esperado != self.cumple_regulacion:
            raise ValueError(
                f"cumple_regulacion inconsistente: capital={self.capital_minimo_pagado}, "
                f"RCS={self.rcs_total}, cumple={self.cumple_regulacion}"
            )

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rcs_mortalidad": "15000000.00",
                    "rcs_longevidad": "8000000.00",
                    "rcs_invalidez": "5000000.00",
                    "rcs_gastos": "3000000.00",
                    "rcs_prima": "20000000.00",
                    "rcs_reserva": "12000000.00",
                    "rcs_mercado": "25000000.00",
                    "rcs_credito": "8000000.00",
                    "rcs_concentracion": "5000000.00",
                    "rcs_suscripcion_vida": "28000000.00",
                    "rcs_suscripcion_danos": "30000000.00",
                    "rcs_inversion": "35000000.00",
                    "rcs_total": "75000000.00",
                    "capital_minimo_pagado": "100000000.00",
                    "excedente_solvencia": "25000000.00",
                    "ratio_solvencia": "0.75",
                    "cumple_regulacion": True,
                    "desglose_por_riesgo": {
                        "mortalidad": "15000000.00",
                        "longevidad": "8000000.00",
                        "prima": "20000000.00",
                        "mercado": "25000000.00",
                    },
                }
            ]
        }
    }
