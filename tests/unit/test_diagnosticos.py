"""Tests para diagnósticos de reserva.

Mack (1993) ya está implementado (`reservas/mack.py`, pruebas en
`tests/unit/test_mack.py`). Lo que queda aquí es la banda de dispersión
agrupada, que sigue existiendo como señal cruda de estabilidad del triángulo.
Estas pruebas fijan que la banda **no** se confunda con un error de predicción:
sobre el mismo triángulo donde Mack da cero, la banda da un positivo grande.
"""

from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.core.warnings import ExperimentalModelWarning
from suite_actuarial.reservas.diagnosticos import (
    MackUncertainty,
    banda_dispersion_link_ratios,
    calcular_mack_uncertainty,
    validar_reserva,
)
from suite_actuarial.reservas.mack import ResultadoMack, calcular_mack


@pytest.fixture
def triangulo_multiplicativo():
    """Triángulo exactamente multiplicativo: C[i,j] = a[i] * b[j].

    Dentro de cada periodo de desarrollo todas las razones age-to-age son
    idénticas, así que la varianza de Mack sigma_k^2 es exactamente cero para
    todo k, y el error estándar total de Mack es cero.
    """
    a = [1000.0, 1200.0, 1500.0, 1800.0]
    b = [1.0, 1.5, 1.8, 1.9]
    data = {j: [a[i] * b[j] if i + j <= 3 else None for i in range(4)] for j in range(4)}
    return pd.DataFrame(data, index=[2021, 2022, 2023, 2024])


@pytest.fixture
def triangulo_real():
    """Triángulo con dispersión genuina entre filas."""
    data = {
        0: [3000.0, 3200.0, 3500.0, 3800.0],
        1: [5000.0, 5200.0, 5500.0, None],
        2: [5600.0, 5800.0, None, None],
        3: [5800.0, None, None, None],
    }
    return pd.DataFrame(data, index=[2021, 2022, 2023, 2024])


class TestBandaNoEsMack:
    """La banda agrupada mide otra cosa que el error de predicción de Mack."""

    def test_donde_mack_da_cero_la_banda_da_un_positivo_grande(self, triangulo_multiplicativo):
        """Contraste directo entre las dos medidas sobre el mismo triángulo.

        En un triángulo exactamente multiplicativo cada razón age-to-age es
        constante dentro de su periodo de desarrollo: `calcular_mack` devuelve
        sigma_k = 0 para todo k y error estándar cero, que es la respuesta
        correcta. La banda agrupa los periodos, así que mide la variación
        *entre* periodos (1.5, 1.2, 1.056) y devuelve un positivo grande.

        Esto no es un defecto de la banda — es lo que la banda es. La prueba
        existe para que las dos cantidades no se confundan en una interfaz.
        """
        with pytest.warns(ExperimentalModelWarning):
            banda = banda_dispersion_link_ratios(triangulo_multiplicativo, Decimal("1000"))
        mack = calcular_mack(triangulo_multiplicativo)

        assert float(mack.standard_error) == pytest.approx(0.0, abs=1e-9)
        assert banda.standard_error > Decimal("100")
        assert banda.method == "dispersion-link-ratios"

    def test_no_se_llama_a_si_misma_mack(self, triangulo_real):
        """El método reportado no puede afirmar Mack."""
        with pytest.warns(ExperimentalModelWarning):
            banda = banda_dispersion_link_ratios(triangulo_real, Decimal("1000"))

        assert "mack" not in banda.method.lower()

    def test_avisa_que_no_estima_sigma_por_periodo(self, triangulo_real):
        """La limitación viaja con la llamada, no en una nota al pie."""
        with pytest.warns(ExperimentalModelWarning, match="sigma_k por periodo"):
            banda_dispersion_link_ratios(triangulo_real, Decimal("1000"))

    def test_alias_deprecado_devuelve_el_mack_real(self, triangulo_real):
        """La firma vieja sobrevive, pero ahora entrega el modelo real.

        `reserva` se ignora: Mack deriva la suya con factores ponderados por
        volumen, que es lo único con lo que su error estándar es coherente.
        """
        with pytest.warns(DeprecationWarning, match="calcular_mack"):
            resultado = calcular_mack_uncertainty(triangulo_real, Decimal("999999"))

        directo = calcular_mack(triangulo_real)

        assert isinstance(resultado, ResultadoMack)
        assert MackUncertainty is ResultadoMack
        assert resultado.method == "mack-1993"
        assert resultado.reserva_total == directo.reserva_total
        assert resultado.reserva_total != Decimal("999999")


