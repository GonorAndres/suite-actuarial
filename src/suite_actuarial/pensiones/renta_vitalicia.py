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
    """

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

        Returns:
            Factor de renta actuarial
        """
        tc = self._tabla_conm
        x = self.edad
        n_dif = self.periodo_diferimiento
        n_gar = self.periodo_garantizado

        # Base age for annuity payments (after deferral)
        x_pago = x + n_dif

        if n_gar > 0:
            # Annuity with guaranteed period:
            # Factor = annuity-certain for n_gar years + deferred life annuity
            # a_certain:n = (1 - v^n) / d  where d = i/(1+i)
            v = Decimal("1") / (Decimal("1") + self.tasa_interes)
            d = self.tasa_interes / (Decimal("1") + self.tasa_interes)

            # Annuity-certain for guaranteed period (discounted from payment start)
            v_n_gar = v ** n_gar
            a_cierta = (Decimal("1") - v_n_gar) / d if d > 0 else Decimal(str(n_gar))

            # Deferred life annuity starting after guarantee period
            # This is the expected value of payments AFTER the guarantee period,
            # conditional on survival
            edad_post_garantia = x_pago + n_gar
            if edad_post_garantia <= tc.edad_max:
                dx_pago = tc.Dx(x_pago)
                if dx_pago > 0:
                    # Life annuity value at age x_pago for payments starting at x_pago + n_gar
                    a_vida_diferida = tc.Nx(edad_post_garantia) / dx_pago
                else:
                    a_vida_diferida = Decimal("0")
            else:
                a_vida_diferida = Decimal("0")

            factor_at_payment_start = a_cierta + a_vida_diferida

        else:
            # No guaranteed period: simple life annuity at payment age
            if x_pago > tc.edad_max:
                return Decimal("0")
            factor_at_payment_start = tc.ax(x_pago)

        # If deferred, discount back to current age
        if n_dif > 0:
            nEx = tc.nEx(x, n_dif)
            return factor_at_payment_start * nEx
        else:
            return factor_at_payment_start

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

            # Deferred annuity factor from age x+t
            nEx_remaining = tc.nEx(edad_actual, n_dif - t)

            if n_gar > 0:
                # Need to compute the factor at payment start
                v = Decimal("1") / (Decimal("1") + self.tasa_interes)
                d = self.tasa_interes / (Decimal("1") + self.tasa_interes)
                v_n_gar = v ** n_gar
                a_cierta = (Decimal("1") - v_n_gar) / d if d > 0 else Decimal(str(n_gar))

                edad_post_garantia = x_pago + n_gar
                if edad_post_garantia <= tc.edad_max:
                    dx_pago = tc.Dx(x_pago)
                    if dx_pago > 0:
                        a_vida_diferida = tc.Nx(edad_post_garantia) / dx_pago
                    else:
                        a_vida_diferida = Decimal("0")
                else:
                    a_vida_diferida = Decimal("0")

                factor_pago = a_cierta + a_vida_diferida
            else:
                factor_pago = tc.ax(x_pago)

            return self.monto_anual * factor_pago * nEx_remaining

        else:
            # Already receiving payments
            anos_pagando = t - n_dif

            if n_gar > 0 and anos_pagando < n_gar:
                # Still within guarantee period
                anos_garantia_restantes = n_gar - anos_pagando
                v = Decimal("1") / (Decimal("1") + self.tasa_interes)
                d = self.tasa_interes / (Decimal("1") + self.tasa_interes)
                v_n = v ** anos_garantia_restantes
                a_cierta = (Decimal("1") - v_n) / d if d > 0 else Decimal(str(anos_garantia_restantes))

                edad_post_garantia = edad_actual + anos_garantia_restantes
                if edad_post_garantia <= tc.edad_max:
                    dx_actual = tc.Dx(edad_actual)
                    if dx_actual > 0:
                        a_vida_diferida = tc.Nx(edad_post_garantia) / dx_actual
                    else:
                        a_vida_diferida = Decimal("0")
                else:
                    a_vida_diferida = Decimal("0")

                factor = a_cierta + a_vida_diferida
            else:
                # Past guarantee period (or no guarantee): pure life annuity
                factor = tc.ax(edad_actual)

            return self.monto_anual * factor

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

            resultados.append({
                "ano": t,
                "edad": edad_actual,
                "pago_anual": pago_anual,
                "prob_supervivencia": prob_supervivencia,
                "pago_esperado": pago_esperado,
                "en_diferimiento": en_diferimiento,
                "en_garantia": en_garantia,
                "reserva": reserva,
            })

            # Update survival probability for next year
            try:
                qx = self.tabla_mortalidad.obtener_qx(edad_actual, self.sexo)
                prob_supervivencia *= (Decimal("1") - qx)
            except (ValueError, KeyError):
                break

        return resultados

    def __repr__(self) -> str:
        tipo = "inmediata" if self.periodo_diferimiento == 0 else f"diferida {self.periodo_diferimiento} anos"
        gar = f", garantia {self.periodo_garantizado} anos" if self.periodo_garantizado > 0 else ""
        return (
            f"RentaVitalicia(edad={self.edad}, sexo={self.sexo.value}, "
            f"monto_mensual=${self.monto_mensual:,.2f}, tipo={tipo}{gar})"
        )
