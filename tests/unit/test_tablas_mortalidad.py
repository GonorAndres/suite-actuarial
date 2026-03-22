"""
Tests para el manejo de tablas de mortalidad
"""

from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.validators import Sexo


@pytest.fixture
def tabla_ejemplo():
    """Crea una tabla de mortalidad de ejemplo para testing"""
    datos = pd.DataFrame(
        {
            "edad": [30, 31, 32, 30, 31, 32],
            "sexo": ["H", "H", "H", "M", "M", "M"],
            "qx": [0.001, 0.0012, 0.0014, 0.0005, 0.0006, 0.0007],
        }
    )
    return TablaMortalidad(nombre="Test", datos=datos)


class TestTablaMortalidad:
    """Tests para la clase TablaMortalidad"""

    def test_creacion_tabla_valida(self, tabla_ejemplo):
        """Una tabla válida debe crearse correctamente"""
        assert tabla_ejemplo.nombre == "Test"
        assert len(tabla_ejemplo.datos) == 6

    def test_tabla_sin_columnas_requeridas_falla(self):
        """Debe fallar si faltan columnas necesarias"""
        datos_invalidos = pd.DataFrame(
            {
                "edad": [30, 31],
                # Falta 'sexo' y 'qx'
            }
        )

        with pytest.raises(ValueError) as exc_info:
            TablaMortalidad(nombre="Invalida", datos=datos_invalidos)

        assert "columnas requeridas" in str(exc_info.value).lower()

    def test_obtener_qx_exacto(self, tabla_ejemplo):
        """Debe obtener qx cuando existe el valor exacto"""
        qx = tabla_ejemplo.obtener_qx(edad=30, sexo=Sexo.HOMBRE)
        assert qx == Decimal("0.001")

        qx_mujer = tabla_ejemplo.obtener_qx(edad=30, sexo=Sexo.MUJER)
        assert qx_mujer == Decimal("0.0005")

    def test_obtener_qx_inexistente_sin_interpolar_falla(self, tabla_ejemplo):
        """Debe fallar si no existe el valor y no se pide interpolación"""
        with pytest.raises(ValueError) as exc_info:
            tabla_ejemplo.obtener_qx(edad=50, sexo=Sexo.HOMBRE, interpolar=False)

        assert "no existe" in str(exc_info.value).lower()

    def test_obtener_tabla_completa_hombres(self, tabla_ejemplo):
        """Debe filtrar correctamente por sexo"""
        df_hombres = tabla_ejemplo.obtener_tabla_completa(Sexo.HOMBRE)
        assert len(df_hombres) == 3
        assert all(df_hombres["sexo"] == "H")

    def test_calcular_lx(self, tabla_ejemplo):
        """Debe calcular lx correctamente"""
        tabla_vida = tabla_ejemplo.calcular_lx(Sexo.HOMBRE, raiz=100000)

        # Verificar que lx disminuye
        assert tabla_vida.iloc[0]["lx"] == 100000
        assert tabla_vida.iloc[1]["lx"] < tabla_vida.iloc[0]["lx"]
        assert tabla_vida.iloc[2]["lx"] < tabla_vida.iloc[1]["lx"]

        # Verificar que dx existe
        assert "dx" in tabla_vida.columns


class TestCargaEMSSA09:
    """Tests para cargar la tabla EMSSA-09 de ejemplo"""

    def test_cargar_emssa09(self):
        """Debe cargar la tabla EMSSA-09 desde el archivo CSV"""
        # Intentar cargar la tabla
        try:
            tabla = TablaMortalidad.cargar_emssa09()

            # Verificaciones básicas
            assert tabla.nombre == "EMSSA-09"
            assert len(tabla.datos) > 0

            # Verificar que tiene datos para hombres y mujeres
            assert "H" in tabla.datos["sexo"].values
            assert "M" in tabla.datos["sexo"].values

            # Verificar rangos de edad razonables
            assert tabla.datos["edad"].min() >= 18
            assert tabla.datos["edad"].max() <= 100

            # Verificar que qx está en rango válido
            assert (tabla.datos["qx"] >= 0).all()
            assert (tabla.datos["qx"] <= 1).all()

        except FileNotFoundError:
            pytest.skip("Archivo EMSSA-09 no encontrado (esperado en desarrollo)")

    def test_desde_csv(self, tmp_path):
        """Debe cargar desde CSV correctamente"""
        # Crear CSV temporal
        csv_path = tmp_path / "test_tabla.csv"
        csv_content = """edad,sexo,qx
30,H,0.001
31,H,0.0012
30,M,0.0005
31,M,0.0006
"""
        csv_path.write_text(csv_content)

        # Cargar tabla
        tabla = TablaMortalidad.desde_csv(csv_path)

        assert tabla.nombre == "test_tabla"
        assert len(tabla.datos) == 4
