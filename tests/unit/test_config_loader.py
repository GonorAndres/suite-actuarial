"""Pruebas del cargador de perfiles regulatorios en el borde de su cobertura.

El paquete solo trae perfiles con parámetros publicados y con fuente. Cuando la
fecha pedida cae fuera de esa cobertura, la única respuesta defendible es un
fallo explícito: no se inventan parámetros del año siguiente ni se reutiliza en
silencio el último perfil publicado.

Estas pruebas fijan ese comportamiento en la frontera y comprueban que el error
nombra el rango cubierto, que es lo que el usuario necesita para saber qué
hacer.
"""

from datetime import date

import pytest

from suite_actuarial.config import loader
from suite_actuarial.config.loader import (
    ConfiguracionNoDisponibleError,
    cargar_config,
    cargar_config_fecha,
    config_vigente,
    rango_cobertura,
)


class TestCoberturaDeclarada:
    def test_el_rango_sale_de_los_perfiles_empaquetados(self):
        """La cobertura se deriva de los perfiles, no de una fecha escrita a mano.

        Los perfiles 2024-2026 declaran vigencias de febrero a enero: el primero
        arranca el 2024-02-01 y el último cierra el 2027-01-31.
        """
        inicio, fin = rango_cobertura()
        assert inicio == date(2024, 2, 1)
        assert fin == date(2027, 1, 31)


class TestFechaFueraDeCobertura:
    def test_ultimo_dia_cubierto_sigue_resolviendo(self):
        """Frontera inferior del fallo: el 2027-01-31 todavía tiene perfil."""
        assert cargar_config_fecha(date(2027, 1, 31)).anio == 2026

    def test_dia_siguiente_falla_con_error_tipado(self):
        """Un día después ya no hay perfil y el error lo dice con el rango."""
        with pytest.raises(ConfiguracionNoDisponibleError) as exc:
            cargar_config_fecha(date(2027, 2, 1))

        mensaje = str(exc.value)
        assert "2027-02-01" in mensaje
        assert "2024-02-01 a 2027-01-31" in mensaje

    def test_fecha_anterior_al_primer_perfil_tambien_falla(self):
        with pytest.raises(ConfiguracionNoDisponibleError) as exc:
            cargar_config_fecha(date(2024, 1, 31))

        assert "2024-02-01 a 2027-01-31" in str(exc.value)

    def test_anio_sin_perfil_falla_con_el_rango(self):
        with pytest.raises(ConfiguracionNoDisponibleError) as exc:
            cargar_config(2030)

        assert "2024-02-01 a 2027-01-31" in str(exc.value)

    def test_el_error_sigue_siendo_module_not_found(self):
        """El tipo nuevo hereda del viejo para no romper a quien ya lo atrapaba.

        El CLI, el router de configuración y la carga de tablas atrapan
        `ModuleNotFoundError`. Introducir un tipo hermano habría dejado esas
        rutas descubiertas sin que ninguna prueba lo notara.
        """
        assert issubclass(ConfiguracionNoDisponibleError, ModuleNotFoundError)
        with pytest.raises(ModuleNotFoundError):
            cargar_config_fecha(date(2027, 2, 1))


class TestFechaPorOmisionFueraDeCobertura:
    """La fecha por omisión es la de hoy: también puede quedarse sin perfil.

    Este es el escenario que hacía caer el endpoint de RCS con un 500: nada
    fallaba mientras la fecha del servidor estuviera cubierta, y el día que
    dejara de estarlo el fallo aparecía en `AgregadorRCS.__init__`, lejos de
    donde se podía explicar.
    """

    @pytest.fixture
    def hoy_sin_cobertura(self, monkeypatch):
        monkeypatch.setattr(loader, "_hoy", lambda: date(2030, 6, 15))

    def test_config_vigente_falla_explicitamente(self, hoy_sin_cobertura):
        with pytest.raises(ConfiguracionNoDisponibleError) as exc:
            config_vigente()

        assert "2030-06-15" in str(exc.value)
        assert "2024-02-01 a 2027-01-31" in str(exc.value)

    def test_cargar_config_sin_anio_falla_explicitamente(self, hoy_sin_cobertura):
        with pytest.raises(ConfiguracionNoDisponibleError):
            cargar_config()

    def test_el_agregador_rcs_propaga_el_error(self, hoy_sin_cobertura):
        """El agregador lee los factores CNSF del perfil vigente al construirse.

        Debe propagar el error tipado, no sustituir factores de un año que ya
        no está vigente: un RCS calculado con factores caducos no es un RCS.
        """
        from decimal import Decimal

        from suite_actuarial.core.validators import ConfiguracionRCSVida
        from suite_actuarial.regulatorio.agregador_rcs import AgregadorRCS

        with pytest.raises(ConfiguracionNoDisponibleError):
            AgregadorRCS(
                config_vida=ConfiguracionRCSVida(
                    suma_asegurada_total=Decimal("50000000"),
                    reserva_matematica=Decimal("15000000"),
                    edad_promedio_asegurados=40,
                    duracion_promedio_polizas=10,
                    numero_asegurados=1000,
                ),
                capital_minimo_pagado=Decimal("100000000"),
            )
