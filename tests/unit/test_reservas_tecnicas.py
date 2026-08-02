"""
Tests para módulo de reservas técnicas (orientado a la Circular S-11.4).

Cubre RRC, la Reserva Matemática prospectiva de primas netas y el validador de
suficiencia.

Los tests de la Reserva Matemática usan dos capas de oráculo, ninguna de las
cuales reenuncia la fórmula bajo prueba:

1. **Identidad retrospectiva/prospectiva (recursión de Fackler).** La reserva se
   calcula prospectivamente (`A - P·ä`); la recursión de Fackler la recorre
   hacia adelante año contra año. Son rutas distintas. Cada verificación de este
   tipo va acompañada de un test que la hace **fallar** bajo un defecto
   deliberado: una comprobación que no puede fallar no comprueba nada.
2. **Valores a mano.** Sobre una tabla sintética diminuta, la reserva se calcula
   con aritmética exacta de fracciones fuera del test y se fija como literal,
   con la derivación escrita en el docstring. También se contrasta contra las
   funciones de conmutación (Dx/Nx/Mx), que llegan al mismo valor por otra
   construcción.
"""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.core.warnings import ExperimentalModelWarning
from suite_actuarial.pensiones.conmutacion import TablaConmutacion
from suite_actuarial.regulatorio.reservas_tecnicas import (
    DISCLAIMER_RM,
    CalculadoraRM,
    CalculadoraRRC,
    ConfiguracionRM,
    ConfiguracionRRC,
    MetodoCalculoRRC,
    ValidadorSuficiencia,
)

# ======================================
# Fixtures
# ======================================


@pytest.fixture
def config_rrc_basico():
    """Configuración básica de RRC"""
    return ConfiguracionRRC(
        prima_emitida=Decimal("100000000"),
        prima_devengada=Decimal("60000000"),
        fecha_calculo=date(2024, 6, 30),
        metodo=MetodoCalculoRRC.AVOS_365,
    )


@pytest.fixture
def config_rrc_con_dias():
    """Configuración de RRC con días específicos"""
    return ConfiguracionRRC(
        prima_emitida=Decimal("100000000"),
        prima_devengada=Decimal("60000000"),
        fecha_calculo=date(2024, 6, 30),
        dias_promedio_vigencia=365,
        dias_promedio_transcurridos=219,  # ~60% del año
        metodo=MetodoCalculoRRC.AVOS_365,
    )


@pytest.fixture
def tabla_sintetica():
    """Tabla mínima de cuatro edades, para aritmética exacta a mano.

    Edades 60 a 63. La edad terminal es 63: ahí el modelo fuerza q = 1 con la
    convención auditada, aunque la tabla publique 0.30 (hombres) y 0.20
    (mujeres). Las mujeres tienen mortalidad estrictamente menor, para poder
    comprobar que el sexo cambia la reserva.
    """
    datos = pd.DataFrame(
        {
            "edad": [60, 61, 62, 63, 60, 61, 62, 63],
            "sexo": ["masculino"] * 4 + ["femenino"] * 4,
            "qx": [0.10, 0.20, 0.25, 0.30, 0.05, 0.10, 0.15, 0.20],
        }
    )
    return TablaMortalidad(nombre="Sintetica-4", datos=datos)


@pytest.fixture
def tabla_emssa09():
    """Tabla EMSSA-09 empaquetada; se omite el test si no está instalada."""
    try:
        return TablaMortalidad.cargar_emssa09()
    except FileNotFoundError:  # pragma: no cover - depende de la instalación
        pytest.skip("Tabla EMSSA-09 no disponible")


def _config_temporal(
    *,
    edad_asegurado: int,
    sexo: Sexo,
    edad_contratacion: int = 35,
    plazo_seguro: int = 20,
    plazo_pago: int = 20,
    suma_asegurada: str = "1000000",
    tasa: str = "0.055",
    prima: str | None = None,
) -> ConfiguracionRM:
    """Arma una configuración de temporal a plazo con pago nivelado."""
    return ConfiguracionRM(
        suma_asegurada=Decimal(suma_asegurada),
        edad_contratacion=edad_contratacion,
        edad_asegurado=edad_asegurado,
        sexo=sexo,
        plazo_seguro_anios=plazo_seguro,
        plazo_pago_anios=plazo_pago,
        tasa_interes_tecnico=Decimal(tasa),
        prima_nivelada_anual=None if prima is None else Decimal(prima),
    )


