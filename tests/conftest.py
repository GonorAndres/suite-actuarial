"""Shared test fixtures for suite_actuarial test suite."""

from decimal import Decimal

import pytest

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    ConfiguracionRCSDanos,
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
    Sexo,
)
from suite_actuarial.pensiones.conmutacion import TablaConmutacion


@pytest.fixture(scope="session")
def tabla_emssa09():
    """Session-scoped EMSSA-09 mortality table (loaded once)."""
    return TablaMortalidad.cargar_emssa09()


@pytest.fixture(scope="session")
def tabla_conmutacion_hombre(tabla_emssa09):
    """Commutation table for males at i=5.5%."""
    return TablaConmutacion(tabla_emssa09, "H", Decimal("0.055"))


@pytest.fixture(scope="session")
def tabla_conmutacion_mujer(tabla_emssa09):
    """Commutation table for females at i=5.5%."""
    return TablaConmutacion(tabla_emssa09, "M", Decimal("0.055"))


@pytest.fixture
def config_vida_20():
    """Standard 20-year vida product config."""
    return ConfiguracionProducto(
        nombre_producto="Test Temporal 20",
        plazo_years=20,
        tasa_interes_tecnico=Decimal("0.055"),
        recargo_gastos_admin=Decimal("0.05"),
        recargo_gastos_adq=Decimal("0.10"),
        recargo_utilidad=Decimal("0.03"),
    )


@pytest.fixture
def asegurado_35_h():
    """Standard insured: male, age 35, 1M MXN sum assured."""
    return Asegurado(
        edad=35,
        sexo=Sexo.HOMBRE,
        suma_asegurada=Decimal("1000000"),
    )


@pytest.fixture
def asegurado_30_m():
    """Standard insured: female, age 30, 500K MXN sum assured."""
    return Asegurado(
        edad=30,
        sexo=Sexo.MUJER,
        suma_asegurada=Decimal("500000"),
    )


@pytest.fixture
def config_rcs_vida():
    """Standard RCS vida configuration."""
    return ConfiguracionRCSVida(
        suma_asegurada_total=Decimal("50000000"),
        reserva_matematica=Decimal("15000000"),
        edad_promedio_asegurados=40,
        duracion_promedio_polizas=10,
        numero_asegurados=1000,
    )


@pytest.fixture
def config_rcs_danos():
    """Standard RCS danos configuration."""
    return ConfiguracionRCSDanos(
        primas_retenidas_12m=Decimal("20000000"),
        reserva_siniestros=Decimal("8000000"),
        coeficiente_variacion=Decimal("0.15"),
        numero_ramos=3,
    )


@pytest.fixture
def config_rcs_inversion():
    """Standard RCS inversion configuration."""
    return ConfiguracionRCSInversion(
        valor_acciones=Decimal("10000000"),
        valor_bonos_gubernamentales=Decimal("30000000"),
        valor_bonos_corporativos=Decimal("15000000"),
        valor_inmuebles=Decimal("5000000"),
        duracion_promedio_bonos=Decimal("5"),
        calificacion_promedio_bonos="AA",
    )


@pytest.fixture
def triangulo_acumulado():
    """Standard 5x5 cumulative development triangle."""
    return [
        [3000, 5000, 5600, 5800, 5900],
        [3200, 5200, 5800, 6000, None],
        [3500, 5500, 6100, None, None],
        [3800, 5900, None, None, None],
        [4000, None, None, None, None],
    ]


@pytest.fixture
def origin_years_5():
    """Origin years for a 5x5 triangle."""
    return [2019, 2020, 2021, 2022, 2023]


@pytest.fixture(scope="session")
def api_client():
    """TestClient for FastAPI integration tests."""
    try:
        from fastapi.testclient import TestClient

        from suite_actuarial.api.main import app
        return TestClient(app)
    except ImportError:
        pytest.skip("fastapi/httpx not installed (install with: pip install -e '.[dev,api]')")
