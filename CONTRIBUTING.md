# Guía de Contribución

¡Gracias por tu interés en contribuir al proyecto Mexican Insurance Analytics Suite! 🎉

## Cómo Contribuir

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub, luego:
git clone https://github.com/TU_USUARIO/Analisis_Seguros_Mexico.git
cd Analisis_Seguros_Mexico
```

### 2. Configurar Entorno de Desarrollo

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Instalar pre-commit hooks
pre-commit install
```

### 3. Crear una Rama

```bash
git checkout -b feature/mi-nueva-funcionalidad
# o
git checkout -b fix/corregir-bug
```

### 4. Hacer Cambios

- Escribe código limpio y documentado
- Agrega docstrings en español
- Incluye type hints
- Sigue las convenciones de PEP 8

### 5. Escribir Tests

```bash
# Escribir tests en tests/unit/ o tests/integration/
# Ejecutar tests
pytest

# Verificar cobertura
pytest --cov=mexican_insurance
```

### 6. Lint y Format

```bash
# Los pre-commit hooks hacen esto automáticamente, pero puedes ejecutar:
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

### 7. Commit

```bash
git add .
git commit -m "feat: descripción concisa del cambio"
# o
git commit -m "fix: descripción del bug corregido"
```

**Convenciones de commit:**
- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bug
- `docs:` - Cambios en documentación
- `test:` - Agregar o modificar tests
- `refactor:` - Refactorización sin cambiar funcionalidad
- `style:` - Cambios de formato (no afectan código)
- `chore:` - Tareas de mantenimiento

### 8. Push y Pull Request

```bash
git push origin feature/mi-nueva-funcionalidad
```

Luego crea un Pull Request en GitHub.

## Estándares de Código

### Python Style Guide

- **Idioma**: Código en inglés, comentarios/docstrings en español
- **Formato**: Sigue PEP 8 (validado con ruff)
- **Type Hints**: Obligatorios en funciones públicas
- **Docstrings**: Estilo Google

### Ejemplo de Docstring

```python
def calcular_prima(
    edad: int,
    suma_asegurada: Decimal,
) -> Decimal:
    """
    Calcula la prima para un asegurado.

    Esta función aplica las fórmulas actuariales estándar
    para determinar la prima neta de un seguro.

    Args:
        edad: Edad del asegurado en años cumplidos
        suma_asegurada: Monto de cobertura en pesos

    Returns:
        Prima calculada en la moneda del producto

    Raises:
        ValueError: Si la edad está fuera de rango

    Examples:
        >>> calcular_prima(35, Decimal("1000000"))
        Decimal('5432.10')
    """
    pass
```

## Tests

### Cobertura Mínima

- **Core modules**: >90% cobertura
- **Products**: >85% cobertura
- **Utilities**: >80% cobertura

### Tipos de Tests

1. **Unit Tests**: Probar funciones individuales
2. **Integration Tests**: Probar flujos completos
3. **Property Tests**: Usar `hypothesis` para casos edge

### Ejemplo de Test

```python
def test_calcular_prima_aumenta_con_edad(producto, tabla):
    """La prima debe aumentar con la edad"""
    joven = Asegurado(edad=25, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000"))
    mayor = Asegurado(edad=50, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000"))

    prima_joven = producto.calcular_prima(joven).prima_total
    prima_mayor = producto.calcular_prima(mayor).prima_total

    assert prima_mayor > prima_joven, "Prima debe aumentar con edad"
```

## Checklist del Pull Request

Antes de enviar tu PR, verifica que:

- [ ] Los tests pasan (`pytest`)
- [ ] La cobertura no disminuyó
- [ ] El código pasa linting (`ruff check`)
- [ ] Hay type hints (`mypy src/`)
- [ ] Los docstrings están completos
- [ ] Se actualizó el README si es necesario
- [ ] Se agregaron ejemplos si es una nueva feature

## Preguntas

Si tienes dudas, abre un issue con la etiqueta `question`.

¡Gracias por contribuir! 🙏
