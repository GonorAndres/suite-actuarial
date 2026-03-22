# suite_actuarial

Libreria actuarial fundamental para el mercado mexicano de seguros.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-587%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Instalacion

```bash
pip install suite-actuarial
```

Para desarrollo con todas las dependencias:

```bash
pip install -e ".[dev,viz]"
```

## Dominios

| Dominio | Modulos | Descripcion |
|---------|---------|-------------|
| **Vida** | VidaTemporal, VidaOrdinario, VidaDotal | Seguros de vida con mortalidad EMSSA-09 |
| **Danos** | SeguroAuto, ModeloColectivo, FactorCredibilidad | P&C con tablas AMIS y modelo colectivo |
| **Salud** | GMM, AccidentesEnfermedades | Gastos medicos mayores y A&E |
| **Pensiones** | RentaVitalicia, PensionLey73, PensionLey97 | Pensiones IMSS y rentas vitalicias |
| **Reservas** | ChainLadder, BornhuetterFerguson, Bootstrap | Metodos de reservas IBNR |
| **Reaseguro** | QuotaShare, ExcessOfLoss, StopLoss | Contratos de reaseguro |
| **Regulatorio** | AgregadorRCS, ValidadorPrimas, CalculadoraRetenciones | CNSF, SAT, Circular S-11.4 |
| **Config** | cargar_config, ConfigAnual | Parametros regulatorios versionados (2024-2026) |

## Ejemplo rapido

### Tarificacion de seguro de vida

```python
from decimal import Decimal
from suite_actuarial import VidaTemporal, TablaMortalidad, Asegurado, ConfiguracionProducto
from suite_actuarial.core.validators import Sexo

tabla = TablaMortalidad()
config = ConfiguracionProducto(
    nombre_producto="Vida Temporal 20",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),
)
producto = VidaTemporal(config, tabla)
asegurado = Asegurado(edad=35, sexo=Sexo.HOMBRE, suma_asegurada=Decimal("1000000"))
resultado = producto.calcular_prima(asegurado, frecuencia_pago="mensual")
print(f"Prima mensual: ${resultado.prima_total:,.2f}")
```

### Cotizacion de seguro de auto

```python
from suite_actuarial import SeguroAuto, Cobertura

auto = SeguroAuto(
    valor_vehiculo=Decimal("450000"),
    modelo_anio=2024,
    uso="particular",
    zona="Ciudad de Mexico",
)
coberturas = [Cobertura.DANOS_MATERIALES, Cobertura.ROBO_TOTAL, Cobertura.RC_OBLIGATORIA]
cotizacion = auto.cotizar(coberturas)
print(f"Prima anual: ${cotizacion.prima_total:,.2f}")
```

### Prima de gastos medicos mayores

```python
from suite_actuarial import GMM, NivelHospitalario, ZonaGeografica

gmm = GMM(
    edad=40,
    sexo="masculino",
    nivel_hospitalario=NivelHospitalario.ALTO,
    zona=ZonaGeografica.CDMX,
    suma_asegurada=Decimal("20000000"),
    deducible=Decimal("30000"),
    coaseguro=Decimal("0.10"),
)
prima = gmm.calcular_prima()
print(f"Prima anual GMM: ${prima:,.2f}")
```

### Calculo de pension IMSS

```python
from suite_actuarial import PensionLey73, CalculadoraIMSS

calc = CalculadoraIMSS()
pension = PensionLey73(
    salario_promedio_5a=Decimal("25000"),
    semanas_cotizadas=1800,
    edad=65,
    calculadora=calc,
)
resultado = pension.calcular()
print(f"Pension mensual Ley 73: ${resultado.pension_mensual:,.2f}")
```

## Configuracion regulatoria

La libreria incluye un sistema de configuracion regulatoria versionada por anio fiscal.
Cada configuracion contiene los parametros oficiales de la UMA, tasas del SAT, factores
de la CNSF y parametros tecnicos actuariales.

```python
from suite_actuarial import cargar_config

# Cargar configuracion del anio 2026
cfg = cargar_config(2026)
print(f"UMA diaria: ${cfg.uma.uma_diaria}")
print(f"UMA anual: ${cfg.uma.uma_anual}")
print(f"ISR personas morales: {cfg.tasas_sat.tasa_isr_personas_morales}")
print(f"Tasa tecnica vida (CNSF): {cfg.factores_tecnicos.tasa_interes_tecnico_vida}")
```

Configuraciones disponibles: 2024, 2025, 2026.

## Demo interactivo

La suite incluye una aplicacion Streamlit con 7 paginas demostrativas:

```bash
streamlit run streamlit_app/Home.py
```

Paginas: Productos de Vida, Danos, Salud, Pensiones, Reservas Tecnicas,
Regulatorio, Reaseguro.

## Desarrollo

```bash
git clone https://github.com/GonorAndres/Analisis_Seguros_Mexico.git
cd suite-actuarial
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,viz]"
pytest
```

## Tests

587 tests | 4 dominios | Python 3.11+

```bash
pytest --cov=suite_actuarial --cov-report=term-missing
```

## Autor

Andres Gonzalez Ortega - UNAM Actuaria

## Licencia

MIT