def _reservas_por_duracion(
    tabla: TablaMortalidad,
    *,
    sexo: Sexo,
    edad_contratacion: int = 35,
    plazo_seguro: int = 20,
    plazo_pago: int = 20,
    suma_asegurada: str = "1000000",
    tasa: str = "0.055",
) -> tuple[list[Decimal], Decimal]:
    """Trayectoria ₜV para t = 0..n y la prima nivelada usada."""
    reservas: list[Decimal] = []
    prima = Decimal("0")
    for t in range(plazo_seguro + 1):
        config = _config_temporal(
            edad_asegurado=edad_contratacion + t,
            sexo=sexo,
            edad_contratacion=edad_contratacion,
            plazo_seguro=plazo_seguro,
            plazo_pago=plazo_pago,
            suma_asegurada=suma_asegurada,
            tasa=tasa,
        )
        resultado = CalculadoraRM(config, tabla).calcular()
        reservas.append(resultado.reserva_matematica)
        prima = resultado.prima_neta_anual
    return reservas, prima


def _maxima_diferencia_fackler(
    tabla: TablaMortalidad,
    *,
    reservas: list[Decimal],
    prima: Decimal,
    sexo: Sexo,
    edad_contratacion: int,
    plazo_pago: int,
    suma_asegurada: Decimal,
    tasa: Decimal,
) -> Decimal:
    """Máxima desviación relativa de la recursión de Fackler.

    Identidad (Bowers et al., *Actuarial Mathematics*, cap. 7):

        (ₜV + P) · (1 + i) = q_{x+t} · SA + p_{x+t} · ₜ₊₁V

    La reserva del año t más la prima, capitalizadas un año, deben alcanzar
    exactamente para pagar a quienes mueren y constituir la reserva del año
    siguiente para quienes sobreviven. Es una relación **retrospectiva**: recorre
    la trayectoria hacia adelante, mientras que la reserva bajo prueba se calcula
    de forma prospectiva. Por eso puede fallar.

    La q se lee aquí directamente de la tabla, para el sexo indicado; el módulo
    no participa en obtenerla.
    """
    maxima = Decimal("0")
    for t in range(len(reservas) - 1):
        qx = tabla.obtener_qx(edad_contratacion + t, sexo)
        px = Decimal("1") - qx
        pago = prima if t < plazo_pago else Decimal("0")
        izquierda = (reservas[t] + pago) * (Decimal("1") + tasa)
        derecha = qx * suma_asegurada + px * reservas[t + 1]
        maxima = max(maxima, abs(izquierda - derecha) / suma_asegurada)
    return maxima


# ======================================
# Tests de RRC
# ======================================


class TestCalculadoraRRC:
    """Tests para CalculadoraRRC"""

    def test_calcular_rrc_prima_no_devengada(self, config_rrc_basico):
        """Debe calcular RRC como prima no devengada"""
        calc = CalculadoraRRC(config_rrc_basico)
        resultado = calc.calcular()

        # RRC = 100M - 60M = 40M
        assert resultado.reserva_calculada == Decimal("40000000.00")
        assert resultado.prima_no_devengada == Decimal("40000000.00")
        assert resultado.porcentaje_reserva == Decimal("0.4000")

    def test_calcular_rrc_con_dias_especificos(self, config_rrc_con_dias):
        """Debe calcular RRC usando días específicos"""
        calc = CalculadoraRRC(config_rrc_con_dias)
        resultado = calc.calcular()

        # Días por transcurrir = 365 - 219 = 146
        # Fracción = 146/365 = 0.4
        # RRC = 100M × 0.4 = 40M
        assert resultado.reserva_calculada == Decimal("40000000.00")
        assert resultado.dias_vigencia_promedio == 365
        assert resultado.dias_transcurridos_promedio == 219

    def test_metodo_prima_no_devengada(self):
        """Debe calcular con método prima no devengada"""
        config = ConfiguracionRRC(
            prima_emitida=Decimal("50000000"),
            prima_devengada=Decimal("30000000"),
            fecha_calculo=date(2024, 6, 30),
            metodo=MetodoCalculoRRC.PRIMA_NO_DEVENGADA,
        )

        calc = CalculadoraRRC(config)
        resultado = calc.calcular()

        assert resultado.reserva_calculada == Decimal("20000000.00")
        assert resultado.metodo_utilizado == MetodoCalculoRRC.PRIMA_NO_DEVENGADA

    def test_rrc_con_toda_prima_devengada(self):
        """RRC debe ser cero si toda la prima está devengada"""
        config = ConfiguracionRRC(
            prima_emitida=Decimal("100000000"),
            prima_devengada=Decimal("100000000"),
            fecha_calculo=date(2024, 12, 31),
        )

        calc = CalculadoraRRC(config)
        resultado = calc.calcular()

        assert resultado.reserva_calculada == Decimal("0.00")
        assert resultado.porcentaje_reserva == Decimal("0.0000")

    def test_rrc_al_inicio_vigencia(self):
        """RRC debe ser casi total al inicio de vigencia"""
        config = ConfiguracionRRC(
            prima_emitida=Decimal("100000000"),
            prima_devengada=Decimal("5000000"),  # Solo 5% devengado
            fecha_calculo=date(2024, 1, 15),
        )

        calc = CalculadoraRRC(config)
        resultado = calc.calcular()

        assert resultado.reserva_calculada == Decimal("95000000.00")
        assert resultado.porcentaje_reserva == Decimal("0.9500")


