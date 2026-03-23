# Guia de Contribucion

Gracias por tu interes en contribuir a **suite_actuarial**.

## Como Contribuir

### 1. Fork y Clone

```bash
git clone https://github.com/GonorAndres/Analisis_Seguros_Mexico.git
cd Analisis_Seguros_Mexico
```

### 2. Configurar Entorno de Desarrollo

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

### 3. Crear una Rama

```bash
git checkout -b feature/mi-nueva-funcionalidad
# o
git checkout -b fix/corregir-bug
```

### 4. Hacer Cambios

- Codigo limpio y documentado
- Docstrings en espanol (con acentos en texto visible al usuario)
- Type hints en funciones publicas
- Variables, funciones y clases en ASCII (sin acentos)
- Sin emojis

### 5. Escribir Tests

```bash
pytest
pytest --cov=suite_actuarial --cov-report=term-missing
```

Los tests actuariales rigurosos van en `tests/unit/test_actuarial_rigor.py`.
Tests por dominio van en archivos separados (`test_vida_*.py`, `test_danos_*.py`, etc.).

### 6. Lint

```bash
ruff check src/ tests/
ruff format src/ tests/
```

### 7. Commit

Convenciones:
- `feat:` Nueva funcionalidad
- `fix:` Correccion de bug
- `docs:` Cambios en documentacion
- `test:` Agregar o modificar tests
- `refactor:` Refactorizacion sin cambiar funcionalidad
- `chore:` Tareas de mantenimiento
- `ci:` Cambios en CI/CD

### 8. Push y Pull Request

```bash
git push origin feature/mi-nueva-funcionalidad
```

Crea un Pull Request en GitHub.

## Estandares de Codigo

- **Idioma**: Nombres en ingles/ASCII, docstrings y UI en espanol con acentos
- **Formato**: PEP 8 (validado con ruff, line-length 100)
- **Type Hints**: Obligatorios en funciones publicas
- **Docstrings**: Estilo Google
- **Precision**: Usar `Decimal` para valores monetarios, `float`/`numpy` solo internamente

### Ejemplo de Docstring

```python
def calcular_prima(
    edad: int,
    suma_asegurada: Decimal,
) -> Decimal:
    """
    Calcula la prima para un asegurado.

    Args:
        edad: Edad del asegurado en anos cumplidos
        suma_asegurada: Monto de cobertura en pesos

    Returns:
        Prima calculada en la moneda del producto

    Raises:
        ValueError: Si la edad esta fuera de rango
    """
```

## Tests

### Cobertura Minima

- **Core / Vida / Pensiones**: >85% cobertura
- **Danos / Salud**: >70% cobertura
- **Regulatorio**: >75% cobertura

### Tipos de Tests

1. **Unit Tests** (`tests/unit/`): Funciones individuales
2. **Rigor Tests** (`test_actuarial_rigor.py`): Identidades actuariales, restricciones regulatorias
3. **Integration Tests** (`tests/integration/`): Flujos completos (pendiente)

## Checklist del Pull Request

- [ ] Los tests pasan (`pytest`)
- [ ] La cobertura no disminuyo
- [ ] El codigo pasa linting (`ruff check src/ tests/`)
- [ ] Hay type hints en funciones publicas
- [ ] Los docstrings estan completos
- [ ] Se actualizo el README si aplica

## Preguntas

Abre un issue con la etiqueta `question`.
