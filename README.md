# 🏦 Mexican Insurance Analytics Suite

> Suite de herramientas actuariales para el mercado asegurador mexicano

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Un conjunto de herramientas en Python para análisis actuarial, cálculo de primas, reservas técnicas y cumplimiento regulatorio para el mercado de seguros en México.

## 🎯 Características

### Fase 1 (Actual) - Fundamentos ✅
- ✅ **Tablas de Mortalidad**: Carga y manejo de EMSSA-09 y otras tablas mexicanas
- ✅ **Seguros de Vida**: Cálculo de primas para seguros temporales
- ✅ **Reservas Técnicas**: Cálculo de reservas matemáticas
- ✅ **Validación de Datos**: Modelos Pydantic para garantizar consistencia
- ✅ **Tests Completos**: Suite de tests con pytest (>90% cobertura)

### Próximamente 🔄
- **Reaseguro**: Quota Share, Exceso de Pérdida, Stop Loss
- **Cumplimiento CNSF**: Reportes regulatorios automatizados
- **RCS (Solvencia)**: Cálculo de requerimientos de capital
- **Reservas Avanzadas**: Chain Ladder, Bornhuetter-Ferguson
- **Dashboard Streamlit**: Interfaz visual para análisis

## 🚀 Inicio Rápido

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/TuUsuario/Analisis_Seguros_Mexico.git
cd Analisis_Seguros_Mexico

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar en modo desarrollo
pip install -e ".[dev]"
```

### Ejemplo Básico

```python
from decimal import Decimal
from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad
from mexican_insurance.products.vida.temporal import VidaTemporal
from mexican_insurance.core.validators import (
    Asegurado,
    ConfiguracionProducto,
    Sexo
)

# Cargar tabla de mortalidad EMSSA-09
tabla = TablaMortalidad.cargar_emssa09()

# Configurar producto: Vida Temporal 20 años
config = ConfiguracionProducto(
    nombre_producto="Vida Temporal 20 años",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),  # 5.5%
)

# Crear el producto
producto = VidaTemporal(config, tabla)

# Definir asegurado
asegurado = Asegurado(
    edad=35,
    sexo=Sexo.HOMBRE,
    suma_asegurada=Decimal("1000000")  # 1 millón de pesos
)

# Calcular prima
resultado = producto.calcular_prima(asegurado, frecuencia_pago="mensual")

print(f"Prima Neta: ${resultado.prima_neta:,.2f} MXN")
print(f"Prima Total: ${resultado.prima_total:,.2f} MXN")
print(f"\nDesglose de Recargos:")
for concepto, monto in resultado.desglose_recargos.items():
    print(f"  - {concepto}: ${monto:,.2f}")
```

## 📄 Resumen Ejecutivo para Portafolio

**¿Necesitas entender el proyecto sin profundizar en el código?**

Hemos creado un [**Resumen Ejecutivo en HTML**](docs/resumen_ejecutivo.html) que explica:

- 🎯 **Visión general** del proyecto y problema que resuelve
- 🏗️ **Arquitectura** y diseño del sistema
- 📊 **Conceptos actuariales** traducidos a lenguaje de negocio
- ✅ **Fase 1 completada** con explicaciones detalladas de cada componente
- 🔄 **Fase 2 en progreso** (Vida Ordinario, Vida Dotal)
- 📈 **Valor de negocio** y beneficios cuantificables
- 🗺️ **Roadmap futuro** con siguientes fases

**Ideal para:**
- Presentar el proyecto en portafolio profesional
- Explicar la solución a stakeholders no técnicos
- Compartir con equipos de negocio o actuariales
- Documentar decisiones de diseño y arquitectura

👉 **[Ver Resumen Ejecutivo](docs/resumen_ejecutivo.html)** - Se puede abrir en cualquier navegador y exportar a PDF.

## 📚 Estructura del Proyecto

```
mexican-insurance-suite/
├── src/mexican_insurance/       # Código fuente principal
│   ├── core/                    # Clases base y validadores
│   │   ├── base_product.py     # Clase abstracta ProductoSeguro
│   │   └── validators.py       # Modelos Pydantic
│   ├── products/vida/           # Seguros de vida
│   │   └── temporal.py         # Vida temporal
│   ├── actuarial/               # Herramientas actuariales
│   │   ├── mortality/          # Tablas de mortalidad
│   │   └── pricing/            # Fórmulas de tarificación
│   └── regulatory/              # Cumplimiento regulatorio
├── data/mortality_tables/       # Tablas de mortalidad
│   └── emssa_09.csv            # EMSSA-09
├── tests/                       # Suite de tests
│   ├── unit/                   # Tests unitarios
│   └── integration/            # Tests de integración
└── docs/                        # Documentación
```

## 🧪 Tests

El proyecto incluye una suite completa de tests:

```bash
# Ejecutar todos los tests
pytest

# Con reporte de cobertura
pytest --cov=mexican_insurance --cov-report=html

# Solo tests específicos
pytest tests/unit/test_vida_temporal.py -v
```

**Cobertura actual**: >90% en módulos core

## 🛠️ Desarrollo

### Configuración del Entorno

```bash
# Instalar todas las dependencias
pip install -e ".[all]"

# Instalar pre-commit hooks
pre-commit install

# Ejecutar linting
ruff check src/ tests/

# Type checking
mypy src/
```

## 📝 Roadmap

### Fase 1: Fundamentos ✅ (Completada)
- [x] Estructura base del proyecto
- [x] Tablas de mortalidad
- [x] Seguros de vida temporal
- [x] Tests unitarios

### Fase 2: Expansión de Productos
- [ ] Vida Ordinario
- [ ] Vida Dotal
- [ ] Gastos Médicos Mayores

### Fase 3: Reaseguro
- [ ] Quota Share
- [ ] Exceso de Pérdida
- [ ] Stop Loss

### Fase 4: Reservas Avanzadas
- [ ] Chain Ladder
- [ ] Bornhuetter-Ferguson
- [ ] Bootstrap

### Fase 5: Regulatorio
- [ ] Cálculo de RCS (Solvencia)
- [ ] Reportes CNSF automáticos

### Fase 6: Interfaz
- [ ] Dashboard Streamlit
- [ ] API REST

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Escribe tests para tu código
4. Asegúrate que todos los tests pasen
5. Abre un Pull Request

## ⚖️ Licencia

MIT License - ver archivo [LICENSE](LICENSE)

## 📧 Contacto

Para preguntas o reportar bugs, abre un issue en GitHub.

---

**Nota Legal**: Esta librería es para propósitos educativos y de análisis. Para uso en producción en una aseguradora, valida los resultados con un actuario certificado y asegúrate de cumplir con todas las regulaciones de la CNSF.
