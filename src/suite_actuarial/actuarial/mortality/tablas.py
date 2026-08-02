"""
Cargador y manipulador de tablas de mortalidad

Soporta las principales tablas usadas en México:
- EMSSA-09 (Experiencia Mexicana de Seguridad Social Actualizada)
- CNSF-2000-I y CNSF-2000-II
- Tablas personalizadas

Nota sobre q_omega en EMSSA-09: la tabla publica q_100 = 0.442 para hombres
y q_100 = 0.2455 para mujeres, es decir, q_omega != 1.0. El metodo ``calcular_lx``
acepta un parametro ``omega_convention`` para elegir entre forzar lx=0
en la edad terminal ("force_zero", default) o respetar los valores
publicados ("table_as_is").
"""

import hashlib
import json
import warnings
from decimal import Decimal
from importlib import resources
from pathlib import Path
from typing import Any

import pandas as pd

from suite_actuarial.core.validators import Sexo, normalizar_sexo

# El CSV de EMSSA-09 es un insumo controlado y conserva su columna `sexo` con
# las iniciales publicadas "H" (hombre) y "M" (mujer). Esa es la unica
# convencion de una letra que sobrevive en el proyecto, y solo dentro del
# archivo. Aqui, en la frontera de lectura, se traduce una sola vez a los
# valores de `Sexo`; a partir de ese punto el DataFrame en memoria y todas las
# consultas publicas usan "masculino"/"femenino".
_SEXO_CSV_HEREDADO = {
    "H": Sexo.MASCULINO,
    "M": Sexo.FEMENINO,
}

# Las tablas que viajan con el paquete se leen siempre desde el paquete de
# datos instalado, nunca desde rutas relativas al directorio de trabajo. Una
# copia suelta en el repositorio no es la tabla instalada: cargarla haria que
# el mismo codigo diera resultados distintos segun desde donde se invoque.
_PAQUETE_TABLAS = "suite_actuarial.data.mortality_tables"
_ARCHIVO_METADATOS = "metadata.json"
_ARCHIVO_EMSSA09 = "emssa_09.csv"
_CLAVE_EMSSA09 = "emssa_09"


def _normalizar_columna_sexo(datos: pd.DataFrame, origen: str) -> pd.DataFrame:
    """Traduce la columna `sexo` de un CSV a los valores de `Sexo`.

    Acepta dos formas: las iniciales heredadas del CSV ("H"/"M", bajo la
    convencion hombre/mujer de EMSSA-09) y los valores actuales
    ("masculino"/"femenino"). Cualquier otra cosa es un error: en particular
    una "F", que delataria un archivo escrito bajo la convencion
    masculino/femenino, donde "M" significaria lo contrario.

    Args:
        datos: DataFrame recien leido del CSV.
        origen: Ruta o nombre del archivo, para el mensaje de error.

    Returns:
        El mismo DataFrame con la columna `sexo` normalizada.

    Raises:
        ValueError: Si la columna contiene un valor fuera de las dos formas.
    """
    if "sexo" not in datos.columns:
        return datos

    valores = set(datos["sexo"].astype(str).unique())
    validos = {miembro.value for miembro in Sexo}
    desconocidos = valores - validos - set(_SEXO_CSV_HEREDADO)
    if desconocidos:
        raise ValueError(
            f"La columna 'sexo' de {origen} contiene valores no reconocidos: "
            f"{sorted(desconocidos)}. Se aceptan {sorted(validos)} o las "
            f"iniciales heredadas {sorted(_SEXO_CSV_HEREDADO)} (H=hombre, M=mujer)."
        )
    if valores & set(_SEXO_CSV_HEREDADO) and valores & validos:
        raise ValueError(
            f"La columna 'sexo' de {origen} mezcla iniciales heredadas y valores "
            "actuales; no hay forma de saber que convencion aplica a cada fila."
        )

    datos = datos.copy()
    datos["sexo"] = [
        _SEXO_CSV_HEREDADO[str(valor)].value if str(valor) in _SEXO_CSV_HEREDADO else str(valor)
        for valor in datos["sexo"]
    ]
    return datos


