"""Fija los benchmarks publicados en ``docs/VALIDATION.md``.

Ese documento publica cifras concretas -- spot checks de qx de la EMSSA-09,
valores de conmutacion a i = 5.5% y la identidad Ax + d*ax = 1 -- pero ninguna
prueba las sujetaba. Un cambio en la tabla, en la convencion de edad terminal o
en el motor de conmutacion podia dejar el documento mintiendo sin que ningun
gate se enterara. Aqui el oraculo es el documento publicado: los valores estan
transcritos literalmente de ``docs/VALIDATION.md``, no recalculados con la misma
formula que se prueba.

Cada valor se comparo primero contra el computo antes de fijarlo. Si un dia una
de estas pruebas falla, la pregunta es cual de los dos lados cambio: el modelo o
lo que el documento promete. No se corrige el valor esperado sin resolver eso.

Alcance: la tabla EMSSA-09 incluida es una version simplificada con estatus
ilustrativo (ver el inventario Clase B en ``docs/AUDIT.md``). Fijar estos
numeros verifica que el codigo reproduce lo que el documento publica; no
convierte la tabla en un dato oficial vigente.
"""

from __future__ import annotations

import warnings
from decimal import ROUND_HALF_EVEN, Decimal

import pytest

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.pensiones.conmutacion import TablaConmutacion

# --------------------------------------------------------------------------
# Valores transcritos de docs/VALIDATION.md
# --------------------------------------------------------------------------

TASA_TECNICA = Decimal("0.055")

# Seccion 1, "Spot checks de qx": (edad, qx masculino, qx femenino).
# El documento usa los rotulos heredados "Hombre"/"Mujer"; la API expone hoy
# los valores "masculino"/"femenino" de `Sexo`.
QX_PUBLICADOS = [
    (18, Decimal("0.0009"), Decimal("0.0004")),
    (25, Decimal("0.00104"), Decimal("0.00047")),
    (35, Decimal("0.0013"), Decimal("0.00066")),
    (50, Decimal("0.0033"), Decimal("0.0018")),
    (65, Decimal("0.0135"), Decimal("0.006")),
    (80, Decimal("0.062"), Decimal("0.0273")),
    (100, Decimal("0.442"), Decimal("0.2455")),
]

# Seccion 2, "Valores a tasa tecnica i = 5.5% (Hombres)": (edad, Dx, Nx, ax).
# Dx y Nx con cuatro decimales, ax con cuatro decimales, tal como se publican.
CONMUTACION_PUBLICADA = [
    (25, Decimal("26047.6559"), Decimal("461607.5134"), Decimal("17.7217")),
    (35, Decimal("15075.3886"), Decimal("255389.5012"), Decimal("16.9408")),
    (45, Decimal("8685.3941"), Decimal("136208.4928"), Decimal("15.6825")),
    (55, Decimal("4921.8250"), Decimal("67904.8867"), Decimal("13.7967")),
    (65, Decimal("2658.9288"), Decimal("29774.5785"), Decimal("11.1980")),
]

# Seccion 2, "Identidades actuariales verificadas": (edad, Ax, ax).
IDENTIDAD_PUBLICADA = [
    (25, Decimal("0.076122"), Decimal("17.7217")),
    (35, Decimal("0.116829"), Decimal("16.9408")),
    (45, Decimal("0.182430"), Decimal("15.6825")),
    (55, Decimal("0.280741"), Decimal("13.7967")),
    (65, Decimal("0.416220"), Decimal("11.1980")),
]

# "d = i/(1+i) = 0.052133", publicado con seis decimales.
D_PUBLICADA = Decimal("0.052133")

# "Desviacion maxima sobre todas las edades (18-100): 0.0000000000".
# El documento la publica con diez decimales, asi que la prueba exige que
# redondeada a diez decimales siga siendo cero.
DECIMALES_DESVIACION_PUBLICADA = 10


def _redondear(valor: Decimal, decimales: int) -> Decimal:
    """Redondea al numero de decimales con que el documento publica el valor."""
    return valor.quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_EVEN)


# --------------------------------------------------------------------------
# Seccion 1: tabla de mortalidad EMSSA-09
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("edad", "qx_masculino", "qx_femenino"),
    QX_PUBLICADOS,
    ids=[f"edad_{edad}" for edad, _, _ in QX_PUBLICADOS],
)
def test_spot_checks_de_qx_publicados(
    tabla_emssa09: TablaMortalidad,
    edad: int,
    qx_masculino: Decimal,
    qx_femenino: Decimal,
):
    """docs/VALIDATION.md seccion 1: qx exacto por edad y sexo."""
    assert tabla_emssa09.obtener_qx(edad, "masculino") == qx_masculino
    assert tabla_emssa09.obtener_qx(edad, "femenino") == qx_femenino


