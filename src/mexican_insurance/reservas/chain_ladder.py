"""
Método Chain Ladder (Escalera de Cadena) para cálculo de reservas.

El método Chain Ladder es el estándar de la industria para proyectar
el desarrollo futuro de siniestros basado en patrones históricos.
"""

from decimal import Decimal

import pandas as pd

from mexican_insurance.core.validators import (
    ConfiguracionChainLadder,
    MetodoPromedio,
    MetodoReserva,
    ResultadoReserva,
)
from mexican_insurance.reservas.triangulo import (
    acumular_triangulo,
    calcular_age_to_age,
    obtener_ultima_diagonal,
    promedio_geometrico,
    promedio_ponderado,
    promedio_simple,
    validar_triangulo,
)


class ChainLadder:
    """
    Implementación del método Chain Ladder para cálculo de reservas.

    El método Chain Ladder:
    1. Calcula factores age-to-age (link ratios) para cada período
    2. Promedia estos factores para obtener factores de desarrollo
    3. Usa estos factores para completar el triángulo
    4. Calcula ultimates (valor final proyectado) para cada año
    5. Calcula reservas (IBNR) = ultimate - pagado hasta la fecha

    Ejemplo:
        >>> config = ConfiguracionChainLadder(
        ...     metodo_promedio=MetodoPromedio.SIMPLE,
        ...     calcular_tail_factor=False
        ... )
        >>> cl = ChainLadder(config)
        >>> resultado = cl.calcular(triangulo_acumulado)
        >>> print(f"Reserva total: ${resultado.reserva_total:,.2f}")
    """

    def __init__(self, config: ConfiguracionChainLadder):
        """
        Inicializa el método Chain Ladder.

        Args:
            config: Configuración del método
        """
        self.config = config
        self.triangulo_original: pd.DataFrame | None = None
        self.triangulo_completo: pd.DataFrame | None = None
        self.factores_age_to_age: pd.DataFrame | None = None
        self.factores_desarrollo: list[Decimal] | None = None

    def calcular_factores_desarrollo(
        self, triangulo: pd.DataFrame
    ) -> list[Decimal]:
        """
        Calcula los factores de desarrollo promedio para cada período.

        Args:
            triangulo: Triángulo acumulado de siniestros

        Returns:
            Lista de factores de desarrollo (uno por período)
        """
        # Calcular factores age-to-age
        self.factores_age_to_age = calcular_age_to_age(triangulo)

        factores = []
        n_cols = self.factores_age_to_age.shape[1]

        for col_idx in range(n_cols):
            # Obtener factores de esta columna (eliminando NaN)
            columna = self.factores_age_to_age.iloc[:, col_idx].dropna()

            if len(columna) == 0:
                factores.append(Decimal("1.0"))
                continue

            valores = columna.tolist()

            # Calcular promedio según método configurado
            if self.config.metodo_promedio == MetodoPromedio.SIMPLE:
                factor = promedio_simple(valores)

            elif self.config.metodo_promedio == MetodoPromedio.GEOMETRICO:
                factor = promedio_geometrico(valores)

            elif self.config.metodo_promedio == MetodoPromedio.PONDERADO:
                # Para promedio ponderado necesitamos los volúmenes
                # Usar los valores del triángulo como pesos
                volumenes = []
                for i in range(len(columna)):
                    idx_row = columna.index[i]
                    row_idx = triangulo.index.get_loc(idx_row)
                    vol = triangulo.iloc[row_idx, col_idx]
                    volumenes.append(vol if pd.notna(vol) else 0)

                factor = promedio_ponderado(valores, volumenes)

            else:
                factor = promedio_simple(valores)

            factores.append(Decimal(str(factor)))

        # Agregar tail factor si está configurado
        if self.config.calcular_tail_factor:
            # Método simple: usar el último factor
            tail = factores[-1] if factores else Decimal("1.0")
            factores.append(tail)
        elif self.config.tail_factor is not None:
            factores.append(self.config.tail_factor)

        return factores

    def completar_triangulo(
        self, triangulo: pd.DataFrame, factores: list[Decimal]
    ) -> pd.DataFrame:
        """
        Completa el triángulo proyectando valores futuros.

        Args:
            triangulo: Triángulo original (incompleto)
            factores: Factores de desarrollo a aplicar

        Returns:
            Triángulo completo con proyecciones
        """
        # Crear copia para no modificar el original
        triangulo_completo = triangulo.copy()

        n_rows, n_cols = triangulo.shape

        # Para cada fila, proyectar hacia adelante
        for i in range(n_rows):
            # Encontrar el último valor conocido
            row = triangulo_completo.iloc[i]
            ultima_col_conocida = row.last_valid_index()

            if ultima_col_conocida is None:
                continue

            # Posición de la última columna conocida
            col_idx = triangulo_completo.columns.get_loc(ultima_col_conocida)
            ultimo_valor = float(row[ultima_col_conocida])

            # Proyectar desde col_idx+1 hasta el final
            for j in range(col_idx + 1, n_cols):
                # Factor a aplicar
                factor_idx = min(j - 1, len(factores) - 1)
                factor = float(factores[factor_idx])

                # Proyectar
                ultimo_valor = ultimo_valor * factor
                triangulo_completo.iloc[i, j] = ultimo_valor

        return triangulo_completo

    def calcular_ultimates(
        self, triangulo_completo: pd.DataFrame
    ) -> dict[int, Decimal]:
        """
        Calcula el valor ultimate (final proyectado) para cada año.

        Args:
            triangulo_completo: Triángulo con todas las proyecciones

        Returns:
            Diccionario {año_origen: ultimate}
        """
        ultimates = {}

        for idx in triangulo_completo.index:
            # El ultimate es el último valor de la fila
            row = triangulo_completo.loc[idx]
            ultimate = row.iloc[-1]

            # Convertir a Decimal
            ultimates[int(idx)] = Decimal(str(ultimate))

        return ultimates

    def calcular_reservas(
        self, triangulo_original: pd.DataFrame, ultimates: dict[int, Decimal]
    ) -> dict[int, Decimal]:
        """
        Calcula las reservas (IBNR) para cada año.

        Reserva = Ultimate - Pagado hasta la fecha

        Args:
            triangulo_original: Triángulo original con valores conocidos
            ultimates: Valores ultimate calculados

        Returns:
            Diccionario {año_origen: reserva}
        """
        reservas = {}
        ultima_diagonal = obtener_ultima_diagonal(triangulo_original)

        for idx in triangulo_original.index:
            ultimate = ultimates[int(idx)]
            pagado = Decimal(str(ultima_diagonal[idx]))

            # Reserva = Ultimate - Pagado
            reserva = ultimate - pagado

            # No puede ser negativa (mínimo 0)
            reservas[int(idx)] = max(reserva, Decimal("0"))

        return reservas

    def calcular(self, triangulo: pd.DataFrame) -> ResultadoReserva:
        """
        Ejecuta el método Chain Ladder completo.

        Args:
            triangulo: Triángulo de desarrollo (acumulado o incremental)

        Returns:
            ResultadoReserva con análisis completo
        """
        # Validar triángulo
        validar_triangulo(triangulo)

        # Asegurar que sea acumulado
        self.triangulo_original = triangulo.copy()

        # Si es incremental, acumular
        # (asumimos acumulado si los valores son monótonos)
        primer_row = triangulo.iloc[0].dropna()
        if not primer_row.is_monotonic_increasing:
            self.triangulo_original = acumular_triangulo(triangulo)

        # 1. Calcular factores de desarrollo
        self.factores_desarrollo = self.calcular_factores_desarrollo(
            self.triangulo_original
        )

        # 2. Completar triángulo
        self.triangulo_completo = self.completar_triangulo(
            self.triangulo_original, self.factores_desarrollo
        )

        # 3. Calcular ultimates
        ultimates = self.calcular_ultimates(self.triangulo_completo)

        # 4. Calcular reservas
        reservas = self.calcular_reservas(self.triangulo_original, ultimates)

        # 5. Calcular totales
        reserva_total = sum(reservas.values())
        ultimate_total = sum(ultimates.values())

        # Pagado total = última diagonal
        ultima_diagonal = obtener_ultima_diagonal(self.triangulo_original)
        pagado_total = sum(Decimal(str(v)) for v in ultima_diagonal)

        # 6. Construir detalles
        detalles = {
            "metodo_promedio": self.config.metodo_promedio.value,
            "numero_anios": len(self.triangulo_original),
            "numero_periodos": len(self.triangulo_original.columns),
            "tail_factor_usado": (
                str(self.factores_desarrollo[-1])
                if self.config.calcular_tail_factor
                or self.config.tail_factor is not None
                else "No"
            ),
            "factores_desarrollo_count": len(self.factores_desarrollo),
        }

        # 7. Construir resultado
        resultado = ResultadoReserva(
            metodo=MetodoReserva.CHAIN_LADDER,
            reserva_total=reserva_total,
            ultimate_total=ultimate_total,
            pagado_total=pagado_total,
            reservas_por_anio=reservas,
            ultimates_por_anio=ultimates,
            factores_desarrollo=self.factores_desarrollo,
            percentiles=None,  # No aplica en Chain Ladder básico
            detalles=detalles,
        )

        return resultado

    def obtener_triangulo_completo(self) -> pd.DataFrame | None:
        """
        Obtiene el triángulo completo (con proyecciones).

        Returns:
            DataFrame con triángulo completo o None si no se ha calculado
        """
        return self.triangulo_completo

    def obtener_factores_age_to_age(self) -> pd.DataFrame | None:
        """
        Obtiene los factores age-to-age calculados.

        Returns:
            DataFrame con factores age-to-age o None si no se ha calculado
        """
        return self.factores_age_to_age

    def __repr__(self) -> str:
        """Representación string del método"""
        return (
            f"ChainLadder("
            f"metodo={self.config.metodo_promedio.value}, "
            f"tail={self.config.calcular_tail_factor})"
        )
