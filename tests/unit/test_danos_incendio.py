"""
Tests para el producto de seguro de incendio y danos a propiedad.

~20 tests cubriendo:
- Construccion valida con distintas combinaciones de tipo, zona y uso
- Validaciones de entrada (tipo, zona, uso, valor)
- Calculo de prima con verificacion manual
- Consulta de factores contra diccionarios internos
- Cotizacion completa (claves, tipos, coherencia)
- Valores limite (muy pequenos y muy grandes)
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest

from suite_actuarial.danos.incendio import (
    FACTOR_USO,
    TASAS_CONSTRUCCION,
    ZONAS_INCENDIO,
    SeguroIncendio,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def casa_habitacional():
    """Casa habitacional de concreto en zona urbana baja."""
    return SeguroIncendio(
        valor_inmueble=Decimal("2000000"),
        tipo_construccion="concreto",
        zona="urbana_baja",
        uso="habitacional",
    )


@pytest.fixture
def bodega_industrial():
    """Bodega de lamina en zona industrial."""
    return SeguroIncendio(
        valor_inmueble=Decimal("5000000"),
        tipo_construccion="lamina",
        zona="industrial",
        uso="bodega",
    )


@pytest.fixture
def oficina_mixta():
    """Oficinas en construccion mixta, zona urbana media."""
    return SeguroIncendio(
        valor_inmueble=Decimal("3500000"),
        tipo_construccion="mixta",
        zona="urbana_media",
        uso="oficinas",
    )


# ---------------------------------------------------------------------------
# 1. Construccion valida (distintas combinaciones)
# ---------------------------------------------------------------------------


class TestConstruccionValida:
    """Instanciacion correcta con diversas combinaciones de parametros."""

    def test_concreto_urbana_baja_habitacional(self, casa_habitacional):
        assert casa_habitacional.tipo_construccion == "concreto"
        assert casa_habitacional.zona == "urbana_baja"
        assert casa_habitacional.uso == "habitacional"
        assert casa_habitacional.valor_inmueble == Decimal("2000000")

    def test_lamina_industrial_bodega(self, bodega_industrial):
        assert bodega_industrial.tipo_construccion == "lamina"
        assert bodega_industrial.zona == "industrial"
        assert bodega_industrial.uso == "bodega"

    def test_mixta_urbana_media_oficinas(self, oficina_mixta):
        assert oficina_mixta.tipo_construccion == "mixta"
        assert oficina_mixta.zona == "urbana_media"
        assert oficina_mixta.uso == "oficinas"

    def test_madera_forestal_restaurante(self):
        seg = SeguroIncendio(
            valor_inmueble=Decimal("800000"),
            tipo_construccion="madera",
            zona="forestal",
            uso="restaurante",
        )
        assert seg.tasa_base == Decimal("2.50")
        assert seg.factor_zona == Decimal("1.60")
        assert seg.factor_uso == Decimal("1.45")


# ---------------------------------------------------------------------------
# 2. Errores de validacion
# ---------------------------------------------------------------------------


class TestValidaciones:
    """Cada parametro invalido debe lanzar ValueError descriptivo."""

    def test_tipo_construccion_invalido(self):
        with pytest.raises(ValueError, match="Tipo de construccion desconocido"):
            SeguroIncendio(
                valor_inmueble=Decimal("1000000"),
                tipo_construccion="adobe",
                zona="urbana_media",
                uso="habitacional",
            )

    def test_zona_invalida(self):
        with pytest.raises(ValueError, match="Zona desconocida"):
            SeguroIncendio(
                valor_inmueble=Decimal("1000000"),
                tipo_construccion="concreto",
                zona="costera",
                uso="habitacional",
            )

    def test_uso_invalido(self):
        with pytest.raises(ValueError, match="Uso desconocido"):
            SeguroIncendio(
                valor_inmueble=Decimal("1000000"),
                tipo_construccion="concreto",
                zona="urbana_media",
                uso="hospital",
            )

    def test_valor_negativo(self):
        with pytest.raises(ValueError, match="valor del inmueble debe ser positivo"):
            SeguroIncendio(
                valor_inmueble=Decimal("-500000"),
                tipo_construccion="concreto",
                zona="urbana_media",
                uso="habitacional",
            )

    def test_valor_cero(self):
        with pytest.raises(ValueError, match="valor del inmueble debe ser positivo"):
            SeguroIncendio(
                valor_inmueble=Decimal("0"),
                tipo_construccion="concreto",
                zona="urbana_media",
                uso="habitacional",
            )


# ---------------------------------------------------------------------------
# 3. Calculo de prima (verificacion manual)
# ---------------------------------------------------------------------------


class TestCalculoPrima:
    """Verificar prima = (valor / 1000) * tasa_base * factor_zona * factor_uso."""

    def test_prima_casa_habitacional(self, casa_habitacional):
        # (2_000_000 / 1000) * 0.80 * 0.85 * 1.00 = 2000 * 0.68 = 1360.00
        expected = Decimal("1360.00")
        assert casa_habitacional.calcular_prima() == expected

    def test_prima_bodega_industrial(self, bodega_industrial):
        # (5_000_000 / 1000) * 3.00 * 1.40 * 1.35 = 5000 * 5.67 = 28350.00
        expected = Decimal("28350.00")
        assert bodega_industrial.calcular_prima() == expected

    def test_prima_oficina_mixta(self, oficina_mixta):
        # (3_500_000 / 1000) * 1.20 * 1.00 * 1.10 = 3500 * 1.32 = 4620.00
        expected = Decimal("4620.00")
        assert oficina_mixta.calcular_prima() == expected

    def test_prima_acero_rural_comercial(self):
        seg = SeguroIncendio(
            valor_inmueble=Decimal("10000000"),
            tipo_construccion="acero",
            zona="rural",
            uso="comercial",
        )
        # (10_000_000 / 1000) * 0.90 * 1.10 * 1.20 = 10000 * 1.188 = 11880.00
        expected = Decimal("11880.00")
        assert seg.calcular_prima() == expected


# ---------------------------------------------------------------------------
# 4. Consulta de factores
# ---------------------------------------------------------------------------


class TestFactores:
    """Los atributos de factores deben coincidir con los diccionarios globales."""

    def test_tasa_base_coincide_con_diccionario(self, casa_habitacional):
        assert casa_habitacional.tasa_base == TASAS_CONSTRUCCION["concreto"]

    def test_factor_zona_coincide_con_diccionario(self, bodega_industrial):
        assert bodega_industrial.factor_zona == ZONAS_INCENDIO["industrial"]

    def test_factor_uso_coincide_con_diccionario(self, oficina_mixta):
        assert oficina_mixta.factor_uso == FACTOR_USO["oficinas"]

    @pytest.mark.parametrize(
        "tipo, expected_tasa",
        [
            ("concreto", Decimal("0.80")),
            ("madera", Decimal("2.50")),
            ("lamina", Decimal("3.00")),
        ],
    )
    def test_tasas_construccion_seleccionadas(self, tipo, expected_tasa):
        assert TASAS_CONSTRUCCION[tipo] == expected_tasa


# ---------------------------------------------------------------------------
# 5. Cotizacion completa
# ---------------------------------------------------------------------------


class TestCotizacion:
    """generar_cotizacion() devuelve dict con las claves y tipos esperados."""

    EXPECTED_KEYS = {
        "valor_inmueble",
        "tipo_construccion",
        "tasa_base",
        "zona",
        "factor_zona",
        "uso",
        "factor_uso",
        "prima_anual",
    }

    def test_claves_presentes(self, casa_habitacional):
        cot = casa_habitacional.generar_cotizacion()
        assert set(cot.keys()) == self.EXPECTED_KEYS

    def test_tipos_de_valores(self, casa_habitacional):
        cot = casa_habitacional.generar_cotizacion()
        assert isinstance(cot["valor_inmueble"], Decimal)
        assert isinstance(cot["tipo_construccion"], str)
        assert isinstance(cot["tasa_base"], Decimal)
        assert isinstance(cot["zona"], str)
        assert isinstance(cot["factor_zona"], Decimal)
        assert isinstance(cot["uso"], str)
        assert isinstance(cot["factor_uso"], Decimal)
        assert isinstance(cot["prima_anual"], Decimal)

    def test_cotizacion_coherente_con_prima(self, bodega_industrial):
        cot = bodega_industrial.generar_cotizacion()
        assert cot["prima_anual"] == bodega_industrial.calcular_prima()
        assert cot["valor_inmueble"] == bodega_industrial.valor_inmueble
        assert cot["tipo_construccion"] == bodega_industrial.tipo_construccion


# ---------------------------------------------------------------------------
# 6. Valores limite
# ---------------------------------------------------------------------------


class TestValoresLimite:
    """Valores extremos no deben provocar errores."""

    def test_valor_muy_pequeno(self):
        seg = SeguroIncendio(
            valor_inmueble=Decimal("100"),
            tipo_construccion="concreto",
            zona="urbana_baja",
            uso="habitacional",
        )
        prima = seg.calcular_prima()
        # (100 / 1000) * 0.80 * 0.85 * 1.00 = 0.1 * 0.68 = 0.068 -> 0.07
        expected = (
            (Decimal("100") / Decimal("1000"))
            * Decimal("0.80")
            * Decimal("0.85")
            * Decimal("1.00")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert prima == expected

    def test_valor_muy_grande(self):
        seg = SeguroIncendio(
            valor_inmueble=Decimal("999999999"),
            tipo_construccion="ladrillo",
            zona="urbana_alta",
            uso="industrial",
        )
        prima = seg.calcular_prima()
        # (999_999_999 / 1000) * 1.00 * 1.15 * 1.50 = 999999.999 * 1.725
        expected = (
            (Decimal("999999999") / Decimal("1000"))
            * Decimal("1.00")
            * Decimal("1.15")
            * Decimal("1.50")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert prima == expected

    def test_valor_un_peso(self):
        seg = SeguroIncendio(
            valor_inmueble=Decimal("1"),
            tipo_construccion="acero",
            zona="forestal",
            uso="restaurante",
        )
        prima = seg.calcular_prima()
        # (1 / 1000) * 0.90 * 1.60 * 1.45 = 0.001 * 2.088 = 0.002088 -> 0.00
        expected = (
            (Decimal("1") / Decimal("1000"))
            * Decimal("0.90")
            * Decimal("1.60")
            * Decimal("1.45")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert prima == expected
