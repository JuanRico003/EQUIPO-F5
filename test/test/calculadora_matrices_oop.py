import datetime
import random
import tkinter as tk
from tkinter import messagebox, ttk

# MÓDULO 1: CLASE MATRIZ (LÓGICA MATEMÁTICA)

class Matriz:
    """Representa una matriz numérica y encapsula todas sus operaciones."""

    def __init__(self, datos):
        if not Matriz.es_valida(datos):
            raise ValueError("La estructura proporcionada no es una matriz numérica válida.")
        self.datos = datos
        self.filas = len(datos)
        self.columnas = len(datos[0])

    # ---------- Validación / utilidades de construcción ----------

    @staticmethod
    def es_valida(datos):
        """Verifica si la estructura es una matriz rectangular válida de números."""
        if not datos or not isinstance(datos, list):
            return False
        columnas = len(datos[0])
        for fila in datos:
            if not isinstance(fila, list) or len(fila) != columnas:
                return False
            for elem in fila:
                if not isinstance(elem, (int, float)):
                    return False
        return True

    @classmethod
    def generar_aleatoria(cls, filas, columnas, min_val=-10, max_val=10):
        """Crea una Matriz de dimensiones filas x columnas con enteros aleatorios."""
        datos = [[random.randint(min_val, max_val) for _ in range(columnas)] for _ in range(filas)]
        return cls(datos)

    def dimensiones(self):
        """Retorna una tupla (filas, columnas)."""
        return self.filas, self.columnas

    # ---------- Validaciones internas ----------

    def _validar_misma_dimension(self, otra, verbo):
        if self.dimensiones() != otra.dimensiones():
            raise ValueError(
                f"No se pueden {verbo} matrices de dimensiones distintas: "
                f"({self.filas}x{self.columnas}) vs ({otra.filas}x{otra.columnas})."
            )

    def _validar_cuadrada(self, contexto):
        if self.filas != self.columnas:
            raise ValueError(
                f"{contexto} solo existe para matrices cuadradas. "
                f"Dimensión actual: ({self.filas}x{self.columnas})."
            )

    # ---------- Operaciones binarias A y B ----------

    def sumar(self, otra):
        """Suma esta matriz con otra si sus dimensiones coinciden."""
        self._validar_misma_dimension(otra, "sumar")
        datos = [[self.datos[i][j] + otra.datos[i][j] for j in range(self.columnas)] for i in range(self.filas)]
        return Matriz(datos)

    def restar(self, otra):
        """Resta otra matriz a esta si sus dimensiones coinciden."""
        self._validar_misma_dimension(otra, "restar")
        datos = [[self.datos[i][j] - otra.datos[i][j] for j in range(self.columnas)] for i in range(self.filas)]
        return Matriz(datos)

    def multiplicar(self, otra):
        """Multiplica esta matriz por otra si columnas(self) == filas(otra)."""
        if self.columnas != otra.filas:
            raise ValueError(
                f"Incompatibilidad de dimensiones: Columnas de A ({self.columnas}) "
                f"deben ser iguales a Filas de B ({otra.filas})."
            )
        datos = [[0.0 for _ in range(otra.columnas)] for _ in range(self.filas)]
        for i in range(self.filas):
            for j in range(otra.columnas):
                datos[i][j] = sum(self.datos[i][k] * otra.datos[k][j] for k in range(self.columnas))
        return Matriz(datos)
    
    def multiplicar_elemento_a_elemento(self, otra): 
        """Multiplica esta matriz con otra celda por celda (producto de Hadamard).""" 
        self._validar_misma_dimension(otra, "multiplicar elemento a elemento") 
        datos = [[self.datos[i][j] * otra.datos[i][j] for j in range(self.columnas)] for i in range(self.filas)] 
        return Matriz(datos) 
    
    def dividir_elemento_a_elemento(self, otra):
        """Divide esta matriz entre otra celda por celda."""
        self._validar_misma_dimension(otra, "dividir elemento a elemento")
        datos = []
        for i in range(self.filas):
            fila = []
            for j in range(self.columnas):
                if otra.datos[i][j] == 0:
                    raise ValueError(f"No se puede dividir: la celda ({i+1},{j+1}) de la matriz B es 0.")
                fila.append(round(self.datos[i][j] / otra.datos[i][j], 4))
            datos.append(fila)
        return Matriz(datos)

    # ---------- Operaciones Escalares----------

    def multiplicar_por_escalar(self, escalar):
        """Retorna una nueva Matriz con cada elemento multiplicado por 'escalar'."""
        datos = [[round(self.datos[i][j] * escalar, 4) for j in range(self.columnas)] for i in range(self.filas)]
        return Matriz(datos)

    def sumar_escalar(self, escalar):
        """Retorna una nueva Matriz con 'escalar' sumado a cada elemento."""
        datos = [[round(self.datos[i][j] + escalar, 4) for j in range(self.columnas)] for i in range(self.filas)]
        return Matriz(datos)

    def restar_escalar(self, escalar):
        """Retorna una nueva Matriz con 'escalar' restado a cada elemento."""
        datos = [[round(self.datos[i][j] - escalar, 4) for j in range(self.columnas)] for i in range(self.filas)]
        return Matriz(datos)

    def dividir_por_escalar(self, escalar):
        """Retorna una nueva Matriz con cada elemento dividido entre 'escalar'."""
        if escalar == 0:
            raise ValueError("No se puede dividir entre 0.")
        datos = [[round(self.datos[i][j] / escalar, 4) for j in range(self.columnas)] for i in range(self.filas)]
        return Matriz(datos)
    
