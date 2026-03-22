"""
Módulo de validaciones fiscales SAT para seguros.

Este módulo implementa las validaciones fiscales requeridas por el SAT
(Servicio de Administración Tributaria) para operaciones de seguros en México.

Componentes:
    - ValidadorPrimasDeducibles: Valida deducibilidad de primas para ISR
    - ValidadorSiniestrosGravables: Determina gravabilidad de siniestros
    - CalculadoraRetencionesISR: Calcula retenciones de ISR en pagos

Modelos:
    - TipoSeguroFiscal: Enum con tipos de seguros fiscales
    - ResultadoDeducibilidadPrima: Resultado de validación de deducibilidad
    - ResultadoGravabilidadSiniestro: Resultado de validación de gravabilidad
    - ResultadoRetencion: Resultado de cálculo de retenciones

Ejemplo:
    >>> from suite_actuarial.regulatorio.validaciones_sat import (
    ...     ValidadorPrimasDeducibles,
    ...     TipoSeguroFiscal
    ... )
    >>> from decimal import Decimal
    >>>
    >>> validador = ValidadorPrimasDeducibles(uma_anual=Decimal("37500"))
    >>> resultado = validador.validar_deducibilidad(
    ...     tipo_seguro=TipoSeguroFiscal.GASTOS_MEDICOS,
    ...     monto_prima=Decimal("50000"),
    ...     es_persona_fisica=True
    ... )
    >>> print(f"Deducible: ${resultado.monto_deducible:,.0f}")
"""

from suite_actuarial.regulatorio.validaciones_sat.models import (
    ResultadoDeducibilidadPrima,
    ResultadoGravabilidadSiniestro,
    ResultadoIVA,
    ResultadoRetencion,
    TipoSeguroFiscal,
)
from suite_actuarial.regulatorio.validaciones_sat.validador_primas import (
    ValidadorPrimasDeducibles,
)
from suite_actuarial.regulatorio.validaciones_sat.validador_retenciones import (
    CalculadoraRetencionesISR,
)
from suite_actuarial.regulatorio.validaciones_sat.validador_siniestros import (
    ValidadorSiniestrosGravables,
)

__all__ = [
    # Modelos
    "TipoSeguroFiscal",
    "ResultadoDeducibilidadPrima",
    "ResultadoGravabilidadSiniestro",
    "ResultadoRetencion",
    "ResultadoIVA",
    # Validadores
    "ValidadorPrimasDeducibles",
    "ValidadorSiniestrosGravables",
    "CalculadoraRetencionesISR",
]
