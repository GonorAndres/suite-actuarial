"""
Calculadora de rentas vitalicias (life annuities).

Soporta multiples modalidades de rentas vitalicias usadas en el sistema
de pensiones mexicano y en productos de seguros de vida:

- Inmediata: pagos comienzan de inmediato
- Diferida: pagos comienzan despues de n anos
- Con periodo cierto: garantiza pagos por al menos n anos
- Conjunta: para matrimonios (joint-life) -- placeholder

Referencia: Bowers et al., Ley del Seguro Social, CONSAR
"""

from decimal import Decimal

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.pensiones.conmutacion import TablaConmutacion


class RentaVitalicia:
    """
    Calculadora de rentas vitalicias (life annuities).

    Soporta:
    - Inmediata: pagos comienzan de inmediato
    - Diferida: pagos comienzan despues de n anos
    - Con periodo cierto: garantiza pagos por al menos n anos

    Los pagos son mensuales, asi que la valuacion lleva la correccion 1/m
    (`a_x^(12) ~= a_x - 11/24`). Ver `calcular_factor_renta`.
    """

    #: Pagos por ano. La renta es mensual, y de ahi la correccion 1/m.
    PAGOS_POR_ANIO = 12

    def __init__(
        self,
        edad: int,
        sexo: Sexo | str,
        monto_mensual: Decimal | float,
        tabla_mortalidad: TablaMortalidad,
        tasa_interes: Decimal | float,
        periodo_diferimiento: int = 0,
        periodo_garantizado: int = 0,
    ):
        """
        Inicializa la calculadora de renta vitalicia.

        Args:
            edad: Edad actual del rentista
            sexo: Sexo del rentista
            monto_mensual: Monto mensual de la renta en pesos
            tabla_mortalidad: Tabla de mortalidad a usar
            tasa_interes: Tasa de interes tecnico anual
            periodo_diferimiento: Anos de diferimiento (0 = inmediata)
            periodo_garantizado: Anos de pago garantizado minimo (0 = sin garantia)
        """
        if isinstance(sexo, str):
            sexo = Sexo(sexo)

        self.edad = edad
        self.sexo = sexo
        self.monto_mensual = Decimal(str(monto_mensual))
        self.monto_anual = self.monto_mensual * Decimal("12")
        self.tasa_interes = Decimal(str(tasa_interes))
        self.periodo_diferimiento = periodo_diferimiento
        self.periodo_garantizado = periodo_garantizado
        self.tabla_mortalidad = tabla_mortalidad

        # Build commutation table
        self._tabla_conm = TablaConmutacion(
            tabla_mortalidad=tabla_mortalidad,
            sexo=sexo,
            tasa_interes=tasa_interes,
        )

    def calcular_factor_renta(self) -> Decimal:
        """
        Factor de renta (valor actuarial de la anualidad).

        Combina las tres modalidades:
        - Inmediata: ax (whole-life annuity at current age)
        - Diferida: n|ax = N(x+n) / Dx
        - Con periodo cierto: annuity-certain + deferred life annuity

        El factor corresponde a una renta **mensual**, asi que lleva la
        correccion 1/m: `a_x^(12) ~= a_x - 11/24`. La version anterior valuaba
        pagos mensuales con la anualidad anual, lo que sobreestimaba la prima
        unica en ~3.9% y subestimaba la pension mensual en la misma proporcion
        (hallazgo A6 de `docs/AUDIT.md`).

        La correccion se aplica a cada pierna que representa pagos: la
        anualidad cierta se corrige por `1 - v^n`, y la vitalicia diferida por
        el valor de un peso al inicio de sus pagos.

        Returns:
            Factor de renta actuarial, en unidades de renta anual
        """
        tc = self._tabla_conm
        n_dif = self.periodo_diferimiento

        factor_at_payment_start = self._factor_en_inicio_de_pagos(
            self.edad + n_dif, self.periodo_garantizado
        )

        # If deferred, discount back to current age
        if n_dif > 0:
            return factor_at_payment_start * tc.nEx(self.edad, n_dif)
        return factor_at_payment_start

    def _factor_en_inicio_de_pagos(self, edad_pago: int, anos_garantia: int) -> Decimal:
        """Factor de renta mensual valuado a la edad en que empiezan los pagos.

        Es la unica definicion del factor en este modulo: la usan tanto el
        calculo de la prima como el de la reserva. Estaban duplicadas, y la
        duplicacion se separo al corregir A6 — la reserva en t=0 dejo de
        coincidir con la prima unica, que es una identidad obligatoria.

        Args:
            edad_pago: Edad a la que arrancan los pagos
            anos_garantia: Anos de pago garantizado (0 = sin garantia)

        Returns:
            Factor de renta, en unidades de renta anual
        """
        tc = self._tabla_conm
        if edad_pago > tc.edad_max:
            return Decimal("0")

        ajuste = tc.ajuste_fraccionamiento(self.PAGOS_POR_ANIO)

        if anos_garantia <= 0:
            # Sin garantia: anualidad vitalicia fraccionada.
            return tc.ax_m(edad_pago, m=self.PAGOS_POR_ANIO)

        # Con garantia: anualidad cierta + vitalicia diferida al fin de la
        # garantia. a_cierta:n = (1 - v^n) / d, con d = i/(1+i).
        v = Decimal("1") / (Decimal("1") + self.tasa_interes)
        d = self.tasa_interes / (Decimal("1") + self.tasa_interes)
        v_n = v**anos_garantia
        a_cierta = (Decimal("1") - v_n) / d if d > 0 else Decimal(str(anos_garantia))
        # Correccion 1/m de la anualidad cierta: solo sobre los anos que
        # efectivamente se pagan, de ahi el peso (1 - v^n).
        a_cierta = a_cierta - ajuste * (Decimal("1") - v_n)

        edad_post_garantia = edad_pago + anos_garantia
        a_vida_diferida = Decimal("0")
        if edad_post_garantia <= tc.edad_max:
            dx_pago = tc.Dx(edad_pago)
            if dx_pago > 0:
                # Correccion 1/m ponderada por el valor de un peso al inicio
                # de los pagos diferidos: D(x+n)/D(x).
                a_vida_diferida = (
                    tc.Nx(edad_post_garantia) - ajuste * tc.Dx(edad_post_garantia)
                ) / dx_pago

        return a_cierta + a_vida_diferida

    def calcular_prima_unica(self) -> Decimal:
        """
        Prima unica (single premium) para comprar la renta.

        Prima = monto_anual * factor_de_renta

        Returns:
            Monto unico necesario para fondear la renta vitalicia
        """
        factor = self.calcular_factor_renta()
        return self.monto_anual * factor

    def calcular_reserva_matematica(self, t: int) -> Decimal:
        """
        Reserva matematica al tiempo t.

        Para una renta vitalicia inmediata, la reserva al tiempo t es
        el valor presente de los pagos futuros para un rentista de edad x+t.

        Para una diferida, antes del inicio de pagos es el valor actuarial
        futuro descontado; despues del inicio es como la inmediata.

        Args:
            t: Anos transcurridos desde la compra

        Returns:
            Reserva matematica al tiempo t
        """
        if t < 0:
            raise ValueError(f"Tiempo t={t} no puede ser negativo")

        tc = self._tabla_conm
        x = self.edad
        edad_actual = x + t

        if edad_actual > tc.edad_max:
            return Decimal("0")

        n_dif = self.periodo_diferimiento
        n_gar = self.periodo_garantizado

        if t < n_dif:
            # Still in deferral period: reserve = PV of future annuity
            # from current age (x+t) with remaining deferral (n_dif - t)
            x_pago = x + n_dif
            if x_pago > tc.edad_max:
                return Decimal("0")

            factor_pago = self._factor_en_inicio_de_pagos(x_pago, n_gar)
            return self.monto_anual * factor_pago * tc.nEx(edad_actual, n_dif - t)

        # Already receiving payments. La garantia remanente se agota conforme
        # avanzan los pagos; pasada esa fecha queda una vitalicia pura.
        anos_pagando = t - n_dif
        garantia_restante = max(0, n_gar - anos_pagando)

        return self.monto_anual * self._factor_en_inicio_de_pagos(edad_actual, garantia_restante)

    def tabla_pagos(self, anos: int = 30) -> list[dict]:
        """
        Genera tabla de pagos proyectados con probabilidades de supervivencia.

        Args:
            anos: Numero de anos a proyectar

        Returns:
            Lista de dicts con: ano, edad, pago_anual, prob_supervivencia,
            pago_esperado, reserva
        """
        tc = self._tabla_conm
        resultados = []

        # tpx: cumulative survival probability from initial age
        prob_supervivencia = Decimal("1")

        for t in range(anos):
            edad_actual = self.edad + t
            if edad_actual > tc.edad_max:
                break

            # Determine if payment is made this year
            en_diferimiento = t < self.periodo_diferimiento
            pago_anual = Decimal("0") if en_diferimiento else self.monto_anual

            pago_esperado = pago_anual * prob_supervivencia

            # If within guaranteed period (after deferral), pago is certain
            anos_pagando = max(0, t - self.periodo_diferimiento)
            en_garantia = (
                not en_diferimiento
                and self.periodo_garantizado > 0
                and anos_pagando < self.periodo_garantizado
            )

            if en_garantia:
                pago_esperado = pago_anual  # guaranteed regardless of survival

            # Calculate reserve
            try:
                reserva = self.calcular_reserva_matematica(t)
            except (ValueError, ZeroDivisionError):
                reserva = Decimal("0")

            resultados.append(
                {
                    "ano": t,
                    "edad": edad_actual,
                    "pago_anual": pago_anual,
                    "prob_supervivencia": prob_supervivencia,
                    "pago_esperado": pago_esperado,
                    "en_diferimiento": en_diferimiento,
                    "en_garantia": en_garantia,
                    "reserva": reserva,
                }
            )

            # Update survival probability for next year
            try:
                qx = self.tabla_mortalidad.obtener_qx(edad_actual, self.sexo)
                prob_supervivencia *= Decimal("1") - qx
            except (ValueError, KeyError):
                break

        return resultados

    def __repr__(self) -> str:
        tipo = (
            "inmediata"
            if self.periodo_diferimiento == 0
            else f"diferida {self.periodo_diferimiento} anos"
        )
        gar = f", garantia {self.periodo_garantizado} anos" if self.periodo_garantizado > 0 else ""
        return (
            f"RentaVitalicia(edad={self.edad}, sexo={self.sexo.value}, "
            f"monto_mensual=${self.monto_mensual:,.2f}, tipo={tipo}{gar})"
        )
