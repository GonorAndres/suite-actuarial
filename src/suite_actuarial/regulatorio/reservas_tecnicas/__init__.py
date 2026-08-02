"""
Módulo de reservas técnicas, orientado a la Circular S-11.4 CNSF.

Reproduce, de forma simplificada y con fines didácticos, el tipo de reservas
técnicas que las aseguradoras deben constituir bajo la normativa mexicana. No
certifica conformidad regulatoria: los métodos aquí implementados no son la
nota técnica registrada ni el método institucional de valuación.

Componentes principales:
- CalculadoraRRC: Reserva de Riesgos en Curso (seguros corto plazo)
- CalculadoraRM: Reserva Matemática prospectiva de primas netas (vida). Emite
  `ExperimentalModelWarning` y publica `DISCLAIMER_RM` dentro del resultado.
- ValidadorSuficiencia: Validación de suficiencia de reservas

Ejemplo de uso:
    >>> from decimal import Decimal
    >>> from datetime import date
    >>> from suite_actuarial.regulatorio.reservas_tecnicas import (
    ...     ConfiguracionRRC,
    ...     CalculadoraRRC
    ... )
    >>>
    >>> config = ConfiguracionRRC(
    ...     prima_emitida=Decimal("100000000"),
    ...     prima_devengada=Decimal("60000000"),
    ...     fecha_calculo=date(2024, 6, 30)
    ... )
    >>> calc = CalculadoraRRC(config)
    >>> resultado = calc.calcular()
    >>> print(f"RRC: ${resultado.reserva_calculada:,.0f}")
"""

from suite_actuarial.regulatorio.reservas_tecnicas.models import (
    DISCLAIMER_RM,
    ConfiguracionRM,
    ConfiguracionRRC,
    MetodoCalculoRRC,
    ResultadoRM,
    ResultadoRRC,
    ResultadoValidacionSuficiencia,
)
from suite_actuarial.regulatorio.reservas_tecnicas.reserva_matematica import (
    CalculadoraRM,
)
from suite_actuarial.regulatorio.reservas_tecnicas.reserva_riesgos_curso import (
    CalculadoraRRC,
)
from suite_actuarial.regulatorio.reservas_tecnicas.validador_suficiencia import (
    ValidadorSuficiencia,
)

__all__ = [
    # Modelos
    "ConfiguracionRRC",
    "ConfiguracionRM",
    "MetodoCalculoRRC",
    "ResultadoRRC",
    "ResultadoRM",
    "ResultadoValidacionSuficiencia",
    # Calculadoras
    "CalculadoraRRC",
    "CalculadoraRM",
    # Validadores
    "ValidadorSuficiencia",
    # Avisos
    "DISCLAIMER_RM",
]
