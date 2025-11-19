# Mejores Prácticas para Gestión de Issues en GitHub

Una guía completa para crear, organizar y gestionar issues de manera profesional.

---

## 1. Anatomía de un Issue Perfecto

### Componentes Esenciales

```markdown
## [Título Descriptivo] - [Tipo]: [Descripción Breve]

**Prioridad**: [Alta/Media/Baja]
**Labels**: `bug`, `feature`, `documentation`, etc.
**Assignee**: @username o TBD
**Milestone**: v1.0.0
**Proyecto**: Sprint 2025-Q1

---

### Descripción

[Explicación clara y concisa del problema o feature request]

### Contexto

[Información relevante sobre cuándo/cómo se descubrió]

### Pasos para Reproducir (si es bug)

1. Paso 1
2. Paso 2
3. Paso 3

### Comportamiento Esperado

[Qué debería suceder]

### Comportamiento Actual

[Qué está sucediendo]

### Solución Propuesta (opcional)

[Ideas sobre cómo resolver]

### Criterios de Aceptación

- [ ] Criterio 1
- [ ] Criterio 2

### Esfuerzo Estimado

- **Tiempo**: X horas
- **Complejidad**: [Alta/Media/Baja]

### Referencias

- #123 (issue relacionado)
- [Documentación relevante](url)
```

---

## 2. Sistema de Prioridades

### Matriz de Priorización (Impacto vs Urgencia)

|                | **Urgente**        | **No Urgente**     |
|----------------|--------------------|--------------------|
| **Alto Impacto**   | 🔴 P0 - Crítico   | 🟠 P1 - Alto       |
| **Bajo Impacto**   | 🟡 P2 - Medio     | 🟢 P3 - Bajo       |

### Definiciones

**P0 - Crítico** (🔴)
- Producción caída
- Seguridad comprometida
- Pérdida de datos
- **SLA**: 24 horas

**P1 - Alto** (🟠)
- Funcionalidad principal rota
- Bloquea otros desarrollos
- Afecta a muchos usuarios
- **SLA**: 3-5 días

**P2 - Medio** (🟡)
- Bug menor
- Feature importante
- Mejora de UX
- **SLA**: 1-2 semanas

**P3 - Bajo** (🟢)
- Nice to have
- Optimizaciones
- Deuda técnica menor
- **SLA**: Backlog

---

## 3. Sistema de Labels

### Labels por Tipo

```
tipo:bug          - Error en el código
tipo:feature      - Nueva funcionalidad
tipo:enhancement  - Mejora de funcionalidad existente
tipo:documentation - Documentación
tipo:refactor     - Refactorización sin cambio funcional
tipo:test         - Tests
tipo:performance  - Optimización de rendimiento
tipo:security     - Seguridad
```

### Labels por Área

```
area:core         - Módulo core
area:api          - API REST
area:frontend     - UI/UX
area:backend      - Backend
area:database     - Base de datos
area:devops       - CI/CD, deployment
area:tests        - Testing
```

### Labels por Estado

```
status:triage         - Necesita revisión
status:confirmed      - Confirmado
status:in-progress    - En desarrollo
status:blocked        - Bloqueado por otro issue
status:needs-review   - Esperando code review
status:needs-testing  - Esperando QA
```

### Labels Especiales

```
good-first-issue    - Fácil para nuevos contribuyentes
help-wanted         - Se busca ayuda
breaking-change     - Cambio que rompe compatibilidad
duplicate           - Duplicado de otro issue
wontfix             - No se arreglará
invalid             - No es válido
question            - Pregunta, no issue
```

---

## 4. Templates de Issues

### Template: Bug Report

```markdown
---
name: Bug Report
about: Reportar un error o comportamiento inesperado
title: '[BUG] '
labels: tipo:bug, status:triage
assignees: ''
---

## Descripción del Bug
[Descripción clara y concisa]

## Pasos para Reproducir
1. Ir a '...'
2. Hacer click en '...'
3. Scroll hasta '...'
4. Ver error

## Comportamiento Esperado
[Qué debería suceder]

## Comportamiento Actual
[Qué está sucediendo + screenshots si aplica]

## Entorno
- OS: [e.g. macOS 14.0]
- Python: [e.g. 3.11.5]
- Versión: [e.g. v0.2.0]
- Browser (si aplica): [e.g. Chrome 120]

## Logs o Mensajes de Error
```
[Pegar logs aquí]
```

## Posible Solución (opcional)
[Si tienes idea de cómo arreglarlo]

## Contexto Adicional
[Cualquier otra información relevante]
```

### Template: Feature Request

