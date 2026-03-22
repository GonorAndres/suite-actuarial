"""
Contrato de reaseguro Excess of Loss (Exceso de Pérdida).

El reasegurador paga cuando un siniestro excede la retención,
hasta un límite máximo. Protege contra siniestros grandes.
"""

from decimal import Decimal

from suite_actuarial.core.validators import (
    ExcessOfLossConfig,
    ResultadoReaseguro,
    Siniestro,
)
from suite_actuarial.reaseguro.base_reinsurance import ContratoReaseguro


class ExcessOfLoss(ContratoReaseguro):
    """
    Contrato Excess of Loss (XL - Exceso de Pérdida).

    Características:
    - El reasegurador paga solo cuando un siniestro excede la retención
    - Cobertura hasta un límite máximo
    - Puede ser por riesgo (cada póliza) o por evento (catastrófico)
    - Permite reinstatements (reinstalar el límite después de usarlo)

    Ejemplo:
        Contrato XL 500 xs 200 (límite $500K, retención $200K)
        - Siniestro $150K → cedente paga $150K, reaseguro $0
        - Siniestro $400K → cedente paga $200K, reaseguro $200K
        - Siniestro $800K → cedente paga $200K, reaseguro $500K (límite)

    Notación estándar: "límite xs retención"
    Ejemplo: "500 xs 200" = límite de $500K en exceso de $200K de retención
    """

    def __init__(self, config: ExcessOfLossConfig):
        """
        Inicializa el contrato Excess of Loss.

        Args:
            config: Configuración del contrato con retención, límite y reinstatements
        """
        super().__init__(config)
        self.config: ExcessOfLossConfig = config  # Type hint más específico

        # Tracking de límite disponible (se reduce con siniestros)
        self.limite_disponible = config.limite
        self.reinstatements_usados = 0

    def calcular_recuperacion(self, siniestro: Siniestro) -> Decimal:
        """
        Calcula la recuperación del reasegurador para un siniestro.

        Fórmula:
            Si monto <= retención:
                recuperación = 0
            Si monto > retención:
                exceso = monto - retención
                recuperación = min(exceso, límite_disponible)

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

        # Si el siniestro no excede la retención, no hay recuperación
        if siniestro.monto_bruto <= self.config.retencion:
            return Decimal("0")

        # Calcular exceso sobre la retención
        exceso = siniestro.monto_bruto - self.config.retencion

        # Recuperación limitada al menor de: exceso o límite disponible
        recuperacion = min(exceso, self.limite_disponible)

        # Actualizar límite disponible
        self.limite_disponible -= recuperacion

        return recuperacion

    def calcular_recuperacion_multiple(
        self, siniestros: list[Siniestro]
    ) -> tuple[Decimal, list[tuple[str, Decimal, Decimal]]]:
        """
        Calcula la recuperación para múltiples siniestros.

        Procesa los siniestros en orden y va consumiendo el límite disponible.

        Args:
            siniestros: Lista de siniestros

        Returns:
            Tupla con:
            - Recuperación total
            - Lista de (id_siniestro, monto_bruto, recuperacion) para cada siniestro
        """
        recuperacion_total = Decimal("0")
        detalle = []

        for siniestro in siniestros:
            if self.validar_siniestro(siniestro):
                recup = self.calcular_recuperacion(siniestro)
                recuperacion_total += recup
                detalle.append(
                    (siniestro.id_siniestro, siniestro.monto_bruto, recup)
                )

        return recuperacion_total, detalle

    def aplicar_reinstatement(
        self, monto_usado: Decimal
    ) -> tuple[bool, Decimal]:
        """
        Aplica un reinstatement para reinstalar el límite consumido.

        Los reinstatements permiten "recargar" el límite del contrato
        después de haberlo usado. Típicamente se cobra una prima proporcional.

        Args:
            monto_usado: Monto del límite que se quiere reinstalar

        Returns:
            Tupla con:
            - bool: True si se aplicó el reinstatement exitosamente
            - Decimal: Prima adicional a pagar por el reinstatement

        Raises:
            ValueError: Si no quedan reinstatements disponibles
        """
        if self.reinstatements_usados >= self.config.numero_reinstatements:
            raise ValueError("No quedan reinstatements disponibles")

        # Reinstalar el límite (parcial o total)
        monto_reinstalado = min(monto_usado, self.config.limite)
        self.limite_disponible += monto_reinstalado
        self.reinstatements_usados += 1

        # Prima proporcional: (monto_reinstalado / límite) * prima_original
        # Simplificado: tasa_prima * monto_reinstalado / 100
        prima_adicional = (
            monto_reinstalado * self.config.tasa_prima / Decimal("100")
        )

        return True, prima_adicional

    def obtener_limite_disponible(self) -> Decimal:
        """
        Consulta cuánto límite queda disponible.

        Returns:
            Monto de límite disponible
        """
        return self.limite_disponible

    def obtener_reinstatements_disponibles(self) -> int:
        """
        Consulta cuántos reinstatements quedan disponibles.

        Returns:
            Número de reinstatements disponibles
        """
        return self.config.numero_reinstatements - self.reinstatements_usados

    def resetear_limite(self) -> None:
        """
        Resetea el límite disponible y reinstatements.

        Útil para simular un nuevo periodo o para testing.
        """
        self.limite_disponible = self.config.limite
        self.reinstatements_usados = 0

    def calcular_prima_reaseguro(self) -> Decimal:
        """
        Calcula la prima del contrato de reaseguro.

        Método simplificado usando burning cost approach:
            prima = límite * tasa_prima / 100

        En la práctica, esto se ajustaría con:
        - Experiencia siniestral histórica
        - Distribución de severidad
        - Simulaciones de Monte Carlo

        Returns:
            Prima anual del contrato XL
        """
        prima = self.config.limite * (self.config.tasa_prima / Decimal("100"))
        return prima

    def calcular_resultado_neto(
        self,
        prima_reaseguro_cobrada: Decimal,
        siniestros: list[Siniestro],
    ) -> ResultadoReaseguro:
        """
        Calcula el resultado neto del contrato XL para un periodo.

        En XL, el flujo es diferente a Quota Share:
        - No se ceden primas proporcionalmente
        - Se paga una prima fija por el contrato
        - Se recuperan solo los siniestros que exceden la retención

        Args:
            prima_reaseguro_cobrada: Prima pagada al reasegurador
            siniestros: Lista de siniestros ocurridos en el periodo

        Returns:
            ResultadoReaseguro con el análisis completo
        """
        # Calcular siniestros totales
        siniestros_totales = sum(
            s.monto_bruto for s in siniestros if self.validar_siniestro(s)
        )

        # Calcular recuperaciones
        # Nota: esto consume el límite disponible
        recuperacion, detalle_siniestros = self.calcular_recuperacion_multiple(
            siniestros
        )

        # Siniestros retenidos = siniestros totales - recuperación
        siniestros_retenidos = siniestros_totales - recuperacion

        # Resultado neto para cedente:
        # - Paga: prima de reaseguro + siniestros retenidos
        # + Recibe: recuperación
        # Neto = recuperación - prima_reaseguro - siniestros_retenidos
        resultado_neto = recuperacion - prima_reaseguro_cobrada

        # Construir detalles
        detalles = {
            "retencion": str(self.config.retencion),
            "limite_original": str(self.config.limite),
            "limite_disponible": str(self.limite_disponible),
            "modalidad": self.config.modalidad.value,
            "numero_reinstatements": self.config.numero_reinstatements,
            "reinstatements_usados": self.reinstatements_usados,
            "siniestros_totales": str(siniestros_totales),
            "siniestros_retenidos": str(siniestros_retenidos),
            "numero_siniestros": len(siniestros),
            "detalle_siniestros": [
                {
                    "id": id_sin,
                    "monto": str(monto),
                    "recuperacion": str(recup),
                }
                for id_sin, monto, recup in detalle_siniestros
            ],
        }

        # En XL, monto_cedido y ratio_cesion no aplican de la misma forma
        # que en Quota Share. Usamos valores dummy para cumplir con el modelo.
        ratio_cesion = (
            (recuperacion / siniestros_totales * 100)
            if siniestros_totales > 0
            else Decimal("0")
        )

        return ResultadoReaseguro(
            tipo_contrato=self.config.tipo_contrato,
            monto_cedido=Decimal("0"),  # No aplica en XL
            monto_retenido=siniestros_retenidos,
            recuperacion_reaseguro=recuperacion,
            comision_recibida=Decimal("0"),  # No aplica en XL
            prima_reaseguro_pagada=prima_reaseguro_cobrada,
            ratio_cesion=ratio_cesion,
            resultado_neto_cedente=resultado_neto,
            detalles=detalles,
        )

    def __repr__(self) -> str:
        """Representación string del contrato"""
        return (
            f"ExcessOfLoss("
            f"{self.config.limite} xs {self.config.retencion}, "
            f"modalidad={self.config.modalidad.value})"
        )
