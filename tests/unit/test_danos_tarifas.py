"""
Tests para el motor de tarificacion y credibilidad.

~20 tests cubriendo:
- Credibilidad de Buhlmann con ejemplos conocidos
- Buhlmann-Straub con exposicion ponderada
- Transiciones Bonus-Malus a lo largo de multiples anos
- TablaTarifas busqueda y aplicacion
"""

from decimal import Decimal

import pytest

from suite_actuarial.danos.tarifas import (
    CalculadoraBonusMalus,
    FactorCredibilidad,
    TablaTarifas,
)


# ---------------------------------------------------------------------------
# Tests de Buhlmann clasico
# ---------------------------------------------------------------------------

class TestBuhlmann:
    def test_sin_experiencia(self):
        """Sin datos propios, Z=0, se usa prima manual."""
        resultado = FactorCredibilidad.buhlmann([], Decimal("1000"))
        assert resultado["Z"] == Decimal("0")
        assert resultado["prima_credibilidad"] == Decimal("1000")

    def test_un_periodo(self):
        """Con un solo periodo, no se puede estimar varianza."""
        resultado = FactorCredibilidad.buhlmann([Decimal("500")], Decimal("1000"))
        assert resultado["Z"] == Decimal("0")
        assert resultado["prima_credibilidad"] == Decimal("1000")

    def test_multiples_periodos(self):
        """Con variacion entre periodos, Z > 0."""
        experiencia = [Decimal("800"), Decimal("1200"), Decimal("900"), Decimal("1100")]
        resultado = FactorCredibilidad.buhlmann(experiencia, Decimal("1000"))
        assert Decimal("0") <= resultado["Z"] <= Decimal("1")
        assert resultado["n_periodos"] == 4

    def test_experiencia_constante(self):
        """Si la experiencia es constante, toda la variacion es proceso."""
        experiencia = [Decimal("500"), Decimal("500"), Decimal("500")]
        resultado = FactorCredibilidad.buhlmann(experiencia, Decimal("1000"))
        # Sin variacion entre periodos
        assert resultado["Z"] == Decimal("0")

    def test_prima_credibilidad_entre_experiencia_y_manual(self):
        """La prima de credibilidad esta entre experiencia propia y manual."""
        experiencia = [Decimal("600"), Decimal("1400"), Decimal("700"), Decimal("1300"),
                       Decimal("800"), Decimal("1200")]
        manual = Decimal("1500")
        resultado = FactorCredibilidad.buhlmann(experiencia, manual)
        if resultado["Z"] > 0:
            media_exp = sum(experiencia) / len(experiencia)
            pc = resultado["prima_credibilidad"]
            assert min(media_exp, manual) <= pc <= max(media_exp, manual)


# ---------------------------------------------------------------------------
# Tests de Buhlmann-Straub
# ---------------------------------------------------------------------------

class TestBuhlmannStraub:
    def test_sin_experiencia(self):
        resultado = FactorCredibilidad.buhlmann_straub([], Decimal("500"))
        assert resultado["Z"] == Decimal("0")
        assert resultado["prima_credibilidad"] == Decimal("500")

    def test_un_periodo(self):
        experiencias = [{"siniestros": Decimal("10000"), "exposicion": 100}]
        resultado = FactorCredibilidad.buhlmann_straub(experiencias, Decimal("120"))
        assert resultado["Z"] == Decimal("0")
        assert resultado["exposicion_total"] == 100

    def test_multiples_periodos(self):
        experiencias = [
            {"siniestros": Decimal("8000"), "exposicion": 100},
            {"siniestros": Decimal("12000"), "exposicion": 150},
            {"siniestros": Decimal("9500"), "exposicion": 120},
        ]
        resultado = FactorCredibilidad.buhlmann_straub(experiencias, Decimal("100"))
        assert resultado["exposicion_total"] == 370
        assert Decimal("0") <= resultado["Z"] <= Decimal("1")

    def test_exposicion_cero(self):
        experiencias = [{"siniestros": Decimal("0"), "exposicion": 0}]
        resultado = FactorCredibilidad.buhlmann_straub(experiencias, Decimal("100"))
        assert resultado["Z"] == Decimal("0")


# ---------------------------------------------------------------------------
# Tests de Bonus-Malus
# ---------------------------------------------------------------------------

