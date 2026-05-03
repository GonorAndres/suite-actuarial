"""
Tests para módulo de reportes regulatorios CNSF.

Tests unitarios para modelos, generadores y exportadores de reportes.
"""

import tempfile
from datetime import date
from decimal import Decimal

import pytest

from suite_actuarial.reportes import (
    DatosInversionActivo,
    DatosReporteRCS,
    DatosSiniestrosRamo,
    DatosSuscripcionRamo,
    ExportadorCSV,
    ExportadorExcel,
    GeneradorReporteInversiones,
    GeneradorReporteRCS,
    GeneradorReporteSiniestros,
    GeneradorReporteSuscripcion,
    MetadatosReporte,
    ReporteInversiones,
    ReporteRCS,
    ReporteSiniestros,
    ReporteSuscripcion,
    TipoActivoInversion,
    TipoRamo,
    TrimesteCNSF,
)

# ======================================
# Fixtures
# ======================================


@pytest.fixture
def metadata_basico():
    """Metadatos básicos para tests"""
    return MetadatosReporte(
        clave_aseguradora="A0123",
        nombre_aseguradora="Seguros XYZ S.A.",
        trimestre=TrimesteCNSF.Q1,
        anio=2024,
        fecha_presentacion=date(2024, 4, 30),
    )


@pytest.fixture
def datos_suscripcion_autos():
    """Datos de suscripción para ramo de autos"""
    return DatosSuscripcionRamo(
        ramo=TipoRamo.AUTOS,
        primas_emitidas=Decimal("50000000"),
        primas_devengadas=Decimal("48000000"),
        primas_canceladas=Decimal("2000000"),
        numero_polizas=15000,
        suma_asegurada_total=Decimal("2000000000"),
    )


@pytest.fixture
def datos_suscripcion_vida():
    """Datos de suscripción para ramo de vida"""
    return DatosSuscripcionRamo(
        ramo=TipoRamo.VIDA_INDIVIDUAL,
        primas_emitidas=Decimal("100000000"),
        primas_devengadas=Decimal("98000000"),
        primas_canceladas=Decimal("2000000"),
        numero_polizas=5000,
        suma_asegurada_total=Decimal("5000000000"),
    )


@pytest.fixture
def datos_siniestros_autos():
    """Datos de siniestros para ramo de autos"""
    return DatosSiniestrosRamo(
        ramo=TipoRamo.AUTOS,
        siniestros_ocurridos=Decimal("35000000"),
        siniestros_pagados=Decimal("28000000"),
        reserva_siniestros=Decimal("15000000"),
        numero_siniestros=450,
        numero_siniestros_pendientes=85,
    )


@pytest.fixture
def datos_inversion_gubernamentales():
    """Datos de inversión en valores gubernamentales"""
    return DatosInversionActivo(
        tipo_activo=TipoActivoInversion.VALORES_GUBERNAMENTALES,
        valor_mercado=Decimal("300000000"),
        valor_libros=Decimal("295000000"),
        rendimiento_trimestre=Decimal("0.015"),
    )


@pytest.fixture
def datos_inversion_acciones():
    """Datos de inversión en acciones"""
    return DatosInversionActivo(
        tipo_activo=TipoActivoInversion.ACCIONES,
        valor_mercado=Decimal("50000000"),
        valor_libros=Decimal("52000000"),
        rendimiento_trimestre=Decimal("-0.025"),
    )


@pytest.fixture
def datos_rcs():
    """Datos de RCS"""
    return DatosReporteRCS(
        rcs_suscripcion_vida=Decimal("18000000"),
        rcs_suscripcion_danos=Decimal("95000000"),
        rcs_inversion=Decimal("62000000"),
        rcs_total=Decimal("125000000"),
        capital_pagado=Decimal("100000000"),
        superavit=Decimal("50000000"),
    )


# ======================================
# Tests de Modelos
# ======================================


class TestMetadatosReporte:
    """Tests para MetadatosReporte"""

    def test_crear_metadata_valido(self, metadata_basico):
        """Debe crear metadatos válidos"""
        assert metadata_basico.clave_aseguradora == "A0123"
        assert metadata_basico.trimestre == TrimesteCNSF.Q1
        assert metadata_basico.anio == 2024

    def test_fecha_antes_trimestre_invalida(self):
        """Fecha de presentación antes del trimestre debe fallar"""
        with pytest.raises((ValueError, Exception)):
            MetadatosReporte(
                clave_aseguradora="A0123",
                nombre_aseguradora="Seguros XYZ",
                trimestre=TrimesteCNSF.Q1,
                anio=2024,
                fecha_presentacion=date(2024, 2, 28),  # Antes de Q1
            )


