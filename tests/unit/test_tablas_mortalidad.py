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
            "sexo": ["masculino"] * 3 + ["femenino"] * 3,
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
        qx = tabla_ejemplo.obtener_qx(edad=30, sexo=Sexo.MASCULINO)
        assert qx == Decimal("0.001")

        qx_mujer = tabla_ejemplo.obtener_qx(edad=30, sexo=Sexo.FEMENINO)
        assert qx_mujer == Decimal("0.0005")

    def test_obtener_qx_inexistente_sin_interpolar_falla(self, tabla_ejemplo):
        """Debe fallar si no existe el valor y no se pide interpolación"""
        with pytest.raises(ValueError) as exc_info:
            tabla_ejemplo.obtener_qx(edad=50, sexo=Sexo.MASCULINO, interpolar=False)

        assert "no existe" in str(exc_info.value).lower()

    def test_obtener_tabla_completa_hombres(self, tabla_ejemplo):
        """Debe filtrar correctamente por sexo"""
        df_hombres = tabla_ejemplo.obtener_tabla_completa(Sexo.MASCULINO)
        assert len(df_hombres) == 3
        assert all(df_hombres["sexo"] == "masculino")

    def test_calcular_lx(self, tabla_ejemplo):
        """Debe calcular lx correctamente"""
        tabla_vida = tabla_ejemplo.calcular_lx(Sexo.MASCULINO, raiz=100000)

        # Verificar que lx disminuye
        assert tabla_vida.iloc[0]["lx"] == 100000
        assert tabla_vida.iloc[1]["lx"] < tabla_vida.iloc[0]["lx"]
        assert tabla_vida.iloc[2]["lx"] < tabla_vida.iloc[1]["lx"]

        # Verificar que dx existe
        assert "dx" in tabla_vida.columns

    def test_calcular_lx_force_zero_convention(self, tabla_ejemplo):
        """Under force_zero, last dx equals last lx (all die at omega)"""
        tabla_vida = tabla_ejemplo.calcular_lx(
            Sexo.MASCULINO, raiz=100000, omega_convention="force_zero"
        )
        last = tabla_vida.iloc[-1]
        assert last["dx"] == pytest.approx(last["lx"])

    def test_calcular_lx_table_as_is_convention(self, tabla_ejemplo):
        """Under table_as_is, last dx < last lx (some survive past omega)"""
        tabla_vida = tabla_ejemplo.calcular_lx(
            Sexo.MASCULINO, raiz=100000, omega_convention="table_as_is"
        )
        last = tabla_vida.iloc[-1]
        assert last["dx"] < last["lx"]

    def test_omega_convention_default_backward_compatible(self, tabla_ejemplo):
        """Default behavior matches explicit force_zero exactly"""
        default = tabla_ejemplo.calcular_lx(Sexo.MASCULINO, raiz=100000)
        explicit = tabla_ejemplo.calcular_lx(
            Sexo.MASCULINO, raiz=100000, omega_convention="force_zero"
        )
        pd.testing.assert_frame_equal(default, explicit)


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
            assert "masculino" in tabla.datos["sexo"].values
            assert "femenino" in tabla.datos["sexo"].values

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


class TestFronteraSexoCSV:
    """El CSV conserva "H"/"M"; la traduccion ocurre una sola vez, al leerlo.

    EMSSA-09 se distribuye con la columna `sexo` en iniciales publicadas
    (H = hombre, M = mujer) y es un insumo controlado que no se edita. El
    paquete, en cambio, solo habla "masculino"/"femenino". El punto de contacto
    entre ambas convenciones es `desde_csv`, y estas pruebas lo fijan ahi: si
    alguien moviera la traduccion a `obtener_qx` o la duplicara, la tabla en
    memoria volveria a aceptar letras y el error dejaria de saltar.
    """

    def test_csv_heredado_se_traduce_al_cargar(self, tmp_path):
        """Un CSV con H/M queda en memoria como masculino/femenino."""
        csv_path = tmp_path / "heredado.csv"
        csv_path.write_text("edad,sexo,qx\n30,H,0.001\n30,M,0.0005\n")

        tabla = TablaMortalidad.desde_csv(csv_path)

        assert set(tabla.datos["sexo"]) == {"masculino", "femenino"}
        # H era hombre: su qx debe seguir siendo el de la fila H.
        assert tabla.obtener_qx(30, Sexo.MASCULINO) == Decimal("0.001")
        assert tabla.obtener_qx(30, Sexo.FEMENINO) == Decimal("0.0005")

    def test_emssa09_publica_los_valores_actuales(self):
        """La tabla instalada no expone ninguna inicial hacia afuera."""
        tabla = TablaMortalidad.cargar_emssa09()

        assert set(tabla.datos["sexo"]) == {"masculino", "femenino"}
        assert not tabla.obtener_tabla_completa(Sexo.MASCULINO).empty
        assert not tabla.obtener_tabla_completa(Sexo.FEMENINO).empty

    def test_csv_con_convencion_mf_es_rechazado(self, tmp_path):
        """Una "F" delata la convencion opuesta, donde "M" significa hombre.

        Traducirla seria adivinar: bajo M/F la misma "M" es masculino, bajo H/M
        es mujer. El cargador se niega en vez de elegir.
        """
        csv_path = tmp_path / "convencion_mf.csv"
        csv_path.write_text("edad,sexo,qx\n30,M,0.001\n30,F,0.0005\n")

        with pytest.raises(ValueError) as exc_info:
            TablaMortalidad.desde_csv(csv_path)

        assert "no reconocidos" in str(exc_info.value)

    def test_dataframe_en_memoria_con_iniciales_es_rechazado(self):
        """Construir la tabla directamente con letras falla; no se traduce."""
        datos = pd.DataFrame(
            {
                "edad": [30, 30],
                "sexo": ["H", "M"],
                "qx": [0.001, 0.0005],
            }
        )

        with pytest.raises(ValueError) as exc_info:
            TablaMortalidad(nombre="Invalida", datos=datos)

        mensaje = str(exc_info.value)
        assert "masculino" in mensaje
        assert "femenino" in mensaje
