"""
Tests para Gastos Medicos Mayores (GMM).

~25 tests cubriendo:
- Mapeo de bandas de edad
- Calculo de prima base
- Aplicacion de factores (zona, nivel, deducible, coaseguro)
- Desglose de prima
- Simulacion de gasto medico
- Casos extremos (edad 0, 65+, deducibles min/max)
- Relaciones monotónicas (mayor edad = mayor prima, mayor deducible = menor prima)
"""

from decimal import Decimal

import pytest

from suite_actuarial.salud.gmm import GMM, NivelHospitalario, ZonaGeografica

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def gmm_base():
    """GMM estandar: 35 anos, CDMX, nivel medio, deducible 50k, coaseguro 10%."""
    return GMM(
        edad=35,
        sexo="M",
        suma_asegurada=Decimal("5000000"),
        deducible=Decimal("50000"),
        coaseguro_pct=Decimal("0.10"),
        tope_coaseguro=Decimal("150000"),
        zona=ZonaGeografica.URBANO,
        nivel=NivelHospitalario.MEDIO,
    )


@pytest.fixture
def gmm_joven():
    """GMM para bebe: edad 0."""
    return GMM(
        edad=0,
        sexo="F",
        suma_asegurada=Decimal("3000000"),
        deducible=Decimal("25000"),
        coaseguro_pct=Decimal("0.10"),
        zona=ZonaGeografica.METRO,
        nivel=NivelHospitalario.MEDIO,
    )


@pytest.fixture
def gmm_senior():
    """GMM para adulto mayor: edad 68."""
    return GMM(
        edad=68,
        sexo="M",
        suma_asegurada=Decimal("10000000"),
        deducible=Decimal("100000"),
        coaseguro_pct=Decimal("0.20"),
        tope_coaseguro=Decimal("500000"),
        zona=ZonaGeografica.METRO,
        nivel=NivelHospitalario.ALTO,
    )


# ---------------------------------------------------------------------------
# Tests de bandas de edad
# ---------------------------------------------------------------------------

class TestBandasEdad:
    def test_banda_edad_0(self):
        g = GMM(0, "M", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))
        assert g._obtener_banda_edad() == "0-4"

    def test_banda_edad_4(self):
        g = GMM(4, "F", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))
        assert g._obtener_banda_edad() == "0-4"

    def test_banda_edad_5(self):
        g = GMM(5, "M", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))
        assert g._obtener_banda_edad() == "5-9"

    def test_banda_edad_25(self):
        g = GMM(25, "M", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))
        assert g._obtener_banda_edad() == "25-29"

    def test_banda_edad_64(self):
        g = GMM(64, "M", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))
        assert g._obtener_banda_edad() == "60-64"

    def test_banda_edad_65(self):
        g = GMM(65, "M", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))
        assert g._obtener_banda_edad() == "65+"

    def test_banda_edad_100(self):
        g = GMM(100, "F", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))
        assert g._obtener_banda_edad() == "65+"


# ---------------------------------------------------------------------------
# Tests de prima base
# ---------------------------------------------------------------------------

