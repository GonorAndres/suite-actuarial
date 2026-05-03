# Tabla de Mortalidad EMSSA-09

## Fuente

La tabla **EMSSA-09** (Experiencia Mexicana de Seguridad Social Actualizada 2009) es la tabla
de mortalidad estandar utilizada en Mexico para la valuacion de seguros de vida y pensiones.

## Origen y autoridad

- **Publicada por:** Comision Nacional de Seguros y Fianzas (CNSF)
- **Base estadistica:** Experiencia de mortalidad del Instituto Mexicano del Seguro Social (IMSS)
  y otras instituciones de seguridad social en Mexico
- **Periodo de observacion:** Datos de mortalidad observados hasta 2009
- **Uso regulatorio:** Requerida por la CNSF para valuacion de reservas tecnicas en seguros de vida
  (Circular Unica de Seguros y Fianzas, Titulo 22)

## Estructura del archivo

El archivo `emssa_09.csv` contiene tres columnas:

| Columna | Tipo   | Descripcion                                      |
|---------|--------|--------------------------------------------------|
| `edad`  | int    | Edad del asegurado (18-100)                      |
| `sexo`  | string | `H` (Hombre) o `M` (Mujer)                      |
| `qx`    | float  | Probabilidad de muerte entre edad x y edad x+1   |

Las filas estan ordenadas primero por sexo (H, luego M) y dentro de cada sexo por edad ascendente.

El archivo `metadata.json` contiene informacion descriptiva de la tabla: nombre completo, fuente,
rango de edades, sexos disponibles, uso recomendado y notas sobre precision.

## Rango de edades

- Edad minima: 18
- Edad maxima: 100
- Sexo: H (Hombre), M (Mujer)
- Total de registros: 166 (83 por sexo)

## Nota sobre precision

Los valores qx (probabilidad de muerte) se almacenan con precision decimal completa.
La libreria usa `Decimal` para todas las operaciones monetarias derivadas de esta tabla.

## Nota sobre alcance

Segun `metadata.json`, esta es una version simplificada con datos aproximados para propositos
demostrativos. Para uso en produccion, descargar las tablas oficiales de la CNSF.

## Limitaciones conocidas

La tabla EMSSA-09 no define q_omega = 1.0 en la edad terminal. Los valores
publicados son q_100_H = 0.442 y q_100_M = 0.2455, lo que implica que un
porcentaje de la cohorte sobrevive mas alla de la edad 100.

El metodo `TablaMortalidad.calcular_lx()` expone un parametro
`omega_convention` para controlar este comportamiento:

- `"force_zero"` (default): fuerza lx[omega+1] = 0, de modo que
  dx[omega] = lx[omega] (toda la cohorte restante muere). Preserva
  compatibilidad con versiones anteriores.
- `"table_as_is"`: calcula lx[omega+1] = lx[omega] * (1 - qx[omega]) y
  dx[omega] = lx[omega] * qx[omega], respetando el valor publicado de qx.

El default es `"force_zero"` para no alterar resultados existentes.

## Actualizacion

Si la CNSF publica una tabla actualizada (e.g., EMSSA-19), reemplazar el archivo CSV
y verificar que el formato de columnas sea compatible con `TablaMortalidad.cargar_emssa09()`.