class TestDatosSuscripcionRamo:
    """Tests para DatosSuscripcionRamo"""

    def test_crear_datos_suscripcion_validos(self, datos_suscripcion_autos):
        """Debe crear datos de suscripción válidos"""
        assert datos_suscripcion_autos.ramo == TipoRamo.AUTOS
        assert datos_suscripcion_autos.primas_emitidas == Decimal("50000000")
        assert datos_suscripcion_autos.numero_polizas == 15000

    def test_primas_devengadas_razonables(self):
        """Primas devengadas razonables deben ser válidas"""
        datos = DatosSuscripcionRamo(
            ramo=TipoRamo.AUTOS,
            primas_emitidas=Decimal("50000000"),
            primas_devengadas=Decimal("48000000"),  # Razonable
            primas_canceladas=Decimal("0"),
            numero_polizas=15000,
            suma_asegurada_total=Decimal("2000000000"),
        )
        assert datos.primas_devengadas <= datos.primas_emitidas


class TestDatosSiniestrosRamo:
    """Tests para DatosSiniestrosRamo"""

    def test_crear_datos_siniestros_validos(self, datos_siniestros_autos):
        """Debe crear datos de siniestros válidos"""
        assert datos_siniestros_autos.ramo == TipoRamo.AUTOS
        assert datos_siniestros_autos.siniestros_ocurridos == Decimal("35000000")
        assert datos_siniestros_autos.numero_siniestros == 450

    def test_pendientes_exceden_total(self):
        """Pendientes mayores a total debe fallar"""
        with pytest.raises((ValueError, Exception)):
            DatosSiniestrosRamo(
                ramo=TipoRamo.AUTOS,
                siniestros_ocurridos=Decimal("35000000"),
                siniestros_pagados=Decimal("28000000"),
                reserva_siniestros=Decimal("15000000"),
                numero_siniestros=450,
                numero_siniestros_pendientes=500,  # Mayor que total
            )


class TestDatosInversionActivo:
    """Tests para DatosInversionActivo"""

    def test_ganancia_no_realizada_positiva(self, datos_inversion_gubernamentales):
        """Debe calcular ganancia no realizada positiva"""
        ganancia = datos_inversion_gubernamentales.ganancia_no_realizada
        assert ganancia == Decimal("5000000")  # 300M - 295M

    def test_perdida_no_realizada(self, datos_inversion_acciones):
        """Debe calcular pérdida no realizada (negativa)"""
        ganancia = datos_inversion_acciones.ganancia_no_realizada
        assert ganancia == Decimal("-2000000")  # 50M - 52M


class TestDatosReporteRCS:
    """Tests para DatosReporteRCS"""

    def test_capital_disponible(self, datos_rcs):
        """Debe calcular capital disponible correctamente"""
        assert datos_rcs.capital_disponible == Decimal("150000000")  # 100M + 50M

    def test_ratio_solvencia(self, datos_rcs):
        """Debe calcular ratio de solvencia"""
        # 150M / 125M = 1.2 = 120%
        assert datos_rcs.ratio_solvencia == Decimal("1.2")

    def test_cumple_regulacion_si(self, datos_rcs):
        """Debe indicar que cumple regulación"""
        assert datos_rcs.cumple_regulacion is True

    def test_cumple_regulacion_no(self):
        """Debe indicar que NO cumple regulación"""
        datos = DatosReporteRCS(
            rcs_suscripcion_vida=Decimal("18000000"),
            rcs_suscripcion_danos=Decimal("95000000"),
            rcs_inversion=Decimal("62000000"),
            rcs_total=Decimal("125000000"),
            capital_pagado=Decimal("80000000"),  # Insuficiente
            superavit=Decimal("30000000"),
        )
        assert datos.cumple_regulacion is False  # 110M < 125M

    def test_excedente_positivo(self, datos_rcs):
        """Debe calcular excedente positivo"""
        assert datos_rcs.excedente_deficit == Decimal("25000000")  # 150M - 125M

    def test_deficit_negativo(self):
        """Debe calcular déficit negativo"""
        datos = DatosReporteRCS(
            rcs_suscripcion_vida=Decimal("18000000"),
            rcs_suscripcion_danos=Decimal("95000000"),
            rcs_inversion=Decimal("62000000"),
            rcs_total=Decimal("125000000"),
            capital_pagado=Decimal("80000000"),
            superavit=Decimal("30000000"),
        )
        assert datos.excedente_deficit == Decimal("-15000000")  # 110M - 125M