def test_qx_masculino_mayor_que_femenino_en_todas_las_edades(tabla_emssa09: TablaMortalidad):
    """docs/VALIDATION.md seccion 1: "qx_H > qx_M para todas las edades"."""
    hombres = tabla_emssa09.obtener_tabla_completa("masculino").sort_values("edad")
    mujeres = tabla_emssa09.obtener_tabla_completa("femenino").sort_values("edad")

    assert list(hombres["edad"]) == list(mujeres["edad"])
    fallas = [
        (int(edad), qx_h, qx_m)
        for edad, qx_h, qx_m in zip(hombres["edad"], hombres["qx"], mujeres["qx"], strict=True)
        if not qx_h > qx_m
    ]
    assert fallas == [], f"Edades donde no se cumple qx masculino > qx femenino: {fallas}"


@pytest.mark.parametrize("sexo", ["masculino", "femenino"])
def test_qx_es_monotona_creciente_con_la_edad(tabla_emssa09: TablaMortalidad, sexo: str):
    """docs/VALIDATION.md seccion 1: "qx aumenta con la edad"."""
    tabla = tabla_emssa09.obtener_tabla_completa(sexo).sort_values("edad")
    valores = list(tabla["qx"])
    edades = [int(edad) for edad in tabla["edad"]]

    fallas = [
        (edades[i], valores[i], edades[i + 1], valores[i + 1])
        for i in range(len(valores) - 1)
        if not valores[i + 1] > valores[i]
    ]
    assert fallas == [], f"qx no crece entre estas edades ({sexo}): {fallas}"


@pytest.mark.parametrize("sexo", ["masculino", "femenino"])
def test_qx_dentro_del_intervalo_unitario(tabla_emssa09: TablaMortalidad, sexo: str):
    """docs/VALIDATION.md seccion 1: "0 <= qx <= 1 para todas las entradas"."""
    tabla = tabla_emssa09.obtener_tabla_completa(sexo)
    fuera = [
        (int(edad), qx)
        for edad, qx in zip(tabla["edad"], tabla["qx"], strict=True)
        if not 0 <= qx <= 1
    ]
    assert fuera == [], f"qx fuera de [0, 1] ({sexo}): {fuera}"


@pytest.mark.parametrize("convencion", ["force_zero", "table_as_is"])
@pytest.mark.parametrize("sexo", ["masculino", "femenino"])
def test_lx_es_no_creciente(tabla_emssa09: TablaMortalidad, sexo: str, convencion: str):
    """docs/VALIDATION.md seccion 1: "lx es no-creciente".

    Se comprueba bajo las dos convenciones de edad terminal, porque el
    documento no fija ninguna: la propiedad debe sostenerse en ambas.
    """
    with warnings.catch_warnings():
        # `force_zero` avisa que es una convencion legacy. Aqui se prueba a
        # proposito, no por descuido; el aviso no aporta a la salida del gate.
        warnings.simplefilter("ignore", UserWarning)
        vida = tabla_emssa09.calcular_lx(sexo, omega_convention=convencion)

    vida = vida.sort_values("edad")
    lx = list(vida["lx"])
    edades = [int(edad) for edad in vida["edad"]]

    fallas = [
        (edades[i], lx[i], edades[i + 1], lx[i + 1])
        for i in range(len(lx) - 1)
        if lx[i + 1] > lx[i]
    ]
    assert fallas == [], f"lx crece entre estas edades ({sexo}, {convencion}): {fallas}"


# --------------------------------------------------------------------------
# Seccion 2: funciones de conmutacion
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("edad", "dx", "nx", "ax"),
    CONMUTACION_PUBLICADA,
    ids=[f"edad_{edad}" for edad, _, _, _ in CONMUTACION_PUBLICADA],
)
def test_valores_de_conmutacion_publicados(
    tabla_conmutacion_hombre: TablaConmutacion,
    edad: int,
    dx: Decimal,
    nx: Decimal,
    ax: Decimal,
):
    """docs/VALIDATION.md seccion 2: Dx, Nx y ax masculinos a i = 5.5%."""
    # `TablaConmutacion` guarda la tasa como float porque las columnas de
    # conmutacion se construyen con numpy; se compara contra el Decimal
    # publicado por su representacion exacta, no por conversion binaria.
    assert Decimal(str(tabla_conmutacion_hombre.tasa_interes)) == TASA_TECNICA
    assert _redondear(tabla_conmutacion_hombre.Dx(edad), 4) == dx
    assert _redondear(tabla_conmutacion_hombre.Nx(edad), 4) == nx
    assert _redondear(tabla_conmutacion_hombre.ax(edad), 4) == ax


