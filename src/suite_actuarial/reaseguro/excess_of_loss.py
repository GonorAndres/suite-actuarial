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

    Límite por ocurrencia y límite agregado
    ---------------------------------------
    El `limite` es el máximo que el reasegurador paga **por ocurrencia**. Las
    reinstalaciones determinan cuántas veces puede reponerse esa capacidad, así
    que el tope del periodo es

        límite agregado = límite * (1 + número de reinstalaciones)

    Sin reinstalaciones, el contrato cubre una sola pérdida de tamaño completo.
    Con una reinstalación, dos; y así sucesivamente. La versión anterior erosionaba
    un único límite compartido entre todas las ocurrencias y nunca aplicaba las
    reinstalaciones, de modo que "5M xs 5M con 1 reinstalación" frente a dos
    pérdidas de 12M cedía 5M en vez de 10M (hallazgo A4 de `docs/AUDIT.md`).
    """

    def __init__(self, config: ExcessOfLossConfig):
        """
        Inicializa el contrato Excess of Loss.

        Args:
            config: Configuración del contrato con retención, límite y reinstatements
        """
        super().__init__(config)
        self.config: ExcessOfLossConfig = config  # Type hint más específico

        # El agregado del periodo: la capacidad inicial mas las reinstalaciones.
        self.limite_agregado = config.limite * (
            Decimal("1") + Decimal(config.numero_reinstatements)
        )
        self.limite_disponible = self.limite_agregado
        self.recuperacion_acumulada = Decimal("0")

    @property
    def reinstatements_usados(self) -> int:
        """Reinstalaciones consumidas por la erosión acumulada del agregado.

        Se consume una reinstalación por cada límite completo erosionado: la
        primera capacidad la paga la prima original, y a partir de ahí cada
        límite adicional requiere reponer el anterior.
        """
        if self.config.limite <= 0:
            return 0
        completos = int(self.recuperacion_acumulada / self.config.limite)
        return min(completos, self.config.numero_reinstatements)

    def calcular_recuperacion(self, siniestro: Siniestro) -> Decimal:
        """
        Calcula la recuperación del reasegurador para un siniestro.

        Fórmula:
            Si monto <= retención:
                recuperación = 0
            Si monto > retención:
                exceso = monto - retención
                por_ocurrencia = min(exceso, límite)
                recuperación = min(por_ocurrencia, agregado disponible)

        El tope por ocurrencia y el agregado son restricciones distintas: la
        primera acota cada siniestro al ancho de la capa; la segunda acota la
        suma del periodo al límite reinstalable.

        Args:
            siniestro: Siniestro para el cual calcular recuperación

        Returns:
            Monto a recuperar del reasegurador

        Raises:
            ValueError: Si el siniestro no está dentro de vigencia
        """
        if not self.validar_siniestro(siniestro):
            raise ValueError(f"Siniestro {siniestro.id_siniestro} fuera de vigencia del contrato")

        # Si el siniestro no excede la retención, no hay recuperación
        if siniestro.monto_bruto <= self.config.retencion:
            return Decimal("0")

        # Calcular exceso sobre la retención
        exceso = siniestro.monto_bruto - self.config.retencion

        # Tope por ocurrencia: el ancho de la capa
        por_ocurrencia = min(exceso, self.config.limite)

        # Tope agregado del periodo
        recuperacion = min(por_ocurrencia, self.limite_disponible)

        # Erosionar el agregado
        self.limite_disponible -= recuperacion
        self.recuperacion_acumulada += recuperacion

        return recuperacion

    def calcular_prima_reinstalacion(self) -> Decimal:
        """
        Prima de reinstalación devengada por la erosión del agregado.

        Convención implementada: **pro rata a la cantidad, al 100%**. Cada peso
        de límite repuesto cuesta la misma proporción de la prima base:

            prima_reinstalacion = (monto repuesto / límite) * prima base

        donde el monto repuesto es la erosión acumulada acotada por la capacidad
        reinstalable (`límite * número de reinstalaciones`).

        Simplificación declarada: no se aplica prorrateo *temporal* (pro rata a
        tiempo), que en el mercado ajusta la prima por la fracción de vigencia
        restante al momento de la pérdida, ni tasas de reinstalación distintas
        de 100% por cada reinstalación sucesiva.

        Returns:
            Prima adicional a pagar por las reinstalaciones consumidas
        """
        if self.config.numero_reinstatements == 0 or self.config.limite <= 0:
            return Decimal("0")

        capacidad_reinstalable = self.config.limite * Decimal(self.config.numero_reinstatements)
        monto_repuesto = min(self.recuperacion_acumulada, capacidad_reinstalable)

        return (monto_repuesto / self.config.limite) * self.calcular_prima_reaseguro()

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
                detalle.append((siniestro.id_siniestro, siniestro.monto_bruto, recup))

        return recuperacion_total, detalle

    def obtener_limite_disponible(self) -> Decimal:
        """
        Consulta cuánto agregado queda disponible en el periodo.

        Returns:
            Monto de límite agregado disponible
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
        Resetea el agregado disponible y la erosión acumulada.

        Útil para simular un nuevo periodo o para testing.
        """
        self.limite_disponible = self.limite_agregado
        self.recuperacion_acumulada = Decimal("0")

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
        siniestros_totales = sum(s.monto_bruto for s in siniestros if self.validar_siniestro(s))

        # Calcular recuperaciones
        # Nota: esto consume el límite disponible
        recuperacion, detalle_siniestros = self.calcular_recuperacion_multiple(siniestros)

        # Siniestros retenidos = siniestros totales - recuperación
        siniestros_retenidos = siniestros_totales - recuperacion

        # Resultado neto del contrato de reaseguro para la cedente:
        # + Recibe: recuperación
        # - Paga:   prima de reaseguro
        #
        # Neto = recuperación - prima_reaseguro
        #
        # Mide el contrato, no el resultado técnico: los siniestros retenidos
        # NO se restan aquí, porque la cedente los pagaría igual sin reaseguro.
        # Ojo: en Quota Share este mismo campo tiene otra semántica, límite ya
        # inventariado en docs/AUDIT.md (Clase B). El comentario anterior
        # enunciaba `- siniestros_retenidos`, término que el código nunca aplicó.
        resultado_neto = recuperacion - prima_reaseguro_cobrada

        # Construir detalles
        detalles = {
            "retencion": str(self.config.retencion),
            "limite_original": str(self.config.limite),
            "limite_por_ocurrencia": str(self.config.limite),
            "limite_agregado": str(self.limite_agregado),
            "limite_disponible": str(self.limite_disponible),
            "modalidad": self.config.modalidad.value,
            "numero_reinstatements": self.config.numero_reinstatements,
            "reinstatements_usados": self.reinstatements_usados,
            "prima_reinstalacion": str(self.calcular_prima_reinstalacion()),
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
            (recuperacion / siniestros_totales * 100) if siniestros_totales > 0 else Decimal("0")
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
