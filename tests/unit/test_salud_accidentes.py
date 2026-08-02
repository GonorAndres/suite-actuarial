"""
Tests para Accidentes y Enfermedades (A&E).

~15 tests cubriendo:
- Calculo basico de prima
- Impacto del factor de ocupacion
- Rating por banda de edad
- Tabla de indemnizaciones
- Validaciones de entrada
"""

import warnings
from decimal import Decimal

import pytest

from suite_actuarial.core.warnings import ExperimentalModelWarning
from suite_actuarial.salud.accidentes import (
    DISCLAIMER,
    VALIDATION_TIER,
    AccidentesEnfermedades,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ae_base():
    """A&E estandar: 35 anos, oficina, SA 1M."""
    return AccidentesEnfermedades(
        edad=35,
        sexo="masculino",
        suma_asegurada=Decimal("1000000"),
        ocupacion="oficina",
    )


@pytest.fixture
def ae_riesgo():
    """A&E alto riesgo: 45 anos, industrial pesado, SA 500k."""
    return AccidentesEnfermedades(
        edad=45,
        sexo="masculino",
        suma_asegurada=Decimal("500000"),
        ocupacion="industrial_pesado",
    )


# ---------------------------------------------------------------------------
# Tests de prima basica
# ---------------------------------------------------------------------------


class TestPrimaBasica:
    def test_prima_positiva(self, ae_base):
        prima = ae_base.calcular_prima()
        assert prima > 0

    def test_prima_calculo_manual(self, ae_base):
        """Edad 35 => banda 31-40, tasa 3.0, SA 1M, ocup oficina (1.0).
        (1M / 1000) * 3.0 * 1.0 = 3000.00"""
        prima = ae_base.calcular_prima()
        assert prima == Decimal("3000.00")

    def test_prima_tipo_decimal(self, ae_base):
        prima = ae_base.calcular_prima()
        assert isinstance(prima, Decimal)


# ---------------------------------------------------------------------------
# Tests de factor de ocupacion
# ---------------------------------------------------------------------------


class TestFactorOcupacion:
    def test_ocupacion_mayor_riesgo_mayor_prima(self):
        ae_oficina = AccidentesEnfermedades(
            30,
            "masculino",
            Decimal("1000000"),
            ocupacion="oficina",
        )
        ae_pesado = AccidentesEnfermedades(
            30,
            "masculino",
            Decimal("1000000"),
            ocupacion="industrial_pesado",
        )
        assert ae_pesado.calcular_prima() > ae_oficina.calcular_prima()

    def test_alto_riesgo_factor(self):
        """Alto riesgo (2.20) vs oficina (1.00): prima 2.2x mayor."""
        ae_oficina = AccidentesEnfermedades(
            30,
            "masculino",
            Decimal("1000000"),
            ocupacion="oficina",
        )
        ae_alto = AccidentesEnfermedades(
            30,
            "masculino",
            Decimal("1000000"),
            ocupacion="alto_riesgo",
        )
        ratio = ae_alto.calcular_prima() / ae_oficina.calcular_prima()
        assert ratio == Decimal("2.20")

    def test_comercio_mayor_que_oficina(self):
        ae_oficina = AccidentesEnfermedades(
            30,
            "masculino",
            Decimal("500000"),
            ocupacion="oficina",
        )
        ae_comercio = AccidentesEnfermedades(
            30,
            "masculino",
            Decimal("500000"),
            ocupacion="comercio",
        )
        assert ae_comercio.calcular_prima() > ae_oficina.calcular_prima()

    def test_ocupacion_invalida(self):
        with pytest.raises(ValueError, match="Ocupacion"):
            AccidentesEnfermedades(30, "masculino", Decimal("500000"), ocupacion="astronauta")


# ---------------------------------------------------------------------------
# Tests de banda de edad
# ---------------------------------------------------------------------------


class TestBandaEdad:
    def test_banda_18(self):
        ae = AccidentesEnfermedades(18, "masculino", Decimal("500000"))
        assert ae._obtener_banda_edad() == "18-30"

    def test_banda_30(self):
        ae = AccidentesEnfermedades(30, "masculino", Decimal("500000"))
        assert ae._obtener_banda_edad() == "18-30"

    def test_banda_31(self):
        ae = AccidentesEnfermedades(31, "masculino", Decimal("500000"))
        assert ae._obtener_banda_edad() == "31-40"

    def test_banda_70(self):
        ae = AccidentesEnfermedades(70, "masculino", Decimal("500000"))
        assert ae._obtener_banda_edad() == "61-70"

    def test_mayor_edad_mayor_prima(self):
        """Primas crecen con la edad."""
        ae_joven = AccidentesEnfermedades(25, "masculino", Decimal("1000000"))
        ae_mayor = AccidentesEnfermedades(65, "masculino", Decimal("1000000"))
        assert ae_mayor.calcular_prima() > ae_joven.calcular_prima()


# ---------------------------------------------------------------------------
# Tests de tabla de indemnizaciones
# ---------------------------------------------------------------------------


class TestTablaIndemnizaciones:
    def test_tabla_estructura(self, ae_base):
        tabla = ae_base.tabla_indemnizaciones()
        assert "suma_asegurada" in tabla
        assert "perdidas_organicas" in tabla
        assert "indemnizacion_diaria" in tabla
        assert "gastos_funerarios" in tabla
        assert "prima_anual" in tabla

    def test_muerte_accidental_100pct(self, ae_base):
        tabla = ae_base.tabla_indemnizaciones()
        muerte = tabla["perdidas_organicas"]["muerte_accidental"]
        assert muerte["porcentaje"] == Decimal("1.00")
        assert muerte["monto"] == Decimal("1000000.00")

    def test_perdida_una_mano_60pct(self, ae_base):
        tabla = ae_base.tabla_indemnizaciones()
        mano = tabla["perdidas_organicas"]["perdida_una_mano"]
        assert mano["porcentaje"] == Decimal("0.60")
        assert mano["monto"] == Decimal("600000.00")

    def test_gastos_funerarios(self, ae_base):
        tabla = ae_base.tabla_indemnizaciones()
        # 10% of 1M = 100k
        assert tabla["gastos_funerarios"] == Decimal("100000.00")

    def test_indemnizacion_diaria_default(self, ae_base):
        """Default daily: 0.1% of 1M = 1000."""
        tabla = ae_base.tabla_indemnizaciones()
        assert tabla["indemnizacion_diaria"]["monto_diario"] == Decimal("1000.00")

    def test_indemnizacion_diaria_custom(self):
        ae = AccidentesEnfermedades(
            30,
            "masculino",
            Decimal("1000000"),
            indemnizacion_diaria=Decimal("2500"),
        )
        tabla = ae.tabla_indemnizaciones()
        assert tabla["indemnizacion_diaria"]["monto_diario"] == Decimal("2500")


# ---------------------------------------------------------------------------
# Tests de validaciones
# ---------------------------------------------------------------------------


class TestValidaciones:
    def test_edad_menor_18(self):
        with pytest.raises(ValueError, match="18"):
            AccidentesEnfermedades(17, "masculino", Decimal("500000"))

    def test_edad_mayor_70(self):
        with pytest.raises(ValueError, match="70"):
            AccidentesEnfermedades(71, "masculino", Decimal("500000"))

    def test_suma_asegurada_negativa(self):
        with pytest.raises(ValueError, match="positiva"):
            AccidentesEnfermedades(30, "masculino", Decimal("-100000"))


class TestAvisoDeAlcance:
    """A&E no tenia ningun aviso: ni constante, ni warning, ni campo en el API.

    Sus tasas, factores de ocupacion y porcentajes de perdidas organicas se
    presentaban como "estandar del mercado mexicano" sin fuente que lo sostenga.
    """

    def test_construir_emite_experimental_model_warning(self):
        with pytest.warns(ExperimentalModelWarning, match="ILUSTRATIVOS"):
            AccidentesEnfermedades(35, "masculino", Decimal("1000000"))

    def test_el_aviso_nombra_que_el_sexo_no_altera_la_prima(self):
        """El constructor exige sexo y la prima no lo usa: hay que decirlo."""
        hombre = AccidentesEnfermedades(35, "masculino", Decimal("1000000"))
        mujer = AccidentesEnfermedades(35, "femenino", Decimal("1000000"))
        assert hombre.calcular_prima() == mujer.calcular_prima()
        assert "el sexo se registra pero no altera la prima" in DISCLAIMER

    def test_una_entrada_invalida_no_emite_el_aviso(self):
        with warnings.catch_warnings(record=True) as capturadas:
            warnings.simplefilter("always")
            with pytest.raises(ValueError):
                AccidentesEnfermedades(17, "masculino", Decimal("500000"))
        assert not [c for c in capturadas if issubclass(c.category, ExperimentalModelWarning)]

    def test_el_nivel_de_respaldo_es_experimental(self):
        assert VALIDATION_TIER == "experimental"