class TestPrimaBase:
    def test_prima_base_positiva(self, gmm_base):
        prima = gmm_base.calcular_prima_base()
        assert prima > 0

    def test_prima_base_calculo_manual(self):
        """Edad 35 => banda 35-39, tasa 9.0, SA 5M => (5M/1000)*9 = 45000."""
        g = GMM(35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"))
        prima = g.calcular_prima_base()
        assert prima == Decimal("45000.00")

    def test_prima_base_bebe(self, gmm_joven):
        """Edad 0 => banda 0-4, tasa 8.5, SA 3M => (3M/1000)*8.5 = 25500."""
        prima = gmm_joven.calcular_prima_base()
        assert prima == Decimal("25500.00")

    def test_prima_base_senior(self, gmm_senior):
        """Edad 68 => banda 65+, tasa 62.0, SA 10M => (10M/1000)*62 = 620000."""
        prima = gmm_senior.calcular_prima_base()
        assert prima == Decimal("620000.00")


# ---------------------------------------------------------------------------
# Tests de factores
# ---------------------------------------------------------------------------

class TestFactores:
    def test_factor_zona_metro(self):
        g_metro = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
            zona=ZonaGeografica.METRO, nivel=NivelHospitalario.MEDIO,
        )
        g_urbano = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
            zona=ZonaGeografica.URBANO, nivel=NivelHospitalario.MEDIO,
        )
        assert g_metro.calcular_prima_ajustada() > g_urbano.calcular_prima_ajustada()

    def test_factor_zona_foraneo_menor(self):
        g_foraneo = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
            zona=ZonaGeografica.FORANEO, nivel=NivelHospitalario.MEDIO,
        )
        g_urbano = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
            zona=ZonaGeografica.URBANO, nivel=NivelHospitalario.MEDIO,
        )
        assert g_foraneo.calcular_prima_ajustada() < g_urbano.calcular_prima_ajustada()

    def test_factor_nivel_alto_mayor(self):
        g_alto = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
            nivel=NivelHospitalario.ALTO,
        )
        g_medio = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
            nivel=NivelHospitalario.MEDIO,
        )
        assert g_alto.calcular_prima_ajustada() > g_medio.calcular_prima_ajustada()

    def test_factor_nivel_estandar_menor(self):
        g_estandar = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
            nivel=NivelHospitalario.ESTANDAR,
        )
        g_medio = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
            nivel=NivelHospitalario.MEDIO,
        )
        assert g_estandar.calcular_prima_ajustada() < g_medio.calcular_prima_ajustada()

    def test_deducible_alto_menor_prima(self):
        g_ded_alto = GMM(
            35, "M", Decimal("5000000"), Decimal("500000"), Decimal("0.10"),
        )
        g_ded_bajo = GMM(
            35, "M", Decimal("5000000"), Decimal("10000"), Decimal("0.10"),
        )
        assert g_ded_alto.calcular_prima_ajustada() < g_ded_bajo.calcular_prima_ajustada()

    def test_coaseguro_alto_menor_prima(self):
        g_coa_30 = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.30"),
        )
        g_coa_10 = GMM(
            35, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
        )
        assert g_coa_30.calcular_prima_ajustada() < g_coa_10.calcular_prima_ajustada()

    def test_factor_deducible_interpolacion(self):
        """Deducible no estandar (75000) se interpola linealmente."""
        g = GMM(
            35, "M", Decimal("5000000"), Decimal("75000"), Decimal("0.10"),
        )
        factor = g._obtener_factor_deducible()
        # Between 50000 (1.00) and 100000 (0.80), at 50% => 0.90
        assert factor == Decimal("0.9000")


# ---------------------------------------------------------------------------
# Tests de mayor edad = mayor prima
# ---------------------------------------------------------------------------

class TestEdadMonotona:
    def test_mayor_edad_mayor_prima(self):
        """Primas deben crecer con la edad (misma configuracion)."""
        primas = []
        for edad in [20, 35, 50, 65]:
            g = GMM(
                edad, "M", Decimal("5000000"), Decimal("50000"), Decimal("0.10"),
            )
            primas.append(g.calcular_prima_ajustada())
        for i in range(len(primas) - 1):
            assert primas[i] < primas[i + 1]


# ---------------------------------------------------------------------------
# Tests de desglose
# ---------------------------------------------------------------------------

