"""
CLI para mexican_insurance

Comando de línea para usar la librería desde terminal.
"""

import sys
from decimal import Decimal

from mexican_insurance import __version__


def main() -> int:
    """
    Punto de entrada principal del CLI.

    Returns:
        Exit code (0 = éxito, 1 = error)
    """
    print(f"🏦 Mexican Insurance Analytics Suite v{__version__}")
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

    print(f"❌ Comando desconocido: {comando}")
    print("Usa 'seguros --help' para ver los comandos disponibles.")
    return 1


def mostrar_ayuda() -> None:
    """Muestra la ayuda del CLI"""
    ayuda = """
Uso: seguros [comando] [opciones]

Comandos disponibles:
  demo              Ejecuta un ejemplo de cálculo de primas
  --help, -h       Muestra esta ayuda
  --version, -v    Muestra la versión

Ejemplos:
  seguros demo          # Ejecuta una demostración
  seguros --version     # Muestra la versión

Para más información, visita:
https://github.com/GonorAndres/Analisis_Seguros_Mexico
"""
    print(ayuda)


def ejecutar_demo() -> None:
    """Ejecuta una demostración del sistema"""
    from mexican_insurance.actuarial.mortality.tablas import TablaMortalidad
    from mexican_insurance.core.validators import (
        Asegurado,
        ConfiguracionProducto,
        Sexo,
    )
    from mexican_insurance.products.vida.temporal import VidaTemporal

    print("\n📊 Demostración: Cálculo de Prima de Vida Temporal")
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
        print("\n✓ Demostración completada exitosamente!")
        print(
            "\nPara más ejemplos, revisa los notebooks en notebooks/01_ejemplo_basico.ipynb"
        )

    except FileNotFoundError:
        print("\n❌ Error: No se encontró la tabla de mortalidad EMSSA-09")
        print(
            "   Asegúrate de que el archivo data/mortality_tables/emssa_09.csv existe."
        )
    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")


if __name__ == "__main__":
    sys.exit(main())