# ==========================================================================
# RM — capa 1: valores calculados a mano sobre una tabla sintética
# ==========================================================================


class TestReservaMatematicaValoresAMano:
    """Valores exactos, derivados fuera del test y fijados como literales.

    La tabla sintética tiene cuatro edades, así que la aritmética cabe en un
    docstring. Ninguno de estos números sale de ejecutar el módulo: se
    obtuvieron con fracciones exactas y se escriben aquí junto con su derivación.
    """

    def test_prima_y_reservas_temporal_3_anios(self, tabla_sintetica):
        """Temporal 3 años emitido a los 60, i = 5%, SA = 1,000,000, hombre.

        Con v = 1/1.05 = 20/21, q60 = 0.10, q61 = 0.20, q62 = 0.25:

            A_{60:3} = v(0.10) + v²(0.90)(0.20) + v³(0.90)(0.80)(0.25)
                     = 2/21 + 8/49 + 160/1029
                     = (98 + 168 + 160)/1029 = 426/1029 = 142/343

            ä_{60:3} = 1 + v(0.90) + v²(0.72)
                     = 1 + 6/7 + 32/49 = (49 + 42 + 32)/49 = 123/49

            P = SA · A/ä = 1,000,000 · (142/343)(49/123) = 1,000,000 · 142/861
              = 164,924.50638…  →  164,924.51

            A_{61:2} = v(0.20) + v²(0.80)(0.25) = 4/21 + 80/441 = 164/441
            ä_{61:2} = 1 + v(0.80) = 37/21
            ₁V = 1,000,000 [164/441 - (142/861)(37/21)] = 10,000,000/123
               = 81,300.813…  →  81,300.81

            A_{62:1} = v(0.25) = 5/21;  ä_{62:1} = 1
            ₂V = 1,000,000 [5/21 - 142/861] = 1,000,000 · 63/861 = 3,000,000/41
               = 73,170.7317…  →  73,170.73

        En t = 0 la reserva vale cero por el principio de equivalencia, y no
        porque el módulo devuelva una constante: la fórmula prospectiva la
        produce sola.
        """
        esperados = {
            0: Decimal("0.00"),
            1: Decimal("81300.81"),
            2: Decimal("73170.73"),
            3: Decimal("0.00"),
        }

        for t, esperado in esperados.items():
            config = _config_temporal(
                edad_asegurado=60 + t,
                sexo=Sexo.MASCULINO,
                edad_contratacion=60,
                plazo_seguro=3,
                plazo_pago=3,
                tasa="0.05",
            )
            resultado = CalculadoraRM(config, tabla_sintetica).calcular()

            assert resultado.reserva_matematica == esperado, f"t={t}"
            assert resultado.prima_neta_anual == Decimal("164924.51")
            assert resultado.prima_determinada_por_equivalencia is True
            assert resultado.edad_terminal_tabla == 63

    def test_edad_terminal_paga_el_beneficio_con_certeza(self, tabla_sintetica):
        """En ω el beneficio se paga con certeza: ₃V = SA · v.

        Contrato: temporal 4 años emitido a los 60, primas 3 años. En t = 3 el
        asegurado tiene 63 años, que es la edad terminal de la tabla; la
        convención auditada fuerza q₆₃ = 1 (la tabla publica 0.30). Queda un
        año de cobertura, ninguna prima por cobrar, y el beneficio se paga con
        probabilidad 1:

            ₃V = SA · v = 1,000,000 · 20/21 = 952,380.952…  →  952,380.95

        Sin la convención de edad terminal la cohorte viva a los 63 nunca
        cobraría y la reserva quedaría en 1,000,000 · v · 0.30 = 285,714.29.
        """
        config = _config_temporal(
            edad_asegurado=63,
            sexo=Sexo.MASCULINO,
            edad_contratacion=60,
            plazo_seguro=4,
            plazo_pago=3,
            tasa="0.05",
        )
        resultado = CalculadoraRM(config, tabla_sintetica).calcular()

        assert resultado.reserva_matematica == Decimal("952380.95")
        assert resultado.valor_presente_primas == Decimal("0.00")
        assert resultado.factor_anualidad_primas == Decimal("0")

    def test_el_sexo_cambia_la_reserva(self, tabla_sintetica):
        """Mujeres y hombres no comparten reserva: la tabla los distingue.

        La versión anterior del módulo consultaba siempre mortalidad masculina.
        Con la tabla sintética la mortalidad femenina es la mitad de la
        masculina en cada edad, así que la prima neta femenina debe ser
        estrictamente menor.
        """
        comun = {"edad_contratacion": 60, "plazo_seguro": 3, "plazo_pago": 3, "tasa": "0.05"}

        hombre = CalculadoraRM(
            _config_temporal(edad_asegurado=61, sexo=Sexo.MASCULINO, **comun), tabla_sintetica
        ).calcular()
        mujer = CalculadoraRM(
            _config_temporal(edad_asegurado=61, sexo=Sexo.FEMENINO, **comun), tabla_sintetica
        ).calcular()

        assert mujer.prima_neta_anual < hombre.prima_neta_anual
        assert mujer.reserva_matematica != hombre.reserva_matematica
        assert mujer.sexo == Sexo.FEMENINO
        assert hombre.sexo == Sexo.MASCULINO

    def test_probabilidad_supervivencia_cubre_el_plazo_restante(self, tabla_sintetica):
        """La probabilidad publicada es ₙp_x, no la de un solo año.

        A los 61 con 2 años de cobertura restantes: p₆₁ · p₆₂ = 0.80 · 0.75 =
        0.60. El defecto anterior publicaba 1 - q₆₁ = 0.80 y, peor, la usaba
        como si cubriera todo el plazo.
        """
        config = _config_temporal(
            edad_asegurado=61,
            sexo=Sexo.MASCULINO,
            edad_contratacion=60,
            plazo_seguro=3,
            plazo_pago=3,
            tasa="0.05",
        )
        resultado = CalculadoraRM(config, tabla_sintetica).calcular()

        assert resultado.probabilidad_supervivencia_plazo == pytest.approx(Decimal("0.60"))


