# suite_actuarial

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-18222D.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-B4472D.svg)](LICENSE)
[![Status: Beta](https://img.shields.io/badge/status-beta-B77A1E.svg)]()

**Construye, prueba y comprende modelos actuariales, en abierto.**  
*Build, test, and understand actuarial models in the open.*

`suite_actuarial` es una plataforma de código abierto para la modelación actuarial,
desarrollada desde el contexto asegurador mexicano. Reúne métodos, ejemplos y herramientas
para transformar una pregunta de producto en beneficios, supuestos, cálculos, resultados y
pruebas reproducibles.

La aplicación organiza cada modelo con un método común: propósito, beneficios, supuestos,
método, resultados y validación. El paquete Python permite reproducir, extender e integrar
los mismos modelos en proyectos universitarios, investigación aplicada e innovación.

## Ejemplo guiado: dotal educativo 20/10

El [dotal educativo 20/10](docs/labs/dotal-educativo.md) documenta un seguro con 20 años
de cobertura y primas durante 10 años. El recorrido incluye:

1. la necesidad y la promesa contractual;
2. los beneficios por fallecimiento y supervivencia;
3. mortalidad, interés, plazo y suma asegurada;
4. el principio de equivalencia y la descomposición del valor presente;
5. la prima y el perfil anual de la reserva; y
6. las identidades que permiten revisar el resultado.

Ejecuta su versión reproducible sin interfaz:

```bash
python examples/labs/lab_01_dotal_educativo.py
```

El [guion del video](docs/video/dotal-educativo-script.md) sigue exactamente el mismo
recorrido para que demostración, documentación y código cuenten una sola historia.

## Explora por pregunta actuarial

| Pregunta | Dominio | Modelos disponibles |
|---|---|---|
| ¿Cómo financiar un beneficio? | Vida | Temporal, ordinario, dotal, reservas matemáticas |
| ¿Cómo emerge una pérdida agregada? | Daños | Frecuencia-severidad, auto, incendio, RC, credibilidad |
| ¿Cómo se comparte un gasto médico? | Salud | GMM, deducible, coaseguro, accidentes |
| ¿Cómo convertir ahorro en ingreso vitalicio? | Pensiones | Ley 73/97, rentas vitalicias, conmutación |
| ¿Qué costo falta por desarrollarse? | Reservas | Chain Ladder, Bornhuetter-Ferguson, Bootstrap, Mack |
| ¿Cómo transferir cola y capital? | Reaseguro | Cuota parte, exceso de pérdida, stop loss |
| ¿Cómo examinar solvencia y reglas? | Referencia regulatoria | RCS, reservas técnicas, SAT, configuración anual |

Los [casos por dominio](examples/casos/) son scripts autocontenidos con supuestos y
afirmaciones actuariales. La [visión del proyecto](docs/PROJECT_VISION.md) explica el
alcance de la plataforma y cómo puede crecer la comunidad alrededor de ella.

## Usar la plataforma

### Aplicación web

```bash
docker compose up
```

- Plataforma web: <http://localhost:3000>
- Interfaz técnica: <http://localhost:8000/docs>

Para desarrollo sin Docker:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,api]"
uvicorn suite_actuarial.api.main:app --reload
```

En otra terminal:

```bash
cd frontend
npm ci
npm run dev
```

La aplicación Streamlit, útil como banco de trabajo directo sobre Python, se inicia con:

```bash
pip install -e ".[viz]"
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/Home.py
```

### Paquete Python

```bash
pip install git+https://github.com/GonorAndres/suite-actuarial.git
```

```python
from decimal import Decimal

from suite_actuarial import Asegurado, ConfiguracionProducto, TablaMortalidad, VidaDotal
from suite_actuarial.core.validators import Sexo

config = ConfiguracionProducto(
    nombre_producto="Dotal educativo 20/10",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),
)
producto = VidaDotal(config, TablaMortalidad.cargar_emssa09(), plazo_pago=10)
asegurado = Asegurado(
    edad=35,
    sexo=Sexo.HOMBRE,
    suma_asegurada=Decimal("1000000"),
)
analisis = producto.analizar_producto(asegurado)

print(analisis.prima_neta_anual_equivalente)
print(analisis.verificaciones)
```

## Cómo está construido

```text
src/suite_actuarial/
├── core/          modelos compartidos, validación y abstracciones
├── actuarial/     mortalidad, interés, valuación y funciones de vida
├── vida/          temporal, ordinario y dotal
├── danos/         tarificación y modelos de pérdidas
├── salud/         gastos médicos y accidentes
├── pensiones/     conmutación, IMSS y rentas vitalicias
├── reservas/      métodos determinísticos y estocásticos
├── reaseguro/     estructuras proporcionales y no proporcionales
├── regulatorio/   modelos de referencia y reservas técnicas
├── config/        parámetros mexicanos versionados
└── api/           adaptación técnica para las interfaces

frontend/          plataforma bilingüe principal (Next.js)
streamlit_app/     banco de trabajo secundario sobre el paquete
examples/labs/     recorridos completos y reproducibles
examples/casos/    casos autocontenidos por dominio
tests/             comportamiento, contratos e identidades actuariales
docs/              evidencia, límites, visión y materiales del video
```

La lógica actuarial vive en el paquete Python. Las interfaces traducen entradas y
presentan resultados; no duplican fórmulas. Los importes y tasas usan `Decimal` en los
límites relevantes, y las pruebas cubren identidades además de resultados puntuales.

## Evidencia y límites

La tabla EMSSA-09 incluida y ciertos parámetros son datos de referencia o ilustrativos.
Cada uso profesional debe revisar vigencia, unidad, fuente, segmentación, experiencia
propia, calibración y gobierno del modelo. Consulta:

- [Validación, evidencia y limitaciones](docs/VALIDATION.md)
- [Referencia regulatoria](docs/REGULATORY.md)
- [Configuración y datos de mortalidad](data/mortality_tables/README.md)

Este proyecto no sustituye notas técnicas registradas, sistemas de la CNSF, asesoría
fiscal, determinaciones del IMSS ni el juicio de un actuario responsable.

## Contribuir

Una contribución puede ser un producto, una hipótesis, un caso reproducible, una prueba
de identidad, una mejora de evidencia o una traducción. Consulta
[CONTRIBUTING.md](CONTRIBUTING.md) para el formato de modelo y las verificaciones.

```bash
pytest
ruff check src/ tests/
cd frontend && npm run lint && npm run build
```

Licencia [MIT](LICENSE).
