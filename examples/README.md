# Notebooks de Ejemplo - Mexican Insurance Analytics Suite

Ejemplos prácticos de uso de la librería `mexican_insurance` para análisis actuarial, reaseguro, reservas técnicas y cumplimiento regulatorio en México.

## Contenido

### 01. Introducción y Productos de Vida
**Archivo**: `01_introduccion_productos_vida.ipynb`

Aprende los fundamentos de la librería calculando primas y reservas para seguros de vida.

**Temas cubiertos**:
- Carga de tabla de mortalidad EMSSA-09
- Seguro de Vida Temporal (protección por plazo fijo)
- Seguro de Vida Ordinario (cobertura vitalicia)
- Seguro de Vida Dotal (protección + ahorro)
- Comparación de productos
- Análisis de sensibilidad por edad
- Análisis de cartera

**Duración estimada**: 30-45 minutos

---

### 02. Reaseguro
**Archivo**: `02_reaseguro.ipynb`

Domina las estrategias de reaseguro para gestionar la exposición al riesgo.

**Temas cubiertos**:
- Quota Share (Cuota Parte) - reaseguro proporcional
- Excess of Loss (Exceso de Pérdida) - por siniestro individual
- Stop Loss (Exceso de Siniestralidad) - por resultado agregado
- Comparación de estructuras
- Optimización de estrategias

**Duración estimada**: 35-50 minutos

---

### 03. Reservas Técnicas
**Archivo**: `03_reservas_tecnicas.ipynb`

Implementa métodos actuariales avanzados para calcular reservas de siniestros.

**Temas cubiertos**:
- Chain Ladder (método clásico de triángulos)
- Bornhuetter-Ferguson (combinación históricos + esperados)
- Bootstrap (estimación de incertidumbre)
- Intervalos de confianza
- Comparación de métodos
- Análisis de sensibilidad

**Duración estimada**: 40-55 minutos

---

### 04. Cumplimiento Regulatorio CNSF
**Archivo**: `04_cumplimiento_cnsf.ipynb`

Calcula los requerimientos regulatorios de la CNSF para aseguradoras mexicanas.

**Temas cubiertos**:
- RCS Vida (capital de solvencia para seguros de vida)
- RCS Daños (capital de solvencia para seguros generales)
- Reservas Técnicas según Circular S-11.4
  - Reserva Matemática
  - Reserva de Riesgos en Curso
- Validación de suficiencia
- Dashboard de solvencia

**Duración estimada**: 45-60 minutos

---

### 05. Validaciones Fiscales SAT
**Archivo**: `05_validaciones_sat.ipynb`

Asegura el cumplimiento de las obligaciones fiscales ante el SAT.

**Temas cubiertos**:
- Validación de deducibilidad de primas
- Validación de requisitos fiscales de siniestros
- Cálculo de retenciones ISR
- Casos prácticos de cumplimiento
- Dashboard fiscal

**Duración estimada**: 35-45 minutos

---

### 06. Reportes CNSF Automatizados
**Archivo**: `06_reportes_cnsf.ipynb`

Genera reportes regulatorios automatizados para la CNSF.

**Temas cubiertos**:
- Reporte de Suscripción (primas y pólizas)
- Reporte de Siniestros (siniestralidad y reservas)
- Reporte de Inversiones (portafolio y riesgo)
- Reporte RCS (capital regulatorio)
- Exportación a Excel y PDF

**Duración estimada**: 40-50 minutos

---

### 07. Casos Prácticos Completos (End-to-End)
**Archivo**: `07_casos_practicos_completos.ipynb`

Integra todos los módulos en workflows completos de negocio.

**Casos cubiertos**:
1. **Aseguradora Nueva**: Tarificación completa de cartera
2. **Optimización de Reaseguro**: Comparación de estructuras
3. **Análisis de Solvencia**: Proyecciones de RCS a 3 años
4. **Auditoría Regulatoria**: CNSF + SAT completo
5. **Pipeline Completo**: Producto → Reaseguro → Reservas → Reportes

**Duración estimada**: 60-90 minutos

---

## Instalación y Configuración

### Requisitos Previos

```bash
# Python 3.11+
python --version

# Clonar el repositorio
git clone https://github.com/TuUsuario/Analisis_Seguros_Mexico.git
cd Analisis_Seguros_Mexico
```

### Instalación de Dependencias

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar la librería con dependencias de visualización
pip install -e ".[viz]"
```

### Ejecutar Jupyter

```bash
# Iniciar Jupyter Lab
jupyter lab

# O Jupyter Notebook clásico
jupyter notebook
```

Navega a la carpeta `examples/` y abre cualquier notebook.

---

## Datos de Ejemplo

Los notebooks utilizan datos sintéticos ubicados en `examples/data/`:

- **cartera_ejemplo.csv**: 20 pólizas de vida con diferentes características
- **siniestros_ejemplo.csv**: 10 siniestros en diferentes estados
- **inversiones_ejemplo.csv**: 15 instrumentos de inversión
- **triangulo_ejemplo.csv**: Triángulo de desarrollo de siniestros (6 años)

Estos datos son ficticios y están diseñados para fines educativos.

---

## Orden Recomendado

### Para principiantes:
1. **01_introduccion_productos_vida.ipynb** ← Empezar aquí
2. **02_reaseguro.ipynb**
3. **03_reservas_tecnicas.ipynb**
4. **04_cumplimiento_cnsf.ipynb**
5. **05_validaciones_sat.ipynb**
6. **06_reportes_cnsf.ipynb**
7. **07_casos_practicos_completos.ipynb**

### Para usuarios avanzados:
- Ve directamente a **07_casos_practicos_completos.ipynb** para ver integraciones completas
- Usa los notebooks específicos (02-06) como referencia según necesites

---

## Visualizaciones

Todos los notebooks incluyen visualizaciones profesionales con:
- Matplotlib y Seaborn para gráficas estáticas
- Tablas comparativas
- Dashboards de análisis
- Heatmaps y distribuciones

---

## Exportación de Resultados

Los notebooks 06 y 07 incluyen ejemplos de exportación a:
- **Excel** (.xlsx) con múltiples hojas
- **PDF** (requiere instalación adicional de reportlab)
- **CSV** para análisis externos

---

## Troubleshooting

### Error: "Module not found"
```bash
# Asegúrate de tener la librería instalada
pip install -e ".[viz]"
```

### Error: "File not found" al cargar datos
```bash
# Verifica que estés en el directorio correcto
cd /ruta/a/Analisis_Seguros_Mexico
jupyter lab
```

### Gráficas no se muestran
```python
# Añade esta línea al inicio del notebook
%matplotlib inline
```

---

## Contribuir

Si encuentras errores o tienes sugerencias para mejorar los notebooks:

1. Abre un issue en GitHub
2. Describe el problema o mejora
3. Si es posible, incluye código de ejemplo

---

## Recursos Adicionales

- **[Documentación Completa](../docs/JOURNAL.md)**: Detalles técnicos de implementación
- **[Resumen Ejecutivo](../docs/resumen_ejecutivo.html)**: Visión general del proyecto
- **[README Principal](../README.md)**: Información general del repositorio

---

## Licencia

MIT License - Los notebooks y código de ejemplo están disponibles libremente para uso educativo y comercial.

---

## Contacto

Para preguntas sobre los notebooks o la librería, abre un issue en GitHub.

**Nota Legal**: Los ejemplos son para propósitos educativos. Para uso en producción, valida con un actuario certificado y cumple con todas las regulaciones de la CNSF.
