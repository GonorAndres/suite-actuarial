"""
Clase base abstracta para contratos de reaseguro.

Define la interfaz que todos los contratos de reaseguro deben implementar.
Usa el patrón Template Method para compartir lógica común.
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import List

from mexican_insurance.core.validators import (
    ConfiguracionReaseguro,
    ResultadoReaseguro,
    Siniestro,
    TipoContrato,
)


class ContratoReaseguro(ABC):
    """
    Clase base abstracta para todos los contratos de reaseguro.

    Implementa el patrón Template Method:
    - Métodos abstractos: calcular_recuperacion, calcular_prima_reaseguro
    - Métodos concretos: validar_siniestro, validar_vigencia, generar_resultado

    Cada tipo de contrato (Quota Share, XL, Stop Loss) hereda de esta clase
    e implementa su propia lógica de recuperación.
    """

    def __init__(self, config: ConfiguracionReaseguro):
        """
        Inicializa el contrato con su configuración.

        Args:
            config: Configuración del contrato (QuotaShareConfig, XLConfig, etc.)

        Raises:
            ValueError: Si la configuración es inválida
        """
        self.config = config
        self._validar_config()

    def _validar_config(self) -> None:
        """
        Valida que la configuración sea correcta.

        Pydantic ya hace la validación básica, pero aquí podemos agregar
        validaciones adicionales específicas del negocio.
        """
        # Validar que las fechas sean coherentes
        if self.config.vigencia_fin <= self.config.vigencia_inicio:
            raise ValueError(
                "La fecha de fin debe ser posterior a la de inicio"
            )

    def validar_siniestro(self, siniestro: Siniestro) -> bool:
        """
        Valida que un siniestro esté dentro de la vigencia del contrato.

        Args:
            siniestro: Siniestro a validar

        Returns:
            True si el siniestro está dentro de vigencia, False si no
        """
        return (
            self.config.vigencia_inicio
            <= siniestro.fecha_ocurrencia
            <= self.config.vigencia_fin
        )

    def validar_vigencia(self, fecha: date) -> bool:
        """
        Valida que una fecha esté dentro de la vigencia del contrato.

        Args:
            fecha: Fecha a validar

        Returns:
            True si la fecha está dentro de vigencia, False si no
        """
        return self.config.vigencia_inicio <= fecha <= self.config.vigencia_fin

    @abstractmethod
    def calcular_recuperacion(self, *args, **kwargs) -> Decimal:
        """
        Calcula la recuperación del reasegurador para un siniestro o cartera.

        Este método debe ser implementado por cada tipo de contrato.

        Returns:
            Monto a recuperar del reasegurador
        """
        pass

    @abstractmethod
    def calcular_prima_reaseguro(self) -> Decimal:
        """
        Calcula la prima a pagar al reasegurador.

        Este método debe ser implementado por cada tipo de contrato.

        Returns:
            Prima del contrato de reaseguro
        """
        pass

    def generar_resultado(
        self,
        monto_total: Decimal,
        monto_cedido: Decimal,
        recuperacion: Decimal,
        comision: Decimal = Decimal("0"),
        prima_pagada: Decimal = Decimal("0"),
        detalles: dict = None,
    ) -> ResultadoReaseguro:
        """
        Genera un objeto ResultadoReaseguro con la información del cálculo.

        Método auxiliar para estandarizar la creación de resultados.

        Args:
            monto_total: Monto total (prima o siniestro)
            monto_cedido: Monto cedido al reasegurador
            recuperacion: Monto recuperado del reasegurador
            comision: Comisión recibida del reasegurador
            prima_pagada: Prima pagada al reasegurador
            detalles: Diccionario con detalles adicionales

        Returns:
            Objeto ResultadoReaseguro completo
        """
        monto_retenido = monto_total - monto_cedido

        # Calcular ratio de cesión
        if monto_total > 0:
            ratio_cesion = (monto_cedido / monto_total) * 100
        else:
            ratio_cesion = Decimal("0")

        # Resultado neto = monto retenido + comisión - prima pagada + recuperación
        # Para primas: retenido + comisión - prima_reaseguro
        # Para siniestros: -retenido + recuperacion
        resultado_neto = (
            monto_retenido + comision - prima_pagada + recuperacion
        )

        return ResultadoReaseguro(
            tipo_contrato=self.config.tipo_contrato,
            monto_cedido=monto_cedido,
            monto_retenido=monto_retenido,
            recuperacion_reaseguro=recuperacion,
            comision_recibida=comision,
            prima_reaseguro_pagada=prima_pagada,
            ratio_cesion=ratio_cesion,
            resultado_neto_cedente=resultado_neto,
            detalles=detalles or {},
        )

    def __repr__(self) -> str:
        """Representación string del contrato"""
        return (
            f"{self.__class__.__name__}("
            f"tipo={self.config.tipo_contrato}, "
            f"vigencia={self.config.vigencia_inicio} a {self.config.vigencia_fin})"
        )