# ---------- Operaciones Unarias ----------

    def transpuesta(self):
        """Calcula y retorna la matriz transpuesta."""
        datos = [[self.datos[j][i] for j in range(self.filas)] for i in range(self.columnas)]
        return Matriz(datos)

    def submatriz(self, fila_eliminar, col_eliminar):
        """Retorna una Matriz sin la fila y columna indicadas (usado en cofactores)."""
        datos = [
            [self.datos[i][j] for j in range(self.columnas) if j != col_eliminar]
            for i in range(self.filas) if i != fila_eliminar
        ]
        return Matriz(datos)
    
    def traza(self):
        """Calcula la traza: suma de los elementos de la diagonal principal."""
        self._validar_cuadrada("La traza")
        return sum(self.datos[i][i] for i in range(self.filas))

    def determinante(self):
        """Calcula el determinante de la matriz (debe ser cuadrada) de forma recursiva."""
        self._validar_cuadrada("El determinante")

        if self.filas == 1:
            return self.datos[0][0]
        if self.filas == 2:
            return self.datos[0][0] * self.datos[1][1] - self.datos[0][1] * self.datos[1][0]

        det = 0.0
        for j in range(self.columnas):
            sub = self.submatriz(0, j)
            cofactor = ((-1) ** j) * sub.determinante()
            det += self.datos[0][j] * cofactor
        return det

    def inversa(self):
        """Calcula la matriz inversa utilizando la matriz adjunta y el determinante."""
        self._validar_cuadrada("La matriz inversa")

        det = self.determinante()
        if abs(det) < 1e-9:
            raise ValueError("La matriz es singular (determinante = 0), por lo que NO tiene inversa.")

        if self.filas == 1:
            return Matriz([[1.0 / self.datos[0][0]]])

        # Matriz de cofactores
        matriz_cofactores = []
        for i in range(self.filas):
            fila_cofactores = []
            for j in range(self.columnas):
                sub = self.submatriz(i, j)
                cofactor = ((-1) ** (i + j)) * sub.determinante()
                fila_cofactores.append(cofactor)
            matriz_cofactores.append(fila_cofactores)

        # Adjunta es la transpuesta de la matriz de cofactores
        matriz_adjunta = Matriz(matriz_cofactores).transpuesta()

        # Inversa = (1/det) * Adjunta
        datos_inversa = [
            [round(matriz_adjunta.datos[i][j] / det, 4) for j in range(self.columnas)]
            for i in range(self.filas)
        ]
        return Matriz(datos_inversa)

    # ---------- Representación ----------

    def __str__(self):
        """Formatea la matriz como texto plano alineado, sin decimales innecesarios."""
        lineas = []
        for fila in self.datos:
            celdas_texto = []
            for val in fila:
                if isinstance(val, float) and val == int(val):
                    celdas_texto.append(f"{int(val):4}")
                elif isinstance(val, float):
                    celdas_texto.append(f"{val:8.2f}")
                else:
                    celdas_texto.append(f"{val:4}")
            lineas.append("  [ " + "  ".join(celdas_texto) + " ]")
        return "\n".join(lineas)

