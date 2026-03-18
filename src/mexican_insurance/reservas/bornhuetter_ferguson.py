"""
Método Bornhuetter-Ferguson para cálculo de reservas.

El método B-F combina la experiencia observada (Chain Ladder) con
expectativas a priori del loss ratio, proporcionando mayor estabilidad
en años con poco desarrollo o experiencia limitada.
"""

from decimal import Decimal

import pandas as pd

from mexican_insurance.core.validators import (
    ConfiguracionBornhuetterFerguson,
    MetodoReserva,
    ResultadoReserva,
)
from mexican_insurance.reservas.chain_ladder import ChainLadder
from mexican_insurance.reservas.triangulo import (
    obtener_ultima_diagonal,
    validar_triangulo,
)


class BornhuetterFerguson:
    """
    Implementación del método Bornhuetter-Ferguson para cálculo de reservas.

    El método B-F:
    1. Usa Chain Ladder para calcular factores de desarrollo
    2. Calcula % de siniestros ya reportados para cada año
    3. Estima Ultimate combinando:
       - Siniestros observados (pagados hasta la fecha)
       - Expectativa a priori de siniestros no reportados

    Fórmula:
        Ultimate = Pagado + (Primas * LR_apriori * %_No_Reportado)

    Ventajas:
    - Más estable que Chain Ladder para años recientes
    - Incorpora conocimiento del negocio (loss ratio esperado)
    - Menos sensible a fluctuaciones en triángulo

    Ejemplo:
        >>> config = ConfiguracionBornhuetterFerguson(
        ...     loss_ratio_apriori=Decimal("0.65"),
        ...     metodo_promedio=MetodoPromedio.SIMPLE
        ... )
        >>> bf = BornhuetterFerguson(config)
        >>> resultado = bf.calcular(triangulo, primas_por_anio)
        >>> print(f"Reserva total: ${resultado.reserva_total:,.2f}")
    """

    def __init__(self, config: ConfiguracionBornhuetterFerguson):
        """
        Inicializa el método Bornhuetter-Ferguson.

        Args:
            config: Configuración del método
        """
        self.config = config
        self.chain_ladder: ChainLadder | None = None
        self.factores_desarrollo: list[Decimal] | None = None
        self.porcentajes_reportados: dict[int, Decimal] | None = None

    def calcular_porcentajes_reportados(
        self, triangulo: pd.DataFrame, factores: list[Decimal]
    ) -> dict[int, Decimal]:
        """
        Calcula el % de siniestros ya reportados para cada año de origen.

        El % reportado se calcula como:
            1 / (producto de factores restantes)

        Args:
            triangulo: Triángulo original
            factores: Factores de desarrollo del Chain Ladder

        Returns:
            Diccionario {año_origen: % reportado (0-1)}
        """
        porcentajes = {}
        triangulo.shape[1]

        for _i, idx in enumerate(triangulo.index):
            # Encontrar cuántos períodos han transcurrido
            row = triangulo.loc[idx]
            periodos_observados = row.notna().sum()

            # Factores que faltan por aplicar
            factores_restantes = factores[periodos_observados - 1 :]

            # Producto acumulado de factores restantes
            producto_factores = Decimal("1.0")
            for f in factores_restantes:
                producto_factores *= f

            # % reportado = 1 / producto_factores
            # Si producto = 1.5, significa que falta 50% por desarrollar
            # Entonces % reportado = 1/1.5 = 66.67%
            pct_reportado = Decimal("1.0") / producto_factores
            porcentajes[int(idx)] = pct_reportado

        return porcentajes

    def calcular_ultimates(
        self,
        triangulo: pd.DataFrame,
        primas_por_anio: dict[int, Decimal],
        porcentajes_reportados: dict[int, Decimal],
    ) -> dict[int, Decimal]:
        """
        Calcula ultimates usando el método Bornhuetter-Ferguson.

        Fórmula:
            Ultimate = Pagado + (Prima * LR_apriori * % No Reportado)

        Donde:
            % No Reportado = 1 - % Reportado

        Args:
            triangulo: Triángulo original
            primas_por_anio: Primas ganadas por año de origen
            porcentajes_reportados: % de siniestros reportados por año

        Returns:
            Diccionario {año_origen: ultimate}
        """
        ultimates = {}
        ultima_diagonal = obtener_ultima_diagonal(triangulo)

        for idx in triangulo.index:
            anio = int(idx)

            # Pagado hasta la fecha
            pagado = Decimal(str(ultima_diagonal[idx]))

            # Prima del año
            if anio not in primas_por_anio:
                raise ValueError(
                    f"Falta prima para año {anio}. "
                    "Debe proporcionar primas para todos los años del triángulo."
                )

            prima = primas_por_anio[anio]

            # % reportado y no reportado
            pct_reportado = porcentajes_reportados[anio]
            pct_no_reportado = Decimal("1.0") - pct_reportado

            # Ultimate esperado a priori
            ultimate_apriori = prima * self.config.loss_ratio_apriori

            # IBNR esperado (siniestros no reportados)
            ibnr_esperado = ultimate_apriori * pct_no_reportado

            # Ultimate B-F = Pagado + IBNR esperado
            ultimate_bf = pagado + ibnr_esperado

            ultimates[anio] = ultimate_bf

        return ultimates

    def calcular_reservas(
        self, triangulo: pd.DataFrame, ultimates: dict[int, Decimal]
    ) -> dict[int, Decimal]:
        """
        Calcula las reservas (IBNR) para cada año.

        Reserva = Ultimate - Pagado hasta la fecha

        Args:
            triangulo: Triángulo original con valores conocidos
            ultimates: Valores ultimate calculados

        Returns:
            Diccionario {año_origen: reserva}
        """
        reservas = {}
        ultima_diagonal = obtener_ultima_diagonal(triangulo)

        for idx in triangulo.index:
            ultimate = ultimates[int(idx)]
            pagado = Decimal(str(ultima_diagonal[idx]))

            # Reserva = Ultimate - Pagado
            reserva = ultimate - pagado

            # No puede ser negativa (mínimo 0)
            reservas[int(idx)] = max(reserva, Decimal("0"))

        return reservas

    def calcular(
        self,
        triangulo: pd.DataFrame,
        primas_por_anio: dict[int, Decimal],
    ) -> ResultadoReserva:
        """
        Ejecuta el método Bornhuetter-Ferguson completo.

        Args:
            triangulo: Triángulo de desarrollo (acumulado)
            primas_por_anio: Primas ganadas por año de origen
                            Ej: {2020: Decimal("1000000"), 2021: ...}

        Returns:
            ResultadoReserva con análisis completo

        Raises:
            ValueError: Si faltan primas para algún año del triángulo
        """
        # Validar triángulo
        validar_triangulo(triangulo)

        # Validar que haya primas para todos los años
        for idx in triangulo.index:
            if int(idx) not in primas_por_anio:
                raise ValueError(
                    f"Falta prima para año {int(idx)}. "
                    "Debe proporcionar primas_por_anio para todos los años."
                )

        # 1. Ejecutar Chain Ladder para obtener factores de desarrollo
        from mexican_insurance.core.validators import (
            ConfiguracionChainLadder,
        )

        config_cl = ConfiguracionChainLadder(
            metodo_promedio=self.config.metodo_promedio,
            calcular_tail_factor=False,
        )

        self.chain_ladder = ChainLadder(config_cl)
        self.factores_desarrollo = (
            self.chain_ladder.calcular_factores_desarrollo(triangulo)
        )

        # 2. Calcular porcentajes reportados
        self.porcentajes_reportados = self.calcular_porcentajes_reportados(
            triangulo, self.factores_desarrollo
        )

        # 3. Calcular ultimates usando B-F
        ultimates = self.calcular_ultimates(
            triangulo, primas_por_anio, self.porcentajes_reportados
        )

        # 4. Calcular reservas
        reservas = self.calcular_reservas(triangulo, ultimates)

        # 5. Calcular totales
        reserva_total = sum(reservas.values())
        ultimate_total = sum(ultimates.values())

        # Pagado total = última diagonal
        ultima_diagonal = obtener_ultima_diagonal(triangulo)
        pagado_total = sum(Decimal(str(v)) for v in ultima_diagonal)

        # 6. Calcular total de primas
        prima_total = sum(primas_por_anio.values())

        # 7. Calcular loss ratio implícito
        loss_ratio_implicito = (
            ultimate_total / prima_total if prima_total > 0 else Decimal("0")
        )

        # 8. Construir detalles
        detalles = {
            "loss_ratio_apriori": str(self.config.loss_ratio_apriori),
            "loss_ratio_implicito": f"{loss_ratio_implicito:.2%}",
            "prima_total": str(prima_total),
            "metodo_promedio": self.config.metodo_promedio.value,
            "numero_anios": len(triangulo),
            "porcentajes_reportados": {
                anio: f"{pct:.2%}"
                for anio, pct in self.porcentajes_reportados.items()
            },
        }

        # 9. Construir resultado
        resultado = ResultadoReserva(
            metodo=MetodoReserva.BORNHUETTER_FERGUSON,
            reserva_total=reserva_total,
            ultimate_total=ultimate_total,
            pagado_total=pagado_total,
            reservas_por_anio=reservas,
            ultimates_por_anio=ultimates,
            factores_desarrollo=self.factores_desarrollo,
            percentiles=None,  # No aplica en B-F básico
            detalles=detalles,
        )

        return resultado

    def obtener_porcentajes_reportados(self) -> dict[int, Decimal] | None:
        """
        Obtiene los porcentajes reportados calculados.

        Returns:
            Diccionario con % reportado por año o None si no se ha calculado
        """
        return self.porcentajes_reportados

    def comparar_con_chain_ladder(
        self, triangulo: pd.DataFrame, primas_por_anio: dict[int, Decimal]
    ) -> pd.DataFrame:
        """
        Compara resultados de B-F vs Chain Ladder.

        Args:
            triangulo: Triángulo de desarrollo
            primas_por_anio: Primas por año

        Returns:
            DataFrame con comparación lado a lado
        """
        # Calcular B-F
        resultado_bf = self.calcular(triangulo, primas_por_anio)

        # Calcular Chain Ladder
        from mexican_insurance.core.validators import ConfiguracionChainLadder

        config_cl = ConfiguracionChainLadder(
            metodo_promedio=self.config.metodo_promedio
        )
        cl = ChainLadder(config_cl)
        resultado_cl = cl.calcular(triangulo)

        # Construir DataFrame comparativo
        comparacion = pd.DataFrame(
            {
                "Ultimate_CL": [
                    resultado_cl.ultimates_por_anio[anio]
                    for anio in sorted(resultado_cl.ultimates_por_anio.keys())
                ],
                "Ultimate_BF": [
                    resultado_bf.ultimates_por_anio[anio]
                    for anio in sorted(resultado_bf.ultimates_por_anio.keys())
                ],
                "Reserva_CL": [
                    resultado_cl.reservas_por_anio[anio]
                    for anio in sorted(resultado_cl.reservas_por_anio.keys())
                ],
                "Reserva_BF": [
                    resultado_bf.reservas_por_anio[anio]
                    for anio in sorted(resultado_bf.reservas_por_anio.keys())
                ],
                "Diferencia_%": [
                    (
                        (
                            resultado_bf.ultimates_por_anio[anio]
                            - resultado_cl.ultimates_por_anio[anio]
                        )
                        / resultado_cl.ultimates_por_anio[anio]
                        * 100
                    )
                    for anio in sorted(resultado_cl.ultimates_por_anio.keys())
                ],
            },
            index=sorted(resultado_cl.ultimates_por_anio.keys()),
        )

        return comparacion

    def __repr__(self) -> str:
        """Representación string del método"""
        return (
            f"BornhuetterFerguson("
            f"LR_apriori={self.config.loss_ratio_apriori}, "
            f"metodo={self.config.metodo_promedio.value})"
        )
