"""
Integridad del insumo de mortalidad: un solo camino de carga, verificado.

La tabla EMSSA-09 que viaja con el paquete es un insumo controlado. Estas
pruebas fijan tres cosas que antes no se sostenian:

1. El contenido del CSV esta anclado a un sha256 concreto, escrito aqui y
   declarado en `metadata.json`. Un cambio silencioso del archivo -- otra
   version, otra escala de qx -- rompe la prueba en lugar de propagarse a las
   primas.
2. La carga verifica ese hash en vez de recalcularlo y sobrescribirlo. Un hash
   recalculado en cada carga siempre coincide consigo mismo y no verifica nada.
3. No hay carga de respaldo. Antes, si el paquete de datos no estaba a la vista,
   el cargador leia una copia suelta del CSV sin metadatos, y la tabla
   sintetica terminaba reportando `validation_tier: supported`. Una tabla
   ilustrativa debe reportar `experimental` siempre.

El valor esperado del hash no se deriva del codigo bajo prueba: se calculo con
`sha256sum` sobre el CSV empaquetado y coincide con el declarado en
`metadata.json`.
"""

import hashlib
import json
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from importlib import resources
from pathlib import Path

import pytest

from suite_actuarial.actuarial.mortality import tablas as modulo_tablas
from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    Sexo,
)
from suite_actuarial.vida.temporal import VidaTemporal

# sha256 del CSV empaquetado `emssa_09.csv`, obtenido con `sha256sum`.
HASH_EMSSA09 = "31786604a174ddc1a07352bbb331643c633da2f804949d9e639f0b6924df1b58"


@contextmanager
def directorio_empaquetado() -> Iterator[Path]:
    """Entrega la carpeta de datos instalada como ruta del sistema de archivos."""
    with resources.as_file(resources.files(modulo_tablas._PAQUETE_TABLAS)) as directorio:
        yield Path(directorio)


def _sha256_archivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestHashDeclarado:
    """El hash es un compromiso escrito, no un calculo que se contesta solo."""

    def test_csv_empaquetado_tiene_el_hash_fijado(self):
        """El CSV instalado es exactamente el archivo que estas pruebas conocen."""
        with directorio_empaquetado() as directorio:
            assert _sha256_archivo(directorio / "emssa_09.csv") == HASH_EMSSA09

    def test_metadata_declara_el_mismo_hash(self):
        """`metadata.json` declara el hash; no es decorativo."""
        with directorio_empaquetado() as directorio:
            declarado = json.loads((directorio / "metadata.json").read_text(encoding="utf-8"))
        entrada = declarado["tablas"]["emssa_09"]
        assert entrada["content_hash"] == f"sha256:{HASH_EMSSA09}"

    def test_la_carga_conserva_el_hash_declarado(self):
        """La tabla cargada publica el hash declarado, no uno recalculado."""
        tabla = TablaMortalidad.cargar_emssa09()
        assert tabla.metadata["content_hash"] == f"sha256:{HASH_EMSSA09}"


