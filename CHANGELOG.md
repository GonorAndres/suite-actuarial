# Changelog

## 2.0.0 (2026-03-22)

### Nuevo
- Dominio Danos: SeguroAuto con tablas AMIS, ModeloColectivo, credibilidad Buhlmann
- Dominio Salud: GMM con bandas quinquenales, AccidentesEnfermedades
- Dominio Pensiones: Conmutacion, RentaVitalicia, PensionLey73, PensionLey97 con tablas IMSS completas
- Sistema de configuracion regulatoria versionada (config_2024, config_2025, config_2026)
- Modulo de tasas de interes (CurvaRendimiento)
- Demo interactivo con 7 paginas Streamlit mostrando uso de la libreria

### Cambiado
- Renombrado paquete: mexican_insurance -> suite_actuarial
- Dividido validators.py (1297 lineas) en core/models/ submodulos
- Aplanado products/vida/ -> vida/, reinsurance/ -> reaseguro/
- RCS inversion usa correlacion 0.75 (antes 1.0 suma simple)
- RCS vida usa matriz de correlacion CNSF (antes correlacion cero)

### Corregido
- validador_siniestros.py: nombres de campo Pydantic incorrectos (crasheaba PM)
- Tasa de aportacion AFORE: 6.5% -> 10.775% (era 40% menor)
- reserva_matematica.py: soporte para tabla EMSSA-09 real + duracion de poliza
- UMA 2024 anual: 39628.08 -> 39628.05

## 1.0.0 (2026-03-18)
- Lanzamiento inicial con Vida, Reaseguro, Reservas, Regulatorio
- 307 tests, 87% cobertura