class TestBonusMalus:
    def test_nivel_inicial(self):
        bms = CalculadoraBonusMalus(nivel_actual=0)
        assert bms.factor_actual() == Decimal("1.00")

    def test_sin_siniestros_baja_nivel(self):
        bms = CalculadoraBonusMalus(0)
        nuevo = bms.transicion(0)
        assert nuevo == -1
        assert bms.factor_actual() == Decimal("0.90")

    def test_un_siniestro_sube_dos(self):
        bms = CalculadoraBonusMalus(0)
        nuevo = bms.transicion(1)
        assert nuevo == 2
        assert bms.factor_actual() == Decimal("1.30")

    def test_multiples_siniestros_sube_tres(self):
        bms = CalculadoraBonusMalus(0)
        nuevo = bms.transicion(3)
        assert nuevo == 3
        assert bms.factor_actual() == Decimal("1.50")

    def test_no_baja_de_minimo(self):
        bms = CalculadoraBonusMalus(-5)
        nuevo = bms.transicion(0)
        assert nuevo == -5  # Ya esta en el minimo
        assert bms.factor_actual() == Decimal("0.70")

    def test_no_sube_de_maximo(self):
        bms = CalculadoraBonusMalus(3)
        nuevo = bms.transicion(5)
        assert nuevo == 3  # Ya esta en el maximo
        assert bms.factor_actual() == Decimal("1.50")

    def test_historial_completo(self):
        bms = CalculadoraBonusMalus(0)
        historial = bms.historial_completo([0, 0, 1, 0, 0])
        assert len(historial) == 5
        # Ano 1: 0 sin -> nivel -1
        assert historial[0]["nivel_nuevo"] == -1
        # Ano 2: 0 sin -> nivel -2
        assert historial[1]["nivel_nuevo"] == -2
        # Ano 3: 1 sin -> nivel 0 (-2 + 2)
        assert historial[2]["nivel_nuevo"] == 0
        # Ano 4: 0 sin -> nivel -1
        assert historial[3]["nivel_nuevo"] == -1
        # Ano 5: 0 sin -> nivel -2
        assert historial[4]["nivel_nuevo"] == -2

    def test_historial_formato(self):
        bms = CalculadoraBonusMalus(0)
        historial = bms.historial_completo([0, 1])
        assert "ano" in historial[0]
        assert "siniestros" in historial[0]
        assert "nivel_previo" in historial[0]
        assert "nivel_nuevo" in historial[0]
        assert "factor" in historial[0]

    def test_nivel_invalido(self):
        with pytest.raises(ValueError, match="Nivel"):
            CalculadoraBonusMalus(nivel_actual=10)

    def test_siniestros_negativos(self):
        bms = CalculadoraBonusMalus(0)
        with pytest.raises(ValueError, match="negativos"):
            bms.transicion(-1)


# ---------------------------------------------------------------------------
# Tests de TablaTarifas
# ---------------------------------------------------------------------------

class TestTablaTarifas:
    @pytest.fixture
    def tabla(self):
        return TablaTarifas({
            "zona": {
                "cdmx": Decimal("1.30"),
                "gdl": Decimal("1.10"),
                "mty": Decimal("1.15"),
            },
            "edad": {
                "joven": Decimal("1.35"),
                "adulto": Decimal("1.00"),
                "mayor": Decimal("1.20"),
            },
        })

    def test_obtener_factor(self, tabla):
        assert tabla.obtener_factor(zona="cdmx") == Decimal("1.30")
        assert tabla.obtener_factor(edad="joven") == Decimal("1.35")

    def test_factor_no_encontrado(self, tabla):
        with pytest.raises(KeyError):
            tabla.obtener_factor(zona="marte")

    def test_dimension_no_encontrada(self, tabla):
        with pytest.raises(KeyError):
            tabla.obtener_factor(genero="m")

    def test_aplicar_un_factor(self, tabla):
        prima = tabla.aplicar_factores(Decimal("1000"), zona="cdmx")
        assert prima == Decimal("1300.00")

    def test_aplicar_multiples_factores(self, tabla):
        prima = tabla.aplicar_factores(Decimal("1000"), zona="cdmx", edad="joven")
        # 1000 * 1.30 * 1.35 = 1755
        assert prima == Decimal("1755.00")

    def test_aplicar_sin_factores_error(self, tabla):
        with pytest.raises(ValueError, match="exactamente una dimension"):
            tabla.obtener_factor()