# ==========================================================================
# RM — capa 2: identidad retrospectiva/prospectiva (Fackler)
# ==========================================================================


class TestReservaMatematicaFackler:
    """La recursión de Fackler contra la reserva prospectiva, y su falsación."""

    def test_recursion_se_sostiene_en_toda_la_trayectoria(self, tabla_emssa09):
        """(ₜV + P)(1+i) = q_{x+t}·SA + p_{x+t}·ₜ₊₁V para t = 0..n-1.

        Temporal 20 años emitido a los 35, EMSSA-09, i = 5.5%, SA = 1,000,000.
        Las reservas se calculan prospectivamente, duración por duración; la
        recursión las recorre hacia adelante con las q leídas de la tabla en el
        propio test.
        """
        for sexo in (Sexo.MASCULINO, Sexo.FEMENINO):
            reservas, prima = _reservas_por_duracion(tabla_emssa09, sexo=sexo)

            # En t=0 la equivalencia exige reserva nula, y en t=n no queda nada.
            assert abs(reservas[0]) < Decimal("1")
            assert reservas[-1] == Decimal("0.00")

            diferencia = _maxima_diferencia_fackler(
                tabla_emssa09,
                reservas=reservas,
                prima=prima,
                sexo=sexo,
                edad_contratacion=35,
                plazo_pago=20,
                suma_asegurada=Decimal("1000000"),
                tasa=Decimal("0.055"),
            )
            assert diferencia < Decimal("0.00001"), f"Fackler falla para {sexo.value}: {diferencia}"

    def test_recursion_detecta_una_reserva_desviada(self, tabla_emssa09):
        """Desviar una sola reserva intermedia 2% debe romper la recursión.

        Defecto deliberado: la comprobación anterior sería inútil si no pudiera
        fallar.
        """
        reservas, prima = _reservas_por_duracion(tabla_emssa09, sexo=Sexo.MASCULINO)
        reservas[10] = reservas[10] * Decimal("1.02")

        diferencia = _maxima_diferencia_fackler(
            tabla_emssa09,
            reservas=reservas,
            prima=prima,
            sexo=Sexo.MASCULINO,
            edad_contratacion=35,
            plazo_pago=20,
            suma_asegurada=Decimal("1000000"),
            tasa=Decimal("0.055"),
        )
        assert diferencia > Decimal("0.00001")

    def test_recursion_detecta_el_sexo_equivocado(self, tabla_emssa09):
        """Reservas de hombre contrastadas contra mortalidad de mujer: falla.

        Esta es exactamente la forma del defecto anterior, que consultaba
        `Sexo.MASCULINO` sin mirar al asegurado. Las reservas correctas para
        mujer sí pasan la misma comprobación.
        """
        reservas_h, prima_h = _reservas_por_duracion(tabla_emssa09, sexo=Sexo.MASCULINO)
        reservas_m, prima_m = _reservas_por_duracion(tabla_emssa09, sexo=Sexo.FEMENINO)

        argumentos = {
            "edad_contratacion": 35,
            "plazo_pago": 20,
            "suma_asegurada": Decimal("1000000"),
            "tasa": Decimal("0.055"),
        }

        cruzada = _maxima_diferencia_fackler(
            tabla_emssa09, reservas=reservas_h, prima=prima_h, sexo=Sexo.FEMENINO, **argumentos
        )
        correcta = _maxima_diferencia_fackler(
            tabla_emssa09, reservas=reservas_m, prima=prima_m, sexo=Sexo.FEMENINO, **argumentos
        )

        assert cruzada > Decimal("0.00001")
        assert correcta < Decimal("0.00001")

    def test_recursion_detecta_la_supervivencia_de_un_solo_anio(self, tabla_emssa09):
        """El defecto original —p de un año como si cubriera el plazo— falla.

        Se reconstruye aquí la fórmula que el módulo usaba antes:

            V ≈ SA · vⁿ⁻ᵗ · q_{x+t}  -  P · [(1 - vᵐ⁻ᵗ)/(1 - v)] · (1 - q_{x+t})

        es decir, la probabilidad de morir en UN año multiplicando un beneficio
        descontado todo el plazo, y una anualidad cierta escalada por la
        supervivencia de un año. La recursión de Fackler la rechaza con una
        desviación máxima de ≈ 0.0050 de la suma asegurada, unas 500 veces la
        tolerancia con que pasa la trayectoria correcta: el test habría
        detectado el defecto.
        """
        v = Decimal("1") / Decimal("1.055")
        suma_asegurada = Decimal("1000000")
        prima = Decimal("3000")

        reservas_defectuosas: list[Decimal] = []
        for t in range(21):
            qx = tabla_emssa09.obtener_qx(35 + t, Sexo.MASCULINO)
            px = Decimal("1") - qx
            vp_beneficios = suma_asegurada * (v ** (20 - t)) * qx
            pagos = 20 - t
            anualidad = (
                (Decimal("1") - v**pagos) / (Decimal("1") - v) if pagos > 0 else Decimal("0")
            )
            reservas_defectuosas.append(vp_beneficios - prima * anualidad * px)

        diferencia = _maxima_diferencia_fackler(
            tabla_emssa09,
            reservas=reservas_defectuosas,
            prima=prima,
            sexo=Sexo.MASCULINO,
            edad_contratacion=35,
            plazo_pago=20,
            suma_asegurada=suma_asegurada,
            tasa=Decimal("0.055"),
        )
        assert diferencia > Decimal("0.001")


