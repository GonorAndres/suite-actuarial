"""
Utilidades de cálculos para dashboards de Streamlit.

Funciones helper para realizar cálculos actuariales reutilizables
en los diferentes dashboards.
"""

from decimal import Decimal
from typing import Dict, List, Tuple

import pandas as pd

# Importar desde el paquete principal
from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad
from mexican_insurance.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    Sexo,
)
from mexican_insurance.products.vida.dotal import VidaDotal
from mexican_insurance.products.vida.ordinario import VidaOrdinario
from mexican_insurance.products.vida.temporal import VidaTemporal


def crear_asegurado(
    edad: int,
    sexo: str,
    suma_asegurada: float,
) -> Asegurado:
    """
    Crea objeto Asegurado desde inputs de Streamlit.

    Args:
        edad: Edad del asegurado
        sexo: "Hombre" o "Mujer"
        suma_asegurada: Suma asegurada en pesos

    Returns:
        Objeto Asegurado validado
    """
    sexo_enum = Sexo.HOMBRE if sexo == "Hombre" else Sexo.MUJER

    return Asegurado(
        edad=edad,
        sexo=sexo_enum,
        suma_asegurada=Decimal(str(suma_asegurada)),
    )


def calcular_prima_temporal(
    edad: int,
    sexo: str,
    suma_asegurada: float,
    plazo: int,
    tasa_interes: float,
    tabla: TablaMortalidad,
) -> Dict:
    """
    Calcula prima para Vida Temporal.

    Returns:
        Diccionario con resultados del cálculo
    """
    config = ConfiguracionProducto(
        nombre_producto=f"Vida Temporal {plazo} años",
        plazo_years=plazo,
        tasa_interes_tecnico=Decimal(str(tasa_interes)),
    )

    producto = VidaTemporal(config, tabla)
    asegurado = crear_asegurado(edad, sexo, suma_asegurada)

    resultado = producto.calcular_prima(asegurado, frecuencia_pago="mensual")

    return {
        "prima_neta": float(resultado.prima_neta),
        "prima_total": float(resultado.prima_total),
        "recargos": {k: float(v) for k, v in resultado.desglose_recargos.items()},
        "producto": "Temporal",
    }


def calcular_prima_ordinario(
    edad: int,
    sexo: str,
    suma_asegurada: float,
    plazo_pago: int | None,
    tasa_interes: float,
    tabla: TablaMortalidad,
) -> Dict:
    """
    Calcula prima para Vida Ordinario.

    Args:
        plazo_pago: Periodo de pago de primas (None = vitalicio)

    Returns:
        Diccionario con resultados del cálculo
    """
    plazo = plazo_pago if plazo_pago else 20
    config = ConfiguracionProducto(
        nombre_producto="Vida Ordinario",
        plazo_years=plazo,
        tasa_interes_tecnico=Decimal(str(tasa_interes)),
    )

    producto = VidaOrdinario(
        config, tabla, plazo_pago_vitalicio=(plazo_pago is None)
    )
    asegurado = crear_asegurado(edad, sexo, suma_asegurada)

    resultado = producto.calcular_prima(asegurado, frecuencia_pago="mensual")

    return {
        "prima_neta": float(resultado.prima_neta),
        "prima_total": float(resultado.prima_total),
        "recargos": {k: float(v) for k, v in resultado.desglose_recargos.items()},
        "producto": "Ordinario",
    }


def calcular_prima_dotal(
    edad: int,
    sexo: str,
    suma_asegurada: float,
    plazo: int,
    tasa_interes: float,
    tabla: TablaMortalidad,
) -> Dict:
    """
    Calcula prima para Vida Dotal.

    Returns:
        Diccionario con resultados del cálculo
    """
    config = ConfiguracionProducto(
        nombre_producto=f"Vida Dotal {plazo} años",
        plazo_years=plazo,
        tasa_interes_tecnico=Decimal(str(tasa_interes)),
    )

    producto = VidaDotal(config, tabla)
    asegurado = crear_asegurado(edad, sexo, suma_asegurada)

    resultado = producto.calcular_prima(asegurado, frecuencia_pago="mensual")

    return {
        "prima_neta": float(resultado.prima_neta),
        "prima_total": float(resultado.prima_total),
        "recargos": {k: float(v) for k, v in resultado.desglose_recargos.items()},
        "producto": "Dotal",
    }


def calcular_reserva_matematica(
    producto_tipo: str,
    edad_inicial: int,
    sexo: str,
    suma_asegurada: float,
    plazo: int,
    tasa_interes: float,
    tabla: TablaMortalidad,
    anos_transcurridos: int,
) -> float:
    """
    Calcula reserva matemática en un punto del tiempo.

    Args:
        producto_tipo: "Temporal", "Ordinario", o "Dotal"
        anos_transcurridos: Años desde inicio de la póliza

    Returns:
        Monto de reserva matemática
    """
    asegurado = crear_asegurado(edad_inicial, sexo, suma_asegurada)

    if producto_tipo == "Temporal":
        config = ConfiguracionProducto(
            nombre_producto=f"Vida Temporal {plazo} años",
            plazo_years=plazo,
            tasa_interes_tecnico=Decimal(str(tasa_interes)),
        )
        producto = VidaTemporal(config, tabla)

    elif producto_tipo == "Ordinario":
        config = ConfiguracionProducto(
            nombre_producto="Vida Ordinario",
            plazo_years=plazo,
            tasa_interes_tecnico=Decimal(str(tasa_interes)),
        )
        producto = VidaOrdinario(config, tabla)

    elif producto_tipo == "Dotal":
        config = ConfiguracionProducto(
            nombre_producto=f"Vida Dotal {plazo} años",
            plazo_years=plazo,
            tasa_interes_tecnico=Decimal(str(tasa_interes)),
        )
        producto = VidaDotal(config, tabla)

    else:
        raise ValueError(f"Tipo de producto desconocido: {producto_tipo}")

    reserva = producto.calcular_reserva(asegurado, anio=anos_transcurridos)
    return float(reserva)


