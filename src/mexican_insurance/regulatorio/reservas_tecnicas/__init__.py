"""
Módulo de reservas técnicas según Circular S-11.4 CNSF.

Proporciona cálculo y validación de reservas técnicas que las aseguradoras
deben constituir conforme a la normativa mexicana.

Componentes principales:
- CalculadoraRRC: Reserva de Riesgos en Curso (seguros corto plazo)
- CalculadoraRM: Reserva Matemática (seguros largo plazo/vida)
- ValidadorSuficiencia: Validación de suficiencia de reservas

Ejemplo de uso:
    >>> from decimal import Decimal
    >>> from datetime import date
    >>> from mexican_insurance.regulatorio.reservas_tecnicas import (
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

from mexican_insurance.regulatorio.reservas_tecnicas.models import (
    ConfiguracionRM,
    ConfiguracionRRC,
    MetodoCalculoRRC,
    ResultadoRM,
    ResultadoRRC,
    ResultadoValidacionSuficiencia,
)
from mexican_insurance.regulatorio.reservas_tecnicas.reserva_matematica import (
    CalculadoraRM,
)
from mexican_insurance.regulatorio.reservas_tecnicas.reserva_riesgos_curso import (
    CalculadoraRRC,
)
from mexican_insurance.regulatorio.reservas_tecnicas.validador_suficiencia import (
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
]