# ==========================================================================
# RM — capa 2b: oráculo independiente por funciones de conmutación
# ==========================================================================


class TestReservaMatematicaContraConmutacion:
    """Las columnas Dx/Nx/Mx llegan al mismo valor por otra construcción."""

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_reserva_coincide_con_conmutacion(self, tabla_emssa09):
        """ₜV = SA·(M_{x+t} - M_{x+n})/D_{x+t} - P·(N_{x+t} - N_{x+m})/D_{x+t}.

        La tabla de conmutación acumula lx desde una raíz entera y descuenta con
        Dx; el módulo suma v^(t+1)·ₜp_x·q_{x+t} año por año. Son dos
        implementaciones distintas del mismo valor actuarial.
        """
        tc = TablaConmutacion(tabla_emssa09, Sexo.MASCULINO, Decimal("0.055"))
        suma_asegurada = Decimal("1000000")

        for t in (0, 1, 5, 10, 19):
            config = _config_temporal(edad_asegurado=35 + t, sexo=Sexo.MASCULINO)
            resultado = CalculadoraRM(config, tabla_emssa09).calcular()

            edad = 35 + t
            esperado = suma_asegurada * tc.Ax(edad, 20 - t) - resultado.prima_neta_anual * tc.ax(
                edad, 20 - t
            )

            assert float(resultado.reserva_matematica) == pytest.approx(float(esperado), abs=1.0), (
                f"t={t}"
            )

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_prima_por_equivalencia_coincide_con_conmutacion(self, tabla_emssa09):
        """P = SA·A_{x:n}/ä_{x:m}, con A y ä tomados de la conmutación."""
        tc = TablaConmutacion(tabla_emssa09, Sexo.FEMENINO, Decimal("0.055"))
        config = _config_temporal(edad_asegurado=35, sexo=Sexo.FEMENINO)
        resultado = CalculadoraRM(config, tabla_emssa09).calcular()

        esperado = Decimal("1000000") * tc.Ax(35, 20) / tc.ax(35, 20)

        assert float(resultado.prima_neta_anual) == pytest.approx(float(esperado), rel=1e-4)


