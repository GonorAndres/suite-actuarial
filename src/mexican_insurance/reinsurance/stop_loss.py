"""
Contrato de reaseguro Stop Loss (Limitación de Pérdidas).

Protege cuando la siniestralidad agregada de la cartera
excede un porcentaje objetivo (attachment point).
"""

from decimal import Decimal
from typing import Dict, List

from mexican_insurance.core.validators import (
    ResultadoReaseguro,
    Siniestro,
    StopLossConfig,
)
from mexican_insurance.reinsurance.base_reinsurance import ContratoReaseguro


class StopLoss(ContratoReaseguro):
    """
    Contrato Stop Loss (Limitación de Pérdidas).

    Características:
    - Protege cuando la siniestralidad agregada excede un umbral
    - Se activa cuando: siniestros_totales / primas_totales > attachment%
    - Cubre el exceso hasta un límite adicional
    - Se evalúa sobre toda la cartera (no por siniestro individual)

    Ejemplo:
        Contrato Stop Loss 80% xs 20% sobre $10M de primas
        - Attachment: 80% (se activa si siniestralidad > 80%)
        - Límite: 20% adicional (cubre hasta 100% total)
        - Primas sujetas: $10M

        Escenarios:
        - Siniestros $7M → 70% → No activa
        - Siniestros $9M → 90% → Activa:
          * Exceso: 10% (90% - 80%)
          * Recuperación: $1M (10% de $10M)
        - Siniestros $11M → 110% → Activa:
          * Exceso: 30% (110% - 80%)
          * Recuperación: $2M (20% de $10M, límite máximo)
    """

    def __init__(self, config: StopLossConfig):
        """
        Inicializa el contrato Stop Loss.

        Args:
            config: Configuración del contrato con attachment point y límite
        """
        super().__init__(config)
        self.config: StopLossConfig = config  # Type hint más específico

    def calcular_siniestralidad(
        self,
        siniestros_totales: Decimal,
        primas_totales: Decimal,
    ) -> Decimal:
        """
        Calcula el ratio de siniestralidad (loss ratio).

        Fórmula:
            siniestralidad = (siniestros_totales / primas_totales) * 100

        Args:
            siniestros_totales: Suma de todos los siniestros
            primas_totales: Suma de todas las primas

        Returns:
            Ratio de siniestralidad en porcentaje

        Raises:
            ValueError: Si las primas son cero
        """
        if primas_totales == 0:
            raise ValueError("Las primas totales no pueden ser cero")

        siniestralidad = (siniestros_totales / primas_totales) * Decimal(
            "100"
        )
        return siniestralidad

    def calcular_recuperacion(
        self,
        siniestros_totales: Decimal,
        primas_totales: Decimal,
    ) -> Decimal:
        """
        Calcula la recuperación del reasegurador.

        Lógica:
        1. Calcular siniestralidad real
        2. Si siniestralidad <= attachment_point: recuperación = 0
        3. Si siniestralidad > attachment_point:
           - exceso_porcentual = siniestralidad - attachment_point
           - exceso_monto = primas_totales * (exceso_porcentual / 100)
           - recuperación = min(exceso_monto, límite_monto)

        Args:
            siniestros_totales: Suma total de siniestros
            primas_totales: Suma total de primas (o primas sujetas)

        Returns:
            Monto a recuperar del reasegurador
        """
        # Calcular siniestralidad
        siniestralidad = self.calcular_siniestralidad(
            siniestros_totales, primas_totales
        )

        # Si no excede el attachment point, no hay recuperación
        if siniestralidad <= self.config.attachment_point:
            return Decimal("0")

        # Calcular exceso porcentual
        exceso_pct = siniestralidad - self.config.attachment_point

        # Convertir exceso a monto
        exceso_monto = primas_totales * (exceso_pct / Decimal("100"))

        # Calcular límite en monto
        limite_monto = primas_totales * (
            self.config.limite_cobertura / Decimal("100")
        )

        # Recuperación es el menor entre exceso y límite
        recuperacion = min(exceso_monto, limite_monto)

        return recuperacion

    def calcular_siniestralidad_neta(
        self,
        siniestros_totales: Decimal,
        primas_totales: Decimal,
        recuperacion: Decimal,
    ) -> Decimal:
        """
        Calcula la siniestralidad neta después del reaseguro.

        Fórmula:
            siniestralidad_neta = ((siniestros - recuperacion) / primas) * 100

        Args:
            siniestros_totales: Suma de siniestros
            primas_totales: Suma de primas
            recuperacion: Recuperación del reaseguro

        Returns:
            Ratio de siniestralidad neta en porcentaje
        """
        siniestros_netos = siniestros_totales - recuperacion

        if primas_totales == 0:
            return Decimal("0")

        siniestralidad_neta = (siniestros_netos / primas_totales) * Decimal(
            "100"
        )
        return siniestralidad_neta

    def calcular_prima_reaseguro(self) -> Decimal:
        """
        Calcula la prima del contrato de reaseguro.

        Método simplificado basado en tasa estimada.
        Típicamente 2-5% de las primas sujetas.

        En la práctica, se calcula con:
        - Simulaciones de siniestralidad
        - Experiencia histórica
        - Modelos estocásticos

        Returns:
            Prima estimada del contrato
        """
        # Tasa típica para Stop Loss: 3%
        tasa_estimada = Decimal("3")
        prima = self.config.primas_sujetas * (tasa_estimada / Decimal("100"))
        return prima

    def calcular_resultado_neto(
        self,
        primas_totales: Decimal,
        siniestros: List[Siniestro],
        prima_reaseguro_cobrada: Decimal = None,
    ) -> ResultadoReaseguro:
        """
        Calcula el resultado neto del contrato Stop Loss para un periodo.

        Args:
            primas_totales: Prima total de la cartera en el periodo
            siniestros: Lista de siniestros ocurridos en el periodo
            prima_reaseguro_cobrada: Prima pagada al reasegurador
                                     (si no se proporciona, se calcula)

        Returns:
            ResultadoReaseguro con el análisis completo
        """
        # Calcular siniestros totales
        siniestros_totales = sum(
            s.monto_bruto for s in siniestros if self.validar_siniestro(s)
        )

        # Calcular siniestralidad bruta
        siniestralidad_bruta = self.calcular_siniestralidad(
            siniestros_totales, primas_totales
        )

        # Calcular recuperación
        recuperacion = self.calcular_recuperacion(
            siniestros_totales, primas_totales
        )

        # Calcular siniestralidad neta
        siniestralidad_neta = self.calcular_siniestralidad_neta(
            siniestros_totales, primas_totales, recuperacion
        )

        # Prima de reaseguro
        if prima_reaseguro_cobrada is None:
            prima_reaseguro_cobrada = self.calcular_prima_reaseguro()

        # Siniestros retenidos
        siniestros_retenidos = siniestros_totales - recuperacion

        # Resultado neto para cedente:
        # Beneficio de reaseguro - prima pagada
        resultado_neto = recuperacion - prima_reaseguro_cobrada

        # Construir detalles
        detalles: Dict = {
            "attachment_point": f"{self.config.attachment_point}%",
            "limite_cobertura": f"{self.config.limite_cobertura}%",
            "primas_sujetas": str(self.config.primas_sujetas),
            "primas_totales": str(primas_totales),
            "siniestros_totales": str(siniestros_totales),
            "siniestralidad_bruta": f"{siniestralidad_bruta:.2f}%",
            "siniestralidad_neta": f"{siniestralidad_neta:.2f}%",
            "contrato_activado": recuperacion > 0,
            "numero_siniestros": len(siniestros),
            "siniestros_retenidos": str(siniestros_retenidos),
        }

        # Ratio de cesión basado en la recuperación sobre siniestros totales
        ratio_cesion = (
            (recuperacion / siniestros_totales * 100)
            if siniestros_totales > 0
            else Decimal("0")
        )

        return ResultadoReaseguro(
            tipo_contrato=self.config.tipo_contrato,
            monto_cedido=Decimal("0"),  # No aplica en Stop Loss
            monto_retenido=siniestros_retenidos,
            recuperacion_reaseguro=recuperacion,
            comision_recibida=Decimal("0"),  # No aplica en Stop Loss
            prima_reaseguro_pagada=prima_reaseguro_cobrada,
            ratio_cesion=ratio_cesion,
            resultado_neto_cedente=resultado_neto,
            detalles=detalles,
        )

    def __repr__(self) -> str:
        """Representación string del contrato"""
        return (
            f"StopLoss("
            f"attachment={self.config.attachment_point}%, "
            f"limit={self.config.limite_cobertura}%)"
        )