# MÓDULO 2: CLASE HISTORIALMANAGER 

class HistorialManager:
    """Encapsula la lectura, escritura y borrado del historial de operaciones."""

    def __init__(self, nombre_archivo="historial_matrices.txt"):
        self.nombre_archivo = nombre_archivo

    @staticmethod
    def formatear_resultado(resultado):
        """Formatea una Matriz o un valor numérico (ej. determinante) como texto plano."""
        if isinstance(resultado, Matriz):
            return str(resultado) + "\n"
        if isinstance(resultado, (int, float)):
            return f"  {resultado}\n"
        return f"  {str(resultado)}\n"

    def registrar(self, tipo_operacion, detalles_operacion, resultado):
        """Guarda en el archivo la fecha, tipo de operación y el resultado."""
        fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        contenido = f"[{fecha_hora}] OPERACIÓN: {tipo_operacion}\n"
        contenido += f"Detalles: {detalles_operacion}\n"
        contenido += f"Resultado:\n{self.formatear_resultado(resultado)}\n"
        contenido += "-" * 50 + "\n\n"

        try:
            with open(self.nombre_archivo, "a", encoding="utf-8") as archivo:
                archivo.write(contenido)
        except Exception as e:
            print(f"Error al escribir en el historial: {e}")

    def vaciar(self):
        """Borra todo el contenido del archivo de historial."""
        try:
            with open(self.nombre_archivo, "w", encoding="utf-8") as archivo:
                archivo.write("")
        except Exception as e:
            print(f"Error al borrar el historial: {e}")

    def leer(self):
        """Retorna el contenido completo del historial, o None si aún no existe."""
        try:
            with open(self.nombre_archivo, "r", encoding="utf-8") as archivo:
                return archivo.read()
        except FileNotFoundError:
            return None


# MÓDULO 3: INTERFAZ GRÁFICA DE USUARIO (GUI)

class CalculadoraMatricesGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Matrices - Programación Avanzada")
        self.root.geometry("950x850")
        self.root.minsize(1050, 600)

        # Celdas dinámicas para la entrada
        self.celdas_a = []
        self.celdas_b = []

        # Instancia del gestor de historial (composición)
        self.historial = HistorialManager()

        self.crear_interfaz()

    def crear_interfaz(self):
        # Notebook (Pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        btn_salir = ttk.Button(self.root, text="Salir", command=self.salir_aplicacion) 
        btn_salir.place(relx=1.0, x=-15, y=3, anchor="ne")

        # Pestaña 1: Operaciones
        self.tab_operaciones = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_operaciones, text=" Operaciones Matriciales ")

        # Pestaña 2: Histórico
        self.tab_historial = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_historial, text=" Histórico de Operaciones ")

        self.construir_pestana_operaciones()
        self.construir_pestana_historial()

    def construir_pestana_operaciones(self):
        # Panel Superior: Dimensiones y Controles
        frame_controles = ttk.LabelFrame(self.tab_operaciones, text=" Configuración de Matrices ", padding=10)
        frame_controles.pack(fill="x", padx=10, pady=5)

        # Dimensiones Matriz A
        ttk.Label(frame_controles, text="Matriz A (Filas x Cols):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ent_f_a = ttk.Entry(frame_controles, width=5)
        self.ent_f_a.insert(0, "2")
        self.ent_f_a.grid(row=0, column=1, padx=2, pady=5)
        ttk.Label(frame_controles, text="x").grid(row=0, column=2)
        self.ent_c_a = ttk.Entry(frame_controles, width=5)
        self.ent_c_a.insert(0, "2")
        self.ent_c_a.grid(row=0, column=3, padx=2, pady=5)

        # Dimensiones Matriz B
        ttk.Label(frame_controles, text="Matriz B (Filas x Cols):").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.ent_f_b = ttk.Entry(frame_controles, width=5)
        self.ent_f_b.insert(0, "2")
        self.ent_f_b.grid(row=0, column=5, padx=2, pady=5)
        ttk.Label(frame_controles, text="x").grid(row=0, column=6)
        self.ent_c_b = ttk.Entry(frame_controles, width=5)
        self.ent_c_b.insert(0, "2")
        self.ent_c_b.grid(row=0, column=7, padx=2, pady=5)

        btn_generar = ttk.Button(frame_controles, text="Crear Cuadriculas", command=self.generar_cuadriculas)
        btn_generar.grid(row=0, column=8, padx=10, pady=5)

        btn_random = ttk.Button(frame_controles, text="Llenar Aleatorio", command=self.llenar_aleatorio)
        btn_random.grid(row=0, column=9, padx=5, pady=5)

        # Panel Central: Edición de Celdas A y B
        frame_matrices = ttk.Frame(self.tab_operaciones)
        frame_matrices.pack(fill="both", expand=True, padx=10, pady=5)

        self.lbl_frame_a = ttk.LabelFrame(frame_matrices, text=" Matriz A ", padding=10)
        self.lbl_frame_a.pack(side="left", fill="both", expand=True, padx=5)

        self.lbl_frame_b = ttk.LabelFrame(frame_matrices, text=" Matriz B ", padding=10)
        self.lbl_frame_b.pack(side="right", fill="both", expand=True, padx=5)

        # Panel Binarias
        frame_binarias = ttk.LabelFrame(self.tab_operaciones, text=" Operaciones Binarias (A y B) ", padding=10)
        frame_binarias.pack(fill="x", padx=10, pady=5)

        ttk.Button(frame_binarias, text="A + B", command=lambda: self.ejecutar_operacion("Suma")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frame_binarias, text="A - B", command=lambda: self.ejecutar_operacion("Resta")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame_binarias, text="A * B", command=lambda: self.ejecutar_operacion("Multiplicacion")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(frame_binarias, text="A ⊙ B (elem.)", command=lambda: self.ejecutar_operacion("MultElemento")).grid(row=0, column=3, padx=5, pady=5) 
        ttk.Button(frame_binarias, text="A ⊘ B (elem.)", command=lambda: self.ejecutar_operacion("DivElemento")).grid(row=0, column=4, padx=5, pady=5)
        
        # Panel Escalares
        frame_escalares = ttk.LabelFrame(self.tab_operaciones, text=" Operaciones Escalares (k) ", padding=10)
        frame_escalares.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_escalares, text="Escalar k : ").grid(row=0, column=0, padx=(5, 2), pady=5)
        self.ent_escalar = ttk.Entry(frame_escalares, width=6)
        self.ent_escalar.insert(0, "2")
        self.ent_escalar.grid(row=0, column=1, padx=2, pady=5)

        ttk.Label(frame_escalares, text="Matriz A:").grid(row=0, column=2, padx=(15, 2), pady=5)
        ttk.Button(frame_escalares, text="k + A", command=lambda: self.ejecutar_operacion("SumaEscalarA")).grid(row=0, column=3, padx=2, pady=5)
        ttk.Button(frame_escalares, text="k - A", command=lambda: self.ejecutar_operacion("RestaEscalarA")).grid(row=0, column=4, padx=2, pady=5)
        ttk.Button(frame_escalares, text="k * A", command=lambda: self.ejecutar_operacion("EscalarA")).grid(row=0, column=5, padx=2, pady=5)
        ttk.Button(frame_escalares, text="k / A", command=lambda: self.ejecutar_operacion("DivEscalarA")).grid(row=0, column=6, padx=2, pady=5)

        ttk.Label(frame_escalares, text="Matriz B:").grid(row=1, column=2, padx=(15, 2), pady=5)
        ttk.Button(frame_escalares, text="k + B", command=lambda: self.ejecutar_operacion("SumaEscalarB")).grid(row=1, column=3, padx=2, pady=5)
        ttk.Button(frame_escalares, text="k - B", command=lambda: self.ejecutar_operacion("RestaEscalarB")).grid(row=1, column=4, padx=2, pady=5)
        ttk.Button(frame_escalares, text="k * B", command=lambda: self.ejecutar_operacion("EscalarB")).grid(row=1, column=5, padx=2, pady=5)
        ttk.Button(frame_escalares, text="k / B", command=lambda: self.ejecutar_operacion("DivEscalarB")).grid(row=1, column=6, padx=2, pady=5)

        # Panel Unarias
        frame_unarias = ttk.LabelFrame(self.tab_operaciones, text=" Operaciones Unarias ", padding=10)
        frame_unarias.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_unarias, text="Matriz A:").grid(row=0, column=0, padx=(5, 2), pady=5)
        ttk.Button(frame_unarias, text="Transpuesta A", command=lambda: self.ejecutar_operacion("TranspuestaA")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame_unarias, text="Det(A)", command=lambda: self.ejecutar_operacion("DetA")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(frame_unarias, text="Inversa A (A⁻¹)", command=lambda: self.ejecutar_operacion("InversaA")).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(frame_unarias, text="Traza(A)", command=lambda: self.ejecutar_operacion("TrazaA")).grid(row=0, column=4, padx=5, pady=5)

        ttk.Label(frame_unarias, text="Matriz B:").grid(row=1, column=0, padx=(5, 2), pady=5)
        ttk.Button(frame_unarias, text="Transpuesta B", command=lambda: self.ejecutar_operacion("TranspuestaB")).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(frame_unarias, text="Det(B)", command=lambda: self.ejecutar_operacion("DetB")).grid(row=1, column=2, padx=2, pady=2)
        ttk.Button(frame_unarias, text="Inversa B (B⁻¹)", command=lambda: self.ejecutar_operacion("InversaB")).grid(row=1, column=3, padx=2, pady=2)
        ttk.Button(frame_unarias, text="Traza(B)", command=lambda: self.ejecutar_operacion("TrazaB")).grid(row=1, column=4, padx=2, pady=2)
       
        # Panel Resultados
        frame_resultado = ttk.LabelFrame(self.tab_operaciones, text=" Resultado de la Operación ", padding=10)
        frame_resultado.pack(fill="both", expand=True, padx=10, pady=5)

        self.txt_resultado = tk.Text(frame_resultado, height=6, font=("Consolas", 11))
        self.txt_resultado.pack(fill="both", expand=True)

        # Generar cuadrículas iniciales (2x2)
        self.generar_cuadriculas()

    def construir_pestana_historial(self):
        frame = ttk.Frame(self.tab_historial, padding=10)
        frame.pack(fill="both", expand=True)

        btn_cargar = ttk.Button(frame, text="Actualizar Historial", command=self.cargar_historial_txt)
        btn_cargar.pack(anchor="nw", pady=5)
        btn_borrar = ttk.Button(frame, text="Borrar Historial", command=self.borrar_historial_gui)
        btn_borrar.pack(anchor="nw", pady=10)

        self.txt_historial_view = tk.Text(frame, font=("Consolas", 10))
        self.txt_historial_view.pack(fill="both", expand=True)
        self.cargar_historial_txt()

    def borrar_historial_gui(self):
        """Pide confirmación mediante cuadro de diálogo y vacía el historial tanto en disco como en pantalla."""
        confirmacion = messagebox.askyesno(
            "Confirmar Borrado",
            "¿Estás seguro de que deseas eliminar permanentemente el historial de operaciones?"
        )
        if confirmacion:
            self.historial.vaciar()
            self.cargar_historial_txt()
            messagebox.showinfo("Historial Eliminado", "El registro de operaciones ha sido borrado con éxito.")

    def salir_aplicacion(self): 
        """Pide confirmación antes de cerrar la aplicación.""" 
        confirmacion = messagebox.askyesno( 
            "Confirmar Salida", 
            "¿Estás seguro de que deseas salir de la Calculadora de Matrices?" )
    
        if confirmacion: self.root.destroy()

    def generar_cuadriculas(self):
        """Crea dinámicamente las entradas de texto tipo matriz según las dimensiones especificadas."""
        try:
            f_a, c_a = int(self.ent_f_a.get()), int(self.ent_c_a.get())
            f_b, c_b = int(self.ent_f_b.get()), int(self.ent_c_b.get())

            if min(f_a, c_a, f_b, c_b) <= 0 or max(f_a, c_a, f_b, c_b) > 7:
                messagebox.showwarning("Dimensiones Fuera de Rango", "Por favor ingresa dimensiones entre 1 y 7.")
                return
        except ValueError:
            messagebox.showerror("Error de Entrada", "Las dimensiones de las matrices deben ser números enteros válidos.")
            return

        # Limpiar GUI anterior
        for widget in self.lbl_frame_a.winfo_children():
            widget.destroy()
        for widget in self.lbl_frame_b.winfo_children():
            widget.destroy()

        self.celdas_a = []
        for i in range(f_a):
            fila_entries = []
            for j in range(c_a):
                entry = ttk.Entry(self.lbl_frame_a, width=6, justify="center")
                entry.grid(row=i, column=j, padx=2, pady=2)
                entry.insert(0, "0") 
                entry.bind("<FocusIn>", lambda e: e.widget.select_range(0, tk.END))
                fila_entries.append(entry)
            self.celdas_a.append(fila_entries)

        self.celdas_b = []
        for i in range(f_b):
            fila_entries = []
            for j in range(c_b):
                entry = ttk.Entry(self.lbl_frame_b, width=6, justify="center")
                entry.grid(row=i, column=j, padx=2, pady=2)
                entry.insert(0, "0")
                entry.bind("<FocusIn>", lambda e: e.widget.select_range(0, tk.END))
                fila_entries.append(entry)
            self.celdas_b.append(fila_entries)

    def leer_escalar(self): 
        """Lee el escalar ingresado por el usuario y valida que sea un número dentro de un rango razonable.""" 
        texto = self.ent_escalar.get().strip() 
        try: k = float(texto) 
        except ValueError: 
            raise ValueError("El valor del escalar 'k' debe ser un número entero o decimal válido.") 
        if abs(k) > 100: 
            raise ValueError("El escalar debe estar entre -100 y 100 para evitar resultados excesivamente grandes.") 
        return k

    def obtener_matriz_gui(self, celdas):
        """Extrae, valida los datos de las celdas y retorna una instancia de Matriz."""
        datos = []
        for i, fila_entries in enumerate(celdas):
            fila = []
            for j, entry in enumerate(fila_entries):
                val_str = entry.get().strip()
                try:
                    val = float(val_str)
                except ValueError:
                    raise ValueError(f"Fila {i+1}, Columna {j+1}: '{val_str}' no es un número válido.")
                if abs(val) > 100:
                    raise ValueError(f"Fila {i+1}, Columna {j+1}: el valor debe estar entre -100 y 100.")
                fila.append(val)
            datos.append(fila)
        return Matriz(datos)

    def llenar_aleatorio(self):
        """Rellena las celdas activas con enteros aleatorios."""
        for fila in self.celdas_a:
            for entry in fila:
                entry.delete(0, tk.END)
                entry.insert(0, str(random.randint(-9, 9)))
        for fila in self.celdas_b:
            for entry in fila:
                entry.delete(0, tk.END)
                entry.insert(0, str(random.randint(-9, 9)))

    def mostrar_resultado(self, titulo, resultado):
        """Muestra el resultado en la pantalla inferior de la aplicación."""
        self.txt_resultado.delete("1.0", tk.END)
        self.txt_resultado.insert(tk.END, f"--- RESULTADO ({titulo}) ---\n\n")
        self.txt_resultado.insert(tk.END, self.historial.formatear_resultado(resultado))

    def cargar_historial_txt(self):
        """Carga el contenido guardado en el archivo de texto en la pestaña de historial."""
        self.txt_historial_view.delete("1.0", tk.END)
        contenido = self.historial.leer()
        if contenido is None:
            self.txt_historial_view.insert(tk.END, "Aún no se han guardado operaciones en el historial.")
        else:
            self.txt_historial_view.insert(tk.END, contenido)

    def ejecutar_operacion(self, operacion):
        """Controlador central que ejecuta las operaciones solicitadas con captura de excepciones."""
        try:
            matriz_a = self.obtener_matriz_gui(self.celdas_a)
            matriz_resultado = None
            detalles = ""

            if operacion == "Suma":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = matriz_a.sumar(matriz_b)
                detalles = f"Suma de A {matriz_a.dimensiones()} + B {matriz_b.dimensiones()}"

            elif operacion == "Resta":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = matriz_a.restar(matriz_b)
                detalles = f"Resta de A {matriz_a.dimensiones()} - B {matriz_b.dimensiones()}"

            elif operacion == "Multiplicacion":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = matriz_a.multiplicar(matriz_b)
                detalles = f"Multiplicación de A {matriz_a.dimensiones()} * B {matriz_b.dimensiones()}"

            elif operacion == "MultElemento": 
                matriz_b = self.obtener_matriz_gui(self.celdas_b) 
                matriz_resultado = matriz_a.multiplicar_elemento_a_elemento(matriz_b) 
                detalles = f"Multiplicación elemento a elemento de A y B" 

            elif operacion == "DivElemento": 
                matriz_b = self.obtener_matriz_gui(self.celdas_b) 
                matriz_resultado = matriz_a.dividir_elemento_a_elemento(matriz_b) 
                detalles = f"División elemento a elemento de A y B"

            # Operaciones unarias sobre la matriz A
            elif operacion == "EscalarA":
                k = self.leer_escalar()
                matriz_resultado = matriz_a.multiplicar_por_escalar(k)
                detalles = f"Multiplicación de A por Escalar k={k}"

            elif operacion == "SumaEscalarA": 
                k = self.leer_escalar()
                matriz_resultado = matriz_a.sumar_escalar(k) 
                detalles = f"Suma de A + Escalar k={k}" 

            elif operacion == "RestaEscalarA": 
                k = self.leer_escalar()
                matriz_resultado = matriz_a.restar_escalar(k) 
                detalles = f"Resta de A - Escalar k={k}"

            elif operacion == "DivEscalarA": 
                k = self.leer_escalar()
                matriz_resultado = matriz_a.dividir_por_escalar(k) 
                detalles = f"División de A entre Escalar k={k}"

            elif operacion == "TranspuestaA":
                matriz_resultado = matriz_a.transpuesta()
                detalles = f"Transpuesta de A {matriz_a.dimensiones()}"

            elif operacion == "DetA":
                matriz_resultado = matriz_a.determinante()
                detalles = f"Determinante de A {matriz_a.dimensiones()}"

            elif operacion == "TrazaA": 
                matriz_resultado = matriz_a.traza() 
                detalles = f"Traza de A {matriz_a.dimensiones()}"

            elif operacion == "InversaA":
                matriz_resultado = matriz_a.inversa()
                detalles = f"Matriz Inversa de A {matriz_a.dimensiones()}"

            # Operaciones unarias sobre la matriz B
            elif operacion == "EscalarB":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                try:
                    k = self.leer_escalar()
                except ValueError:
                    raise ValueError("El valor del escalar 'k' debe ser un número entero o decimal válido.")
                matriz_resultado = matriz_b.multiplicar_por_escalar(k)
                detalles = f"Multiplicación de B por Escalar k={k}"

            
            elif operacion == "SumaEscalarB": 
                matriz_b = self.obtener_matriz_gui(self.celdas_b) 
                try: k = float(self.ent_escalar.get()) 
                except ValueError: raise ValueError("El valor del escalar 'k' debe ser un número entero o decimal válido.") 
                matriz_resultado = matriz_b.sumar_escalar(k) 
                detalles = f"Suma de B + Escalar k={k}" 

            elif operacion == "RestaEscalarB": 
                matriz_b = self.obtener_matriz_gui(self.celdas_b) 
                try: k = float(self.ent_escalar.get()) 
                except ValueError: raise ValueError("El valor del escalar 'k' debe ser un número entero o decimal válido.") 
                matriz_resultado = matriz_b.restar_escalar(k) 
                detalles = f"Resta de B - Escalar k={k}"

            elif operacion == "DivEscalarB": 
                matriz_b = self.obtener_matriz_gui(self.celdas_b) 
                try: k = float(self.ent_escalar.get()) 
                except ValueError: raise ValueError("El valor del escalar 'k' debe ser un número entero o decimal válido.") 
                matriz_resultado = matriz_b.dividir_por_escalar(k) 
                detalles = f"División de B entre Escalar k={k}"

            elif operacion == "TranspuestaB":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = matriz_b.transpuesta()
                detalles = f"Transpuesta de B {matriz_b.dimensiones()}"

            elif operacion == "DetB":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = matriz_b.determinante()
                detalles = f"Determinante de B {matriz_b.dimensiones()}"

            elif operacion == "TrazaB": 
                matriz_b = self.obtener_matriz_gui(self.celdas_b) 
                matriz_resultado = matriz_b.traza() 
                detalles = f"Traza de B {matriz_b.dimensiones()}"

            elif operacion == "InversaB":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = matriz_b.inversa()
                detalles = f"Matriz Inversa de B {matriz_b.dimensiones()}"

            # Mostrar resultado y registrar en persistencia
            self.mostrar_resultado(operacion, matriz_resultado)
            self.historial.registrar(operacion, detalles, matriz_resultado)
            self.cargar_historial_txt()

        except ValueError as err:
            messagebox.showerror("Error de Operación / Validación", str(err))


# PUNTO DE ENTRADA PRINCIPAL

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculadoraMatricesGUI(root)
    root.mainloop()
