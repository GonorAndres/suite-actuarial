"""
Tests para los validadores Pydantic

Verifica que las validaciones de datos funcionen correctamente.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from mexican_insurance.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    Fumador,
    Moneda,
    RegistroMortalidad,
    ResultadoCalculo,
    Sexo,
)


class TestAsegurado:
    """Tests para la clase Asegurado"""

    def test_asegurado_valido(self):
        """Un asegurado con datos válidos debe crearse sin problemas"""
        asegurado = Asegurado(
            edad=35,
            sexo=Sexo.HOMBRE,
            suma_asegurada=Decimal("1000000"),
        )

        assert asegurado.edad == 35
        assert asegurado.sexo == Sexo.HOMBRE
        assert asegurado.suma_asegurada == Decimal("1000000")
        assert asegurado.fumador == Fumador.NO_ESPECIFICADO

    def test_edad_negativa_falla(self):
        """No se permite edad negativa"""
        with pytest.raises(ValidationError) as exc_info:
            Asegurado(
                edad=-5,
                sexo=Sexo.HOMBRE,
                suma_asegurada=Decimal("1000000"),
            )

        assert "edad" in str(exc_info.value).lower()

    def test_suma_asegurada_cero_falla(self):
        """Suma asegurada debe ser mayor a cero"""
        with pytest.raises(ValidationError) as exc_info:
            Asegurado(
                edad=35,
                sexo=Sexo.HOMBRE,
                suma_asegurada=Decimal("0"),
            )

        # Pydantic v2 usa el nombre del campo (con underscore) en errores
        assert "suma_asegurada" in str(exc_info.value).lower()

    def test_suma_asegurada_excesiva_falla(self):
        """Suma asegurada no debe ser ridículamente alta"""
        with pytest.raises(ValidationError) as exc_info:
            Asegurado(
                edad=35,
                sexo=Sexo.HOMBRE,
                suma_asegurada=Decimal("1e13"),  # 10 billones
            )

        assert "excesivamente alta" in str(exc_info.value).lower()

    def test_sexo_desde_string(self):
        """Debe aceptar sexo como string"""
        asegurado = Asegurado(
            edad=35,
            sexo="H",
            suma_asegurada=Decimal("1000000"),
        )

        assert asegurado.sexo == Sexo.HOMBRE


class TestConfiguracionProducto:
    """Tests para ConfiguracionProducto"""

    def test_configuracion_valida(self):
        """Configuración válida debe crearse correctamente"""
        config = ConfiguracionProducto(
            nombre_producto="Vida Temporal 20 años",
            plazo_years=20,
            tasa_interes_tecnico=Decimal("0.055"),
        )

        assert config.nombre_producto == "Vida Temporal 20 años"
        assert config.plazo_years == 20
        assert config.tasa_interes_tecnico == Decimal("0.055")

    def test_tasa_interes_negativa_falla(self):
        """Tasa de interés no puede ser negativa"""
        with pytest.raises(ValidationError) as exc_info:
            ConfiguracionProducto(
                nombre_producto="Producto Test",
                plazo_years=10,
                tasa_interes_tecnico=Decimal("-0.01"),
            )

        # Pydantic v2 no menciona "negativa", solo valida >= 0
        assert "tasa_interes_tecnico" in str(exc_info.value).lower()

    def test_recargos_excesivos_falla(self):
        """Recargos totales no deben superar 100%"""
        with pytest.raises(ValidationError) as exc_info:
            ConfiguracionProducto(
                nombre_producto="Producto Test",
                plazo_years=10,
                recargo_gastos_admin=Decimal("0.50"),
                recargo_gastos_adq=Decimal("0.40"),
                recargo_utilidad=Decimal("0.30"),  # Total = 120%
            )

        assert "100%" in str(exc_info.value)

    def test_valores_por_defecto(self):
        """Debe usar valores por defecto razonables"""
        config = ConfiguracionProducto(
            nombre_producto="Test",
            plazo_years=10,
        )

        assert config.tasa_interes_tecnico == Decimal("0.055")
        assert config.moneda == Moneda.MXN


class TestResultadoCalculo:
    """Tests para ResultadoCalculo"""

    def test_resultado_valido(self):
        """Resultado válido debe crearse correctamente"""
        resultado = ResultadoCalculo(
            prima_neta=Decimal("5000"),
            prima_total=Decimal("5900"),
            moneda=Moneda.MXN,
            desglose_recargos={
                "gastos_admin": Decimal("250"),
                "gastos_adq": Decimal("500"),
                "utilidad": Decimal("150"),
            },
        )

        assert resultado.prima_neta == Decimal("5000")
        assert resultado.prima_total == Decimal("5900")

    def test_prima_total_menor_que_neta_falla(self):
        """Prima total no puede ser menor a prima neta"""
        with pytest.raises(ValidationError) as exc_info:
            ResultadoCalculo(
                prima_neta=Decimal("5000"),
                prima_total=Decimal("4000"),  # Menor!
                moneda=Moneda.MXN,
            )

        assert "menor" in str(exc_info.value).lower()


class TestRegistroMortalidad:
    """Tests para RegistroMortalidad"""

    def test_registro_valido(self):
        """Registro válido de mortalidad"""
        registro = RegistroMortalidad(
            edad=35,
            sexo=Sexo.HOMBRE,
            qx=Decimal("0.001234"),
            lx=98765,
        )

        assert registro.edad == 35
        assert registro.qx == Decimal("0.001234")

    def test_qx_fuera_de_rango_falla(self):
        """qx debe estar entre 0 y 1"""
        with pytest.raises(ValidationError) as exc_info:
            RegistroMortalidad(
                edad=35,
                sexo=Sexo.HOMBRE,
                qx=Decimal("1.5"),  # Mayor a 1
            )

        # Pydantic v2 valida el rango pero no usa "0 y 1" en el mensaje
        assert "qx" in str(exc_info.value).lower()

    def test_qx_negativo_falla(self):
        """qx no puede ser negativo"""
        with pytest.raises(ValidationError) as exc_info:
            RegistroMortalidad(
                edad=35,
                sexo=Sexo.HOMBRE,
                qx=Decimal("-0.001"),
            )

        # Pydantic v2 valida el rango pero no usa "0 y 1" en el mensaje
        assert "qx" in str(exc_info.value).lower()