# ======================================
# Tests de Reportes Completos
# ======================================


class TestReporteSuscripcion:
    """Tests para ReporteSuscripcion"""

    def test_total_primas_emitidas(
        self, metadata_basico, datos_suscripcion_autos, datos_suscripcion_vida
    ):
        """Debe sumar primas emitidas de todos los ramos"""
        reporte = ReporteSuscripcion(
            metadata=metadata_basico,
            datos_por_ramo=[datos_suscripcion_autos, datos_suscripcion_vida],
        )
        assert reporte.total_primas_emitidas == Decimal("150000000")  # 50M + 100M

    def test_total_primas_devengadas(
        self, metadata_basico, datos_suscripcion_autos, datos_suscripcion_vida
    ):
        """Debe sumar primas devengadas de todos los ramos"""
        reporte = ReporteSuscripcion(
            metadata=metadata_basico,
            datos_por_ramo=[datos_suscripcion_autos, datos_suscripcion_vida],
        )
        assert reporte.total_primas_devengadas == Decimal("146000000")  # 48M + 98M


class TestReporteSiniestros:
    """Tests para ReporteSiniestros"""

    def test_total_siniestros_ocurridos(self, metadata_basico, datos_siniestros_autos):
        """Debe sumar siniestros ocurridos"""
        reporte = ReporteSiniestros(
            metadata=metadata_basico, datos_por_ramo=[datos_siniestros_autos]
        )
        assert reporte.total_siniestros_ocurridos == Decimal("35000000")


class TestReporteInversiones:
    """Tests para ReporteInversiones"""

    def test_total_valor_mercado(
        self, metadata_basico, datos_inversion_gubernamentales, datos_inversion_acciones
    ):
        """Debe sumar valor de mercado de todos los activos"""
        reporte = ReporteInversiones(
            metadata=metadata_basico,
            datos_por_activo=[datos_inversion_gubernamentales, datos_inversion_acciones],
        )
        assert reporte.total_valor_mercado == Decimal("350000000")  # 300M + 50M

    def test_composicion_porcentual(
        self, metadata_basico, datos_inversion_gubernamentales, datos_inversion_acciones
    ):
        """Debe calcular composición porcentual"""
        reporte = ReporteInversiones(
            metadata=metadata_basico,
            datos_por_activo=[datos_inversion_gubernamentales, datos_inversion_acciones],
        )
        comp = reporte.obtener_composicion_pct()

        # 300M de 350M = 85.71%
        assert comp["valores_gubernamentales"] == Decimal("85.71")
        # 50M de 350M = 14.29%
        assert comp["acciones"] == Decimal("14.29")


# ======================================
# Tests de Generadores
# ======================================


class TestGeneradorReporteSuscripcion:
    """Tests para GeneradorReporteSuscripcion"""

    def test_generar_dataframe(
        self, metadata_basico, datos_suscripcion_autos, datos_suscripcion_vida
    ):
        """Debe generar DataFrame con datos de suscripción"""
        reporte = ReporteSuscripcion(
            metadata=metadata_basico,
            datos_por_ramo=[datos_suscripcion_autos, datos_suscripcion_vida],
        )

        generador = GeneradorReporteSuscripcion()
        df = generador.generar_dataframe(reporte)

        # Debe tener 3 filas (2 ramos + TOTAL)
        assert len(df) == 3
        assert "Ramo" in df.columns
        assert df.iloc[-1]["Ramo"] == "TOTAL"

    def test_generar_resumen(
        self, metadata_basico, datos_suscripcion_autos, datos_suscripcion_vida
    ):
        """Debe generar resumen ejecutivo"""
        reporte = ReporteSuscripcion(
            metadata=metadata_basico,
            datos_por_ramo=[datos_suscripcion_autos, datos_suscripcion_vida],
        )

        generador = GeneradorReporteSuscripcion()
        resumen = generador.generar_resumen(reporte)

        assert resumen["total_primas_emitidas"] == 150000000.0
        assert resumen["numero_ramos_activos"] == 2


