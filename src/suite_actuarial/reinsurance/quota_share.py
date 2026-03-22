"""
Contrato de reaseguro Quota Share (Cuota Parte).

El tipo más simple de reaseguro proporcional donde el reasegurador
acepta un porcentaje fijo de todas las pólizas.
"""

from decimal import Decimal

from suite_actuarial.core.validators import (
    QuotaShareConfig,
    ResultadoReaseguro,
    Siniestro,
)
from suite_actuarial.reinsurance.base_reinsurance import ContratoReaseguro


class QuotaShare(ContratoReaseguro):
    """
    Contrato Quota Share (Cuota Parte).

    Características:
    - El reasegurador acepta un % fijo de cada riesgo
    - Recibe el mismo % de las primas
    - Paga el mismo % de los siniestros
    - Paga una comisión a la cedente por los gastos de adquisición

    Ejemplo:
        Si el contrato es 30% quota share con 25% de comisión:
        - Prima: $100,000
        - Prima cedida: $30,000 (30%)
        - Prima retenida: $70,000
        - Comisión recibida: $7,500 (25% de $30,000)

        Si hay un siniestro de $50,000:
        - Siniestro cedido: $15,000 (30%)
        - Siniestro retenido: $35,000
    """

    def __init__(self, config: QuotaShareConfig):
        """
        Inicializa el contrato Quota Share.

        Args:
            config: Configuración del contrato con % de cesión y comisiones
        """
        super().__init__(config)
        self.config: QuotaShareConfig = config  # Type hint más específico

    def calcular_prima_cedida(self, prima_bruta: Decimal) -> Decimal:
        """
        Calcula la prima que se cede al reasegurador.

        Fórmula:
            prima_cedida = prima_bruta * (porcentaje_cesion / 100)

        Args:
            prima_bruta: Prima total de la póliza o cartera

        Returns:
            Monto de prima cedida al reasegurador
        """
        return prima_bruta * (self.config.porcentaje_cesion / Decimal("100"))

    def calcular_prima_retenida(self, prima_bruta: Decimal) -> Decimal:
        """
        Calcula la prima que retiene la cedente.

        Fórmula:
            prima_retenida = prima_bruta * (1 - porcentaje_cesion / 100)

        Args:
            prima_bruta: Prima total de la póliza o cartera

        Returns:
            Monto de prima retenida por la cedente
        """
        prima_cedida = self.calcular_prima_cedida(prima_bruta)
        return prima_bruta - prima_cedida

    def calcular_comision(self, prima_cedida: Decimal) -> Decimal:
        """
        Calcula la comisión total que el reasegurador paga a la cedente.

        La comisión compensa los gastos de adquisición y administración
        que la cedente tuvo para generar el negocio.

        Fórmula:
            comision_base = prima_cedida * (comision_reaseguro / 100)
            comision_override = prima_cedida * (comision_override / 100)
            comision_total = comision_base + comision_override

        Args:
            prima_cedida: Monto de prima cedida al reasegurador

        Returns:
            Comisión total a recibir del reasegurador
        """
        comision_base = prima_cedida * (
            self.config.comision_reaseguro / Decimal("100")
        )
        comision_override = prima_cedida * (
            self.config.comision_override / Decimal("100")
        )
        return comision_base + comision_override

    def calcular_recuperacion(self, siniestro: Siniestro) -> Decimal:
        """
        Calcula la recuperación del reasegurador para un siniestro.

        En Quota Share, la recuperación es simplemente el % de cesión
        aplicado al monto del siniestro.

        Fórmula:
            recuperacion = monto_siniestro * (porcentaje_cesion / 100)

        Args:
            siniestro: Siniestro para el cual calcular recuperación

        Returns:
            Monto a recuperar del reasegurador

        Raises:
            ValueError: Si el siniestro no está dentro de vigencia
        """
        if not self.validar_siniestro(siniestro):
            raise ValueError(
                f"Siniestro {siniestro.id_siniestro} fuera de vigencia del contrato"
            )

        return siniestro.monto_bruto * (
            self.config.porcentaje_cesion / Decimal("100")
        )

    def calcular_recuperacion_multiple(
        self, siniestros: list[Siniestro]
    ) -> tuple[Decimal, list[tuple[str, Decimal]]]:
        """
        Calcula la recuperación para múltiples siniestros.

        Args:
            siniestros: Lista de siniestros

        Returns:
            Tupla con:
            - Recuperación total
            - Lista de (id_siniestro, recuperacion) para cada siniestro
        """
        recuperacion_total = Decimal("0")
        detalle = []

        for siniestro in siniestros:
            if self.validar_siniestro(siniestro):
                recup = self.calcular_recuperacion(siniestro)
                recuperacion_total += recup
                detalle.append((siniestro.id_siniestro, recup))

        return recuperacion_total, detalle

    def calcular_prima_reaseguro(self) -> Decimal:
        """
        En Quota Share, la prima de reaseguro es la prima cedida
        menos la comisión.

        Este método requiere conocer las primas de la cartera,
        así que se calcula normalmente en calcular_resultado_neto.

        Returns:
            Decimal("0") - se calcula en el contexto específico
        """
        # Este método no es aplicable sin conocer las primas
        # Se implementa en calcular_resultado_neto
        return Decimal("0")

    def calcular_resultado_neto(
        self,
        prima_bruta: Decimal,
        siniestros: list[Siniestro],
    ) -> ResultadoReaseguro:
        """
        Calcula el resultado neto del contrato para un periodo.

        Proceso:
        1. Calcular prima cedida y retenida
        2. Calcular comisión recibida del reasegurador
        3. Calcular siniestros cedidos y retenidos
        4. Calcular resultado neto para la cedente

        Args:
            prima_bruta: Prima total de la cartera en el periodo
            siniestros: Lista de siniestros ocurridos en el periodo

        Returns:
            ResultadoReaseguro con el análisis completo
        """
        # Paso 1: Primas
        prima_cedida = self.calcular_prima_cedida(prima_bruta)
        prima_retenida = self.calcular_prima_retenida(prima_bruta)

        # Paso 2: Comisión
        comision = self.calcular_comision(prima_cedida)

        # Paso 3: Siniestros
        siniestros_totales = sum(
            s.monto_bruto for s in siniestros if self.validar_siniestro(s)
        )
        recuperacion, detalle_siniestros = self.calcular_recuperacion_multiple(
            siniestros
        )
        siniestros_retenidos = siniestros_totales - recuperacion

        # Paso 4: Resultado neto
        # Prima retenida + comisión - siniestros retenidos
        resultado_neto = prima_retenida + comision - siniestros_retenidos

        # Construir detalles
        detalles = {
            "porcentaje_cesion": f"{self.config.porcentaje_cesion}%",
            "comision_pct": f"{self.config.comision_reaseguro + self.config.comision_override}%",
            "prima_bruta": str(prima_bruta),
            "prima_cedida": str(prima_cedida),
            "prima_retenida": str(prima_retenida),
            "comision_recibida": str(comision),
            "siniestros_totales": str(siniestros_totales),
            "siniestros_cedidos": str(recuperacion),
            "siniestros_retenidos": str(siniestros_retenidos),
            "numero_siniestros": len(siniestros),
            "detalle_siniestros": [
                {"id": id_sin, "recuperacion": str(recup)}
                for id_sin, recup in detalle_siniestros
            ],
        }

        # Calcular ratio de cesión
        if prima_bruta > 0:
            ratio_cesion = (prima_cedida / prima_bruta) * 100
        else:
            ratio_cesion = Decimal("0")

        # Resultado neto ya calculado arriba
        # No usamos generar_resultado porque su fórmula no aplica para Quota Share

        return ResultadoReaseguro(
            tipo_contrato=self.config.tipo_contrato,
            monto_cedido=prima_cedida,
            monto_retenido=prima_retenida,
            recuperacion_reaseguro=recuperacion,
            comision_recibida=comision,
            prima_reaseguro_pagada=prima_cedida,
            ratio_cesion=ratio_cesion,
            resultado_neto_cedente=resultado_neto,
            detalles=detalles,
        )

    def __repr__(self) -> str:
        """Representación string del contrato"""
        return (
            f"QuotaShare("
            f"cesión={self.config.porcentaje_cesion}%, "
            f"comisión={self.config.comision_reaseguro}%)"
        )
