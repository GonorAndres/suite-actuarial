"""
Modelos Pydantic para reportes regulatorios CNSF.

Estos modelos estructuran los datos que se incluyen en los reportes
trimestrales que las aseguradoras deben presentar a la CNSF.
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TipoRamo(str, Enum):
    """Tipos de ramos de seguro según clasificación CNSF"""

    # Vida
    VIDA_INDIVIDUAL = "vida_individual"
    VIDA_GRUPO = "vida_grupo"
    PENSIONES = "pensiones"

    # Daños
    AUTOS = "autos"
    INCENDIO = "incendio"
    GASTOS_MEDICOS = "gastos_medicos"
    RESPONSABILIDAD_CIVIL = "responsabilidad_civil"
    DIVERSOS = "diversos"
    MARITIMO = "maritimo"
    TERREMOTO = "terremoto"


class TrimesteCNSF(str, Enum):
    """Trimestres del año para reportes CNSF"""

    Q1 = "Q1"  # Enero-Marzo
    Q2 = "Q2"  # Abril-Junio
    Q3 = "Q3"  # Julio-Septiembre
    Q4 = "Q4"  # Octubre-Diciembre


class MetadatosReporte(BaseModel):
    """
    Metadatos del reporte regulatorio.

    Incluye información de identificación del reporte y la aseguradora.

    Ejemplo:
        >>> metadata = MetadatosReporte(
        ...     clave_aseguradora="A0123",
        ...     nombre_aseguradora="Seguros XYZ S.A.",
        ...     trimestre=TrimesteCNSF.Q1,
        ...     anio=2024,
        ...     fecha_presentacion=date(2024, 4, 30)
        ... )
    """

    clave_aseguradora: str = Field(..., min_length=3, max_length=10)
    nombre_aseguradora: str = Field(..., min_length=3, max_length=200)
    trimestre: TrimesteCNSF
    anio: int = Field(..., ge=2020, le=2100)
    fecha_presentacion: date
    contacto_responsable: Optional[str] = Field(default=None, max_length=200)

    @field_validator("fecha_presentacion")
    @classmethod
    def validar_fecha_coherente(cls, v: date, info) -> date:
        """La fecha de presentación debe ser posterior al trimestre reportado"""
        if "anio" in info.data and "trimestre" in info.data:
            anio = info.data["anio"]
            trimestre = info.data["trimestre"]

            # Último día del trimestre
            ultimos_dias = {
                TrimesteCNSF.Q1: date(anio, 3, 31),
                TrimesteCNSF.Q2: date(anio, 6, 30),
                TrimesteCNSF.Q3: date(anio, 9, 30),
                TrimesteCNSF.Q4: date(anio, 12, 31),
            }

            if v < ultimos_dias[trimestre]:
                raise ValueError(
                    f"Fecha de presentación debe ser posterior al trimestre {trimestre} de {anio}"
                )

        return v


class DatosSuscripcionRamo(BaseModel):
    """
    Datos de suscripción por ramo para un trimestre.

    Incluye primas emitidas, devengadas, canceladas y número de pólizas.

    Ejemplo:
        >>> datos = DatosSuscripcionRamo(
        ...     ramo=TipoRamo.AUTOS,
        ...     primas_emitidas=Decimal("50000000"),
        ...     primas_devengadas=Decimal("48000000"),
        ...     primas_canceladas=Decimal("2000000"),
        ...     numero_polizas=15000,
        ...     suma_asegurada_total=Decimal("2000000000")
        ... )
    """

    ramo: TipoRamo
    primas_emitidas: Decimal = Field(..., ge=0)
    primas_devengadas: Decimal = Field(..., ge=0)
    primas_canceladas: Decimal = Field(default=Decimal("0"), ge=0)
    numero_polizas: int = Field(..., ge=0)
    suma_asegurada_total: Decimal = Field(..., ge=0)

    @field_validator("primas_devengadas")
    @classmethod
    def validar_devengadas(cls, v: Decimal, info) -> Decimal:
        """Primas devengadas no pueden exceder emitidas netas"""
        if "primas_emitidas" in info.data and "primas_canceladas" in info.data:
            emitidas_netas = info.data["primas_emitidas"] - info.data.get(
                "primas_canceladas", Decimal("0")
            )
            if v > emitidas_netas * Decimal("1.05"):  # Tolerancia 5%
                raise ValueError(
                    "Primas devengadas exceden significativamente primas emitidas netas"
                )
        return v


class DatosSiniestrosRamo(BaseModel):
    """
    Datos de siniestros por ramo para un trimestre.

    Incluye siniestros ocurridos, pagados, reservas y número de casos.

    Ejemplo:
        >>> datos = DatosSiniestrosRamo(
        ...     ramo=TipoRamo.AUTOS,
        ...     siniestros_ocurridos=Decimal("35000000"),
        ...     siniestros_pagados=Decimal("28000000"),
        ...     reserva_siniestros=Decimal("15000000"),
        ...     numero_siniestros=450,
        ...     numero_siniestros_pendientes=85
        ... )
    """

    ramo: TipoRamo
    siniestros_ocurridos: Decimal = Field(..., ge=0)
    siniestros_pagados: Decimal = Field(..., ge=0)
    reserva_siniestros: Decimal = Field(..., ge=0)
    numero_siniestros: int = Field(..., ge=0)
    numero_siniestros_pendientes: int = Field(..., ge=0)

    @field_validator("numero_siniestros_pendientes")
    @classmethod
    def validar_pendientes(cls, v: int, info) -> int:
        """Siniestros pendientes no pueden exceder total de siniestros"""
        if "numero_siniestros" in info.data:
            if v > info.data["numero_siniestros"]:
                raise ValueError(
                    "Número de siniestros pendientes excede total de siniestros"
                )
        return v


class TipoActivoInversion(str, Enum):
    """Tipos de activos de inversión según clasificación CNSF"""

    VALORES_GUBERNAMENTALES = "valores_gubernamentales"
    VALORES_PRIVADOS = "valores_privados"
    ACCIONES = "acciones"
    INMUEBLES = "inmuebles"
    PRESTAMOS_HIPOTECARIOS = "prestamos_hipotecarios"
    DEPOSITOS = "depositos"
    OTROS = "otros"


class DatosInversionActivo(BaseModel):
    """
    Datos de inversiones por tipo de activo.

    Incluye valor de mercado, valor en libros y rendimiento.

    Ejemplo:
        >>> datos = DatosInversionActivo(
        ...     tipo_activo=TipoActivoInversion.VALORES_GUBERNAMENTALES,
        ...     valor_mercado=Decimal("300000000"),
        ...     valor_libros=Decimal("295000000"),
        ...     rendimiento_trimestre=Decimal("0.015")
        ... )
    """

    tipo_activo: TipoActivoInversion
    valor_mercado: Decimal = Field(..., ge=0)
    valor_libros: Decimal = Field(..., ge=0)
    rendimiento_trimestre: Decimal = Field(..., ge=-1, le=1)  # -100% a +100%

    @property
    def ganancia_no_realizada(self) -> Decimal:
        """Ganancia (o pérdida) no realizada"""
        return self.valor_mercado - self.valor_libros


class DatosReporteRCS(BaseModel):
    """
    Datos del reporte de RCS (Requerimiento de Capital de Solvencia).

    Incluye componentes del RCS y capital disponible.

    Ejemplo:
        >>> datos = DatosReporteRCS(
        ...     rcs_suscripcion_vida=Decimal("18000000"),
        ...     rcs_suscripcion_danos=Decimal("95000000"),
        ...     rcs_inversion=Decimal("62000000"),
        ...     rcs_total=Decimal("125000000"),
        ...     capital_pagado=Decimal("100000000"),
        ...     superavit=Decimal("50000000")
        ... )
    """

    rcs_suscripcion_vida: Decimal = Field(..., ge=0)
    rcs_suscripcion_danos: Decimal = Field(..., ge=0)
    rcs_inversion: Decimal = Field(..., ge=0)
    rcs_operacional: Decimal = Field(default=Decimal("0"), ge=0)
    rcs_total: Decimal = Field(..., gt=0)

    capital_pagado: Decimal = Field(..., gt=0)
    superavit: Decimal = Field(..., ge=0)

    @property
    def capital_disponible(self) -> Decimal:
        """Capital total disponible para cubrir RCS"""
        return self.capital_pagado + self.superavit

    @property
    def ratio_solvencia(self) -> Decimal:
        """Ratio de capital disponible / RCS requerido"""
        return self.capital_disponible / self.rcs_total

    @property
    def cumple_regulacion(self) -> bool:
        """Indica si cumple con el requerimiento mínimo (ratio >= 100%)"""
        return self.ratio_solvencia >= Decimal("1.0")

    @property
    def excedente_deficit(self) -> Decimal:
        """Excedente (positivo) o déficit (negativo) de capital"""
        return self.capital_disponible - self.rcs_total


class ReporteSuscripcion(BaseModel):
    """
    Reporte completo de suscripción trimestral.

    Agrupa datos de todos los ramos con metadatos del reporte.

    Ejemplo:
        >>> reporte = ReporteSuscripcion(
        ...     metadata=metadata,
        ...     datos_por_ramo=[datos_autos, datos_vida, ...]
        ... )
    """

    metadata: MetadatosReporte
    datos_por_ramo: List[DatosSuscripcionRamo]

    @property
    def total_primas_emitidas(self) -> Decimal:
        """Total de primas emitidas en todos los ramos"""
        return sum(d.primas_emitidas for d in self.datos_por_ramo)

    @property
    def total_primas_devengadas(self) -> Decimal:
        """Total de primas devengadas en todos los ramos"""
        return sum(d.primas_devengadas for d in self.datos_por_ramo)

    @property
    def total_suma_asegurada(self) -> Decimal:
        """Total de suma asegurada en todos los ramos"""
        return sum(d.suma_asegurada_total for d in self.datos_por_ramo)


class ReporteSiniestros(BaseModel):
    """
    Reporte completo de siniestros trimestral.

    Agrupa datos de todos los ramos con metadatos del reporte.
    """

    metadata: MetadatosReporte
    datos_por_ramo: List[DatosSiniestrosRamo]

    @property
    def total_siniestros_ocurridos(self) -> Decimal:
        """Total de siniestros ocurridos en todos los ramos"""
        return sum(d.siniestros_ocurridos for d in self.datos_por_ramo)

    @property
    def total_siniestros_pagados(self) -> Decimal:
        """Total de siniestros pagados en todos los ramos"""
        return sum(d.siniestros_pagados for d in self.datos_por_ramo)

    @property
    def total_reservas(self) -> Decimal:
        """Total de reservas de siniestros en todos los ramos"""
        return sum(d.reserva_siniestros for d in self.datos_por_ramo)


class ReporteInversiones(BaseModel):
    """
    Reporte completo de inversiones trimestral.

    Agrupa datos de todos los tipos de activos con metadatos del reporte.
    """

    metadata: MetadatosReporte
    datos_por_activo: List[DatosInversionActivo]

    @property
    def total_valor_mercado(self) -> Decimal:
        """Valor total de mercado de la cartera de inversiones"""
        return sum(d.valor_mercado for d in self.datos_por_activo)

    @property
    def total_valor_libros(self) -> Decimal:
        """Valor total en libros de la cartera de inversiones"""
        return sum(d.valor_libros for d in self.datos_por_activo)

    @property
    def total_ganancia_no_realizada(self) -> Decimal:
        """Total de ganancias (o pérdidas) no realizadas"""
        return sum(d.ganancia_no_realizada for d in self.datos_por_activo)

    def obtener_composicion_pct(self) -> Dict[str, Decimal]:
        """Devuelve composición porcentual por tipo de activo"""
        total = self.total_valor_mercado
        if total == 0:
            return {}

        return {
            d.tipo_activo.value: (d.valor_mercado / total * 100).quantize(
                Decimal("0.01")
            )
            for d in self.datos_por_activo
        }


class ReporteRCS(BaseModel):
    """
    Reporte completo de RCS trimestral.

    Incluye metadatos y datos detallados del RCS.
    """

    metadata: MetadatosReporte
    datos_rcs: DatosReporteRCS