```markdown
---
name: Feature Request
about: Sugerir una nueva funcionalidad
title: '[FEATURE] '
labels: tipo:feature, status:triage
assignees: ''
---

## Problema que Resuelve
[Describe el problema actual]

## Solución Propuesta
[Describe la solución que imaginas]

## Alternativas Consideradas
[Otras soluciones que consideraste]

## Casos de Uso
1. Como [tipo de usuario], quiero [funcionalidad] para [beneficio]
2. ...

## Impacto
- **Usuarios afectados**: [número/porcentaje]
- **Frecuencia de uso**: [diario/semanal/mensual]
- **Prioridad de negocio**: [alta/media/baja]

## Mockups o Ejemplos (opcional)
[Screenshots, wireframes, código de ejemplo]

## Criterios de Aceptación
- [ ] Criterio 1
- [ ] Criterio 2
- [ ] Tests escritos
- [ ] Documentación actualizada

## Esfuerzo Estimado
- **Complejidad**: [Alta/Media/Baja]
- **Tiempo estimado**: [X horas/días]

## Dependencias
- Requiere #123
- Bloquea #456
```

### Template: Documentation

```markdown
---
name: Documentation
about: Mejora o corrección de documentación
title: '[DOCS] '
labels: tipo:documentation
assignees: ''
---

## Sección Afectada
[Qué parte de la documentación]

## Problema Actual
[Qué está mal o falta]

## Mejora Propuesta
[Qué debería decir]

## Referencias
- [Link a código relevante]
- [Link a issue relacionado]
```

---

## 5. Workflow de Issues

### Ciclo de Vida

```
1. New → 2. Triage → 3. Backlog → 4. In Progress → 5. Review → 6. Done
```

### Estados Detallados

**1. New** (Recién creado)
- Issue acabado de crear
- No revisado por mantenedores
- Label: `status:triage`

**2. Triage** (En evaluación)
- Mantenedor revisa
- Asigna prioridad y labels
- Puede cerrar si es duplicado/inválido
- Asigna a milestone

**3. Backlog** (Aceptado, no iniciado)
- Issue válido y priorizado
- Esperando capacidad del equipo
- Label: `status:confirmed`

**4. In Progress** (En desarrollo)
- Asignado a desarrollador
- Branch creada
- Label: `status:in-progress`

**5. Review** (En revisión)
- PR creado y linkeado
- Code review en proceso
- Label: `status:needs-review`

**6. Done** (Completado)
- PR mergeado
- Issue cerrado
- Referenciado en release notes

---

## 6. Vinculación con Pull Requests

### Keywords para Auto-Close

Usar en el mensaje del PR:

```
Closes #123
Fixes #456
Resolves #789
```

Cuando el PR se mergea, los issues se cierran automáticamente.

### Formato Recomendado de PR

```markdown
## Descripción
[Qué hace este PR]

## Issues Relacionados
Closes #123
Relates to #456

## Tipo de Cambio
- [ ] Bug fix (cambio que arregla un issue)
- [ ] Nueva feature (cambio que agrega funcionalidad)
- [ ] Breaking change (arreglo o feature que rompe compatibilidad)
- [ ] Documentación

## Checklist
- [ ] Tests pasando
- [ ] Documentación actualizada
- [ ] CHANGELOG.md actualizado
- [ ] Sin conflictos con main
```

---

## 7. Milestones y Projects

### Milestones

Úsalos para agrupar issues por release:

```
v0.3.0 - Bug Fixes & Pydantic V2
├── #10 Fix Pydantic V2 tests
├── #11 Update documentation
└── #12 Bootstrap reproducibility

v0.4.0 - New Features
├── #20 API REST endpoints
└── #21 Authentication system
```

### Projects (GitHub Projects)

Organiza trabajo con boards Kanban:

**Columnas recomendadas**:
1. 📋 Backlog
2. 🔍 In Review (Triage)
3. 📝 To Do (Sprint actual)
4. 🚧 In Progress
5. 👀 Review
6. ✅ Done

---

## 8. Comunicación en Issues

### Mejores Prácticas

✅ **Hacer**:
- Ser específico y claro
- Proveer contexto
- Usar markdown para formatear
- Agregar screenshots/logs
- Referenciar código con líneas específicas
- Ser respetuoso y profesional

❌ **No Hacer**:
- "+1" o "me too" (usar 👍 reaction)
- Desviar conversación del tema
- Duplicar issues sin buscar primero
- Ser agresivo o grosero
- Pedir actualizaciones constantemente

### Ejemplo de Comentario Útil

```markdown
## Update

He investigado este issue y encontré que la causa raíz es en `validators.py:75`.

### Solución Propuesta

```python
# Antes
if value <= 0:
    raise ValueError("Invalid")

# Después
if value <= 0:
    raise ValueError(f"Value must be > 0, got {value}")
```

### Testing

Probé con estos casos:
- ✅ value = 10 → funciona
- ✅ value = 0 → error correcto
- ✅ value = -5 → error correcto

¿Les parece bien este approach? Puedo crear un PR si están de acuerdo.
```