class TestGeneradorReporteSiniestros:
    """Tests para GeneradorReporteSiniestros"""

    def test_generar_dataframe(self, metadata_basico, datos_siniestros_autos):
        """Debe generar DataFrame con datos de siniestros"""
        reporte = ReporteSiniestros(
            metadata=metadata_basico, datos_por_ramo=[datos_siniestros_autos]
        )

        generador = GeneradorReporteSiniestros()
        df = generador.generar_dataframe(reporte)

        # Debe tener 2 filas (1 ramo + TOTAL)
        assert len(df) == 2
        assert "Siniestros Ocurridos" in df.columns


class TestGeneradorReporteInversiones:
    """Tests para GeneradorReporteInversiones"""

    def test_generar_dataframe(
        self, metadata_basico, datos_inversion_gubernamentales, datos_inversion_acciones
    ):
        """Debe generar DataFrame con datos de inversiones"""
        reporte = ReporteInversiones(
            metadata=metadata_basico,
            datos_por_activo=[datos_inversion_gubernamentales, datos_inversion_acciones],
        )

        generador = GeneradorReporteInversiones()
        df = generador.generar_dataframe(reporte)

        # Debe tener 3 filas (2 activos + TOTAL)
        assert len(df) == 3
        assert "Tipo de Activo" in df.columns
        assert "Composición %" in df.columns


class TestGeneradorReporteRCS:
    """Tests para GeneradorReporteRCS"""

    def test_generar_dataframe(self, metadata_basico, datos_rcs):
        """Debe generar DataFrame con datos de RCS"""
        reporte = ReporteRCS(metadata=metadata_basico, datos_rcs=datos_rcs)

        generador = GeneradorReporteRCS()
        df = generador.generar_dataframe(reporte)

        # Debe tener múltiples filas (componentes + capital + totales)
        assert len(df) > 5
        assert "Componente" in df.columns
        assert "Monto" in df.columns

    def test_generar_dataframe_ratio(self, metadata_basico, datos_rcs):
        """Debe generar DataFrame con ratios de solvencia"""
        reporte = ReporteRCS(metadata=metadata_basico, datos_rcs=datos_rcs)

        generador = GeneradorReporteRCS()
        df = generador.generar_dataframe_ratio(reporte)

        assert len(df) == 5  # 5 métricas
        assert "Métrica" in df.columns
        assert "Formato" in df.columns


# ======================================
# Tests de Exportadores
# ======================================


class TestExportadorCSV:
    """Tests para ExportadorCSV"""

    def test_exportar_dataframe(
        self, metadata_basico, datos_suscripcion_autos
    ):
        """Debe exportar DataFrame a CSV"""
        reporte = ReporteSuscripcion(
            metadata=metadata_basico, datos_por_ramo=[datos_suscripcion_autos]
        )

        generador = GeneradorReporteSuscripcion()
        df = generador.generar_dataframe(reporte)

        exportador = ExportadorCSV()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            ruta = exportador.exportar_dataframe(df, tmp.name)
            assert ruta.exists()
            assert ruta.suffix == ".csv"

            # Limpiar
            ruta.unlink()


class TestExportadorExcel:
    """Tests para ExportadorExcel"""

    @pytest.mark.skipif(
        not hasattr(ExportadorExcel, "__init__"),
        reason="openpyxl no disponible"
    )
    def test_exportar_reporte_completo(
        self,
        metadata_basico,
        datos_suscripcion_autos,
        datos_siniestros_autos,
        datos_inversion_gubernamentales,
        datos_rcs,
    ):
        """Debe exportar reporte completo a Excel"""
        try:
            # Intentar crear exportador
            exportador = ExportadorExcel()
        except ImportError:
            pytest.skip("openpyxl no instalado")

        # Crear reportes
        reporte_susc = ReporteSuscripcion(
            metadata=metadata_basico, datos_por_ramo=[datos_suscripcion_autos]
        )
        reporte_sin = ReporteSiniestros(
            metadata=metadata_basico, datos_por_ramo=[datos_siniestros_autos]
        )
        reporte_inv = ReporteInversiones(
            metadata=metadata_basico, datos_por_activo=[datos_inversion_gubernamentales]
        )
        reporte_rcs = ReporteRCS(metadata=metadata_basico, datos_rcs=datos_rcs)

        # Generar DataFrames
        df_susc = GeneradorReporteSuscripcion().generar_dataframe(reporte_susc)
        df_sin = GeneradorReporteSiniestros().generar_dataframe(reporte_sin)
        df_inv = GeneradorReporteInversiones().generar_dataframe(reporte_inv)
        df_rcs = GeneradorReporteRCS().generar_dataframe(reporte_rcs)

        # Exportar
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            ruta = exportador.exportar_reporte_completo(
                ruta_salida=tmp.name,
                df_suscripcion=df_susc,
                df_siniestros=df_sin,
                df_inversiones=df_inv,
                df_rcs=df_rcs,
                metadata=metadata_basico.__dict__,
            )

            assert ruta.exists()
            assert ruta.suffix == ".xlsx"

            # Limpiar
            ruta.unlink()


