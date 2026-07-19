# Migracion de suite_actuarial 2.0 a 2.1

La version 2.1 mantiene las firmas principales de productos y reservas. Los
resultados ahora pueden incluir `calculation_metadata` y los resultados fiscales
incluyen `estado` (`eligible`, `not_eligible` o `indeterminate`).

Para fechas regulatorias use:

```python
from suite_actuarial import cargar_config_fecha

config = cargar_config_fecha("2026-02-01")
```

Los perfiles de 2026 reflejan la UMA oficial vigente desde el 1 de febrero.
`cargar_config(2026)` sigue disponible como helper anual. No existe un perfil
oficial 2027 hasta que la autoridad publique los datos correspondientes.

Los calculadores RCS simplificados, RRC pro-rata, pensiones aproximadas,
tarifas de mercado y curvas CETES de referencia emiten `ExperimentalModelWarning`.
El campo `cumple_regulacion` de RCS se conserva como alias deprecated; para el
resultado del modelo use `cumple_umbral_modelo`.
