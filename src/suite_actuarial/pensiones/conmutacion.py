"""
Tabla de conmutacion actuarial (commutation functions).

Estas funciones clasicas simplifican el calculo de primas y reservas
de seguros de vida y pensiones. Son la base de toda la matematica
actuarial de beneficios definidos.

Referencia: Bowers, Gerber, Hickman, Jones, Nesbitt -- "Actuarial Mathematics"
"""

from decimal import Decimal

import numpy as np

from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
from suite_actuarial.core.models.common import Sexo, normalizar_sexo


class TablaConmutacion:
    """
    Tabla de conmutacion actuarial (commutation functions).

    Construye Dx, Nx, Sx, Cx, Mx, Rx a partir de una tabla de mortalidad
    y una tasa de interes. Estas funciones simplifican enormemente el
    calculo de primas y reservas de seguros de vida y pensiones.

    Formulas clasicas (Bowers et al.):
    - Dx = lx * v^x         (factor de descuento por sobrevivencia)
    - Nx = sum(Dx, x..omega) (acumulado de Dx)
    - Sx = sum(Nx, x..omega) (acumulado de Nx)
    - Cx = dx * v^(x+1)     (factor de descuento por mortalidad)
    - Mx = sum(Cx, x..omega) (acumulado de Cx)
    - Rx = sum(Mx, x..omega) (acumulado de Mx)

    Where:
    - lx = survivors to age x (from mortality table)
    - dx = lx - l(x+1) = deaths between age x and x+1
    - v = 1/(1+i) = discount factor
    - omega = limiting age
    """

    def __init__(
        self,
        tabla_mortalidad: TablaMortalidad,
        sexo: Sexo | str,
        tasa_interes: Decimal | float,
        raiz: int = 100_000,
    ):
        """
        Construye la tabla de conmutacion completa.

        Args:
            tabla_mortalidad: TablaMortalidad instance
            sexo: Sexo enum or str ("masculino"/"femenino")
            tasa_interes: Decimal or float, e.g. 0.05 for 5%
            raiz: lx starting value (default 100,000)
        """
        sexo = normalizar_sexo(sexo)
        self.sexo = sexo

        # Mismo rango que `ConfiguracionProducto.tasa_interes_tecnico`, que ya
        # lo acotaba en la rama de vida. Aqui no habia cota alguna y `v` se
        # calculaba directo como 1/(1+i): con i = -1 reventaba con
        # ZeroDivisionError, y con i < -1 el factor de descuento se volvia
        # negativo y `ax` devolvia una anualidad negativa, que es
        # actuarialmente imposible. Como `RentaVitalicia` y `PensionLey97`
        # construyen esta clase, validar aqui cubre las tres.
        tasa = Decimal(str(tasa_interes))
        if tasa < 0:
            raise ValueError(f"La tasa de interes no puede ser negativa; se recibio {tasa}.")
        if tasa > Decimal("0.15"):
            raise ValueError(
                f"Tasa de interes muy alta (tipicamente max 15% anual); se recibio {tasa}."
            )

        self.tasa_interes = float(tasa_interes)
        self.raiz = raiz
        self.tabla_mortalidad = tabla_mortalidad

        # Calculate lx from mortality table
        df_vida = tabla_mortalidad.calcular_lx(sexo, raiz=raiz)
        df_vida = df_vida.sort_values("edad").reset_index(drop=True)

        self._edades = df_vida["edad"].values.astype(int)
        self._edad_min = int(self._edades[0])
        self._edad_max = int(self._edades[-1])
        self._n = len(self._edades)

        # Extract lx and dx as float arrays for numpy operations
        lx = df_vida["lx"].values.astype(float)
        dx = df_vida["dx"].values.astype(float)
        self._lx = lx

        # Discount factor
        v = 1.0 / (1.0 + self.tasa_interes)

        # Build commutation columns
        ages_float = self._edades.astype(float)

        # Dx = lx * v^x
        self._Dx = lx * np.power(v, ages_float)

        # Cx = dx * v^(x+1)
        self._Cx = dx * np.power(v, ages_float + 1.0)

        # Nx = sum(Dx from x to omega) -- cumulative sum from the end
        self._Nx = np.cumsum(self._Dx[::-1])[::-1].copy()

        # Sx = sum(Nx from x to omega)
        self._Sx = np.cumsum(self._Nx[::-1])[::-1].copy()

        # Mx = sum(Cx from x to omega)
        self._Mx = np.cumsum(self._Cx[::-1])[::-1].copy()

        # Rx = sum(Mx from x to omega)
        self._Rx = np.cumsum(self._Mx[::-1])[::-1].copy()

    def _idx(self, x: int) -> int:
        """Convert age x to array index. Raises ValueError if out of range."""
        if x < self._edad_min or x > self._edad_max:
            raise ValueError(
                f"Edad {x} fuera del rango de la tabla [{self._edad_min}, {self._edad_max}]"
            )
        return x - self._edad_min

    # ------------------------------------------------------------------
    # Core commutation accessors
    # ------------------------------------------------------------------

    def Dx(self, x: int) -> Decimal:
        """Factor de descuento por sobrevivencia: Dx = lx * v^x"""
        return Decimal(str(self._Dx[self._idx(x)]))

    def Nx(self, x: int) -> Decimal:
        """Acumulado de Dx: Nx = sum(Dk, k=x..omega)"""
        return Decimal(str(self._Nx[self._idx(x)]))

    def Sx(self, x: int) -> Decimal:
        """Acumulado de Nx: Sx = sum(Nk, k=x..omega)"""
        return Decimal(str(self._Sx[self._idx(x)]))

    def Cx(self, x: int) -> Decimal:
        """Factor de descuento por mortalidad: Cx = dx * v^(x+1)"""
        return Decimal(str(self._Cx[self._idx(x)]))

    def Mx(self, x: int) -> Decimal:
        """Acumulado de Cx: Mx = sum(Ck, k=x..omega)"""
        return Decimal(str(self._Mx[self._idx(x)]))

    def Rx(self, x: int) -> Decimal:
        """Acumulado de Mx: Rx = sum(Mk, k=x..omega)"""
        return Decimal(str(self._Rx[self._idx(x)]))

    # ------------------------------------------------------------------
    # Derived actuarial values
    # ------------------------------------------------------------------

    def lx(self, x: int) -> Decimal:
        """Sobrevivientes a la edad x, con raiz `self.raiz`."""
        return Decimal(str(self._lx[self._idx(x)]))

    def ex(self, x: int) -> Decimal:
        """Esperanza de vida abreviada (curtate): anos completos por vivir.

            e_x = sum_{t>=1} t_p_x = sum_{t>=1} l_{x+t} / l_x

        No lleva descuento financiero: cuenta anos, no valor presente. Es la
        cantidad que corresponde cuando hay que repartir un saldo entre los
        anos que se espera vivir, distinta de la anualidad `ax`, que descuenta
        cada pago por interes y por tanto es menor. Confundirlas fue el
        hallazgo A5 de `docs/AUDIT.md`.

        La suma se trunca en la edad terminal de la tabla, asi que la
        esperanza queda acotada por el alcance de la tabla, no por la vida.

        Args:
            x: Edad

        Returns:
            Esperanza de vida abreviada, en anos
        """
        idx = self._idx(x)
        l_x = self._lx[idx]
        if l_x <= 0:
            return Decimal("0")

        posteriores = self._lx[idx + 1 :]
        return Decimal(str(float(posteriores.sum() / l_x)))

    def ax(self, x: int, n: int | None = None) -> Decimal:
        """
        Anualidad vitalicia anticipada o temporal anticipada.

        - Vitalicia: ax = Nx / Dx
        - Temporal:  ax:n = (Nx - N(x+n)) / Dx

        Args:
            x: Edad
            n: Plazo (None para vitalicia)

        Returns:
            Valor actuarial de la anualidad
        """
        dx_val = self.Dx(x)
        if dx_val == 0:
            return Decimal("0")

        if n is None:
            return self.Nx(x) / dx_val
        else:
            if n <= 0:
                return Decimal("0")
            x_n = x + n
            if x_n > self._edad_max:
                # If x+n exceeds omega, treat as whole-life from x
                return self.Nx(x) / dx_val
            return (self.Nx(x) - self.Nx(x_n)) / dx_val

    @staticmethod
    def ajuste_fraccionamiento(m: int = 12) -> Decimal:
        """Correccion 1/m de una anualidad anticipada pagadera m veces al ano.

            a_x^(m) ~= a_x - (m - 1) / (2m)

        Para m = 12 el ajuste es 11/24 ~= 0.4583. Es el primer termino de la
        formula de Woolhouse: una anualidad anual anticipada paga todo el ano
        al principio, mientras que la mensual reparte los pagos a lo largo del
        ano, en promedio medio periodo mas tarde. Ignorarlo sobreestima el
        valor presente de una pension mensual.

        Args:
            m: Pagos por ano (12 = mensual)

        Returns:
            Termino a restar del factor anual
        """
        if m < 1:
            raise ValueError("El numero de pagos por ano debe ser al menos 1")
        return Decimal(m - 1) / (Decimal(2) * Decimal(m))

    def ax_m(self, x: int, m: int = 12, n: int | None = None) -> Decimal:
        """Anualidad anticipada pagadera m veces al ano.

        - Vitalicia:  a_x^(m) ~= a_x - (m-1)/(2m)
        - Temporal:   a_{x:n}^(m) ~= a_{x:n} - (m-1)/(2m) * (1 - nEx)

        El termino de la temporal se pondera por `1 - nEx` porque la
        correccion aplica al primer pago de cada ano efectivamente pagado; al
        final del plazo no hay pago que corregir.

        Limite declarado: es la aproximacion de primer orden. Woolhouse tiene
        un segundo termino, `-(m^2-1)/(12m^2) * (delta + mu_x)`, que este
        modulo no incluye; su efecto es de segundo orden frente al 11/24.

        Args:
            x: Edad
            m: Pagos por ano (12 = mensual)
            n: Plazo (None para vitalicia)

        Returns:
            Valor actuarial de la anualidad fraccionada
        """
        factor_anual = self.ax(x, n)
        if factor_anual == 0:
            return Decimal("0")

        ajuste = self.ajuste_fraccionamiento(m)
        if n is None:
            return factor_anual - ajuste

        peso = Decimal("1") - self.nEx(x, n)
        return factor_anual - ajuste * peso

    def Ax(self, x: int, n: int | None = None) -> Decimal:
        """
        Seguro de vida completo o temporal.

        - Completo:  Ax = Mx / Dx
        - Temporal:  Ax:n = (Mx - M(x+n)) / Dx

        Args:
            x: Edad
            n: Plazo (None para vida entera)

        Returns:
            Valor actuarial del seguro
        """
        dx_val = self.Dx(x)
        if dx_val == 0:
            return Decimal("0")

        if n is None:
            return self.Mx(x) / dx_val
        else:
            if n <= 0:
                return Decimal("0")
            x_n = x + n
            if x_n > self._edad_max:
                return self.Mx(x) / dx_val
            return (self.Mx(x) - self.Mx(x_n)) / dx_val

    def nEx(self, x: int, n: int) -> Decimal:
        """
        Dotal puro (pure endowment).

        nEx = D(x+n) / Dx

        Probabilidad de sobrevivir n anos descontada a valor presente.

        Args:
            x: Edad
            n: Plazo

        Returns:
            Factor de dotal puro
        """
        dx_val = self.Dx(x)
        if dx_val == 0:
            return Decimal("0")
        x_n = x + n
        if x_n > self._edad_max:
            return Decimal("0")
        return self.Dx(x_n) / dx_val

    def Px(self, x: int, n: int | None = None) -> Decimal:
        """
        Prima nivelada (net level premium).

        Px = Ax / ax

        Args:
            x: Edad
            n: Plazo (None para vida entera)

        Returns:
            Prima nivelada por unidad de suma asegurada
        """
        ax_val = self.ax(x, n)
        if ax_val == 0:
            return Decimal("0")
        return self.Ax(x, n) / ax_val

    def tVx(self, x: int, n: int, t: int) -> Decimal:
        """
        Reserva prospectiva al tiempo t para un seguro temporal.

        tVx = A(x+t):n-t - P * a(x+t):n-t

        Donde P es la prima nivelada original calculada a la edad x.

        Args:
            x: Edad original de emision
            n: Plazo original del seguro
            t: Tiempo transcurrido (anos de poliza)

        Returns:
            Reserva matematica al tiempo t

        Raises:
            ValueError: Si t esta fuera de rango
        """
        if t < 0 or t > n:
            raise ValueError(f"Tiempo t={t} fuera de rango [0, {n}]")
        if t == 0 or t == n:
            return Decimal("0")

        # Prima nivelada original
        prima = self.Px(x, n)

        # Valores actuariales al tiempo t
        plazo_restante = n - t
        edad_actual = x + t

        ax_futuro = self.ax(edad_actual, plazo_restante)
        Ax_futuro = self.Ax(edad_actual, plazo_restante)

        return Ax_futuro - prima * ax_futuro

    @property
    def edad_min(self) -> int:
        """Edad minima de la tabla."""
        return self._edad_min

    @property
    def edad_max(self) -> int:
        """Edad maxima (omega) de la tabla."""
        return self._edad_max

    def __repr__(self) -> str:
        return (
            f"TablaConmutacion(tabla={self.tabla_mortalidad.nombre}, "
            f"sexo={self.sexo.value}, i={self.tasa_interes}, "
            f"edades=[{self._edad_min}, {self._edad_max}])"
        )
