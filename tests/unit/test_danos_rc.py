"""
Tests para el producto de responsabilidad civil general.

~20 tests cubriendo:
- Construccion valida con distintas clases de actividad
- Errores de validacion (clase invalida, limite negativo, deducible negativo)
- Busqueda de factor de deducible (exacto, intermedio, debajo del minimo, arriba del maximo)
- Calculo de prima con formula manual
- Cotizacion completa (claves, tipos)
- Valores frontera (limite minimo, limite muy grande)
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest

from suite_actuarial.danos.rc import (
    TASAS_ACTIVIDAD,
    SeguroRC,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rc_oficinas():
    """RC para oficinas con deducible de 25,000."""
    return SeguroRC(
        limite_responsabilidad=Decimal("5000000"),
        deducible=Decimal("25000"),
        clase_actividad="oficinas",
    )


@pytest.fixture
def rc_construccion():
    """RC para construccion con deducible de 100,000."""
    return SeguroRC(
        limite_responsabilidad=Decimal("10000000"),
        deducible=Decimal("100000"),
        clase_actividad="construccion",
    )


@pytest.fixture
def rc_restaurante():
    """RC para restaurante con deducible de 50,000."""
    return SeguroRC(
        limite_responsabilidad=Decimal("2000000"),
        deducible=Decimal("50000"),
        clase_actividad="restaurante",
    )


# ---------------------------------------------------------------------------
# 1. Construccion valida
# ---------------------------------------------------------------------------


class TestConstruccionValida:
    """Verificar inicializacion correcta con distintas clases de actividad."""

    def test_oficinas(self, rc_oficinas):
        assert rc_oficinas.limite_responsabilidad == Decimal("5000000")
        assert rc_oficinas.deducible == Decimal("25000")
        assert rc_oficinas.clase_actividad == "oficinas"
        assert rc_oficinas.tasa_base == Decimal("1.20")

    def test_construccion(self, rc_construccion):
        assert rc_construccion.limite_responsabilidad == Decimal("10000000")
        assert rc_construccion.deducible == Decimal("100000")
        assert rc_construccion.clase_actividad == "construccion"
        assert rc_construccion.tasa_base == Decimal("5.00")

    def test_restaurante(self, rc_restaurante):
        assert rc_restaurante.limite_responsabilidad == Decimal("2000000")
        assert rc_restaurante.deducible == Decimal("50000")
        assert rc_restaurante.clase_actividad == "restaurante"
        assert rc_restaurante.tasa_base == Decimal("2.50")

    def test_todas_las_clases_son_aceptadas(self):
        """Cada clase definida en TASAS_ACTIVIDAD construye sin error."""
        for clase in TASAS_ACTIVIDAD:
            seguro = SeguroRC(
                limite_responsabilidad=Decimal("1000000"),
                deducible=Decimal("25000"),
                clase_actividad=clase,
            )
            assert seguro.tasa_base == TASAS_ACTIVIDAD[clase]


# ---------------------------------------------------------------------------
# 2. Errores de validacion
# ---------------------------------------------------------------------------


class TestValidacionErrores:
    """Verificar que parametros invalidos lanzan ValueError."""

    def test_clase_actividad_desconocida(self):
        with pytest.raises(ValueError, match="Clase de actividad desconocida"):
            SeguroRC(
                limite_responsabilidad=Decimal("1000000"),
                deducible=Decimal("25000"),
                clase_actividad="mineria_submarina",
            )

    def test_limite_negativo(self):
        with pytest.raises(ValueError, match="limite de responsabilidad debe ser positivo"):
            SeguroRC(
                limite_responsabilidad=Decimal("-500000"),
                deducible=Decimal("25000"),
                clase_actividad="oficinas",
            )

    def test_limite_cero(self):
        with pytest.raises(ValueError, match="limite de responsabilidad debe ser positivo"):
            SeguroRC(
                limite_responsabilidad=Decimal("0"),
                deducible=Decimal("25000"),
                clase_actividad="oficinas",
            )

    def test_deducible_negativo(self):
        with pytest.raises(ValueError, match="deducible no puede ser negativo"):
            SeguroRC(
                limite_responsabilidad=Decimal("1000000"),
                deducible=Decimal("-10000"),
                clase_actividad="oficinas",
            )

    def test_clase_actividad_vacia(self):
        with pytest.raises(ValueError, match="Clase de actividad desconocida"):
            SeguroRC(
                limite_responsabilidad=Decimal("1000000"),
                deducible=Decimal("25000"),
                clase_actividad="",
            )


# ---------------------------------------------------------------------------
# 3. Factor de deducible (busqueda estatica)
# ---------------------------------------------------------------------------


class TestBuscarFactorDeducible:
    """Verificar _buscar_factor_deducible con distintos valores."""

    def test_coincidencia_exacta_25000(self):
        """Deducible exacto de 25,000 -> factor 1.00."""
        factor = SeguroRC._buscar_factor_deducible(Decimal("25000"))
        assert factor == Decimal("1.00")

    def test_coincidencia_exacta_100000(self):
        """Deducible exacto de 100,000 -> factor 0.80."""
        factor = SeguroRC._buscar_factor_deducible(Decimal("100000"))
        assert factor == Decimal("0.80")

    def test_valor_entre_brackets(self):
        """Deducible de 75,000 (entre 50k y 100k) -> usa 50k -> 0.90."""
        factor = SeguroRC._buscar_factor_deducible(Decimal("75000"))
        assert factor == Decimal("0.90")

    def test_debajo_del_minimo(self):
        """Deducible de 5,000 (debajo de 10,000) -> default 1.10."""
        factor = SeguroRC._buscar_factor_deducible(Decimal("5000"))
        assert factor == Decimal("1.10")

    def test_arriba_del_maximo(self):
        """Deducible de 500,000 (arriba de 250,000) -> usa 250k -> 0.70."""
        factor = SeguroRC._buscar_factor_deducible(Decimal("500000"))
        assert factor == Decimal("0.70")

    def test_deducible_cero(self):
        """Deducible de 0 -> default 1.10 (debajo de todo bracket)."""
        factor = SeguroRC._buscar_factor_deducible(Decimal("0"))
        assert factor == Decimal("1.10")


# ---------------------------------------------------------------------------
# 4. Calculo de prima
# ---------------------------------------------------------------------------


class TestCalculoPrima:
    """Verificar prima = (limite/1000) * tasa_base * factor_deducible."""

    def test_prima_oficinas(self, rc_oficinas):
        """Oficinas: (5,000,000/1000) * 1.20 * 1.00 = 6,000.00."""
        esperada = (
            (Decimal("5000000") / Decimal("1000"))
            * Decimal("1.20")
            * Decimal("1.00")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert rc_oficinas.calcular_prima() == esperada
        assert rc_oficinas.calcular_prima() == Decimal("6000.00")

    def test_prima_construccion(self, rc_construccion):
        """Construccion: (10,000,000/1000) * 5.00 * 0.80 = 40,000.00."""
        esperada = (
            (Decimal("10000000") / Decimal("1000"))
            * Decimal("5.00")
            * Decimal("0.80")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert rc_construccion.calcular_prima() == esperada
        assert rc_construccion.calcular_prima() == Decimal("40000.00")

    def test_prima_restaurante(self, rc_restaurante):
        """Restaurante: (2,000,000/1000) * 2.50 * 0.90 = 4,500.00."""
        esperada = (
            (Decimal("2000000") / Decimal("1000"))
            * Decimal("2.50")
            * Decimal("0.90")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert rc_restaurante.calcular_prima() == esperada
        assert rc_restaurante.calcular_prima() == Decimal("4500.00")

    def test_prima_transporte_deducible_alto(self):
        """Transporte con deducible 250k: (3,000,000/1000) * 4.00 * 0.70 = 8,400.00."""
        seguro = SeguroRC(
            limite_responsabilidad=Decimal("3000000"),
            deducible=Decimal("250000"),
            clase_actividad="transporte",
        )
        esperada = Decimal("8400.00")
        assert seguro.calcular_prima() == esperada


# ---------------------------------------------------------------------------
# 5. Cotizacion completa
# ---------------------------------------------------------------------------


class TestGenerarCotizacion:
    """Verificar estructura y tipos del dict de cotizacion."""

    def test_claves_presentes(self, rc_oficinas):
        cot = rc_oficinas.generar_cotizacion()
        claves_esperadas = {
            "limite_responsabilidad",
            "deducible",
            "clase_actividad",
            "tasa_base",
            "factor_deducible",
            "prima_anual",
        }
        assert set(cot.keys()) == claves_esperadas

    def test_tipos_correctos(self, rc_oficinas):
        cot = rc_oficinas.generar_cotizacion()
        assert isinstance(cot["limite_responsabilidad"], Decimal)
        assert isinstance(cot["deducible"], Decimal)
        assert isinstance(cot["clase_actividad"], str)
        assert isinstance(cot["tasa_base"], Decimal)
        assert isinstance(cot["factor_deducible"], Decimal)
        assert isinstance(cot["prima_anual"], Decimal)

    def test_coherencia_valores(self, rc_construccion):
        """Los valores en la cotizacion coinciden con los atributos del objeto."""
        cot = rc_construccion.generar_cotizacion()
        assert cot["limite_responsabilidad"] == rc_construccion.limite_responsabilidad
        assert cot["deducible"] == rc_construccion.deducible
        assert cot["clase_actividad"] == rc_construccion.clase_actividad
        assert cot["tasa_base"] == rc_construccion.tasa_base
        assert cot["factor_deducible"] == rc_construccion.factor_deducible
        assert cot["prima_anual"] == rc_construccion.calcular_prima()


# ---------------------------------------------------------------------------
# 6. Valores frontera
# ---------------------------------------------------------------------------


class TestValoresFrontera:
    """Valores extremos que siguen siendo validos."""

    def test_limite_minimo(self):
        """El limite mas pequeno valido es mayor a cero."""
        seguro = SeguroRC(
            limite_responsabilidad=Decimal("0.01"),
            deducible=Decimal("0"),
            clase_actividad="oficinas",
        )
        prima = seguro.calcular_prima()
        # (0.01/1000) * 1.20 * 1.10 = 0.0000132 -> 0.00
        assert prima == Decimal("0.00")
        assert prima >= Decimal("0")

    def test_limite_muy_grande(self):
        """Limite de 100 millones sin errores aritmeticos."""
        seguro = SeguroRC(
            limite_responsabilidad=Decimal("100000000"),
            deducible=Decimal("250000"),
            clase_actividad="manufactura_pesada",
        )
        # (100,000,000/1000) * 4.50 * 0.70 = 315,000.00
        prima = seguro.calcular_prima()
        assert prima == Decimal("315000.00")
        assert prima > Decimal("0")
