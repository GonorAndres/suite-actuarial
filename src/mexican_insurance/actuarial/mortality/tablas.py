"""
Cargador y manipulador de tablas de mortalidad

Soporta las principales tablas usadas en México:
- EMSSA-09 (Experiencia Mexicana de Seguridad Social Actualizada)
- CNSF-2000-I y CNSF-2000-II
- Tablas personalizadas
"""

import json
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from mexican_insurance.core.validators import RegistroMortalidad, Sexo


class TablaMortalidad:
    """
    Maneja tablas de mortalidad para cálculos actuariales.

    Esta clase permite cargar, interpolar y consultar probabilidades
    de muerte (qx) desde diferentes fuentes.

    Attributes:
        nombre: Nombre de la tabla (ej: "EMSSA-09")
        datos: DataFrame con los datos de la tabla
        metadata: Información adicional sobre la tabla

    Examples:
        >>> tabla = TablaMortalidad.cargar_emssa09()
        >>> qx = tabla.obtener_qx(edad=35, sexo=Sexo.HOMBRE)
        >>> print(f"Probabilidad de muerte: {qx:.6f}")
    """

    def __init__(
        self,
        nombre: str,
        datos: pd.DataFrame,
        metadata: Optional[Dict] = None,
    ):
        """
        Inicializa una tabla de mortalidad.

        Args:
            nombre: Nombre identificador de la tabla
            datos: DataFrame con columnas ['edad', 'sexo', 'qx']
            metadata: Dict con información adicional (fuente, año, etc.)
        """
        self.nombre = nombre
        self.datos = datos
        self.metadata = metadata or {}

        # Validar estructura del DataFrame
        self._validar_estructura()

    def _validar_estructura(self) -> None:
        """Valida que el DataFrame tenga las columnas necesarias"""
        columnas_requeridas = {"edad", "sexo", "qx"}
        columnas_presentes = set(self.datos.columns)

        if not columnas_requeridas.issubset(columnas_presentes):
            faltantes = columnas_requeridas - columnas_presentes
            raise ValueError(
                f"Faltan columnas requeridas en la tabla: {faltantes}"
            )

        # Validar tipos de datos
        if not pd.api.types.is_numeric_dtype(self.datos["edad"]):
            raise ValueError("La columna 'edad' debe ser numérica")

        if not pd.api.types.is_numeric_dtype(self.datos["qx"]):
            raise ValueError("La columna 'qx' debe ser numérica")

    def obtener_qx(
        self,
        edad: int,
        sexo: Union[Sexo, str],
        interpolar: bool = False,
    ) -> Decimal:
        """
        Obtiene la probabilidad de muerte para una edad y sexo dados.

        Args:
            edad: Edad en años cumplidos
            sexo: Sexo (Sexo.HOMBRE, Sexo.MUJER o "H"/"M")
            interpolar: Si True, interpola valores faltantes

        Returns:
            Probabilidad de muerte qx

        Raises:
            ValueError: Si no existe el dato y interpolar=False
            KeyError: Si la combinación edad/sexo no existe

        Examples:
            >>> tabla.obtener_qx(35, Sexo.HOMBRE)
            Decimal('0.001234')
        """
        # Normalizar sexo
        if isinstance(sexo, str):
            sexo = Sexo(sexo)

        # Buscar en la tabla
        mascara = (self.datos["edad"] == edad) & (
            self.datos["sexo"] == sexo.value
        )
        resultados = self.datos[mascara]

        if len(resultados) == 0:
            if interpolar:
                return self._interpolar_qx(edad, sexo)
            else:
                raise ValueError(
                    f"No existe qx para edad={edad}, sexo={sexo.value} "
                    f"en la tabla {self.nombre}"
                )

        # Retornar como Decimal para precisión
        qx_valor = resultados.iloc[0]["qx"]
        return Decimal(str(qx_valor))

    def _interpolar_qx(self, edad: int, sexo: Sexo) -> Decimal:
        """
        Interpola linealmente qx cuando falta un valor.

        Args:
            edad: Edad a interpolar
            sexo: Sexo

        Returns:
            qx interpolado

        Raises:
            ValueError: Si no hay suficientes datos para interpolar
        """
        # Filtrar datos del mismo sexo
        datos_sexo = self.datos[self.datos["sexo"] == sexo.value].copy()

        if len(datos_sexo) < 2:
            raise ValueError(
                f"No hay suficientes datos para interpolar en sexo={sexo.value}"
            )

        # Ordenar por edad
        datos_sexo = datos_sexo.sort_values("edad")

        # Encontrar edades circundantes
        edades_menores = datos_sexo[datos_sexo["edad"] < edad]
        edades_mayores = datos_sexo[datos_sexo["edad"] > edad]

        if len(edades_menores) == 0 or len(edades_mayores) == 0:
            raise ValueError(
                f"Edad {edad} está fuera del rango de la tabla "
                f"(min={datos_sexo['edad'].min()}, max={datos_sexo['edad'].max()})"
            )

        # Tomar valores más cercanos
        edad_anterior = edades_menores.iloc[-1]
        edad_siguiente = edades_mayores.iloc[0]

        # Interpolación lineal
        x0, y0 = edad_anterior["edad"], edad_anterior["qx"]
        x1, y1 = edad_siguiente["edad"], edad_siguiente["qx"]

        qx_interpolado = y0 + (y1 - y0) * (edad - x0) / (x1 - x0)

        return Decimal(str(qx_interpolado))

    def obtener_tabla_completa(
        self,
        sexo: Union[Sexo, str],
    ) -> pd.DataFrame:
        """
        Obtiene toda la tabla para un sexo dado.

        Args:
            sexo: Sexo a filtrar

        Returns:
            DataFrame con edad, qx, lx (si existe), etc.

        Examples:
            >>> df = tabla.obtener_tabla_completa(Sexo.HOMBRE)
            >>> print(df.head())
        """
        if isinstance(sexo, str):
            sexo = Sexo(sexo)

        return self.datos[self.datos["sexo"] == sexo.value].copy()

    def calcular_lx(
        self,
        sexo: Union[Sexo, str],
        raiz: int = 100000,
    ) -> pd.DataFrame:
        """
        Calcula lx (número de sobrevivientes) a partir de qx.

        Args:
            sexo: Sexo para el cálculo
            raiz: Número inicial de personas (típicamente 100,000)

        Returns:
            DataFrame con edad, qx, lx, dx

        Examples:
            >>> tabla_vida = tabla.calcular_lx(Sexo.MUJER, raiz=100000)
            >>> print(tabla_vida[['edad', 'lx', 'dx']].head())
        """
        tabla = self.obtener_tabla_completa(sexo).copy()
        tabla = tabla.sort_values("edad").reset_index(drop=True)

        # Inicializar lx
        lx = [raiz]

        # Calcular lx recursivamente: lx[t+1] = lx[t] * (1 - qx[t])
        for i in range(len(tabla) - 1):
            qx = tabla.iloc[i]["qx"]
            lx_siguiente = lx[-1] * (1 - qx)
            lx.append(lx_siguiente)

        # Agregar última entrada (lx final = 0)
        lx.append(0)

        # Asignar a la tabla (lx tiene un elemento más)
        tabla["lx"] = lx[:-1]
        tabla["dx"] = [lx[i] - lx[i + 1] for i in range(len(lx) - 1)]

        return tabla

    @classmethod
    def desde_csv(
        cls,
        path: Union[str, Path],
        nombre: Optional[str] = None,
        **kwargs,
    ) -> "TablaMortalidad":
        """
        Carga una tabla de mortalidad desde un archivo CSV.

        El CSV debe tener columnas: edad, sexo, qx
        Opcionalmente puede tener: lx, dx, ex (esperanza de vida)

        Args:
            path: Ruta al archivo CSV
            nombre: Nombre de la tabla (si no se especifica, usa el nombre del archivo)
            **kwargs: Argumentos adicionales para pd.read_csv

        Returns:
            TablaMortalidad cargada

        Examples:
            >>> tabla = TablaMortalidad.desde_csv("data/emssa09.csv")
        """
        path = Path(path)
        datos = pd.read_csv(path, **kwargs)

        if nombre is None:
            nombre = path.stem

        return cls(nombre=nombre, datos=datos)

    @classmethod
    def cargar_emssa09(cls) -> "TablaMortalidad":
        """
        Carga la tabla EMSSA-09 (si está disponible en data/).

        Returns:
            TablaMortalidad con EMSSA-09

        Raises:
            FileNotFoundError: Si no encuentra el archivo
        """
        # Buscar en directorio de datos
        posibles_rutas = [
            Path("data/mortality_tables/emssa_09.csv"),
            Path("../data/mortality_tables/emssa_09.csv"),
            Path(__file__).parent.parent.parent.parent.parent
            / "data/mortality_tables/emssa_09.csv",
        ]

        for ruta in posibles_rutas:
            if ruta.exists():
                return cls.desde_csv(ruta, nombre="EMSSA-09")

        raise FileNotFoundError(
            "No se encontró la tabla EMSSA-09. "
            "Ejecuta el script de descarga o coloca el archivo en data/mortality_tables/"
        )

    def guardar_csv(self, path: Union[str, Path]) -> None:
        """
        Guarda la tabla en formato CSV.

        Args:
            path: Ruta donde guardar el CSV
        """
        self.datos.to_csv(path, index=False)

    def __repr__(self) -> str:
        """Representación en string"""
        num_registros = len(self.datos)
        edades = f"{self.datos['edad'].min()}-{self.datos['edad'].max()}"
        return (
            f"TablaMortalidad(nombre='{self.nombre}', "
            f"registros={num_registros}, edades={edades})"
        )
