"""Carga determinista y validacion de perfiles regulatorios revisados."""

import importlib
from datetime import date, datetime

from suite_actuarial.config.schema import ConfigAnual

_CONFIGS: dict[int, ConfigAnual] = {}
_SUPPORTED_YEARS = (2024, 2025, 2026)


class ConfiguracionNoDisponibleError(ModuleNotFoundError):
    """La fecha o el ano solicitado cae fuera de los perfiles empaquetados.

    El paquete solo contiene perfiles con parametros publicados y con fuente.
    Cuando la cobertura se agota no se inventan parametros futuros ni se
    reutiliza en silencio el ultimo perfil: se corta aqui con un error tipado
    que nombra el rango cubierto, para que quien lo atrape pueda decirlo.

    Hereda de ``ModuleNotFoundError`` a proposito: las rutas que ya atrapaban
    ese tipo (CLI, router de config, carga de tablas) siguen funcionando sin
    cambios, y quien necesite distinguir este caso puede atrapar el tipo
    especifico.
    """


def _hoy() -> date:
    """Fecha de hoy del servidor.

    Existe como funcion para que las pruebas puedan sustituirla y ejercitar la
    ruta en la que la fecha por omision cae fuera de la cobertura empaquetada.
    """
    return date.today()


def rango_cobertura() -> tuple[date, date | None]:
    """Devuelve el primer y ultimo dia cubiertos por los perfiles empaquetados.

    Returns:
        Tupla ``(inicio, fin)``. ``fin`` es ``None`` si algun perfil no declara
        ``effective_to``, es decir, si la cobertura esta abierta por la derecha.
    """
    perfiles = _todos_los_perfiles()
    inicio = min(p.effective_from or date(p.anio, 1, 1) for p in perfiles)
    fines = [p.effective_to for p in perfiles if p.effective_to is not None]
    fin = max(fines) if len(fines) == len(perfiles) else None
    return inicio, fin


def _texto_cobertura() -> str:
    """Describe el rango cubierto para incluirlo en los mensajes de error."""
    inicio, fin = rango_cobertura()
    fin_txt = fin.isoformat() if fin is not None else "sin fecha de cierre"
    return f"{inicio.isoformat()} a {fin_txt}"


def _cargar_anio(anio: int) -> ConfigAnual:
    """Carga un modulo anual sin descargar datos de internet."""
    if anio not in _CONFIGS:
        try:
            module = importlib.import_module(f"suite_actuarial.config.config_{anio}")
        except ModuleNotFoundError as err:
            available = sorted(_CONFIGS.keys()) or list(_SUPPORTED_YEARS)
            raise ConfiguracionNoDisponibleError(
                f"No existe configuracion para el ano {anio}. Disponibles: {available}."
            ) from err
        config = module.CONFIG
        if not isinstance(config, ConfigAnual):
            raise TypeError(f"config_{anio}.CONFIG debe ser ConfigAnual")
        _CONFIGS[anio] = config
    return _CONFIGS[anio]


def _todos_los_perfiles() -> list[ConfigAnual]:
    """Carga los perfiles conocidos para comprobar sus periodos."""
    return [_cargar_anio(year) for year in _SUPPORTED_YEARS]


def validar_configuraciones() -> list[str]:
    """Valida fuentes, claves, unidades y periodos de los perfiles empaquetados.

    Returns:
        Lista vacia si no se encontraron problemas.

    Raises:
        ValueError: Si existen periodos solapados, huecos entre perfiles o
            parametros con vigencia fuera de su perfil.
    """
    perfiles = sorted(_todos_los_perfiles(), key=lambda item: item.anio)
    problemas: list[str] = []
    for perfil in perfiles:
        if not perfil.parametros:
            problemas.append(f"{perfil.anio}: no contiene parametros con fuente")
        keys: set[str] = set()
        for parametro in perfil.parametros:
            if parametro.key in keys:
                problemas.append(f"{perfil.anio}: clave duplicada {parametro.key}")
            keys.add(parametro.key)
            if not parametro.unit.strip():
                problemas.append(f"{perfil.anio}: unidad vacia para {parametro.key}")
            if perfil.effective_from and parametro.effective_from < perfil.effective_from:
                problemas.append(f"{perfil.anio}: {parametro.key} inicia antes del perfil")
    for anterior, siguiente in zip(perfiles, perfiles[1:], strict=False):
        inicio_siguiente = siguiente.effective_from or date(siguiente.anio, 1, 1)
        fin_anterior = anterior.effective_to or date.fromordinal(inicio_siguiente.toordinal() - 1)
        if fin_anterior >= inicio_siguiente:
            problemas.append(f"Solapamiento entre perfiles {anterior.anio} y {siguiente.anio}")
        elif date.fromordinal(fin_anterior.toordinal() + 1) < inicio_siguiente:
            problemas.append(f"Hueco entre perfiles {anterior.anio} y {siguiente.anio}")
    if problemas:
        raise ValueError("Configuracion regulatoria invalida: " + "; ".join(problemas))
    return problemas