class TestVerificacionAlCargar:
    """Un archivo que no coincide con su declaracion no se carga."""

    def _copiar_insumo(self, destino: Path) -> Path:
        with directorio_empaquetado() as directorio:
            shutil.copy(directorio / "emssa_09.csv", destino / "emssa_09.csv")
            shutil.copy(directorio / "metadata.json", destino / "metadata.json")
        return destino / "emssa_09.csv"

    def _cargar(self, directorio: Path) -> TablaMortalidad:
        return TablaMortalidad._cargar_verificada(
            directorio,
            archivo_csv="emssa_09.csv",
            clave_metadatos="emssa_09",
            nombre="EMSSA-09",
        )

    def test_copia_intacta_carga(self, tmp_path):
        """La copia sin tocar carga: el control detecta cambios, no copias."""
        self._copiar_insumo(tmp_path)
        tabla = self._cargar(tmp_path)
        assert tabla.metadata["content_hash"] == f"sha256:{HASH_EMSSA09}"

    def test_csv_alterado_es_rechazado(self, tmp_path):
        """Alterar un qx invalida el hash y detiene la carga."""
        csv_path = self._copiar_insumo(tmp_path)
        lineas = csv_path.read_text(encoding="utf-8").splitlines()
        # Se altera la primera fila de datos: misma forma, otro contenido.
        campos = lineas[1].split(",")
        campos[-1] = "0.999"
        lineas[1] = ",".join(campos)
        csv_path.write_text("\n".join(lineas) + "\n", encoding="utf-8")

        with pytest.raises(ValueError) as exc_info:
            self._cargar(tmp_path)

        mensaje = str(exc_info.value)
        assert f"sha256:{HASH_EMSSA09}" in mensaje, "el mensaje debe citar el hash declarado"
        assert f"sha256:{_sha256_archivo(csv_path)}" in mensaje, (
            "el mensaje debe citar el hash calculado"
        )

    def test_csv_ausente_es_error_de_instalacion(self, tmp_path):
        """Sin CSV no hay degradacion: se reporta instalacion incompleta."""
        self._copiar_insumo(tmp_path)
        (tmp_path / "emssa_09.csv").unlink()

        with pytest.raises(FileNotFoundError) as exc_info:
            self._cargar(tmp_path)

        assert "instalacion incompleta" in str(exc_info.value)

    def test_metadatos_ausentes_detienen_la_carga(self, tmp_path):
        """Sin metadatos no se carga: la procedencia es parte del insumo."""
        self._copiar_insumo(tmp_path)
        (tmp_path / "metadata.json").unlink()

        with pytest.raises(FileNotFoundError) as exc_info:
            self._cargar(tmp_path)

        assert "metadata.json" in str(exc_info.value)

    def test_metadatos_sin_hash_declarado_son_rechazados(self, tmp_path):
        """Un metadata.json sin content_hash no habilita una carga sin verificar."""
        self._copiar_insumo(tmp_path)
        ruta_metadatos = tmp_path / "metadata.json"
        declarado = json.loads(ruta_metadatos.read_text(encoding="utf-8"))
        del declarado["tablas"]["emssa_09"]["content_hash"]
        ruta_metadatos.write_text(json.dumps(declarado, ensure_ascii=False), encoding="utf-8")

        with pytest.raises(ValueError) as exc_info:
            self._cargar(tmp_path)

        assert "content_hash" in str(exc_info.value)


class TestSinRutaDeRespaldo:
    """Una copia suelta del CSV en el arbol de trabajo no se carga."""

    def test_paquete_de_datos_ausente_no_cae_a_ruta_relativa(self, tmp_path, monkeypatch):
        """Si el paquete de datos falta, se reporta el error; no se degrada."""
        senuelo = tmp_path / "data" / "mortality_tables"
        senuelo.mkdir(parents=True)
        (senuelo / "emssa_09.csv").write_text(
            "edad,sexo,qx\n30,H,0.001\n31,H,0.0012\n30,M,0.0005\n31,M,0.0006\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            modulo_tablas,
            "_PAQUETE_TABLAS",
            "suite_actuarial.data.tablas_que_no_existen",
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            TablaMortalidad.cargar_emssa09()

        assert "paquete de datos" in str(exc_info.value)

    def test_el_repositorio_no_conserva_una_copia_del_csv(self):
        """La copia duplicada en la raiz del repositorio no debe reaparecer."""
        raiz = Path(__file__).resolve().parents[2]
        if not (raiz / "pyproject.toml").is_file():
            pytest.skip("La prueba solo aplica sobre el arbol del repositorio")
        assert not (raiz / "data" / "mortality_tables" / "emssa_09.csv").exists(), (
            "El CSV empaquetado es la unica copia; una segunda copia vuelve a abrir "
            "la puerta a cargar datos sin metadatos"
        )


class TestNivelDeValidacionReportado:
    """Los datos ilustrativos deben reportarse como tales aguas abajo."""

    def test_tabla_declara_data_status_ilustrativo(self):
        tabla = TablaMortalidad.cargar_emssa09()
        assert tabla.metadata["data_status"] == "illustrative"
        assert tabla.strict is True

    def test_producto_de_vida_reporta_experimental(self):
        """VidaTemporal deriva su `validation_tier` del estado de la tabla."""
        tabla = TablaMortalidad.cargar_emssa09()
        config = ConfiguracionProducto(
            nombre_producto="Vida Temporal 20",
            plazo_years=20,
            tasa_interes_tecnico=Decimal("0.055"),
            recargo_gastos_admin=Decimal("0.05"),
            recargo_gastos_adq=Decimal("0.10"),
            recargo_utilidad=Decimal("0.03"),
        )
        asegurado = Asegurado(
            edad=35,
            sexo=Sexo.MASCULINO,
            suma_asegurada=Decimal("1000000"),
        )

        resultado = VidaTemporal(config, tabla).calcular_prima(asegurado)

        assert resultado.calculation_metadata is not None
        assert resultado.calculation_metadata.validation_tier == "experimental"