# ======================================
# NEW -- Generator & Exporter Coverage Tests
# ======================================


class TestGeneradorSiniestrosDetallado:
    """Tests adicionales para GeneradorReporteSiniestros: resumen, vacío, multi-ramo."""

    def test_generar_reporte_estructura_completa(
        self, metadata_basico, datos_siniestros_autos
    ):
        """generar_dataframe() debe tener las columnas esperadas y fila TOTAL."""
        reporte = ReporteSiniestros(
            metadata=metadata_basico, datos_por_ramo=[datos_siniestros_autos]
        )
        generador = GeneradorReporteSiniestros()
        df = generador.generar_dataframe(reporte)

        columnas_esperadas = {
            "Ramo",
            "Siniestros Ocurridos",
            "Siniestros Pagados",
            "Reserva Siniestros",
            "Número Siniestros",
            "Pendientes",
            "Costo Promedio",
        }
        assert columnas_esperadas.issubset(set(df.columns))
        assert df.iloc[-1]["Ramo"] == "TOTAL"

    def test_generar_resumen_ejecutivo(
        self, metadata_basico, datos_siniestros_autos
    ):
        """generar_resumen() debe devolver métricas clave."""
        reporte = ReporteSiniestros(
            metadata=metadata_basico, datos_por_ramo=[datos_siniestros_autos]
        )
        generador = GeneradorReporteSiniestros()
        resumen = generador.generar_resumen(reporte)

        assert resumen["total_siniestros_ocurridos"] == 35_000_000.0
        assert resumen["total_siniestros_pagados"] == 28_000_000.0
        assert resumen["numero_casos"] == 450
        assert resumen["numero_pendientes"] == 85
        assert resumen["ramo_mas_siniestros"] == "Autos"

    def test_generar_dataframe_vacio(self, metadata_basico):
        """generar_dataframe() con lista de ramos vacía debe devolver DataFrame vacío."""
        reporte = ReporteSiniestros(
            metadata=metadata_basico, datos_por_ramo=[]
        )
        generador = GeneradorReporteSiniestros()
        df = generador.generar_dataframe(reporte)

        assert df.empty

    def test_generar_resumen_vacio(self, metadata_basico):
        """generar_resumen() con lista vacía debe devolver dict vacío."""
        reporte = ReporteSiniestros(
            metadata=metadata_basico, datos_por_ramo=[]
        )
        generador = GeneradorReporteSiniestros()
        resumen = generador.generar_resumen(reporte)

        assert resumen == {}

    def test_multiples_ramos_totales(self, metadata_basico, datos_siniestros_autos):
        """Con dos ramos, la fila TOTAL debe sumar ambos."""
        datos_vida = DatosSiniestrosRamo(
            ramo=TipoRamo.VIDA_INDIVIDUAL,
            siniestros_ocurridos=Decimal("20000000"),
            siniestros_pagados=Decimal("15000000"),
            reserva_siniestros=Decimal("10000000"),
            numero_siniestros=200,
            numero_siniestros_pendientes=30,
        )
        reporte = ReporteSiniestros(
            metadata=metadata_basico,
            datos_por_ramo=[datos_siniestros_autos, datos_vida],
        )
        generador = GeneradorReporteSiniestros()
        df = generador.generar_dataframe(reporte)

        assert len(df) == 3  # 2 ramos + TOTAL
        total_row = df.iloc[-1]
        assert total_row["Siniestros Ocurridos"] == 55_000_000.0  # 35M + 20M
        assert total_row["Número Siniestros"] == 650  # 450 + 200