def cargar_config(anio: int | None = None) -> ConfigAnual:
    """Carga el perfil anual solicitado, o el vigente hoy si ``anio`` es None.

    Con ``anio`` explicito se conserva el contrato v2.0 (perfil de ese año).
    Sin argumento delega en :func:`cargar_config_fecha` con la fecha de hoy,
    de modo que ambas rutas publicas respetan la vigencia de febrero de UMA.
    """
    if anio is None:
        return cargar_config_fecha(_hoy())
    if anio not in _SUPPORTED_YEARS:
        raise ConfiguracionNoDisponibleError(
            f"No existe configuracion oficial para el ano {anio}. "
            f"Disponibles: {list(_SUPPORTED_YEARS)} "
            f"(cobertura {_texto_cobertura()}). "
            f"No se crean perfiles futuros antes de su publicacion."
        )
    return _cargar_anio(anio)


def cargar_config_fecha(fecha: date | datetime | str) -> ConfigAnual:
    """Selecciona el perfil vigente en una fecha, sin llamadas de red.

    Enero conserva el perfil de UMA del año anterior; el perfil del nuevo año
    entra en vigor el 1 de febrero. Las fechas fuera del rango cubierto se
    rechazan con :class:`ConfiguracionNoDisponibleError`, que nombra ese rango.

    Raises:
        TypeError: Si ``fecha`` no es date, datetime ni ISO-8601.
        ConfiguracionNoDisponibleError: Si la fecha cae fuera de la cobertura
            de los perfiles empaquetados.
    """
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    elif isinstance(fecha, str):
        fecha = date.fromisoformat(fecha)
    if not isinstance(fecha, date):
        raise TypeError("fecha debe ser date, datetime o ISO-8601")
    perfiles = sorted(_todos_los_perfiles(), key=lambda item: item.effective_from or date.min)
    # El limite de cobertura se deriva de los perfiles empaquetados, no de una
    # fecha fija: agregar config_<anio+1>.py extiende la cobertura sin tocar
    # este cargador. Un perfil sin effective_to se considera abierto.
    fines = [perfil.effective_to for perfil in perfiles if perfil.effective_to is not None]
    if len(fines) == len(perfiles) and fecha > max(fines):
        raise ConfiguracionNoDisponibleError(
            f"No existe snapshot oficial para {fecha.isoformat()}. "
            f"Cobertura de perfiles empaquetados: {_texto_cobertura()}. "
            f"No se extrapolan parametros regulatorios: agregue "
            f"config/config_<anio>.py cuando se publiquen, o use un perfil "
            f"user_supplied."
        )
    for perfil in reversed(perfiles):
        inicio = perfil.effective_from or date(perfil.anio, 1, 1)
        fin = perfil.effective_to
        if inicio <= fecha and (fin is None or fecha <= fin):
            return perfil
    raise ConfiguracionNoDisponibleError(
        f"No existe snapshot oficial para {fecha.isoformat()}. "
        f"Cobertura de perfiles empaquetados: {_texto_cobertura()}. "
        f"No se extrapolan parametros regulatorios: use un perfil user_supplied."
    )


def config_vigente() -> ConfigAnual:
    """Carga la configuracion vigente para hoy.

    Raises:
        ConfiguracionNoDisponibleError: Si la fecha de hoy ya no esta cubierta
            por ningun perfil empaquetado. El error se propaga a proposito: es
            preferible a devolver el ultimo perfil como si siguiera vigente.
    """
    return cargar_config_fecha(_hoy())
