"""
Calculadoras de pensiones del IMSS.

Implementa los calculos para las dos modalidades principales
del sistema de pensiones mexicano:

- Ley 73 (regimen anterior): pension de beneficio definido
- Ley 97 (regimen actual): pension de contribucion definida

Tambien incluye CalculadoraIMSS como interfaz unificada.

Referencia: Ley del Seguro Social, CONSAR, Circular CONSAR 17-2
"""

from datetime import date
from decimal import Decimal

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.config import cargar_config
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.pensiones.conmutacion import TablaConmutacion
from suite_actuarial.pensiones.tablas_imss import (
    DIAS_AGUINALDO_PENSIONADOS,
    EDAD_CESANTIA,
    EDAD_VEJEZ,
    PENSION_GARANTIZADA_2024,
    SEMANAS_MINIMAS_LEY73,
    obtener_factor_edad,
    obtener_porcentaje_ley73,
)


class PensionLey73:
    """
    Calculator for IMSS Ley 73 (pre-1997) pensions.

    La pension Ley 73 es de beneficio definido: se calcula como un porcentaje
    del salario promedio de las ultimas 250 semanas cotizadas, multiplicado
    por un factor de edad.

    Formula:
        pension_mensual = salario_promedio * porcentaje(semanas) * factor(edad)
    """

    def __init__(
        self,
        semanas_cotizadas: int,
        salario_promedio_5_anos: Decimal | float,
        edad_retiro: int,
        config=None,
    ):
        """
        Args:
            semanas_cotizadas: Total de semanas cotizadas ante el IMSS
            salario_promedio_5_anos: Salario promedio diario de las ultimas
                250 semanas cotizadas (aprox. 5 anos)
            edad_retiro: Edad de retiro (60-65)
            config: ConfigAnual opcional (usa vigente si None)
        """
        if semanas_cotizadas < SEMANAS_MINIMAS_LEY73:
            raise ValueError(
                f"Se requieren al menos {SEMANAS_MINIMAS_LEY73} semanas. "
                f"Se tienen {semanas_cotizadas}."
            )
        if edad_retiro < EDAD_CESANTIA:
            raise ValueError(
                f"Edad minima de retiro: {EDAD_CESANTIA}. "
                f"Edad proporcionada: {edad_retiro}"
            )

        self.semanas_cotizadas = semanas_cotizadas
        self.salario_promedio = Decimal(str(salario_promedio_5_anos))
        self.edad_retiro = edad_retiro
        self.config = config or cargar_config()

        # Lookup table values
        self._porcentaje = obtener_porcentaje_ley73(semanas_cotizadas)
        self._factor_edad = obtener_factor_edad(edad_retiro)

    def calcular_pension_mensual(self) -> Decimal:
        """
        Calcula la pension mensual Ley 73.

        Formula:
            pension = salario_promedio_diario * 30 * porcentaje * factor_edad

        Returns:
            Pension mensual en pesos
        """
        # Salario promedio diario * 30 dias = salario mensual promedio
        salario_mensual = self.salario_promedio * Decimal("30")

        # Aplicar porcentaje por semanas y factor por edad
        pension = salario_mensual * self._porcentaje * self._factor_edad

        return pension.quantize(Decimal("0.01"))

    def calcular_aguinaldo(self) -> Decimal:
        """
        Calcula el aguinaldo anual del pensionado.

        El aguinaldo es equivalente a 30 dias de pension.

        Returns:
            Monto del aguinaldo anual
        """
        pension_diaria = self.calcular_pension_mensual() / Decimal("30")
        aguinaldo = pension_diaria * Decimal(str(DIAS_AGUINALDO_PENSIONADOS))
        return aguinaldo.quantize(Decimal("0.01"))

    def calcular_pension_anual_total(self) -> Decimal:
        """
        Calcula el ingreso anual total incluyendo aguinaldo.

        Returns:
            Pension anual (12 meses + aguinaldo)
        """
        pension_mensual = self.calcular_pension_mensual()
        aguinaldo = self.calcular_aguinaldo()
        return (pension_mensual * Decimal("12") + aguinaldo).quantize(Decimal("0.01"))

    def resumen(self) -> dict:
        """Genera resumen completo del calculo."""
        pension_mensual = self.calcular_pension_mensual()
        return {
            "regimen": "Ley 73",
            "semanas_cotizadas": self.semanas_cotizadas,
            "salario_promedio_diario": self.salario_promedio,
            "edad_retiro": self.edad_retiro,
            "porcentaje_pension": self._porcentaje,
            "factor_edad": self._factor_edad,
            "pension_mensual": pension_mensual,
            "aguinaldo_anual": self.calcular_aguinaldo(),
            "pension_anual_total": self.calcular_pension_anual_total(),
        }

    def __repr__(self) -> str:
        return (
            f"PensionLey73(semanas={self.semanas_cotizadas}, "
            f"edad={self.edad_retiro}, "
            f"pension_mensual=${self.calcular_pension_mensual():,.2f})"
        )


