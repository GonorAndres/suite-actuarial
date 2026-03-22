"""Configuracion regulatoria para el ano fiscal 2025."""

from decimal import Decimal

from suite_actuarial.config.schema import (
    ConfigAnual,
    FactoresCNSF,
    FactoresTecnicos,
    TasasSAT,
    UMAConfig,
)

CONFIG = ConfigAnual(
    anio=2025,
    uma=UMAConfig(
        uma_diaria=Decimal("113.14"),
        uma_mensual=Decimal("3439.46"),
        uma_anual=Decimal("41296.10"),
    ),
    tasas_sat=TasasSAT(
        tasa_retencion_rentas_vitalicias=Decimal("0.10"),
        tasa_retencion_retiros_ahorro=Decimal("0.20"),
        tasa_isr_personas_morales=Decimal("0.30"),
        tasa_iva=Decimal("0.16"),
        limite_deducciones_pf_umas=5,
    ),
    factores_cnsf=FactoresCNSF(
        shock_acciones=Decimal("0.35"),
        shock_bonos_gubernamentales=Decimal("0.05"),
        shock_bonos_corporativos=Decimal("0.15"),
        shock_inmuebles=Decimal("0.25"),
        shocks_credito={
            "AAA": Decimal("0.002"),
            "AA": Decimal("0.005"),
            "A": Decimal("0.010"),
            "BBB": Decimal("0.020"),
            "BB": Decimal("0.050"),
            "B": Decimal("0.100"),
            "CCC": Decimal("0.200"),
            "CC": Decimal("0.350"),
            "C": Decimal("0.500"),
        },
        correlacion_vida_danos=Decimal("0.00"),
        correlacion_vida_inversion=Decimal("0.25"),
        correlacion_danos_inversion=Decimal("0.25"),
    ),
    factores_tecnicos=FactoresTecnicos(
        tasa_interes_tecnico_vida=Decimal("0.055"),
        tasa_interes_tecnico_pensiones=Decimal("0.035"),
        edad_omega=100,
        margen_seguridad_s114=Decimal("0.05"),
    ),
)