# ==========================================================================
# RM — comportamiento, avisos y rentas
# ==========================================================================


class TestReservaMatematicaComportamiento:
    """Contrato público de la calculadora: avisos, componentes y rentas."""

    def test_construccion_emite_aviso_experimental(self, tabla_emssa09):
        """El modelo se declara experimental al construirse, no en un pie de página."""
        config = _config_temporal(edad_asegurado=40, sexo=Sexo.MASCULINO)

        with pytest.warns(ExperimentalModelWarning, match="S-11.4"):
            CalculadoraRM(config, tabla_emssa09)

    def test_el_resultado_lleva_el_aviso(self, tabla_emssa09):
        """El aviso viaja dentro del resultado, no solo en el warning."""
        config = _config_temporal(edad_asegurado=40, sexo=Sexo.MASCULINO)
        resultado = CalculadoraRM(config, tabla_emssa09).calcular()

        assert resultado.disclaimer == DISCLAIMER_RM
        assert "NO conforme" in resultado.disclaimer
        assert "prima NETA" in resultado.disclaimer
        assert resultado.tabla_mortalidad == "EMSSA-09"

    def test_prima_suministrada_se_respeta(self, tabla_sintetica):
        """Con prima explícita no se aplica equivalencia.

        Con P = 200,000 (mayor que la prima neta de 164,924.51), la reserva en
        t = 0 debe ser negativa: el valor de las primas futuras excede el de los
        beneficios. El importe a constituir en balance sí se trunca en cero.
        """
        config = _config_temporal(
            edad_asegurado=60,
            sexo=Sexo.MASCULINO,
            edad_contratacion=60,
            plazo_seguro=3,
            plazo_pago=3,
            tasa="0.05",
            prima="200000",
        )
        resultado = CalculadoraRM(config, tabla_sintetica).calcular()

        assert resultado.prima_neta_anual == Decimal("200000.00")
        assert resultado.prima_determinada_por_equivalencia is False
        assert resultado.reserva_matematica < 0
        assert resultado.reserva_a_constituir == Decimal("0.00")

    def test_componentes_suman_la_reserva(self, tabla_emssa09):
        """VP(beneficios) - VP(primas) es la reserva publicada."""
        config = _config_temporal(edad_asegurado=45, sexo=Sexo.MASCULINO)
        resultado = CalculadoraRM(config, tabla_emssa09).calcular()

        diferencia = resultado.valor_presente_beneficios - resultado.valor_presente_primas
        assert abs(diferencia - resultado.reserva_matematica) <= Decimal("0.01")

    def test_edad_fuera_de_la_tabla_se_rechaza(self, tabla_sintetica):
        """Una edad más allá de ω no se extrapola: se rechaza."""
        config = ConfiguracionRM(
            suma_asegurada=Decimal("1000000"),
            edad_contratacion=60,
            edad_asegurado=70,
            sexo=Sexo.MASCULINO,
            plazo_seguro_anios=15,
            tasa_interes_tecnico=Decimal("0.05"),
        )

        with pytest.raises(ValueError, match="edad terminal"):
            CalculadoraRM(config, tabla_sintetica)

    def test_renta_vitalicia_sin_primas_futuras(self, tabla_emssa09):
        """La reserva de una renta en curso es el VP de los pagos restantes."""
        config = ConfiguracionRM(
            edad_contratacion=65,
            edad_asegurado=65,
            sexo=Sexo.MASCULINO,
            tasa_interes_tecnico=Decimal("0.055"),
            es_renta_vitalicia=True,
            monto_renta_mensual=Decimal("10000"),
        )
        resultado = CalculadoraRM(config, tabla_emssa09).calcular()

        assert resultado.reserva_matematica > 0
        assert resultado.valor_presente_primas == Decimal("0.00")
        assert resultado.valor_presente_beneficios == resultado.reserva_matematica

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_renta_vitalicia_coincide_con_anualidad_de_conmutacion(self, tabla_emssa09):
        """RM = 12·renta · ä_x, con ä_x tomada de Nx/Dx."""
        config = ConfiguracionRM(
            edad_contratacion=65,
            edad_asegurado=65,
            sexo=Sexo.FEMENINO,
            tasa_interes_tecnico=Decimal("0.055"),
            es_renta_vitalicia=True,
            monto_renta_mensual=Decimal("10000"),
        )
        resultado = CalculadoraRM(config, tabla_emssa09).calcular()

        tc = TablaConmutacion(tabla_emssa09, Sexo.FEMENINO, Decimal("0.055"))
        esperado = Decimal("120000") * tc.ax(65)

        assert float(resultado.reserva_matematica) == pytest.approx(float(esperado), rel=1e-4)

    def test_renta_femenina_supera_a_la_masculina(self, tabla_emssa09):
        """Menor mortalidad femenina implica más pagos esperados."""

        def reserva(sexo: Sexo) -> Decimal:
            config = ConfiguracionRM(
                edad_contratacion=65,
                edad_asegurado=65,
                sexo=sexo,
                tasa_interes_tecnico=Decimal("0.055"),
                es_renta_vitalicia=True,
                monto_renta_mensual=Decimal("10000"),
            )
            return CalculadoraRM(config, tabla_emssa09).calcular().reserva_matematica

        assert reserva(Sexo.FEMENINO) > reserva(Sexo.MASCULINO)