class TestGeneradorInversionesDetallado:
    """Tests adicionales para GeneradorReporteInversiones: resumen, cero, single."""

    def test_generar_resumen_ejecutivo(
        self, metadata_basico, datos_inversion_gubernamentales, datos_inversion_acciones
    ):
        """generar_resumen() debe incluir composición y rendimiento."""
        reporte = ReporteInversiones(
            metadata=metadata_basico,
            datos_por_activo=[datos_inversion_gubernamentales, datos_inversion_acciones],
        )
        generador = GeneradorReporteInversiones()
        resumen = generador.generar_resumen(reporte)

        assert resumen["total_valor_mercado"] == 350_000_000.0
        assert resumen["activo_principal"] == "Valores Gubernamentales"
        assert resumen["numero_tipos_activos"] == 2
        assert "composicion_detallada" in resumen

    def test_activo_con_valor_cero(self, metadata_basico):
        """Activo con valor de mercado cero no debe generar errores."""
        dato_cero = DatosInversionActivo(
            tipo_activo=TipoActivoInversion.DEPOSITOS,
            valor_mercado=Decimal("0"),
            valor_libros=Decimal("0"),
            rendimiento_trimestre=Decimal("0"),
        )
        dato_normal = DatosInversionActivo(
            tipo_activo=TipoActivoInversion.VALORES_GUBERNAMENTALES,
            valor_mercado=Decimal("100000000"),
            valor_libros=Decimal("100000000"),
            rendimiento_trimestre=Decimal("0.01"),
        )
        reporte = ReporteInversiones(
            metadata=metadata_basico,
            datos_por_activo=[dato_normal, dato_cero],
        )
        generador = GeneradorReporteInversiones()
        df = generador.generar_dataframe(reporte)

        assert len(df) == 3  # 2 activos + TOTAL
        # La composición del activo cero debe ser 0
        fila_cero = df[df["Tipo de Activo"] == "Depósitos"].iloc[0]
        assert fila_cero["Composición %"] == 0.0

    def test_generar_dataframe_vacio(self, metadata_basico):
        """generar_dataframe() con lista vacía debe devolver DataFrame vacío."""
        reporte = ReporteInversiones(
            metadata=metadata_basico, datos_por_activo=[]
        )
        generador = GeneradorReporteInversiones()
        df = generador.generar_dataframe(reporte)

        assert df.empty

    def test_activo_unico_composicion_100(self, metadata_basico):
        """Un solo activo debe tener composición de 100%."""
        dato = DatosInversionActivo(
            tipo_activo=TipoActivoInversion.INMUEBLES,
            valor_mercado=Decimal("500000000"),
            valor_libros=Decimal("480000000"),
            rendimiento_trimestre=Decimal("0.02"),
        )
        reporte = ReporteInversiones(
            metadata=metadata_basico, datos_por_activo=[dato]
        )
        generador = GeneradorReporteInversiones()
        df = generador.generar_dataframe(reporte)

        # Primera fila (activo único) debe tener 100%
        assert df.iloc[0]["Composición %"] == 100.0


class TestGeneradorRCSDetallado:
    """Tests adicionales para GeneradorReporteRCS: resumen, no-cumple, operacional."""

    def test_generar_resumen_cumple(self, metadata_basico, datos_rcs):
        """generar_resumen() debe reflejar ratio de solvencia y cumplimiento."""
        reporte = ReporteRCS(metadata=metadata_basico, datos_rcs=datos_rcs)
        generador = GeneradorReporteRCS()
        resumen = generador.generar_resumen(reporte)

        assert resumen["cumple_regulacion"] is True
        assert resumen["ratio_solvencia"] == 1.2
        assert resumen["excedente_deficit"] == 25_000_000.0
        assert resumen["componente_principal"] == "Suscripción Daños"

    def test_generar_resumen_no_cumple(self, metadata_basico):
        """Cuando ratio < 1, cumple_regulacion debe ser False."""
        datos_insuficientes = DatosReporteRCS(
            rcs_suscripcion_vida=Decimal("18000000"),
            rcs_suscripcion_danos=Decimal("95000000"),
            rcs_inversion=Decimal("62000000"),
            rcs_total=Decimal("125000000"),
            capital_pagado=Decimal("80000000"),
            superavit=Decimal("30000000"),
        )
        reporte = ReporteRCS(
            metadata=metadata_basico, datos_rcs=datos_insuficientes
        )
        generador = GeneradorReporteRCS()
        resumen = generador.generar_resumen(reporte)

        assert resumen["cumple_regulacion"] is False
        assert resumen["excedente_deficit"] == -15_000_000.0

    def test_dataframe_con_rcs_operacional(self, metadata_basico):
        """Si rcs_operacional > 0, debe aparecer como fila extra."""
        datos_op = DatosReporteRCS(
            rcs_suscripcion_vida=Decimal("10000000"),
            rcs_suscripcion_danos=Decimal("50000000"),
            rcs_inversion=Decimal("30000000"),
            rcs_operacional=Decimal("10000000"),
            rcs_total=Decimal("100000000"),
            capital_pagado=Decimal("120000000"),
            superavit=Decimal("20000000"),
        )
        reporte = ReporteRCS(metadata=metadata_basico, datos_rcs=datos_op)
        generador = GeneradorReporteRCS()
        df = generador.generar_dataframe(reporte)

        componentes = df["Componente"].tolist()
        assert "RCS Operacional" in componentes