class PensionLey97:
    """
    Calculator for IMSS Ley 97 (post-1997) pensions.

    La pension Ley 97 es de contribucion definida: el saldo acumulado
    en la cuenta individual (AFORE) se usa para comprar una renta
    vitalicia o un retiro programado.

    Modalidades:
    - Renta vitalicia: se compra una anualidad con una aseguradora
    - Retiro programado: se retira periodicamente de la AFORE
    """

    def __init__(
        self,
        saldo_afore: Decimal | float,
        edad: int,
        sexo: Sexo | str,
        semanas_cotizadas: int,
        tabla_mortalidad: TablaMortalidad | None = None,
        tasa_interes: Decimal | float | None = None,
        config=None,
    ):
        """
        Args:
            saldo_afore: Saldo actual de la cuenta AFORE en pesos
            edad: Edad actual del trabajador
            sexo: Sexo del trabajador
            semanas_cotizadas: Total de semanas cotizadas
            tabla_mortalidad: Tabla de mortalidad (default: EMSSA-09)
            tasa_interes: Tasa de interes tecnico (default: config)
            config: ConfigAnual opcional
        """
        if isinstance(sexo, str):
            sexo = Sexo(sexo)

        self.saldo_afore = Decimal(str(saldo_afore))
        self.edad = edad
        self.sexo = sexo
        self.semanas_cotizadas = semanas_cotizadas
        self.config = config or cargar_config()

        # Defaults
        self.tasa_interes = (
            Decimal(str(tasa_interes))
            if tasa_interes is not None
            else self.config.factores_tecnicos.tasa_interes_tecnico_pensiones
        )

        self._tabla_mortalidad = tabla_mortalidad
        self._tabla_conm = None

    def _get_tabla_conmutacion(self) -> TablaConmutacion:
        """Lazy-load commutation table."""
        if self._tabla_conm is None:
            if self._tabla_mortalidad is None:
                self._tabla_mortalidad = TablaMortalidad.cargar_emssa09()
            self._tabla_conm = TablaConmutacion(
                tabla_mortalidad=self._tabla_mortalidad,
                sexo=self.sexo,
                tasa_interes=self.tasa_interes,
            )
        return self._tabla_conm

    def proyectar_saldo_afore(
        self,
        salario_actual: Decimal | float,
        rendimiento_anual: Decimal | float,
        anos_restantes: int,
    ) -> list[dict]:
        """
        Proyecta el saldo de la AFORE ano por ano.

        Args:
            salario_actual: Salario mensual actual
            rendimiento_anual: Rendimiento anual esperado (ej: 0.045 = 4.5% real)
            anos_restantes: Anos hasta el retiro

        Returns:
            Lista de dicts con proyeccion anual
        """
        salario = Decimal(str(salario_actual))
        rendimiento = Decimal(str(rendimiento_anual))
        saldo = self.saldo_afore

        # Tasa total de aportacion a cuenta individual
        # Retiro (2%) + Cesantia patronal (3.15%) + Cesantia obrero (1.125%)
        # + Cuota social (~4.5% promedio) = ~10.775%
        # Simplified: use total contribution rate
        tasa_aportacion = Decimal("0.065")  # ~6.5% of salary to AFORE

        proyeccion = []
        inflacion_anual = Decimal("0.04")  # 4% assumed inflation

        for ano in range(anos_restantes + 1):
            edad_ano = self.edad + ano
            aportacion_anual = salario * Decimal("12") * tasa_aportacion if ano > 0 else Decimal("0")

            if ano > 0:
                rendimiento_periodo = saldo * rendimiento
                saldo = saldo + aportacion_anual + rendimiento_periodo
                salario = salario * (Decimal("1") + inflacion_anual)

            proyeccion.append({
                "ano": ano,
                "edad": edad_ano,
                "salario_mensual": salario.quantize(Decimal("0.01")),
                "aportacion_anual": aportacion_anual.quantize(Decimal("0.01")),
                "saldo_afore": saldo.quantize(Decimal("0.01")),
            })

        return proyeccion

    def calcular_renta_vitalicia(self) -> Decimal:
        """
        Calcula la pension mensual via renta vitalicia.

        Se compra una anualidad vitalicia con el saldo AFORE.
        pension_mensual = saldo_afore / (12 * ax)

        Returns:
            Pension mensual estimada via renta vitalicia
        """
        tc = self._get_tabla_conmutacion()

        # Life annuity factor at retirement age
        if self.edad > tc.edad_max or self.edad < tc.edad_min:
            return Decimal("0")

        ax = tc.ax(self.edad)

        if ax == 0:
            return Decimal("0")

        # Annual pension = saldo / ax
        pension_anual = self.saldo_afore / ax
        pension_mensual = pension_anual / Decimal("12")

        # Apply minimum guarantee
        pension_mensual = max(pension_mensual, self._pension_garantizada())

        return pension_mensual.quantize(Decimal("0.01"))

    def calcular_retiro_programado(
        self,
        esperanza_vida_anos: int | None = None,
    ) -> Decimal:
        """
        Calcula la pension mensual via retiro programado.

        En retiro programado, se divide el saldo entre la esperanza de vida
        del titular y beneficiarios. Se recalcula cada ano.

        Args:
            esperanza_vida_anos: Esperanza de vida en anos (si None, usa tabla)

        Returns:
            Pension mensual estimada via retiro programado (primer ano)
        """
        if esperanza_vida_anos is None:
            # Estimate from mortality table
            tc = self._get_tabla_conmutacion()
            if self.edad > tc.edad_max or self.edad < tc.edad_min:
                return Decimal("0")
            ax = tc.ax(self.edad)
            esperanza_vida_anos = max(1, int(float(ax)))

        if esperanza_vida_anos <= 0:
            return Decimal("0")

        # Annual draw = saldo / esperanza_vida
        retiro_anual = self.saldo_afore / Decimal(str(esperanza_vida_anos))
        pension_mensual = retiro_anual / Decimal("12")

        # Apply minimum guarantee
        pension_mensual = max(pension_mensual, self._pension_garantizada())

        return pension_mensual.quantize(Decimal("0.01"))

    def comparar_modalidades(self) -> dict:
        """
        Compara renta vitalicia vs retiro programado.

        Returns:
            Dict con comparacion detallada de ambas modalidades
        """
        rv = self.calcular_renta_vitalicia()
        rp = self.calcular_retiro_programado()

        # Determine which is better
        if rv > rp:
            recomendacion = "Renta vitalicia"
            diferencia = rv - rp
        elif rp > rv:
            recomendacion = "Retiro programado"
            diferencia = rp - rv
        else:
            recomendacion = "Ambas modalidades son equivalentes"
            diferencia = Decimal("0")

        return {
            "saldo_afore": self.saldo_afore,
            "edad": self.edad,
            "sexo": self.sexo.value,
            "semanas_cotizadas": self.semanas_cotizadas,
            "renta_vitalicia": {
                "pension_mensual": rv,
                "pension_anual": (rv * Decimal("12")).quantize(Decimal("0.01")),
                "tipo": "Garantizada de por vida",
            },
            "retiro_programado": {
                "pension_mensual": rp,
                "pension_anual": (rp * Decimal("12")).quantize(Decimal("0.01")),
                "tipo": "Se recalcula anualmente, puede agotarse",
            },
            "diferencia_mensual": diferencia.quantize(Decimal("0.01")),
            "recomendacion": recomendacion,
            "pension_garantizada": self._pension_garantizada(),
        }

    def _pension_garantizada(self) -> Decimal:
        """Returns the minimum guaranteed pension based on current config."""
        return PENSION_GARANTIZADA_2024

    def __repr__(self) -> str:
        return (
            f"PensionLey97(saldo=${self.saldo_afore:,.2f}, "
            f"edad={self.edad}, sexo={self.sexo.value}, "
            f"semanas={self.semanas_cotizadas})"
        )


