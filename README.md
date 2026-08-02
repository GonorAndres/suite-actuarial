# suite_actuarial

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-18222D.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-B4472D.svg)](LICENSE)
[![Status: Beta](https://img.shields.io/badge/status-beta-B77A1E.svg)]()

**Construye, prueba y entiende modelos actuariales con el código a la vista.**  
*Build, test, and understand actuarial models with the code in view.*

`suite_actuarial` es una plataforma de código abierto para modelación actuarial, hecha
desde el mercado asegurador mexicano. Reúne los métodos y los ejemplos que hacen falta
para pasar de una pregunta de producto a un modelo que otra persona pueda reproducir.

Cada modelo sigue el mismo recorrido: propósito, beneficios, supuestos, método, resultados
y validación. El paquete de Python sirve para reproducirlos, extenderlos o integrarlos en
una tesis, un curso o un proyecto de trabajo.

## Ejemplo guiado: dotal educativo 20/10

El [dotal educativo 20/10](docs/labs/dotal-educativo.md) documenta un seguro con 20 años
de cobertura y 10 de pago de primas. El recorrido incluye:

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

El [guion del video](docs/video/dotal-educativo-script.md) sigue el mismo recorrido, de
modo que la demostración, la documentación y el código cuentan lo mismo.

## Explora por pregunta actuarial

| Pregunta | Dominio | Modelos disponibles |
|---|---|---|
| ¿Cómo se financia un beneficio? | Vida | Temporal, ordinario, dotal, reservas matemáticas |
| ¿Cómo se forma una pérdida agregada? | Daños | Frecuencia-severidad, auto, incendio, RC, credibilidad |
| ¿Cómo se reparte un gasto médico? | Salud | GMM, deducible, coaseguro, accidentes |
| ¿Cómo se convierte el ahorro en ingreso vitalicio? | Pensiones | Ley 73/97, rentas vitalicias, conmutación |
| ¿Cuánto falta por pagar de los siniestros ya ocurridos? | Reservas | Chain Ladder, Bornhuetter-Ferguson, bandas ilustrativas de dispersión |
| ¿Cómo se transfiere el riesgo de cola? | Reaseguro | Cuota parte, exceso de pérdida, stop loss |
| ¿Cómo se examina la solvencia? | Referencia regulatoria | RCS, reservas técnicas, SAT, configuración anual |

Los [casos por dominio](examples/casos/) son scripts autocontenidos, con sus supuestos y
sus afirmaciones actuariales dentro. La [visión del proyecto](docs/PROJECT_VISION.md)
explica hasta dónde llega la plataforma y cómo puede crecer la comunidad alrededor.

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

La aplicación de Streamlit, un banco de trabajo directo sobre Python, se inicia así:

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
    sexo=Sexo.MASCULINO,
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

La lógica actuarial vive en el paquete de Python. Las interfaces traducen entradas y
presentan resultados, sin duplicar fórmulas. Los importes y las tasas usan `Decimal` donde
importa, y las pruebas cubren identidades, no sólo resultados puntuales.

## Evidencia y límites

La tabla EMSSA-09 incluida y varios parámetros son datos de referencia o ilustrativos.
Antes de un uso profesional hay que revisar su vigencia, su unidad y su fuente, además de
la segmentación, la experiencia propia, la calibración y el gobierno del modelo. Consulta:

- [Validación, evidencia y limitaciones](docs/VALIDATION.md)
- [Referencia regulatoria](docs/REGULATORY.md)
- [Configuración y datos de mortalidad](src/suite_actuarial/data/mortality_tables/README.md)

Este proyecto no sustituye notas técnicas registradas, sistemas de la CNSF, asesoría
fiscal, determinaciones del IMSS ni el juicio de un actuario responsable.

## Contribuir

Una contribución puede ser un producto nuevo, una hipótesis, un caso reproducible, una
prueba de identidad, mejor evidencia para un supuesto o una traducción. En
[CONTRIBUTING.md](CONTRIBUTING.md) están el formato de modelo y las verificaciones.

```bash
pytest
ruff check src/ tests/
cd frontend && npm run lint && npm run build
```

Licencia [MIT](LICENSE).
