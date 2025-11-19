# Issues de Tests Fallando - Mexican Insurance Analytics Suite

**Fecha de detección**: 2025-11-19
**Branch**: main (commit b9f64bf)
**Total de tests**: 307
**Tests fallando**: 12 (3.9%)
**Tests pasando**: 294 (95.8%)
**Cobertura general**: 85%

---

## Resumen Ejecutivo

Se identificaron 12 tests fallando que se agrupan en 4 categorías principales:
1. **Pydantic V2** - Cambio en formato de mensajes de error (4 tests)
2. **Validación de Mensajes** - Tests que buscan texto específico en errores (4 tests)
3. **Bootstrap/Randomización** - Problemas con seeds y reproducibilidad (3 tests)
4. **Validación de Edad Omega** - Error cuando edad > edad máxima de tabla (1 test)

**Prioridad**: Media-Alta
**Impacto**: Los tests fallan pero el código funciona correctamente
**Esfuerzo estimado**: 2-3 horas para corregir todos

---

## Issue #1: Tests de Pydantic V2 - Formato de Mensajes de Error

**Prioridad**: Alta
**Labels**: `bug`, `tests`, `pydantic`, `breaking-change`
**Assignee**: TBD
**Milestone**: v0.3.0

### Descripción

Los tests de validación fallan porque esperan mensajes de error personalizados de Pydantic V1, pero el proyecto usa Pydantic V2 que tiene un formato diferente.

### Tests Afectados

```
tests/unit/test_validators.py::TestAsegurado::test_suma_asegurada_cero_falla
tests/unit/test_validators.py::TestConfiguracionProducto::test_tasa_interes_negativa_falla
tests/unit/test_validators.py::TestRegistroMortalidad::test_qx_fuera_de_rango_falla
tests/unit/test_validators.py::TestRegistroMortalidad::test_qx_negativo_falla
```

### Ejemplo de Error

**Test esperado (Pydantic V1)**:
```python
assert "suma asegurada" in str(exc_info.value).lower()
```

**Error actual (Pydantic V2)**:
```
AssertionError: assert 'suma asegurada' in "1 validation error for Asegurado\nsuma_asegurada\n  Input should be greater than 0 [type=greater_than, input_value=Decimal('0'), input_type=Decimal]"
```

### Causa Raíz

Pydantic V2 cambió completamente el formato de mensajes de validación:
- **V1**: Mensajes personalizados en español: "La suma asegurada debe ser mayor a cero"
- **V2**: Mensajes estándar en inglés: "Input should be greater than 0"

### Solución Propuesta

**Opción A**: Actualizar los tests para buscar campos específicos en lugar de texto
```python
# Antes
assert "suma asegurada" in str(exc_info.value).lower()

# Después
assert "suma_asegurada" in str(exc_info.value)
assert "greater than" in str(exc_info.value).lower()
```

**Opción B**: Usar custom validators de Pydantic V2 para mantener mensajes en español
```python
from pydantic import field_validator

class Asegurado(BaseModel):
    suma_asegurada: Decimal

    @field_validator('suma_asegurada')
    @classmethod
    def validar_suma_asegurada(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("La suma asegurada debe ser mayor a cero")
        return v
```

**Recomendación**: Opción A (más simple, mantiene compatibilidad con Pydantic V2)

### Archivos a Modificar

- `tests/unit/test_validators.py` (líneas ~50-100)

### Criterios de Aceptación

- [ ] Los 4 tests pasan correctamente
- [ ] Tests verifican que el campo correcto está en el error
- [ ] Tests verifican que el tipo de error es correcto
- [ ] Documentar el cambio de Pydantic V2 en CHANGELOG.md

### Esfuerzo Estimado

- **Tiempo**: 30-45 minutos
- **Complejidad**: Baja

---

## Issue #2: Tests de Validación de Edad en Productos de Vida

**Prioridad**: Media
**Labels**: `bug`, `tests`, `products`, `validation`
**Assignee**: TBD
**Milestone**: v0.3.0

### Descripción

Los tests de validación de edad en productos de vida (Temporal, Ordinario, Dotal) fallan porque buscan palabras clave específicas que no están presentes en los mensajes de error actuales.

### Tests Afectados