def generar_tabla_comparacion(
    edad: int,
    sexo: str,
    suma_asegurada: float,
    plazo: int,
    tasa_interes: float,
    tabla: TablaMortalidad,
) -> pd.DataFrame:
    """
    Genera tabla comparativa entre los 3 productos.

    Returns:
        DataFrame con comparación de productos
    """
    # Calcular primas para cada producto
    temporal = calcular_prima_temporal(
        edad, sexo, suma_asegurada, plazo, tasa_interes, tabla
    )

    ordinario = calcular_prima_ordinario(
        edad, sexo, suma_asegurada, None, tasa_interes, tabla
    )

    dotal = calcular_prima_dotal(
        edad, sexo, suma_asegurada, plazo, tasa_interes, tabla
    )

    # Crear DataFrame comparativo
    data = {
        "Producto": ["Temporal", "Ordinario", "Dotal"],
        "Prima Neta": [
            temporal["prima_neta"],
            ordinario["prima_neta"],
            dotal["prima_neta"],
        ],
        "Prima Total": [
            temporal["prima_total"],
            ordinario["prima_total"],
            dotal["prima_total"],
        ],
        "Cobertura": [
            f"{plazo} años (solo muerte)",
            "Vitalicia (solo muerte)",
            f"{plazo} años (muerte + supervivencia)",
        ],
    }

    df = pd.DataFrame(data)

    # Formatear columnas monetarias
    df["Prima Neta"] = df["Prima Neta"].apply(lambda x: f"${x:,.2f}")
    df["Prima Total"] = df["Prima Total"].apply(lambda x: f"${x:,.2f}")

    return df


def analisis_sensibilidad_edad(
    producto_tipo: str,
    edad_min: int,
    edad_max: int,
    sexo: str,
    suma_asegurada: float,
    plazo: int,
    tasa_interes: float,
    tabla: TablaMortalidad,
) -> pd.DataFrame:
    """
    Análisis de sensibilidad de prima vs edad.

    Returns:
        DataFrame con primas por edad
    """
    edades = range(edad_min, edad_max + 1)
    primas_netas = []
    primas_totales = []

    for edad in edades:
        if producto_tipo == "Temporal":
            resultado = calcular_prima_temporal(
                edad, sexo, suma_asegurada, plazo, tasa_interes, tabla
            )
        elif producto_tipo == "Ordinario":
            resultado = calcular_prima_ordinario(
                edad, sexo, suma_asegurada, None, tasa_interes, tabla
            )
        elif producto_tipo == "Dotal":
            resultado = calcular_prima_dotal(
                edad, sexo, suma_asegurada, plazo, tasa_interes, tabla
            )

        primas_netas.append(resultado["prima_neta"])
        primas_totales.append(resultado["prima_total"])

    return pd.DataFrame({
        "Edad": list(edades),
        "Prima Neta": primas_netas,
        "Prima Total": primas_totales,
    })


def analisis_sensibilidad_tasa(
    producto_tipo: str,
    edad: int,
    sexo: str,
    suma_asegurada: float,
    plazo: int,
    tasa_min: float,
    tasa_max: float,
    step: float,
    tabla: TablaMortalidad,
) -> pd.DataFrame:
    """
    Análisis de sensibilidad de prima vs tasa de interés.

    Returns:
        DataFrame con primas por tasa
    """
    # Generar tasas
    tasas = []
    tasa = tasa_min
    while tasa <= tasa_max:
        tasas.append(tasa)
        tasa += step

    primas_netas = []
    primas_totales = []

    for tasa in tasas:
        if producto_tipo == "Temporal":
            resultado = calcular_prima_temporal(
                edad, sexo, suma_asegurada, plazo, tasa, tabla
            )
        elif producto_tipo == "Ordinario":
            resultado = calcular_prima_ordinario(
                edad, sexo, suma_asegurada, None, tasa, tabla
            )
        elif producto_tipo == "Dotal":
            resultado = calcular_prima_dotal(
                edad, sexo, suma_asegurada, plazo, tasa, tabla
            )

        primas_netas.append(resultado["prima_neta"])
        primas_totales.append(resultado["prima_total"])

    return pd.DataFrame({
        "Tasa (%)": [t * 100 for t in tasas],
        "Prima Neta": primas_netas,
        "Prima Total": primas_totales,
    })


def proyeccion_reservas(
    producto_tipo: str,
    edad: int,
    sexo: str,
    suma_asegurada: float,
    plazo: int,
    tasa_interes: float,
    tabla: TablaMortalidad,
) -> pd.DataFrame:
    """
    Proyecta reservas matemáticas a lo largo del tiempo.

    Returns:
        DataFrame con reservas por año
    """
    anos = range(0, plazo + 1)
    reservas = []

    for ano in anos:
        reserva = calcular_reserva_matematica(
            producto_tipo,
            edad,
            sexo,
            suma_asegurada,
            plazo,
            tasa_interes,
            tabla,
            ano,
        )
        reservas.append(reserva)

    return pd.DataFrame({
        "Año": list(anos),
        "Reserva Matemática": reservas,
        "% Suma Asegurada": [(r / suma_asegurada) * 100 for r in reservas],
    })