class TestDesglose:
    def test_desglose_estructura(self, gmm_base):
        desglose = gmm_base.desglose_prima()
        assert "asegurado" in desglose
        assert "producto" in desglose
        assert "tarificacion" in desglose
        assert "siniestralidad_esperada" in desglose

    def test_desglose_asegurado(self, gmm_base):
        desglose = gmm_base.desglose_prima()
        assert desglose["asegurado"]["edad"] == 35
        assert desglose["asegurado"]["sexo"] == "M"
        assert desglose["asegurado"]["banda_edad"] == "35-39"

    def test_desglose_tarificacion_coherente(self, gmm_base):
        desglose = gmm_base.desglose_prima()
        tarif = desglose["tarificacion"]
        # prima_ajustada = prima_base * all factors
        expected = (
            tarif["prima_base"]
            * tarif["factor_zona"]
            * tarif["factor_nivel"]
            * tarif["factor_deducible"]
            * tarif["factor_coaseguro"]
        ).quantize(Decimal("0.01"))
        assert tarif["prima_ajustada"] == expected


# ---------------------------------------------------------------------------
# Tests de simulacion de gasto medico
# ---------------------------------------------------------------------------

class TestSimulacionGasto:
    def test_gasto_menor_deducible(self, gmm_base):
        """Gasto menor al deducible: asegurado paga todo."""
        result = gmm_base.simular_gasto_medico(Decimal("30000"))
        assert result["pago_aseguradora"] == Decimal("0")
        assert result["pago_total_asegurado"] == Decimal("30000")

    def test_gasto_igual_deducible(self, gmm_base):
        """Gasto igual al deducible: asegurado paga todo."""
        result = gmm_base.simular_gasto_medico(Decimal("50000"))
        assert result["pago_aseguradora"] == Decimal("0")
        assert result["pago_total_asegurado"] == Decimal("50000")

    def test_gasto_con_coaseguro(self, gmm_base):
        """Gasto 200k: deducible 50k, excedente 150k, coaseguro 10% = 15k."""
        result = gmm_base.simular_gasto_medico(Decimal("200000"))
        assert result["deducible_aplicado"] == Decimal("50000")
        assert result["monto_excedente"] == Decimal("150000")
        assert result["coaseguro_asegurado"] == Decimal("15000.00")
        expected_aseguradora = Decimal("150000") - Decimal("15000")
        assert result["pago_aseguradora"] == expected_aseguradora

    def test_gasto_con_tope_coaseguro(self, gmm_base):
        """Gasto grande: tope de coaseguro debe limitar pago del asegurado."""
        # Tope es 150,000. Gasto 3M. Excedente = 2.95M. Coaseguro 10% = 295k > tope.
        result = gmm_base.simular_gasto_medico(Decimal("3000000"))
        assert result["coaseguro_asegurado"] == Decimal("150000")  # capped at tope

    def test_gasto_excede_suma_asegurada(self, gmm_base):
        """Gasto mayor a la SA: el exceso no se cubre."""
        result = gmm_base.simular_gasto_medico(Decimal("6000000"))
        assert result["exceso_no_cubierto"] == Decimal("1000000")

    def test_gasto_cero(self, gmm_base):
        """Sin reclamacion."""
        result = gmm_base.simular_gasto_medico(Decimal("0"))
        assert result["pago_aseguradora"] == Decimal("0")
        assert result["pago_total_asegurado"] == Decimal("0")

    def test_gasto_negativo_error(self, gmm_base):
        with pytest.raises(ValueError, match="negativo"):
            gmm_base.simular_gasto_medico(Decimal("-100"))


# ---------------------------------------------------------------------------
# Tests de validaciones de entrada
# ---------------------------------------------------------------------------

class TestValidaciones:
    def test_edad_negativa(self):
        with pytest.raises(ValueError, match="edad"):
            GMM(-1, "M", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))

    def test_edad_mayor_110(self):
        with pytest.raises(ValueError, match="edad"):
            GMM(111, "M", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))

    def test_sexo_invalido(self):
        with pytest.raises(ValueError, match="sexo"):
            GMM(35, "X", Decimal("1000000"), Decimal("50000"), Decimal("0.10"))

    def test_suma_asegurada_minima(self):
        with pytest.raises(ValueError, match="minima"):
            GMM(35, "M", Decimal("500000"), Decimal("50000"), Decimal("0.10"))