```
tests/unit/test_vida_dotal.py::TestVidaDotal::test_validar_edad_vencimiento_maxima
tests/unit/test_vida_ordinario.py::TestVidaOrdinario::test_validar_edad_maxima_emision
tests/unit/test_vida_ordinario.py::TestVidaOrdinario::test_validar_edad_cercana_omega
tests/unit/test_vida_ordinario.py::TestVidaOrdinario::test_error_edad_mayor_omega
tests/unit/test_vida_temporal.py::TestVidaTemporal::test_validar_asegurabilidad_edad_muy_alta
```

### Ejemplo de Error

**Test**: `test_validar_asegurabilidad_edad_muy_alta`

```python
# Test busca:
assert "vencimiento" in str(exc_info.value).lower()

# Mensaje actual del código:
"Edad máxima de aceptación excedida (70 años)"
```

**Error**:
```
AssertionError: assert 'vencimiento' in 'edad máxima de aceptación excedida (70 años)'
```

### Causa Raíz

Los tests fueron escritos esperando mensajes específicos que no coinciden con la implementación actual:
- Tests esperan: "vencimiento", "omega", "edad de emisión"
- Código devuelve: "edad máxima de aceptación excedida"

### Solución Propuesta

**Opción A**: Actualizar los mensajes de error en el código para que sean más descriptivos
```python
# En VidaTemporal.validar_asegurabilidad()
raise ValueError(
    f"Edad de vencimiento ({asegurado.edad + self.config.plazo_years}) "
    f"excede la edad máxima permitida ({EDAD_MAX_VENCIMIENTO})"
)
```

**Opción B**: Actualizar los tests para buscar las palabras correctas
```python
# Antes
assert "vencimiento" in str(exc_info.value).lower()

# Después
assert "edad máxima" in str(exc_info.value).lower()
```

**Recomendación**: Opción A (mejora los mensajes de error para usuarios)

### Archivos a Modificar

- `src/mexican_insurance/products/vida/temporal.py`
- `src/mexican_insurance/products/vida/ordinario.py`
- `src/mexican_insurance/products/vida/dotal.py`
- `tests/unit/test_vida_temporal.py`
- `tests/unit/test_vida_ordinario.py`
- `tests/unit/test_vida_dotal.py`

### Criterios de Aceptación

- [ ] Los 5 tests pasan correctamente
- [ ] Mensajes de error son claros y descriptivos
- [ ] Mensajes incluyen los valores específicos (edad actual, límite, etc.)
- [ ] Consistencia entre los 3 productos de vida

### Esfuerzo Estimado

- **Tiempo**: 1 hora
- **Complejidad**: Baja-Media

---

## Issue #3: Tests de Bootstrap - Problemas de Reproducibilidad

**Prioridad**: Media-Baja
**Labels**: `bug`, `tests`, `reservas`, `random`, `flaky-test`
**Assignee**: TBD
**Milestone**: v0.3.1

### Descripción

Los tests de Bootstrap fallan debido a problemas con la generación de números aleatorios y reproducibilidad de seeds.

### Tests Afectados

```
tests/unit/test_bootstrap.py::TestBootstrapTrianguloSintetico::test_generar_triangulo_sintetico
tests/unit/test_bootstrap.py::TestBootstrapReproducibilidad::test_diferente_seed_diferentes_resultados
tests/unit/test_bootstrap.py::TestBootstrapVaRTVaR::test_calcular_var
```

### Problema 1: test_generar_triangulo_sintetico

**Síntoma**: El test falla de manera intermitente (flaky test)

**Posible causa**:
- Seed no se está aplicando correctamente antes de generar números aleatorios
- Uso de múltiples generadores de números aleatorios (numpy vs random)

### Problema 2: test_diferente_seed_diferentes_resultados

**Síntoma**: El test espera que diferentes seeds produzcan resultados diferentes, pero a veces son iguales

**Posible causa**:
- Número de simulaciones muy bajo
- Seeds muy cercanos produciendo resultados similares

### Problema 3: test_calcular_var

**Síntoma**: Falla el cálculo de Value at Risk (VaR)

**Posible causa**:
- Error en la fórmula de cálculo de VaR
- Problema con el percentil esperado

### Solución Propuesta

1. **Verificar uso consistente de seeds**:
```python
import numpy as np

class Bootstrap:
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)  # Asegurar que seed se aplica
```

2. **Aumentar diferencia entre seeds en tests**:
```python
# Antes
seed1 = 42
seed2 = 43

# Después
seed1 = 42
seed2 = 12345  # Seed muy diferente
```

