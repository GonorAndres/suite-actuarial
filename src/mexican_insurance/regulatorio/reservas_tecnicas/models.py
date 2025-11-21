"""
Modelos Pydantic para reservas técnicas según Circular S-11.4 CNSF.

Define estructuras de datos para cálculo y validación de reservas técnicas
que las aseguradoras deben constituir conforme a normativa mexicana.
"""

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class MetodoCalculoRRC(str, Enum):
    """Métodos de cálculo para Reserva de Riesgos en Curso"""

    AVOS_365 = "365avos"  # Método de 365avos (estándar)
    PRIMA_NO_DEVENGADA = "prima_no_devengada"  # Prima no devengada
    ESTADISTICO = "estadistico"  # Método estadístico


class ConfiguracionRRC(BaseModel):
    """
    Configuración para cálculo de Reserva de Riesgos en Curso (RRC).

    La RRC es la reserva que debe constituirse para seguros de corto plazo
    (típicamente daños) para cubrir la parte no devengada de las primas.

    Ejemplo:
        >>> config = ConfiguracionRRC(
        ...     prima_emitida=Decimal("50000000"),
        ...     prima_devengada=Decimal("30000000"),
        ...     fecha_calculo=date(2024, 6, 30),
        ...     metodo=MetodoCalculoRRC.AVOS_365
        ... )
    """

    prima_emitida: Decimal = Field(..., gt=0, description="Prima emitida en el período")
    prima_devengada: Decimal = Field(..., ge=0, description="Prima ya devengada")
    fecha_calculo: date = Field(..., description="Fecha de cálculo de reserva")
    metodo: MetodoCalculoRRC = Field(
        default=MetodoCalculoRRC.AVOS_365, description="Método de cálculo"
    )

    # Opcional: para método 365avos detallado por póliza
    dias_promedio_vigencia: int | None = Field(
        default=365, ge=1, le=730, description="Días promedio de vigencia"
    )
    dias_promedio_transcurridos: int | None = Field(
        default=None, ge=0, description="Días promedio transcurridos desde emisión"
    )

    @field_validator("prima_devengada")
    @classmethod
    def validar_devengada(cls, v: Decimal, info) -> Decimal:
        """Prima devengada no puede exceder emitida"""
        if "prima_emitida" in info.data:
            if v > info.data["prima_emitida"]:
                raise ValueError("Prima devengada no puede exceder prima emitida")
        return v


class ConfiguracionRM(BaseModel):
    """
    Configuración para cálculo de Reserva Matemática (RM).

    La RM es la reserva para seguros de largo plazo (vida) calculada
    como el valor presente de obligaciones futuras menos primas futuras.

    Ejemplo:
        >>> config = ConfiguracionRM(
        ...     suma_asegurada=Decimal("1000000"),
        ...     edad_asegurado=45,
        ...     edad_contratacion=40,
        ...     tasa_interes_tecnico=Decimal("0.055"),
        ...     prima_nivelada_anual=Decimal("25000")
        ... )
    """

    suma_asegurada: Decimal = Field(..., gt=0)
    edad_asegurado: int = Field(..., ge=0, le=120)
    edad_contratacion: int = Field(..., ge=0, le=120)
    tasa_interes_tecnico: Decimal = Field(..., gt=0, le=Decimal("0.15"))
    prima_nivelada_anual: Decimal = Field(..., ge=0)

    # Para rentas vitalicias
    es_renta_vitalicia: bool = Field(default=False)
    monto_renta_mensual: Decimal | None = Field(default=None, ge=0)

    @field_validator("edad_asegurado")
    @classmethod
    def validar_edad(cls, v: int, info) -> int:
        """Edad actual no puede ser menor a edad de contratación"""
        if "edad_contratacion" in info.data:
            if v < info.data["edad_contratacion"]:
                raise ValueError(
                    "Edad actual no puede ser menor a edad de contratación"
                )
        return v


class ResultadoRRC(BaseModel):
    """
    Resultado del cálculo de Reserva de Riesgos en Curso.

    Ejemplo:
        >>> resultado = ResultadoRRC(
        ...     reserva_calculada=Decimal("20000000"),
        ...     prima_no_devengada=Decimal("20000000"),
        ...     porcentaje_reserva=Decimal("0.40"),
        ...     metodo_utilizado=MetodoCalculoRRC.AVOS_365
        ... )
    """

    reserva_calculada: Decimal = Field(..., ge=0)
    prima_no_devengada: Decimal = Field(..., ge=0)
    porcentaje_reserva: Decimal = Field(..., ge=0, le=1)
    metodo_utilizado: MetodoCalculoRRC
    dias_vigencia_promedio: int | None = Field(default=None)
    dias_transcurridos_promedio: int | None = Field(default=None)


class ResultadoRM(BaseModel):
    """
    Resultado del cálculo de Reserva Matemática.

    Ejemplo:
        >>> resultado = ResultadoRM(
        ...     reserva_matematica=Decimal("450000"),
        ...     valor_presente_beneficios=Decimal("550000"),
        ...     valor_presente_primas=Decimal("100000"),
        ...     edad_actuarial=45
        ... )
    """

    reserva_matematica: Decimal = Field(..., ge=0)
    valor_presente_beneficios: Decimal = Field(..., ge=0)
    valor_presente_primas: Decimal = Field(..., ge=0)
    edad_actuarial: int = Field(..., ge=0, le=120)
    probabilidad_supervivencia: Decimal | None = Field(default=None, ge=0, le=1)


class ResultadoValidacionSuficiencia(BaseModel):
    """
    Resultado de validación de suficiencia de reservas según S-11.4.

    La circular S-11.4 requiere que las reservas sean suficientes para
    cubrir las obligaciones futuras con un nivel de confianza adecuado.
    """

    reserva_constituida: Decimal = Field(..., ge=0)
    reserva_minima_requerida: Decimal = Field(..., ge=0)
    es_suficiente: bool
    deficit_superavit: Decimal  # Negativo = déficit, Positivo = superávit
    porcentaje_cobertura: Decimal = Field(..., ge=0)

    @property
    def requiere_constitucion_adicional(self) -> bool:
        """Indica si se requiere constituir reserva adicional"""
        return self.deficit_superavit < 0
