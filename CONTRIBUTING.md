# Contribuir a suite_actuarial

El proyecto acepta contribuciones actuariales y técnicas. Una buena aportación no empieza
por una pantalla o una ruta: empieza por una pregunta que otra persona pueda comprender,
reproducir y cuestionar.

## Formato de una contribución de modelo

Describe, en este orden:

1. **Propósito:** necesidad o decisión actuarial que se quiere estudiar.
2. **Beneficios o flujos:** qué se paga, cuándo y bajo qué evento.
3. **Supuestos:** población, datos, tasas, unidades, vigencia y fuente.
4. **Método:** fórmula, algoritmo y aproximaciones.
5. **Resultados:** medidas que ayudan a interpretar el modelo.
6. **Validación:** identidades, casos límite, comparación y limitaciones.

Un resultado sin fuente o sin límite explícito debe marcarse como ilustrativo. No se deben
presentar parámetros regulatorios o de mercado como vigentes sin evidencia verificable.

## Preparar el entorno

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,api]"
cd frontend && npm ci
```

## Organización del cambio

- La lógica actuarial pertenece en `src/suite_actuarial/<dominio>/`.
- La validación compartida pertenece en `core/`.
- Las interfaces deben llamar al paquete; no deben duplicar fórmulas.
- Un laboratorio reproducible pertenece en `examples/labs/` y su explicación en
  `docs/labs/`.
- Use `Decimal`, construido desde texto, para tasas, moneda, primas y reservas.
- Mantenga identificadores ASCII y texto visible en español correcto; la web debe conservar
  español e inglés.

Las fórmulas, tablas, unidades, redondeos y umbrales controlados requieren una prueba y una
fuente o justificación documentada.

## Pruebas

Use la prueba más estrecha que demuestre el cambio:

- `tests/unit/`: fórmulas, comportamiento, identidades y casos límite;
- `tests/integration/`: contratos entre backend e interfaz;
- `examples/labs/`: recorrido humano reproducible con afirmaciones explícitas.

```bash
pytest
ruff check src/ tests/
ruff format --check src/ tests/
cd frontend && npm run lint && npm run build
```

No cambie una expectativa sólo para hacer pasar una prueba. Revise primero fórmula, unidad,
redondeo y datos fuente.

## Lista de revisión

- [ ] La pregunta y el usuario del modelo están claros.
- [ ] Beneficios, supuestos y unidades son visibles.
- [ ] Los cálculos viven en el paquete, no en la UI.
- [ ] Las identidades y casos límite tienen pruebas.
- [ ] Fuentes, vigencia y nivel de validación están documentados.
- [ ] Las limitaciones no se esconden en notas técnicas.
- [ ] La documentación y el ejemplo se actualizaron.
- [ ] Python y frontend pasan sus verificaciones relevantes.

Las conversaciones de comunidad, propuestas de nuevos laboratorios y preguntas pueden
abrirse como issues. El código se distribuye bajo licencia MIT.
