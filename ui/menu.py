from algoritmos.algoritmos import (
    Burbuja,
    Seleccion,
    Insercion,
    Merge,
    Quick,
    Counting,
    Radix,
    Heap,
    Bucket
)


class MenuConsola:
    """Interfaz de consola para seleccionar y ejecutar algoritmos."""

    ALGORITMOS = {
        "1": ("Burbuja", Burbuja),
        "2": ("Selección", Seleccion),
        "3": ("Inserción", Insercion),
        "4": ("Merge Sort", Merge),
        "5": ("Quick Sort", Quick),
        "6": ("Counting Sort (solo números enteros)", Counting),
        "7": ("Radix Sort (solo números enteros)", Radix),
        "8": ("Heap Sort", Heap),
        "9": ("Bucket Sort (solo números)", Bucket),
    }

    CRITERIOS = {
        "1": ("Consecutivo", "consecutivo"),
        "2": ("Fecha de actualización", "fecha_actualizacion"),
        "3": ("Vigencia presupuestal", "vigencia_presupuestal"),
        "4": ("Tipo de documento", "tipo_documento"),
        "5": ("Sexo", "sexo"),
        "6": ("Etnia", "etnia"),
        "7": ("Discapacidad", "discapacidad"),
        "8": ("Departamento", "departamento"),
        "9": ("Municipio", "municipio"),
        "10": ("Código de municipio", "codigo_municipio"),
        "11": ("Vereda", "vereda"),
        "12": ("Línea productiva", "linea_productiva"),
        "13": ("Hectáreas", "hectareas"),
    }

    def __init__(self, beneficiarios):
        self.beneficiarios = beneficiarios

    def iniciar(self):
        """Inicia la interfaz principal del programa."""

        print("\n" + "=" * 60)
        print("Registro de Usuarios de Extensión Agropecuaria")
        print("=" * 60)
        print(f"Registros cargados: {len(self.beneficiarios)}")

        if not self.beneficiarios:
            print("\nNo hay datos para trabajar.")
            print("Verifica la conexión con la API o la disponibilidad de datos.")
            return

        while True:
            algoritmo = self._elegir_algoritmo()

            if algoritmo is None:
                print("\n¡Hasta luego!")
                break

            criterio = self._elegir_criterio()

            if criterio is None:
                print("\n¡Hasta luego!")
                break

            ascendente = self._elegir_direccion()

            if ascendente is None:
                print("\n¡Hasta luego!")
                break

            self._ejecutar_y_mostrar(
                algoritmo,
                criterio,
                ascendente
            )

            if not self._quiere_continuar():
                print("\n¡Hasta luego!")
                break

    def _elegir_algoritmo(self):
        """Permite seleccionar el algoritmo de ordenamiento."""

        print("\n--- Elige un algoritmo de ordenamiento ---")

        for clave, (nombre, _) in self.ALGORITMOS.items():
            print(f"  {clave}. {nombre}")

        print("  0. Salir")

        while True:
            opcion = input("Opción: ").strip()

            if opcion == "0":
                return None

            if opcion in self.ALGORITMOS:
                nombre, clase_algoritmo = self.ALGORITMOS[opcion]

                print(f"Elegiste: {nombre}")

                return clase_algoritmo()

            print("Opción inválida, intenta de nuevo.")

    def _elegir_criterio(self):
        """Permite seleccionar el campo por el cual ordenar."""

        print("\n--- Elige por cuál campo ordenar ---")

        for clave, (nombre, _) in self.CRITERIOS.items():
            print(f"  {clave}. {nombre}")

        print("  0. Salir")

        while True:
            opcion = input("Opción: ").strip()

            if opcion == "0":
                return None

            if opcion in self.CRITERIOS:
                nombre, atributo = self.CRITERIOS[opcion]

                print(f"Elegiste: {nombre}")

                return atributo

            print("Opción inválida, intenta de nuevo.")

    def _elegir_direccion(self):
        """Permite seleccionar el orden ascendente o descendente."""

        print("\n--- Elige la dirección ---")
        print("  1. Ascendente (menor a mayor / A-Z)")
        print("  2. Descendente (mayor a menor / Z-A)")
        print("  0. Salir")

        while True:
            opcion = input("Opción: ").strip()

            if opcion == "0":
                return None

            if opcion == "1":
                return True

            if opcion == "2":
                return False

            print("Opción inválida, intenta de nuevo.")

    def _ejecutar_y_mostrar(self, algoritmo, criterio, ascendente):
        """Ejecuta el algoritmo y muestra los primeros resultados."""

        try:
            resultado = algoritmo.ordenar(
                self.beneficiarios,
                criterio,
                ascendente
            )

        except (TypeError, ValueError, AttributeError) as e:
            print(f"\nNo se pudo realizar el ordenamiento: {e}")
            print("Prueba con otro algoritmo o cambia el criterio.")
            return

        if resultado is None:
            print("\nNo se obtuvo ningún resultado.")
            return

        if not resultado:
            print("\nNo se encontraron datos para mostrar.")
            return

        print(
            f"\n--- Primeros 15 resultados "
            f"(de {len(resultado)} totales) ---"
        )

        for i, registro in enumerate(resultado[:15], start=1):

            try:
                valor = getattr(registro, criterio)

                municipio = getattr(
                    registro,
                    "municipio",
                    "Sin municipio"
                )

                vereda = getattr(
                    registro,
                    "vereda",
                    "Sin vereda"
                )

                print(
                    f"  {i}. {municipio} - {vereda} "
                    f"| {criterio}: {valor}"
                )

            except AttributeError:
                print(
                    "\nError: uno de los registros no contiene "
                    f"el campo '{criterio}'."
                )
                return

    def _quiere_continuar(self):
        """Pregunta si el usuario desea realizar otro ordenamiento."""

        while True:
            respuesta = input(
                "\n¿Quieres hacer otro ordenamiento? (s/n): "
            ).strip().lower()

            if respuesta == "s":
                return True

            if respuesta == "n":
                return False

            print(
                "Respuesta inválida. "
                "Escribe 's' para sí o 'n' para no."
            )