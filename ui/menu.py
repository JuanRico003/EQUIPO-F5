from algoritmos.algoritmos import (
    Burbuja, Seleccion, Insercion, Merge, Quick, Counting, Radix, Heap, Bucket
)


class MenuConsola:
    """Interfaz de consola"""

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
        print(" " * 55)
        print("Registro de Usuario de Extensión Agropecuaria")
        print(" " * 55)
        print(f"Registros cargados: {len(self.beneficiarios)}\n")

        if not self.beneficiarios:
            print("No hay datos para trabajar. Verifica la conexión a la API.")
            return

        while True:
            algoritmo = self._elegir_algoritmo()
            criterio = self._elegir_criterio()
            ascendente = self._elegir_direccion()

            self._ejecutar_y_mostrar(algoritmo, criterio, ascendente)

            if not self._quiere_continuar():
                print("\n¡Hasta luego!")
                break

    def _elegir_algoritmo(self):
        print("\n--- Elige un algoritmo de ordenamiento ---")
        for clave, (nombre, _) in self.ALGORITMOS.items():
            print(f"  {clave}. {nombre}")

        while True:
            opcion = input("Opción: ").strip()
            if opcion in self.ALGORITMOS:
                nombre, clase_algoritmo = self.ALGORITMOS[opcion]
                print(f"Elegiste: {nombre}")
                return clase_algoritmo()
            print("Opción inválida, intenta de nuevo.")

    def _elegir_criterio(self):
        print("\n--- Elige por cuál campo ordenar ---")
        for clave, (nombre, _) in self.CRITERIOS.items():
            print(f"  {clave}. {nombre}")

        while True:
            opcion = input("Opción: ").strip()
            if opcion in self.CRITERIOS:
                nombre, atributo = self.CRITERIOS[opcion]
                print(f"Elegiste: {nombre}")
                return atributo
            print("Opción inválida, intenta de nuevo.")

    def _elegir_direccion(self):
        print("\n--- Elige la dirección ---")
        print("  1. Ascendente (menor a mayor / A-Z)")
        print("  2. Descendente (mayor a menor / Z-A)")

        while True:
            opcion = input("Opción: ").strip()
            if opcion == "1":
                return True
            if opcion == "2":
                return False
            print("Opción inválida, intenta de nuevo.")

    def _ejecutar_y_mostrar(self, algoritmo, criterio, ascendente):
        try:
            resultado = algoritmo.ordenar(self.beneficiarios, criterio, ascendente)
        except TypeError as e:
            print(f"\n No se pudo ordenar: {e}")
            print("   Prueba con otro algoritmo o cambia el criterio.")
            return

        print(f"\n--- Primeros 15 resultados (de {len(resultado)} totales) ---")
        for i, registro in enumerate(resultado[:15], start=1):
            valor = getattr(registro, criterio)
            print(f"  {i}. {registro.municipio} - {registro.vereda} "
                  f"| {criterio}: {valor}")

    def _quiere_continuar(self):
        while True:
            respuesta = input("\n¿Quieres hacer otro ordenamiento? (s/n): ").strip().lower()
            if respuesta == "s":
                return True
            if respuesta == "n":
                return False
            print("Respuesta inválida. Escribe 's' para sí o 'n' para no.")