3. **Revisar cálculo de VaR**:
```python
def calcular_var(self, nivel_confianza: float) -> Decimal:
    percentil = int(nivel_confianza * 100)
    return self.percentiles[percentil]
```

### Archivos a Modificar

- `src/mexican_insurance/reservas/bootstrap.py`
- `tests/unit/test_bootstrap.py`

### Criterios de Aceptación

- [ ] Los 3 tests pasan consistentemente (ejecutar 10 veces)
- [ ] Documentar el uso correcto de seeds en docstrings
- [ ] Agregar advertencias sobre reproducibilidad en documentación

### Esfuerzo Estimado

- **Tiempo**: 1-1.5 horas
- **Complejidad**: Media

---

## Issue #4: Documentar Compatibilidad de Pydantic V2

**Prioridad**: Alta
**Labels**: `documentation`, `breaking-change`, `pydantic`
**Assignee**: TBD
**Milestone**: v0.3.0

### Descripción

El proyecto usa Pydantic V2 pero esto no está documentado claramente. Los usuarios que migran de V1 pueden encontrar cambios inesperados.

### Acciones Requeridas

1. **Actualizar README.md**:
```markdown
## Requisitos

- Python 3.11+
- Pydantic V2.x (⚠️ No compatible con Pydantic V1)
```

2. **Crear guía de migración**: `docs/PYDANTIC_V2_MIGRATION.md`

3. **Actualizar CHANGELOG.md**:
```markdown
## [0.3.0] - 2025-XX-XX

### Breaking Changes
- Migrado a Pydantic V2
  - Mensajes de error ahora están en inglés
  - Sintaxis de validadores cambió
  - Ver guía de migración en docs/
```

4. **Actualizar pyproject.toml**:
```toml
dependencies = [
    "pydantic>=2.5.0,<3.0.0",  # Especificar V2 explícitamente
]
```

### Criterios de Aceptación

- [ ] README actualizado con requisito de Pydantic V2
- [ ] Guía de migración creada
- [ ] CHANGELOG documentando breaking change
- [ ] pyproject.toml con versión específica

### Esfuerzo Estimado

- **Tiempo**: 30 minutos
- **Complejidad**: Baja

---

## Plan de Corrección Recomendado

### Fase 1: Correcciones Críticas (Sprint 1)
1. Issue #1: Tests Pydantic V2 ✅ Alta prioridad
2. Issue #4: Documentar Pydantic V2 ✅ Alta prioridad

**Tiempo total**: 1-1.5 horas

### Fase 2: Mejoras de Calidad (Sprint 2)
3. Issue #2: Validación de edad ✅ Mejora UX
4. Issue #3: Bootstrap reproducibilidad ✅ Eliminar flaky tests

**Tiempo total**: 2-2.5 horas

---

## Cómo Ejecutar los Tests Fallando

```bash
# Todos los tests fallando
PYTHONPATH=/home/user/Analisis_Seguros_Mexico/src \
python -m pytest tests/ -v --tb=short | grep FAILED

# Solo tests de Pydantic
PYTHONPATH=/home/user/Analisis_Seguros_Mexico/src \
python -m pytest tests/unit/test_validators.py -v

# Solo tests de Bootstrap
PYTHONPATH=/home/user/Analisis_Seguros_Mexico/src \
python -m pytest tests/unit/test_bootstrap.py -k "reproducibilidad or sintetico or var" -v

# Solo tests de productos de vida
PYTHONPATH=/home/user/Analisis_Seguros_Mexico/src \
python -m pytest tests/unit/test_vida_*.py -k "edad" -v
```

---

## Métricas de Tests

### Antes de Correcciones
- Total: 307 tests
- Pasando: 294 (95.8%)
- Fallando: 12 (3.9%)
- Skipped: 1

### Después de Correcciones (Meta)
- Total: 307 tests
- Pasando: 307 (100%) ✅
- Fallando: 0
- Skipped: 1

### Cobertura
- Actual: 85%
- Meta: >90%

---

## Referencias

- [Pydantic V2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Flaky Tests - Martin Fowler](https://martinfowler.com/articles/nonDeterminism.html)

---

**Última actualización**: 2025-11-19
**Actualizado por**: Claude
**Estado**: Documentado, pendiente de corrección
