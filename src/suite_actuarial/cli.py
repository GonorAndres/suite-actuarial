"""
CLI para suite_actuarial

Comando de línea para usar la librería desde terminal.
"""

import sys
from decimal import Decimal

from suite_actuarial import __version__


def main() -> int:
    """
    Punto de entrada principal del CLI.

    Returns:
        Exit code (0 = éxito, 1 = error)
    """
    print(f"Mexican Insurance Analytics Suite v{__version__}")
    print("=" * 60)

    if len(sys.argv) < 2:
        mostrar_ayuda()
        return 0

    comando = sys.argv[1]

    if comando in ["--help", "-h", "help"]:
        mostrar_ayuda()
        return 0

    if comando in ["--version", "-v", "version"]:
        print(f"Versión: {__version__}")
        return 0

    if comando == "demo":
        ejecutar_demo()
        return 0

    if comando == "api":
        ejecutar_api()
        return 0

    print(f"Comando desconocido: {comando}")
    print("Usa 'seguros --help' para ver los comandos disponibles.")
    return 1


def mostrar_ayuda() -> None:
    """Muestra la ayuda del CLI"""
    ayuda = """
Uso: seguros [comando] [opciones]

Comandos disponibles:
  demo              Ejecuta un ejemplo de calculo de primas
  api               Inicia el servidor REST API (FastAPI)
  --help, -h       Muestra esta ayuda
  --version, -v    Muestra la version

Ejemplos:
  seguros demo          # Ejecuta una demostracion
  seguros api           # Inicia API en http://localhost:8000
  seguros --version     # Muestra la version

Para más información, visita:
https://github.com/GonorAndres/suite-actuarial
"""
    print(ayuda)


def ejecutar_demo() -> None:
    """Ejecuta una demostración del sistema"""
    from suite_actuarial.actuarial.mortality.tablas import TablaMortalidad
    from suite_actuarial.core.validators import (
        Asegurado,
        ConfiguracionProducto,
        Sexo,
    )
    from suite_actuarial.vida.temporal import VidaTemporal

    print("\nDemostracion: Calculo de Prima de Vida Temporal")
    print("-" * 60)

    try:
        # Cargar tabla
        print("\n1. Cargando tabla de mortalidad EMSSA-09...")
        tabla = TablaMortalidad.cargar_emssa09()
        print(f"   ✓ Tabla cargada: {tabla}")

        # Configurar producto
        print("\n2. Configurando producto...")
        config = ConfiguracionProducto(
            nombre_producto="Vida Temporal 20 años",
            plazo_years=20,
            tasa_interes_tecnico=Decimal("0.055"),
        )
        producto = VidaTemporal(config, tabla)
        print(f"   ✓ Producto: {config.nombre_producto}")

        # Crear asegurado
        print("\n3. Creando asegurado de ejemplo...")
        asegurado = Asegurado(
            edad=35,
            sexo=Sexo.HOMBRE,
            suma_asegurada=Decimal("1000000"),
        )
        print("   ✓ Asegurado: Hombre, 35 años, $1,000,000 MXN")

        # Calcular prima
        print("\n4. Calculando prima...")
        resultado = producto.calcular_prima(asegurado)

        print("\n" + "=" * 60)
        print("RESULTADO DEL CÁLCULO")
        print("=" * 60)
        print(f"\nPrima Neta:    ${resultado.prima_neta:>15,.2f} MXN")
        print(f"Prima Total:   ${resultado.prima_total:>15,.2f} MXN")
        print("\nDesglose de Recargos:")
        for concepto, monto in resultado.desglose_recargos.items():
            print(f"  - {concepto:20s}: ${monto:>10,.2f}")

        print("\n" + "=" * 60)
        print("\nDemostracion completada exitosamente.")
        print(
            "\nPara más ejemplos, revisa los notebooks en notebooks/01_ejemplo_basico.ipynb"
        )

    except FileNotFoundError:
        print("\nError: No se encontro la tabla de mortalidad EMSSA-09")
        print(
            "   Asegúrate de que el archivo data/mortality_tables/emssa_09.csv existe."
        )
    except Exception as e:
        print(f"\nError durante la demostracion: {e}")


def ejecutar_api() -> None:
    """Inicia el servidor REST API"""
    try:
        import uvicorn
    except ImportError:
        print("Error: FastAPI no instalado. Ejecuta: pip install mexican-insurance[api]")
        return

    print("Iniciando API REST en http://localhost:8000")
    print("Documentacion interactiva en http://localhost:8000/docs")
    print("Presiona Ctrl+C para detener\n")
    uvicorn.run(
        "suite_actuarial.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    sys.exit(main())
