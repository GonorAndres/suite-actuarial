"""Ejecuta los ejemplos autoverificables como parte de la suite.

Los scripts de ``examples/casos/`` y ``examples/labs/`` llevan aserciones que
comprueban identidades actuariales: principio de equivalencia, descomposicion
de beneficios, recursion de Fackler, cuadre del triangulo de siniestros,
diversificacion del RCS, cesion y retencion en reaseguro. El ``README.md`` de
los casos le promete al lector que "si una falla, el script truena", pero hasta
ahora ningun gate los ejecutaba: ruff y mypy los leian, nadie los corria. Esta
prueba convierte esa promesa en una comprobacion real.

Cada script se ejecuta con ``runpy.run_path(..., run_name="__main__")``, es
decir en las mismas condiciones que ``python examples/casos/caso_01_...py``, y
su salida estandar se captura para que la suite siga siendo silenciosa. Si un
ejemplo falla aqui, el hallazgo es del ejemplo o del modelo que ejercita; no se
debe relajar esta prueba para volverla verde.
"""

from __future__ import annotations

import ast
import io
import runpy
from contextlib import redirect_stdout
from pathlib import Path

import pytest

RAIZ_REPO = Path(__file__).resolve().parents[2]
DIRECTORIOS_DE_EJEMPLOS = (
    RAIZ_REPO / "examples" / "casos",
    RAIZ_REPO / "examples" / "labs",
)

# Numero de scripts existentes cuando esta prueba se escribio (7 casos + 1 lab).
# Es un piso, no una cifra exacta: un ejemplo nuevo entra solo por el glob, pero
# si alguno desaparece del descubrimiento la parametrizacion no se queda vacia
# en silencio.
MINIMO_DE_EJEMPLOS_ESPERADOS = 8


def _descubrir_ejemplos() -> list[Path]:
    """Lista los scripts ejecutables de ejemplo, en orden estable."""
    encontrados: list[Path] = []
    for directorio in DIRECTORIOS_DE_EJEMPLOS:
        encontrados.extend(
            sorted(ruta for ruta in directorio.glob("*.py") if not ruta.name.startswith("_"))
        )
    return encontrados


EJEMPLOS = _descubrir_ejemplos()
IDS = [str(ruta.relative_to(RAIZ_REPO)) for ruta in EJEMPLOS]


def test_se_descubren_los_ejemplos_de_ambos_directorios():
    """Sin esto, un glob roto dejaria la parametrizacion vacia y la suite verde."""
    assert len(EJEMPLOS) >= MINIMO_DE_EJEMPLOS_ESPERADOS, (
        f"Se esperaban al menos {MINIMO_DE_EJEMPLOS_ESPERADOS} ejemplos; "
        f"se descubrieron {len(EJEMPLOS)}: {IDS}"
    )
    for directorio in DIRECTORIOS_DE_EJEMPLOS:
        assert any(ruta.parent == directorio for ruta in EJEMPLOS), (
            f"Ningun ejemplo descubierto en {directorio}"
        )


@pytest.mark.parametrize("script", EJEMPLOS, ids=IDS)
def test_el_ejemplo_conserva_aserciones(script: Path):
    """Un ejemplo sin aserciones se ejecutaria siempre verde sin verificar nada.

    La promesa del README es que el script truena cuando una identidad falla.
    Ejecutarlo solo vale como gate si sigue habiendo algo que pueda tronar.
    """
    arbol = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    aserciones = sum(1 for nodo in ast.walk(arbol) if isinstance(nodo, ast.Assert))
    assert aserciones >= 1, f"{script.name} no contiene ninguna sentencia assert"


@pytest.mark.parametrize("script", EJEMPLOS, ids=IDS)
def test_el_ejemplo_corre_y_sus_identidades_se_cumplen(script: Path):
    """Ejecuta el script completo; cualquier assert interno falla esta prueba."""
    salida = io.StringIO()
    with redirect_stdout(salida):
        runpy.run_path(str(script), run_name="__main__")

    # Los ejemplos son narrativos: imprimen supuestos, resultados y margenes de
    # las verificaciones. Una salida vacia significa que el cuerpo del script
    # dejo de ejecutarse (por ejemplo, si todo quedara bajo un guard sin llamar).
    assert salida.getvalue().strip(), f"{script.name} no imprimio nada al ejecutarse"