# ======================================
# Tests de Validador Suficiencia
# ======================================


class TestValidadorSuficiencia:
    """Tests para ValidadorSuficiencia"""

    def test_validar_reserva_suficiente(self):
        """Debe validar reserva suficiente correctamente"""
        validador = ValidadorSuficiencia()

        resultado = validador.validar_reserva_individual(
            reserva_constituida=Decimal("50000000"),
            reserva_calculada=Decimal("45000000"),
        )

        # 50M > 45M × 1.05 = 47.25M → Suficiente
        assert resultado.es_suficiente is True
        assert resultado.deficit_superavit > 0
        assert resultado.porcentaje_cobertura > Decimal("100")

    def test_validar_reserva_insuficiente(self):
        """Debe detectar reserva insuficiente"""
        validador = ValidadorSuficiencia()

        resultado = validador.validar_reserva_individual(
            reserva_constituida=Decimal("40000000"),
            reserva_calculada=Decimal("50000000"),
        )

        # 40M < 50M × 1.05 = 52.5M → Insuficiente
        assert resultado.es_suficiente is False
        assert resultado.deficit_superavit < 0
        assert resultado.requiere_constitucion_adicional is True
        assert resultado.porcentaje_cobertura < Decimal("100")

    def test_validar_con_margen_personalizado(self):
        """Debe usar margen de seguridad personalizado"""
        validador = ValidadorSuficiencia()

        # Con margen 10% en vez de 5%
        resultado = validador.validar_reserva_individual(
            reserva_constituida=Decimal("50000000"),
            reserva_calculada=Decimal("45000000"),
            margen_seguridad=Decimal("0.10"),
        )

        # 50M vs 45M × 1.10 = 49.5M → Apenas suficiente
        assert resultado.es_suficiente is True
        assert resultado.reserva_minima_requerida == Decimal("49500000.00")

    def test_validar_reservas_agregadas(self):
        """Debe validar múltiples reservas por ramo"""
        validador = ValidadorSuficiencia()

        reservas_const = {
            "autos": Decimal("30000000"),
            "vida": Decimal("80000000"),
            "incendio": Decimal("15000000"),
        }

        reservas_calc = {
            "autos": Decimal("28000000"),
            "vida": Decimal("75000000"),
            "incendio": Decimal("16000000"),  # Insuficiente
        }

        resultados = validador.validar_reservas_agregadas(reservas_const, reservas_calc)

        # Autos y vida suficientes, incendio insuficiente
        assert resultados["autos"].es_suficiente is True
        assert resultados["vida"].es_suficiente is True
        assert resultados["incendio"].es_suficiente is False

    def test_generar_reporte_suficiencia(self):
        """Debe generar reporte resumen de suficiencia"""
        validador = ValidadorSuficiencia()

        reservas_const = {
            "autos": Decimal("30000000"),
            "vida": Decimal("80000000"),
        }

        reservas_calc = {
            "autos": Decimal("28000000"),
            "vida": Decimal("75000000"),
        }

        validaciones = validador.validar_reservas_agregadas(reservas_const, reservas_calc)
        reporte = validador.generar_reporte_suficiencia(validaciones)

        assert reporte["numero_ramos_total"] == 2
        assert reporte["es_suficiente_global"] is True
        assert reporte["numero_ramos_con_deficit"] == 0
        assert reporte["total_reservas_constituidas"] == 110000000.0