def _sha256(path: Path) -> str:
    """Calcula el hash del archivo de datos para reproducibilidad."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
        >>> qx = tabla.obtener_qx(edad=35, sexo=Sexo.MASCULINO)
        >>> print(f"Probabilidad de muerte: {qx:.6f}")
    """

    def __init__(
        self,
        nombre: str,
        datos: pd.DataFrame,
        metadata: dict | None = None,
        strict: bool = False,
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
        self.strict = strict

        # Validar estructura del DataFrame
        self._validar_estructura()

    def _validar_estructura(self) -> None:
        """Valida que el DataFrame tenga las columnas necesarias"""
        columnas_requeridas = {"edad", "sexo", "qx"}
        columnas_presentes = set(self.datos.columns)

        if not columnas_requeridas.issubset(columnas_presentes):
            faltantes = columnas_requeridas - columnas_presentes
            raise ValueError(f"Faltan columnas requeridas en la tabla: {faltantes}")

        # Validar tipos de datos
        if not pd.api.types.is_numeric_dtype(self.datos["edad"]):
            raise ValueError("La columna 'edad' debe ser numérica")

        if not pd.api.types.is_numeric_dtype(self.datos["qx"]):
            raise ValueError("La columna 'qx' debe ser numérica")

        # La tabla en memoria solo habla la convencion actual. Un DataFrame con
        # iniciales ("H", "M", "F") se rechaza en vez de traducirse: la
        # traduccion vive una sola vez, en `desde_csv`.
        valores_sexo = set(self.datos["sexo"].astype(str).unique())
        valores_validos = {miembro.value for miembro in Sexo}
        if not valores_sexo <= valores_validos:
            invalidos = sorted(valores_sexo - valores_validos)
            raise ValueError(
                f"La columna 'sexo' contiene valores no validos: {invalidos}. "
                f"Valores validos: {sorted(valores_validos)}."
            )

        if self.datos[["edad", "sexo"]].duplicated().any():
            raise ValueError("Cada combinación edad/sexo debe ser única")
        if ((self.datos["qx"] < 0) | (self.datos["qx"] > 1)).any():
            raise ValueError("Las probabilidades qx deben estar en [0, 1]")
        if self.strict:
            self._validar_metadatos_y_rangos()

    def _validar_metadatos_y_rangos(self) -> None:
        """Aplica el contrato completo exigido para tablas importadas."""
        required = ("version", "source", "content_hash", "terminal_age_convention")
        missing = [key for key in required if not self.metadata.get(key)]
        if missing:
            raise ValueError("Faltan metadatos obligatorios de mortalidad: " + ", ".join(missing))
        for sexo, grupo in self.datos.groupby("sexo"):
            edades = sorted(int(edad) for edad in grupo["edad"])
            if edades != list(range(edades[0], edades[-1] + 1)):
                raise ValueError(f"El rango de edades de sexo={sexo} no es contiguo")

    def obtener_qx(
        self,
        edad: int,
        sexo: Sexo | str,
        interpolar: bool = False,
    ) -> Decimal:
        """
        Obtiene la probabilidad de muerte para una edad y sexo dados.

        Args:
            edad: Edad en años cumplidos
            sexo: Sexo (Sexo.MASCULINO, Sexo.FEMENINO o "masculino"/"femenino")
            interpolar: Si True, interpola valores faltantes

        Returns:
            Probabilidad de muerte qx

        Raises:
            ValueError: Si no existe el dato y interpolar=False
            KeyError: Si la combinación edad/sexo no existe

        Examples:
            >>> tabla.obtener_qx(35, Sexo.MASCULINO)
            Decimal('0.001234')
        """
        sexo = normalizar_sexo(sexo)

        # Buscar en la tabla
        mascara = (self.datos["edad"] == edad) & (self.datos["sexo"] == sexo.value)
        resultados = self.datos[mascara]

        if len(resultados) == 0:
            if interpolar:
                warnings.warn(
                    "La interpolacion de qx fue solicitada explicitamente; "
                    "queda registrada en metadata.",
                    UserWarning,
                    stacklevel=2,
                )
                self.metadata["interpolation_used"] = True
                return self._interpolar_qx(edad, sexo)
            else:
                raise ValueError(
                    f"No existe qx para edad={edad}, sexo={sexo.value} en la tabla {self.nombre}"
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
            raise ValueError(f"No hay suficientes datos para interpolar en sexo={sexo.value}")

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
        sexo: Sexo | str,
    ) -> pd.DataFrame:
        """
        Obtiene toda la tabla para un sexo dado.

        Args:
            sexo: Sexo a filtrar

        Returns:
            DataFrame con edad, qx, lx (si existe), etc.

        Examples:
            >>> df = tabla.obtener_tabla_completa(Sexo.MASCULINO)
            >>> print(df.head())
        """
        sexo = normalizar_sexo(sexo)

        return self.datos[self.datos["sexo"] == sexo.value].copy()

    def calcular_lx(
        self,
        sexo: Sexo | str,
        raiz: int = 100000,
        omega_convention: str = "force_zero",
    ) -> pd.DataFrame:
        """
        Calcula lx (número de sobrevivientes) a partir de qx.

        Args:
            sexo: Sexo para el cálculo
            raiz: Número inicial de personas (típicamente 100,000)
            omega_convention: Tratamiento de la edad terminal.
                - "force_zero": lx[omega+1] = 0 (todos mueren al final).
                - "table_as_is": lx[omega+1] = lx[omega] * (1 - qx[omega]).

        Returns:
            DataFrame con edad, qx, lx, dx

        Examples:
            >>> tabla_vida = tabla.calcular_lx(Sexo.FEMENINO, raiz=100000)
            >>> print(tabla_vida[['edad', 'lx', 'dx']].head())
        """
        if omega_convention not in ("force_zero", "table_as_is"):
            raise ValueError(
                f"omega_convention debe ser 'force_zero' o 'table_as_is', "
                f"recibido: '{omega_convention}'"
            )
        if omega_convention == "force_zero":
            warnings.warn(
                "force_zero es una convencion legacy; use table_as_is o documente el terminal-age treatment.",
                UserWarning,
                stacklevel=2,
            )
            self.metadata["terminal_age_convention_used"] = "force_zero"

        tabla = self.obtener_tabla_completa(sexo).copy()
        tabla = tabla.sort_values("edad").reset_index(drop=True)

        lx = [raiz]

        for i in range(len(tabla) - 1):
            qx = tabla.iloc[i]["qx"]
            lx_siguiente = lx[-1] * (1 - qx)
            lx.append(lx_siguiente)

        if omega_convention == "force_zero":
            lx.append(0)
            tabla["lx"] = lx[:-1]
            tabla["dx"] = [lx[i] - lx[i + 1] for i in range(len(lx) - 1)]
        else:
            tabla["lx"] = lx
            tabla["dx"] = tabla["lx"] * tabla["qx"]

        return tabla

    @classmethod
    def desde_csv(
        cls,
        path: str | Path,
        nombre: str | None = None,
        metadata: dict[str, Any] | None = None,
        strict: bool = False,
        **kwargs: Any,
    ) -> "TablaMortalidad":
        """
        Carga una tabla de mortalidad desde un archivo CSV.

        El CSV debe tener columnas: edad, sexo, qx
        Opcionalmente puede tener: lx, dx, ex (esperanza de vida)

        La columna `sexo` puede venir con las iniciales heredadas "H"/"M"
        (hombre/mujer, como el archivo publicado de EMSSA-09) o ya con los
        valores actuales "masculino"/"femenino". Este metodo es el unico lugar
        donde ocurre esa traduccion.

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
        datos = _normalizar_columna_sexo(pd.read_csv(path, **kwargs), str(path))

        if nombre is None:
            nombre = path.stem

        return cls(nombre=nombre, datos=datos, metadata=metadata, strict=strict)

    @classmethod
    def _cargar_verificada(
        cls,
        directorio: Path,
        *,
        archivo_csv: str,
        clave_metadatos: str,
        nombre: str,
    ) -> "TablaMortalidad":
        """Carga una tabla empaquetada verificando su hash declarado.

        Es el unico mecanismo de carga de las tablas que viajan con el paquete.
        El directorio debe contener el CSV y el `metadata.json` que lo declara.
        El hash del archivo se compara contra el declarado; no se recalcula ni
        se sobrescribe, porque un hash recalculado en cada carga siempre
        coincide y no verifica nada. La tabla se construye en modo estricto:
        una tabla sin metadatos completos no se carga en modo degradado.

        Args:
            directorio: Carpeta con el CSV y `metadata.json`.
            archivo_csv: Nombre del archivo CSV dentro del directorio.
            clave_metadatos: Clave de la tabla dentro de `metadata.json`.
            nombre: Nombre con el que se publica la tabla.

        Returns:
            TablaMortalidad estricta, con los metadatos declarados.

        Raises:
            FileNotFoundError: Si falta el CSV o el `metadata.json`.
            ValueError: Si el `metadata.json` no declara la tabla, no declara
                su `content_hash`, o el contenido del CSV no coincide con el
                hash declarado.
        """
        csv_path = directorio / archivo_csv
        metadata_path = directorio / _ARCHIVO_METADATOS

        if not csv_path.is_file():
            raise FileNotFoundError(
                f"No se encontro la tabla de mortalidad '{archivo_csv}' en {directorio}. "
                "El archivo viaja dentro del paquete: su ausencia indica una instalacion "
                "incompleta. Reinstala con: pip install -e '.[dev,api,viz]'"
            )
        if not metadata_path.is_file():
            raise FileNotFoundError(
                f"No se encontro '{_ARCHIVO_METADATOS}' junto a '{archivo_csv}' en {directorio}. "
                "Sin metadatos declarados la tabla no se carga: la procedencia y el estado "
                "de los datos son parte del insumo, no un extra opcional."
            )

        declarado = json.loads(metadata_path.read_text(encoding="utf-8"))
        entrada = declarado.get("tablas", {}).get(clave_metadatos)
        if not isinstance(entrada, dict):
            raise ValueError(
                f"'{_ARCHIVO_METADATOS}' no declara la tabla '{clave_metadatos}' en {directorio}."
            )

        metadata: dict[str, Any] = dict(entrada)
        hash_declarado = metadata.get("content_hash")
        if not hash_declarado:
            raise ValueError(
                f"La tabla '{clave_metadatos}' no declara 'content_hash' en "
                f"'{_ARCHIVO_METADATOS}'. Sin hash declarado no hay nada que verificar."
            )

        hash_calculado = f"sha256:{_sha256(csv_path)}"
        if hash_calculado != hash_declarado:
            raise ValueError(
                f"El contenido de '{archivo_csv}' no coincide con el hash declarado en "
                f"'{_ARCHIVO_METADATOS}'. Declarado: {hash_declarado}. "
                f"Calculado: {hash_calculado}. La tabla no se carga: o el archivo cambio "
                "sin actualizar su declaracion, o la declaracion describe otro archivo."
            )

        # `metadata.json` nombra la fuente en espanol (`fuente`); el contrato
        # interno de metadatos la exige bajo `source`. Se traduce la clave a
        # partir de lo declarado, sin inventar procedencia: si el archivo no
        # declara fuente, la validacion estricta lo reporta como metadato
        # faltante en lugar de rellenarlo.
        if not metadata.get("source") and metadata.get("fuente"):
            estado = metadata.get("data_status", "sin declarar")
            metadata["source"] = f"{metadata['fuente']} / instantanea empaquetada ({estado})"

        return cls.desde_csv(
            csv_path,
            nombre=nombre,
            metadata=metadata,
            strict=True,
        )

    @classmethod
    def cargar_emssa09(cls) -> "TablaMortalidad":
        """
        Carga la tabla EMSSA-09 empaquetada, verificando su hash declarado.

        Hay un solo camino de carga: el paquete de datos instalado. No existe
        respaldo por rutas relativas; una copia del CSV en el arbol del
        repositorio no se usa. Si el archivo empaquetado falta, la instalacion
        esta rota y se reporta como tal en vez de degradar la tabla a una carga
        sin metadatos (que reportaria `validation_tier` "supported" para datos
        ilustrativos).

        Returns:
            TablaMortalidad con EMSSA-09, en modo estricto y con
            `data_status: illustrative` tomado de `metadata.json`.

        Raises:
            FileNotFoundError: Si el paquete de datos o alguno de sus archivos
                no esta instalado.
            ValueError: Si el CSV no coincide con el hash declarado o los
                metadatos estan incompletos.
        """
        try:
            recurso = resources.files(_PAQUETE_TABLAS)
        except (ModuleNotFoundError, ImportError) as exc:
            raise FileNotFoundError(
                f"No se encontro el paquete de datos '{_PAQUETE_TABLAS}'. La tabla EMSSA-09 "
                "viaja dentro del paquete: reinstala con pip install -e '.[dev,api,viz]'"
            ) from exc

        with resources.as_file(recurso) as directorio:
            return cls._cargar_verificada(
                Path(directorio),
                archivo_csv=_ARCHIVO_EMSSA09,
                clave_metadatos=_CLAVE_EMSSA09,
                nombre="EMSSA-09",
            )

    def guardar_csv(self, path: str | Path) -> None:
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
            f"TablaMortalidad(nombre='{self.nombre}', registros={num_registros}, edades={edades})"
        )
