# Validacion, evidencia y limitaciones -- suite_actuarial

Este documento describe qué propiedades matemáticas y contratos de software se
verifican en el repositorio. La validación de una fórmula o de una identidad
actuarial no equivale a aprobación regulatoria, validación institucional ni
certificación de datos. El proyecto sirve como toolkit educativo/de referencia
y como workbench para analistas; los resultados deben revisarse contra las
fuentes, supuestos y métodos aprobados por cada organización.

## 1. Tabla de mortalidad EMSSA-09

### Spot checks de qx

| Edad | qx Hombre | qx Mujer |
|------|-----------|----------|
| 18   | 0.0009    | 0.0004   |
| 25   | 0.00104   | 0.00047  |
| 35   | 0.0013    | 0.00066  |
| 50   | 0.0033    | 0.0018   |
| 65   | 0.0135    | 0.006    |
| 80   | 0.062     | 0.0273   |
| 100  | 0.442     | 0.2455   |

### Propiedades verificadas

- qx aumenta con la edad (monotonia para adultos)
- qx(masculino) > qx(femenino) para todas las edades (mortalidad masculina mayor)
- 0 <= qx <= 1 para todas las entradas
- lx es no-creciente

El sexo se identifica con la palabra completa `masculino` / `femenino` en todo el
paquete y la API. El CSV publicado conserva sus iniciales `H`/`M`; la traduccion
ocurre una sola vez, en `TablaMortalidad.desde_csv`.

## 2. Funciones de conmutacion

### Valores a tasa tecnica i = 5.5% (Hombres)

| Edad | Dx          | Nx            | ax (anualidad vitalicia) |
|------|-------------|---------------|--------------------------|
| 25   | 26047.6559  | 461607.5134   | 17.7217                  |
| 35   | 15075.3886  | 255389.5012   | 16.9408                  |
| 45   | 8685.3941   | 136208.4928   | 15.6825                  |
| 55   | 4921.8250   | 67904.8867    | 13.7967                  |
| 65   | 2658.9288   | 29774.5785    | 11.1980                  |

### Identidades actuariales verificadas

**Ax + d*ax = 1** (donde d = i/(1+i) = 0.052133)

| Edad | Ax       | ax       | Ax + d*ax |
|------|----------|----------|-----------|
| 25   | 0.076122 | 17.7217  | 1.000000  |
| 35   | 0.116829 | 16.9408  | 1.000000  |
| 45   | 0.182430 | 15.6825  | 1.000000  |
| 55   | 0.280741 | 13.7967  | 1.000000  |
| 65   | 0.416220 | 11.1980  | 1.000000  |

Desviacion maxima sobre todas las edades (18-100): 0.0000000000

- Nx = sum(Dx from x to omega) -- verificado para todas las edades
- Mx = sum(Cx from x to omega) -- verificado para todas las edades

## 3. Reservas

### Chain Ladder

- Resultado: ultimate = pagado * factores_acumulados
- Verificado: reserva_total = ultimate_total - pagado_total (diferencia < $0.01)

### Bootstrap

- Determinismo: misma semilla produce mismos resultados
- TVaR >= VaR para todos los niveles de confianza

## 4. RCS

- Diversificacion: RCS_agregado <= RCS_vida + RCS_danos + RCS_inversion
- Verificado con correlacion 0.75 entre sub-riesgos de mercado

## 5. IMSS

- Ley 73, 500 semanas: 33.07% del salario (Art. 167 LSS 1973)
- Ley 73, 2060+ semanas: 100% cap
- Factor edad 65: 1.00, Factor edad 60: 0.75

## Qué demuestran los tests

- Que las implementaciones satisfacen las identidades, invariantes y casos de
  frontera que están expresamente cubiertos.
- Que ciertos resultados son deterministas cuando se proporciona una semilla.
- Que los modelos y adaptadores de API rechazan varios datos inválidos conocidos.

## Qué no demuestran los tests

- Que una tabla ilustrativa sea la tabla oficial vigente.
- Que una simplificación represente el método completo exigido por CNSF, SAT,
  CONSAR o IMSS.
- Que un cálculo sea adecuado para una cartera, producto o reporte institucional
  sin validación actuarial independiente.

## 6. Limitaciones conocidas

Cada modulo con datos ilustrativos o simplificados expone una constante `DISCLAIMER`
a nivel de modulo para facilitar su identificacion programatica. El inventario
razonado de estos techos, con fuente, vigencia y ruta de sustitucion por modelo,
esta en [`AUDIT.md`](AUDIT.md#inventario-clase-b-fase-5); esta seccion es el
indice de las constantes.

Daños:

- **AMIS** (`danos/tablas_amis.py`): tasas, zonas y factores representativos, no las tablas oficiales vigentes.
- **Auto** (`danos/auto.py`): ademas de lo anterior, tarifa la RC a terceros sobre el valor del propio vehiculo y redondea en pasos intermedios.
- **Incendio** (`danos/incendio.py`): tasas por tipo de construccion y factores de zona y uso ilustrativos; sin deducible, infraseguro ni riesgo catastrofico.
- **RC general** (`danos/rc.py`): prima por millar del limite, sin frecuencia ni severidad ni medida de exposicion; factor de deducible escalonado.
- **Bonus-Malus** (`danos/tarifas.py`): niveles, factores y reglas de transicion ilustrativos, sin calibrar.
- **Modelo colectivo** (`danos/frecuencia_severidad.py`): metodo estandar sobre parametros que fija quien llama; sin ajuste a datos ni error de simulacion reportado.

Salud:

- **GMM** (`salud/gmm.py`): tasas base por banda de edad ilustrativas; sin frecuencia-severidad ni tendencia medica.
- **Accidentes** (`salud/accidentes.py`): tasas, factores de ocupacion y porcentajes de perdidas organicas construidos para el laboratorio.

Regulatorio y reservas:

- **RCS Vida/Danos/Inversion** (`regulatorio/rcs_vida.py`, `rcs_danos.py`, `rcs_inversion.py`): factores pedagogicos simplificados, no el modelo estocastico completo de la CNSF.
- **Reserva Matematica** (`regulatorio/reservas_tecnicas/models.py`, `DISCLAIMER_RM`): prospectiva de primas netas; **no** es un calculo conforme a la Circular S-11.4.
- **Art. 142 LISR** (`regulatorio/validaciones_sat/validador_siniestros.py`): simplificacion 50/50 para gravabilidad de rentas vitalicias.
- **Chain Ladder, cola y diagnosticos** (`reservas/chain_ladder.py`, `cola.py`, `diagnosticos.py`): avisos sobre extrapolacion de la cola y sobre supuestos del metodo que los datos no verifican.

Tabla de mortalidad:

- **EMSSA-09**: no fuerza q_omega = 1 en edad terminal (qx a los 100, masculino = 0.442). Ver `src/suite_actuarial/data/mortality_tables/README.md`.
- La tabla incluida es una version simplificada con fines demostrativos, declarada
  `illustrative` en su `metadata.json` y verificada por sha256 al cargar; para
  produccion, usar las tablas oficiales de la CNSF.