# ======================================
# Tests de Validación de Modelos
# ======================================


class TestValidacionesModelos:
    """Tests para validaciones de modelos"""

    def test_prima_devengada_no_puede_exceder_emitida(self):
        """Prima devengada no puede ser mayor que emitida"""
        with pytest.raises((ValueError, Exception)):
            ConfiguracionRRC(
                prima_emitida=Decimal("50000000"),
                prima_devengada=Decimal("60000000"),  # Mayor que emitida
                fecha_calculo=date(2024, 6, 30),
            )

    def test_edad_valida(self):
        """Configuración con edades válidas debe funcionar"""
        config = _config_temporal(
            edad_asegurado=45, sexo=Sexo.MASCULINO, edad_contratacion=40, plazo_seguro=25
        )

        assert config.edad_asegurado >= config.edad_contratacion
        assert config.duracion_transcurrida == 5

    def test_edad_actual_menor_a_contratacion_se_rechaza(self):
        """La edad alcanzada no puede ser anterior a la emisión"""
        with pytest.raises(ValueError, match="menor a edad de contratación"):
            _config_temporal(
                edad_asegurado=35, sexo=Sexo.MASCULINO, edad_contratacion=40, plazo_seguro=20
            )

    def test_plazo_de_cobertura_es_obligatorio(self):
        """No hay plazo por omisión: la versión anterior suponía ω = 85."""
        with pytest.raises(ValueError, match="plazo_seguro_anios"):
            ConfiguracionRM(
                suma_asegurada=Decimal("1000000"),
                edad_contratacion=40,
                edad_asegurado=45,
                sexo=Sexo.MASCULINO,
                tasa_interes_tecnico=Decimal("0.055"),
            )

    def test_plazo_de_pago_no_excede_la_cobertura(self):
        """Un pago más largo que la cobertura no describe ningún contrato."""
        with pytest.raises(ValueError, match="plazo de pago"):
            _config_temporal(
                edad_asegurado=40,
                sexo=Sexo.MASCULINO,
                edad_contratacion=40,
                plazo_seguro=10,
                plazo_pago=20,
            )

    def test_poliza_vencida_se_rechaza(self):
        """Una duración mayor al plazo no tiene reserva que valuar."""
        with pytest.raises(ValueError, match="ya venció"):
            _config_temporal(
                edad_asegurado=65,
                sexo=Sexo.MASCULINO,
                edad_contratacion=40,
                plazo_seguro=20,
                plazo_pago=20,
            )

    def test_sexo_es_obligatorio(self):
        """Sin sexo no hay tabla que consultar."""
        with pytest.raises(ValueError):
            ConfiguracionRM(
                suma_asegurada=Decimal("1000000"),
                edad_contratacion=40,
                edad_asegurado=45,
                plazo_seguro_anios=20,
                tasa_interes_tecnico=Decimal("0.055"),
            )

    def test_renta_requiere_monto_mensual(self):
        """Renta vitalicia requiere monto de renta mensual"""
        with pytest.raises(ValueError, match="monto_renta_mensual"):
            ConfiguracionRM(
                edad_contratacion=65,
                edad_asegurado=65,
                sexo=Sexo.MASCULINO,
                tasa_interes_tecnico=Decimal("0.055"),
                es_renta_vitalicia=True,
            )

    def test_seguro_requiere_suma_asegurada(self):
        """Un seguro sin suma asegurada no describe beneficio alguno."""
        with pytest.raises(ValueError, match="suma_asegurada"):
            ConfiguracionRM(
                edad_contratacion=40,
                edad_asegurado=45,
                sexo=Sexo.MASCULINO,
                plazo_seguro_anios=20,
                tasa_interes_tecnico=Decimal("0.055"),
            )