class TestBandaDispersion:
    """Propiedades estructurales de la banda tal como está definida."""

    def test_rango_es_simetrico_alrededor_de_la_reserva(self, triangulo_real):
        """El rango es reserva +/- z*SE por construcción, sin cobertura real.

        Se verifica la construcción declarada — no una propiedad estadística —
        justamente porque no la tiene: `reserve_range` no es un intervalo de
        confianza y esta prueba documenta que solo es aritmética.
        """
        reserva = Decimal("1000")
        with pytest.warns(ExperimentalModelWarning):
            banda = banda_dispersion_link_ratios(triangulo_real, reserva, confidence_z=Decimal("2"))

        inferior, superior = banda.reserve_range
        assert superior - reserva == pytest.approx(
            Decimal("2") * banda.standard_error, abs=Decimal("0.02")
        )
        # El inferior se pisa en cero: la reserva no puede ser negativa aquí.
        assert inferior >= Decimal("0")

    def test_escala_linealmente_con_la_reserva(self, triangulo_real):
        """Duplicar la reserva duplica el SE; el CV queda invariante.

        La dispersión de los link ratios no depende del nivel de la reserva,
        así que el escalamiento es puramente multiplicativo. Es una propiedad
        de invarianza, no una repetición de la fórmula.
        """
        with pytest.warns(ExperimentalModelWarning):
            banda_1 = banda_dispersion_link_ratios(triangulo_real, Decimal("1000"))
            banda_2 = banda_dispersion_link_ratios(triangulo_real, Decimal("2000"))

        assert banda_2.standard_error == pytest.approx(
            2 * banda_1.standard_error, abs=Decimal("0.02")
        )
        assert banda_2.coefficient_of_variation == pytest.approx(
            banda_1.coefficient_of_variation, abs=Decimal("0.0002")
        )

    def test_triangulo_vacio_falla(self):
        with pytest.raises(ValueError, match="no vacio"):
            banda_dispersion_link_ratios(pd.DataFrame(), Decimal("1000"))

    def test_sin_link_ratios_suficientes_falla(self):
        """Una sola razón no permite una desviación estándar muestral."""
        triangulo = pd.DataFrame({0: [1000.0, 1200.0], 1: [1500.0, None]})
        with pytest.raises(ValueError, match="dispersion"):
            banda_dispersion_link_ratios(triangulo, Decimal("1000"))


class TestValidarReserva:
    """Reporte de calidad y disclosure de supuestos."""

    def test_reporta_ambas_medidas_por_separado(self, triangulo_real):
        """Mack y la banda agrupada conviven, cada una con su etiqueta.

        Confundirlas fue el hallazgo A9a. El reporte las nombra distinto y
        declara el límite de cada una.
        """
        with pytest.warns(ExperimentalModelWarning):
            reporte = validar_reserva(triangulo_real, Decimal("1000"), metodo="chain_ladder")

        assert reporte.diagnostics["mack_metodo"] == "mack-1993"
        assert "mack_standard_error" in reporte.diagnostics
        assert "mack_limite" in reporte.diagnostics
        assert reporte.diagnostics["dispersion_metodo"] == "dispersion-link-ratios"
        assert "dispersion_limite" in reporte.diagnostics

    def test_expone_la_diferencia_contra_la_reserva_del_metodo(self, triangulo_real):
        """El rango de Mack se centra en la reserva de Mack, no en la del método.

        Mack exige factores ponderados por volumen; un método que use otra cosa
        produce otra reserva. La diferencia se reporta en vez de esconderse
        detrás de un rango que parecería centrado en la reserva del llamador.
        """
        with pytest.warns(ExperimentalModelWarning):
            reporte = validar_reserva(
                triangulo_real, Decimal("1000"), metodo="bornhuetter_ferguson"
            )

        mack_reserva = Decimal(reporte.diagnostics["mack_reserva"])
        diferencia = Decimal(reporte.diagnostics["mack_diferencia_vs_metodo"])

        assert diferencia == mack_reserva - Decimal("1000")
        assert reporte.reserve_range is not None
        inferior, superior = reporte.reserve_range
        assert inferior <= mack_reserva <= superior

    def test_reporta_triangulo_pequeno(self):
        triangulo = pd.DataFrame({0: [1000.0, 1200.0], 1: [1500.0, None]})
        reporte = validar_reserva(triangulo, Decimal("100"), metodo="chain_ladder")

        assert any("pequeno" in f for f in reporte.data_quality_findings)
        assert reporte.method_suitability == "requires_review"

    def test_reporta_importes_negativos(self, triangulo_real):
        triangulo = triangulo_real.copy()
        triangulo.iloc[0, 0] = -100.0
        with pytest.warns(ExperimentalModelWarning):
            reporte = validar_reserva(triangulo, Decimal("1000"), metodo="chain_ladder")

        assert any("negativos" in f for f in reporte.data_quality_findings)

    def test_declara_el_tail_factor_como_supuesto_material(self, triangulo_real):
        with pytest.warns(ExperimentalModelWarning):
            reporte = validar_reserva(
                triangulo_real,
                Decimal("1000"),
                metodo="chain_ladder",
                tail_factor=Decimal("1.05"),
            )

        assert "tail_factor=1.05" in reporte.material_assumptions