---

## 9. Automatización con GitHub Actions

### Auto-Label por Título

```yaml
name: Auto Label
on:
  issues:
    types: [opened]

jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - if: contains(github.event.issue.title, '[BUG]')
        run: gh issue edit ${{ github.event.issue.number }} --add-label "tipo:bug"
```

### Auto-Assign por Area

```yaml
- if: contains(github.event.issue.labels.*.name, 'area:tests')
  run: gh issue edit ${{ github.event.issue.number }} --add-assignee "qa-team"
```

### Stale Issues

```yaml
name: Close Stale Issues
on:
  schedule:
    - cron: '0 0 * * *'

jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v8
        with:
          stale-issue-message: 'Este issue está inactivo hace 60 días. Se cerrará en 7 días si no hay actividad.'
          days-before-stale: 60
          days-before-close: 7
```

---

## 10. Métricas y KPIs

### Métricas Importantes

**Tiempo de Respuesta**
- Tiempo desde creación hasta primer comentario
- Meta: <24h para P0, <3 días para P1

**Tiempo de Resolución**
- Tiempo desde creación hasta cierre
- Meta: <1 semana para bugs, <2 semanas para features

**Issue Churn**
- Issues reabiertos / Issues cerrados
- Meta: <5%

**Backlog Health**
- Issues en backlog > 90 días
- Meta: <20%

### Dashboard Ejemplo

```
Open Issues: 23
├── P0 (Crítico): 0
├── P1 (Alto): 3
├── P2 (Medio): 12
└── P3 (Bajo): 8

Closed this month: 45
Average time to close: 4.2 days
Reopened: 2 (4.4%)
```

---

## 11. Caso de Estudio: Tu Proyecto

### Issues Actuales Detectados

Basándome en el análisis de tests fallando, así es como se deberían crear los issues:

#### Issue #1: Example

```markdown
Title: [BUG][Tests] Pydantic V2 - Tests de validación fallan por cambio en formato de mensajes

Labels: tipo:bug, area:tests, pydantic, breaking-change, priority:high
Milestone: v0.3.0
Assignee: TBD

---

## Descripción

4 tests de validación en `test_validators.py` fallan porque esperan mensajes de error personalizados de Pydantic V1, pero el proyecto usa Pydantic V2 que tiene formato diferente.

## Tests Afectados

- `test_suma_asegurada_cero_falla`
- `test_tasa_interes_negativa_falla`
- `test_qx_fuera_de_rango_falla`
- `test_qx_negativo_falla`

## Comportamiento Esperado

Tests deberían pasar validando que el campo y tipo de error son correctos.

## Comportamiento Actual

```python
AssertionError: assert 'suma asegurada' in "Input should be greater than 0"
```

## Causa Raíz

Migración a Pydantic V2 cambió formato de mensajes de error.

## Solución Propuesta

Actualizar assertions para buscar campos en lugar de texto específico:
```python
assert "suma_asegurada" in str(exc_info.value)
assert "greater than" in str(exc_info.value).lower()
```

## Criterios de Aceptación

- [ ] 4 tests pasan correctamente
- [ ] Tests verifican campo y tipo de error
- [ ] Documentar cambio en CHANGELOG.md

## Esfuerzo Estimado

- Tiempo: 30-45 min
- Complejidad: Baja

## Referencias

- Ver análisis completo en docs/ISSUES_TEST_FAILURES.md
- Pydantic V2 Migration: https://docs.pydantic.dev/latest/migration/
```

---

## 12. Recursos Adicionales

### Herramientas

- **GitHub CLI**: `gh issue create --title "..." --body "..."`
- **GitHub Desktop**: GUI para gestión visual
- **ZenHub**: Project management sobre GitHub
- **Linear**: Alternativa moderna a GitHub Issues

### Guías Oficiales

- [GitHub Issues Documentation](https://docs.github.com/en/issues)
- [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Issue Templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)

### Ejemplos de Proyectos con Buena Gestión

- [React](https://github.com/facebook/react/issues)
- [VSCode](https://github.com/microsoft/vscode/issues)
- [Kubernetes](https://github.com/kubernetes/kubernetes/issues)

---

## Resumen de Mejores Prácticas

1. ✅ Usa templates consistentes
2. ✅ Asigna labels y prioridades
3. ✅ Vincula issues con PRs
4. ✅ Usa milestones para releases
5. ✅ Mantén comunicación clara y respetuosa
6. ✅ Automatiza tareas repetitivas
7. ✅ Mide y mejora continuamente
8. ✅ Documenta decisiones importantes
9. ✅ Cierra issues obsoletos
10. ✅ Celebra cuando se cierran issues! 🎉

---

**Última actualización**: 2025-11-19
**Autor**: Claude
**Versión**: 1.0
