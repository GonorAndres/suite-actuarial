"""
Modelos Pydantic para reservas técnicas según Circular S-11.4 CNSF.

Define estructuras de datos para cálculo y validación de reservas técnicas
que las aseguradoras deben constituir conforme a normativa mexicana.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from suite_actuarial.core.models.common import Sexo

#: Aviso que acompaña a todo resultado de Reserva Matemática. Viaja dentro de
#: `ResultadoRM` para que llegue a quien lee la cifra, no solo a quien lee el
#: código: un número sin su límite declarado se cita como si fuera válido.
DISCLAIMER_RM = (
    "AVISO: reserva prospectiva de primas netas, orientada a la Circular S-11.4 "
    "pero NO conforme a ella. Se calcula sobre la tabla de mortalidad "
    "suministrada (ver el campo tabla_mortalidad del resultado; la empaquetada "
    "es ilustrativa) y con prima NETA: no incorpora gastos de adquisición ni de "
    "administración, no reconoce caducidad ni rescates, no aplica el margen de "
    "riesgo ni la mejor estimación del método institucional, y no sustituye la "
    "nota técnica registrada ante la CNSF."
)


class MetodoCalculoRRC(StrEnum):
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
    def validar_devengada(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        """Prima devengada no puede exceder emitida"""
        if "prima_emitida" in info.data:
            if v > info.data["prima_emitida"]:
                raise ValueError("Prima devengada no puede exceder prima emitida")
        return v


class ConfiguracionRM(BaseModel):
    """
    Configuración para cálculo de Reserva Matemática (RM) prospectiva.

    Describe el contrato completo, no solo la foto de hoy: la edad de
    contratación y la edad alcanzada fijan la duración transcurrida, y el plazo
    de cobertura y el plazo de pago fijan lo que queda por delante. No hay
    edades ni plazos implícitos: la versión anterior de este modelo suponía en
    silencio una cobertura hasta los 85 años y un pago de primas hasta los 65,
    supuestos sin fuente que decidían la cifra.

    El sexo es obligatorio porque la tabla de mortalidad distingue por sexo y
    la reserva cambia con él.

    Ejemplo (seguro temporal a 20 años, prima pagadera 20 años):
        >>> config = ConfiguracionRM(
        ...     suma_asegurada=Decimal("1000000"),
        ...     edad_contratacion=40,
        ...     edad_asegurado=45,
        ...     sexo=Sexo.MASCULINO,
        ...     plazo_seguro_anios=20,
        ...     plazo_pago_anios=20,
        ...     tasa_interes_tecnico=Decimal("0.055"),
        ... )
    """

    edad_contratacion: int = Field(..., ge=0, le=120, description="Edad de emisión de la póliza")
    edad_asegurado: int = Field(..., ge=0, le=120, description="Edad alcanzada a la valuación")
    sexo: Sexo = Field(..., description="Sexo del asegurado; la tabla de mortalidad lo distingue")
    tasa_interes_tecnico: Decimal = Field(..., gt=0, le=Decimal("0.15"))

    # Seguro de vida (beneficio por fallecimiento)
    suma_asegurada: Decimal | None = Field(
        default=None, gt=0, description="Suma asegurada; obligatoria salvo en rentas"
    )
    plazo_seguro_anios: int | None = Field(
        default=None,
        ge=1,
        description="Plazo de cobertura en años desde la contratación; obligatorio salvo en rentas",
    )
    plazo_pago_anios: int | None = Field(
        default=None,
        ge=1,
        description="Plazo de pago de primas en años desde la contratación (por omisión, el plazo de cobertura)",
    )
    prima_nivelada_anual: Decimal | None = Field(
        default=None,
        ge=0,
        description=(
            "Prima neta nivelada anual del contrato. Si se omite, se determina "
            "por el principio de equivalencia a la edad de contratación."
        ),
    )

    # Renta vitalicia en curso de pago
    es_renta_vitalicia: bool = Field(default=False)
    monto_renta_mensual: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validar_contrato(self) -> "ConfiguracionRM":
        """Comprueba que el contrato descrito sea consistente y esté completo."""
        if self.edad_asegurado < self.edad_contratacion:
            raise ValueError("Edad actual no puede ser menor a edad de contratación")

        if self.es_renta_vitalicia:
            if self.monto_renta_mensual is None:
                raise ValueError("Se requiere monto_renta_mensual para rentas vitalicias")
            return self

        if self.suma_asegurada is None:
            raise ValueError("Se requiere suma_asegurada para un seguro de vida")
        plazo_seguro = self.plazo_seguro_anios
        if plazo_seguro is None:
            raise ValueError(
                "Se requiere plazo_seguro_anios: el plazo de cobertura es un dato del "
                "contrato, no un supuesto del modelo"
            )
        plazo_pago = self.plazo_pago_anios
        if plazo_pago is None:
            self.plazo_pago_anios = plazo_seguro
        elif plazo_pago > plazo_seguro:
            raise ValueError(
                f"El plazo de pago ({plazo_pago}) no puede exceder el plazo "
                f"de cobertura ({plazo_seguro})"
            )
        if self.edad_asegurado - self.edad_contratacion > plazo_seguro:
            raise ValueError(
                f"La duración transcurrida ({self.edad_asegurado - self.edad_contratacion} "
                f"años) excede el plazo de cobertura ({plazo_seguro}): la póliza "
                "ya venció y no tiene reserva que valuar"
            )
        return self

    @property
    def duracion_transcurrida(self) -> int:
        """Años cumplidos desde la contratación (t en la notación ₜV)."""
        return self.edad_asegurado - self.edad_contratacion


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
    Resultado del cálculo de Reserva Matemática prospectiva.

    Publica los dos componentes del método prospectivo por separado, la prima
    que se usó y los supuestos que fijan la cifra (tabla, sexo, edad terminal),
    porque una reserva sin ellos no es reproducible.

    `reserva_matematica` puede ser negativa: significa que el valor de las
    primas futuras excede el de los beneficios futuros, lo que ocurre cuando la
    prima nivelada suministrada es mayor que la prima neta de equivalencia.
    Truncarla a cero en silencio ocultaba esa información y rompía la recursión
    de Fackler. El importe que corresponde constituir en balance sí se trunca,
    y se publica aparte como `reserva_a_constituir`.

    Ejemplo:
        >>> resultado = ResultadoRM(
        ...     reserva_matematica=Decimal("450000"),
        ...     reserva_a_constituir=Decimal("450000"),
        ...     valor_presente_beneficios=Decimal("550000"),
        ...     valor_presente_primas=Decimal("100000"),
        ...     prima_neta_anual=Decimal("25000"),
        ...     factor_anualidad_primas=Decimal("4"),
        ...     edad_actuarial=45,
        ...     duracion_transcurrida=5,
        ...     sexo=Sexo.MASCULINO,
        ...     tabla_mortalidad="EMSSA-09",
        ...     edad_terminal_tabla=100,
        ... )
    """

    reserva_matematica: Decimal = Field(
        ..., description="ₜV prospectiva = VP(beneficios) - VP(primas); puede ser negativa"
    )
    reserva_a_constituir: Decimal = Field(
        ..., ge=0, description="max(ₜV, 0): importe a constituir en balance"
    )
    valor_presente_beneficios: Decimal = Field(..., ge=0)
    valor_presente_primas: Decimal = Field(..., ge=0)
    prima_neta_anual: Decimal = Field(..., ge=0, description="Prima nivelada anual usada")
    factor_anualidad_primas: Decimal = Field(
        ..., ge=0, description="ä de las primas pendientes a la edad alcanzada"
    )
    edad_actuarial: int = Field(..., ge=0, le=120)
    duracion_transcurrida: int = Field(..., ge=0)
    sexo: Sexo
    tabla_mortalidad: str
    edad_terminal_tabla: int = Field(
        ..., ge=0, description="ω de la tabla: edad donde se fuerza q = 1"
    )
    probabilidad_supervivencia_plazo: Decimal | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Probabilidad de sobrevivir el plazo de cobertura restante",
    )
    prima_determinada_por_equivalencia: bool = Field(default=False)
    disclaimer: str = Field(default=DISCLAIMER_RM)


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