class CalculadoraIMSS:
    """
    Calculadora unificada de pensiones IMSS.

    Determina automaticamente el regimen aplicable (Ley 73 o 97)
    y calcula la pension optima.
    """

    # Fecha de transicion: 1 de julio de 1997
    FECHA_TRANSICION = date(1997, 7, 1)

    def determinar_regimen(self, fecha_inscripcion_imss: date | str) -> str:
        """
        Determina el regimen de pension aplicable.

        - Inscritos antes del 1 de julio de 1997: Ley 73
        - Inscritos a partir del 1 de julio de 1997: Ley 97

        Los trabajadores Ley 73 pueden ELEGIR pensionarse bajo Ley 73 o 97.
        Generalmente conviene Ley 73 si tienen buen salario promedio.

        Args:
            fecha_inscripcion_imss: Fecha de primera inscripcion al IMSS

        Returns:
            "Ley 73" o "Ley 97"
        """
        if isinstance(fecha_inscripcion_imss, str):
            fecha_inscripcion_imss = date.fromisoformat(fecha_inscripcion_imss)

        if fecha_inscripcion_imss < self.FECHA_TRANSICION:
            return "Ley 73"
        else:
            return "Ley 97"

    def pension_optima(
        self,
        fecha_inscripcion_imss: date | str,
        semanas_cotizadas: int,
        edad_retiro: int,
        salario_promedio_diario: Decimal | float | None = None,
        saldo_afore: Decimal | float | None = None,
        sexo: Sexo | str = "H",
        tabla_mortalidad: TablaMortalidad | None = None,
        config=None,
    ) -> dict:
        """
        Calcula la pension optima para los parametros dados.

        Para trabajadores Ley 73, compara ambos regimenes y sugiere el mejor.
        Para trabajadores Ley 97, calcula ambas modalidades.

        Args:
            fecha_inscripcion_imss: Fecha de inscripcion al IMSS
            semanas_cotizadas: Total de semanas cotizadas
            edad_retiro: Edad de retiro deseada
            salario_promedio_diario: Salario promedio diario (ultimas 250 semanas)
            saldo_afore: Saldo acumulado en AFORE
            sexo: Sexo del trabajador
            tabla_mortalidad: Tabla de mortalidad (opcional)
            config: ConfigAnual (opcional)

        Returns:
            Dict con pension optima y comparacion
        """
        regimen = self.determinar_regimen(fecha_inscripcion_imss)
        resultado = {
            "regimen_aplicable": regimen,
            "fecha_inscripcion": str(fecha_inscripcion_imss),
            "semanas_cotizadas": semanas_cotizadas,
            "edad_retiro": edad_retiro,
        }

        pension_ley73 = None
        pension_ley97 = None

        # Calculate Ley 73 if applicable and data available
        if regimen == "Ley 73" and salario_promedio_diario is not None:
            if semanas_cotizadas >= SEMANAS_MINIMAS_LEY73 and edad_retiro >= EDAD_CESANTIA:
                calc73 = PensionLey73(
                    semanas_cotizadas=semanas_cotizadas,
                    salario_promedio_5_anos=salario_promedio_diario,
                    edad_retiro=edad_retiro,
                    config=config,
                )
                pension_ley73 = calc73.calcular_pension_mensual()
                resultado["ley_73"] = calc73.resumen()

        # Calculate Ley 97 if AFORE data available
        if saldo_afore is not None:
            calc97 = PensionLey97(
                saldo_afore=saldo_afore,
                edad=edad_retiro,
                sexo=sexo,
                semanas_cotizadas=semanas_cotizadas,
                tabla_mortalidad=tabla_mortalidad,
                config=config,
            )
            pension_ley97_rv = calc97.calcular_renta_vitalicia()
            pension_ley97_rp = calc97.calcular_retiro_programado()
            pension_ley97 = max(pension_ley97_rv, pension_ley97_rp)
            resultado["ley_97"] = calc97.comparar_modalidades()

        # Determine optimal
        if pension_ley73 is not None and pension_ley97 is not None:
            if pension_ley73 >= pension_ley97:
                resultado["pension_optima"] = pension_ley73
                resultado["regimen_recomendado"] = "Ley 73"
            else:
                resultado["pension_optima"] = pension_ley97
                resultado["regimen_recomendado"] = "Ley 97"
        elif pension_ley73 is not None:
            resultado["pension_optima"] = pension_ley73
            resultado["regimen_recomendado"] = "Ley 73"
        elif pension_ley97 is not None:
            resultado["pension_optima"] = pension_ley97
            resultado["regimen_recomendado"] = "Ley 97"
        else:
            resultado["pension_optima"] = Decimal("0")
            resultado["regimen_recomendado"] = "Datos insuficientes"

        return resultado

    def __repr__(self) -> str:
        return "CalculadoraIMSS()"