def test_d_publicada_corresponde_a_la_tasa_tecnica():
    """docs/VALIDATION.md seccion 2: "d = i/(1+i) = 0.052133"."""
    d = TASA_TECNICA / (Decimal("1") + TASA_TECNICA)
    assert _redondear(d, 6) == D_PUBLICADA


@pytest.mark.parametrize(
    ("edad", "ax_seguro", "ax_anualidad"),
    IDENTIDAD_PUBLICADA,
    ids=[f"edad_{edad}" for edad, _, _ in IDENTIDAD_PUBLICADA],
)
def test_identidad_seguro_anualidad_publicada(
    tabla_conmutacion_hombre: TablaConmutacion,
    edad: int,
    ax_seguro: Decimal,
    ax_anualidad: Decimal,
):
    """docs/VALIDATION.md seccion 2: la tabla de Ax, ax y Ax + d*ax = 1."""
    d = TASA_TECNICA / (Decimal("1") + TASA_TECNICA)
    calculado_ax = tabla_conmutacion_hombre.Ax(edad)
    calculado_ax_anualidad = tabla_conmutacion_hombre.ax(edad)

    assert _redondear(calculado_ax, 6) == ax_seguro
    assert _redondear(calculado_ax_anualidad, 4) == ax_anualidad
    assert _redondear(calculado_ax + d * calculado_ax_anualidad, 6) == Decimal("1.000000")


@pytest.mark.parametrize("sexo", ["masculino", "femenino"])
def test_desviacion_maxima_de_la_identidad_sobre_todas_las_edades(
    tabla_conmutacion_hombre: TablaConmutacion,
    tabla_conmutacion_mujer: TablaConmutacion,
    sexo: str,
):
    """docs/VALIDATION.md seccion 2: desviacion maxima 0.0000000000 (edades 18-100).

    El documento reporta la cifra para hombres; se exige tambien para mujeres
    porque la identidad no depende del sexo.
    """
    conmutacion = tabla_conmutacion_hombre if sexo == "masculino" else tabla_conmutacion_mujer
    d = TASA_TECNICA / (Decimal("1") + TASA_TECNICA)

    assert conmutacion.edad_min == 18
    assert conmutacion.edad_max == 100

    desviacion_maxima = max(
        abs(conmutacion.Ax(edad) + d * conmutacion.ax(edad) - Decimal("1"))
        for edad in range(conmutacion.edad_min, conmutacion.edad_max + 1)
    )
    redondeada = _redondear(desviacion_maxima, DECIMALES_DESVIACION_PUBLICADA)
    assert redondeada == Decimal("0"), (
        f"docs/VALIDATION.md publica 0.0000000000 para {sexo}; "
        f"la desviacion maxima calculada es {desviacion_maxima}"
    )


def test_nx_es_la_suma_de_dx_desde_x_hasta_omega(tabla_conmutacion_hombre: TablaConmutacion):
    """docs/VALIDATION.md seccion 2: "Nx = sum(Dx from x to omega)".

    El residuo tolerado es de acumulacion decimal (el orden de suma difiere del
    acumulado precomputado), no un margen sobre la identidad: en la practica
    queda en el orden de 1e-16 relativo.
    """
    omega = tabla_conmutacion_hombre.edad_max
    peor = Decimal("0")
    for edad in range(tabla_conmutacion_hombre.edad_min, omega + 1):
        suma = sum(
            (tabla_conmutacion_hombre.Dx(y) for y in range(edad, omega + 1)),
            start=Decimal("0"),
        )
        relativo = abs(tabla_conmutacion_hombre.Nx(edad) - suma) / abs(suma)
        peor = max(peor, relativo)
    assert peor < Decimal("1e-12"), f"Nx se aparta de sum(Dx): error relativo maximo {peor}"


def test_mx_es_la_suma_de_cx_desde_x_hasta_omega(tabla_conmutacion_hombre: TablaConmutacion):
    """docs/VALIDATION.md seccion 2: "Mx = sum(Cx from x to omega)"."""
    omega = tabla_conmutacion_hombre.edad_max
    peor = Decimal("0")
    for edad in range(tabla_conmutacion_hombre.edad_min, omega + 1):
        suma = sum(
            (tabla_conmutacion_hombre.Cx(y) for y in range(edad, omega + 1)),
            start=Decimal("0"),
        )
        relativo = abs(tabla_conmutacion_hombre.Mx(edad) - suma) / abs(suma)
        peor = max(peor, relativo)
    assert peor < Decimal("1e-12"), f"Mx se aparta de sum(Cx): error relativo maximo {peor}"
