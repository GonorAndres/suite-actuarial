# Validacion y Benchmarks -- suite_actuarial

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
- qx_H > qx_M para todas las edades (mortalidad masculina mayor)
- 0 <= qx <= 1 para todas las entradas
- lx es no-creciente

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

## 6. Limitaciones conocidas

- EMSSA-09 no fuerza q_omega = 1 en edad terminal (qx_100_H = 0.442)
- GMM: tasas base son ilustrativas, no datos reales del mercado
- AMIS: tablas de tarificacion son representativas, no las tablas oficiales vigentes
- Art. 142 LISR: se usa simplificacion 50/50 para gravabilidad de rentas vitalicias
- Tabla EMSSA-09 incluida es version simplificada para propositos demostrativos
  (ver metadata.json); para produccion usar tablas oficiales de la CNSF