class TestExportadoresIO:
    """Tests de I/O para ExportadorCSV y ExportadorExcel usando tmp_path."""

    def test_csv_exporta_con_headers(
        self, tmp_path, metadata_basico, datos_siniestros_autos
    ):
        """ExportadorCSV debe crear archivo con encabezados correctos."""
        reporte = ReporteSiniestros(
            metadata=metadata_basico, datos_por_ramo=[datos_siniestros_autos]
        )
        df = GeneradorReporteSiniestros().generar_dataframe(reporte)

        ruta = tmp_path / "siniestros.csv"
        exportador = ExportadorCSV()
        resultado = exportador.exportar_dataframe(df, str(ruta))

        assert resultado.exists()
        contenido = resultado.read_text(encoding="utf-8-sig")
        lineas = contenido.strip().splitlines()
        # Encabezado es la primera línea
        assert "Ramo" in lineas[0]
        assert "Siniestros Ocurridos" in lineas[0]
        # Debe tener encabezado + 1 ramo + TOTAL = 3 líneas
        assert len(lineas) == 3

    def test_csv_exportar_multiples(
        self, tmp_path, metadata_basico, datos_siniestros_autos, datos_inversion_gubernamentales
    ):
        """exportar_multiples() debe crear un CSV por DataFrame."""
        df_sin = GeneradorReporteSiniestros().generar_dataframe(
            ReporteSiniestros(
                metadata=metadata_basico, datos_por_ramo=[datos_siniestros_autos]
            )
        )
        df_inv = GeneradorReporteInversiones().generar_dataframe(
            ReporteInversiones(
                metadata=metadata_basico,
                datos_por_activo=[datos_inversion_gubernamentales],
            )
        )

        exportador = ExportadorCSV()
        rutas = exportador.exportar_multiples(
            dataframes={"siniestros": df_sin, "inversiones": df_inv},
            directorio_salida=str(tmp_path),
            prefijo="Q1_",
        )

        assert len(rutas) == 2
        nombres = {r.name for r in rutas}
        assert "Q1_siniestros.csv" in nombres
        assert "Q1_inversiones.csv" in nombres

    def test_excel_exportar_y_verificar(
        self, tmp_path, metadata_basico, datos_siniestros_autos, datos_rcs
    ):
        """ExportadorExcel debe crear archivo .xlsx válido."""
        try:
            exportador = ExportadorExcel()
        except ImportError:
            pytest.skip("openpyxl no instalado")

        df_sin = GeneradorReporteSiniestros().generar_dataframe(
            ReporteSiniestros(
                metadata=metadata_basico, datos_por_ramo=[datos_siniestros_autos]
            )
        )
        df_rcs = GeneradorReporteRCS().generar_dataframe(
            ReporteRCS(metadata=metadata_basico, datos_rcs=datos_rcs)
        )

        ruta = tmp_path / "reporte.xlsx"
        resultado = exportador.exportar_reporte_completo(
            ruta_salida=str(ruta),
            df_siniestros=df_sin,
            df_rcs=df_rcs,
            metadata={
                "clave_aseguradora": "A0123",
                "nombre_aseguradora": "Seguros XYZ S.A.",
                "trimestre": "Q1",
                "anio": 2024,
                "fecha_presentacion": "2024-04-30",
            },
        )
        assert resultado.exists()
        assert resultado.suffix == ".xlsx"
        # File should have actual content
        assert resultado.stat().st_size > 0
