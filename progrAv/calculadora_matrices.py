import datetime
import random
import tkinter as tk
from tkinter import messagebox, ttk 

# ==========================================
# MÓDULO 1: LÓGICA DE OPERACIONES MATRICIALES
# ==========================================

def es_matriz_valida(matriz):
    """Verifica si la estructura es una matriz rectangular válida de números."""
    if not matriz or not isinstance(matriz, list):
        return False
    columnas = len(matriz[0])
    for fila in matriz:
        if not isinstance(fila, list) or len(fila) != columnas:
            return False
        for elem in fila:
            if not isinstance(elem, (int, float)):
                return False
    return True

def obtener_dimensiones(matriz):
    """Retorna las dimensiones (filas, columnas) de una matriz."""
    return len(matriz), len(matriz[0])

def generar_matriz_aleatoria(filas, columnas, min_val=-10, max_val=10):
    """Genera una matriz de dimensiones filas x columnas con enteros aleatorios."""
    return [[random.randint(min_val, max_val) for _ in range(columnas)] for _ in range(filas)]

def sumar_matrices(matriz_a, matriz_b):
    """Suma dos matrices A y B si sus dimensiones coinciden."""
    f_a, c_a = obtener_dimensiones(matriz_a)
    f_b, c_b = obtener_dimensiones(matriz_b)
    
    if (f_a, c_a) != (f_b, c_b):
        raise ValueError(f"No se pueden sumar matrices de dimensiones distintas: ({f_a}x{c_a}) vs ({f_b}x{c_b}).")
    
    return [[matriz_a[i][j] + matriz_b[i][j] for j in range(c_a)] for i in range(f_a)]

def restar_matrices(matriz_a, matriz_b):
    """Resta dos matrices A y B si sus dimensiones coinciden."""
    f_a, c_a = obtener_dimensiones(matriz_a)
    f_b, c_b = obtener_dimensiones(matriz_b)
    
    if (f_a, c_a) != (f_b, c_b):
        raise ValueError(f"No se pueden restar matrices de dimensiones distintas: ({f_a}x{c_a}) vs ({f_b}x{c_b}).")
    
    return [[matriz_a[i][j] - matriz_b[i][j] for j in range(c_a)] for i in range(f_a)]

def multiplicar_matrices(matriz_a, matriz_b):
    """Multiplica dos matrices A y B si columnas(A) == filas(B)."""
    f_a, c_a = obtener_dimensiones(matriz_a)
    f_b, c_b = obtener_dimensiones(matriz_b)
    
    if c_a != f_b:
        raise ValueError(f"Incompatibilidad de dimensiones: Columnas de A ({c_a}) deben ser iguales a Filas de B ({f_b}).")
    
    matriz_resultado = [[0.0 for _ in range(c_b)] for _ in range(f_a)]
    for i in range(f_a):
        for j in range(c_b):
            matriz_resultado[i][j] = sum(matriz_a[i][k] * matriz_b[k][j] for k in range(c_a))
    return matriz_resultado

def multiplicar_por_escalar(matriz, escalar):
    """Multiplica cada elemento de la matriz por un escalar dado."""
    f, c = obtener_dimensiones(matriz)
    return [[round(matriz[i][j] * escalar, 4) for j in range(c)] for i in range(f)]

def obtener_transpuesta(matriz):
    """Calcula la matriz transpuesta."""
    f, c = obtener_dimensiones(matriz)
    return [[matriz[j][i] for j in range(f)] for i in range(c)]

def obtener_submatriz(matriz, fila_eliminar, col_eliminar):
    """Elimina la fila y columna indicadas para el cálculo del determinante y cofactores."""
    return [[matriz[i][j] for j in range(len(matriz[i])) if j != col_eliminar] 
            for i in range(len(matriz)) if i != fila_eliminar]

def calcular_determinante(matriz):
    """Calcula el determinante de una matriz cuadrada de forma recursiva."""
    f, c = obtener_dimensiones(matriz)
    if f != c:
        raise ValueError(f"El determinante solo existe para matrices cuadradas. Dimensión actual: ({f}x{c}).")
    
    if f == 1:
        return matriz[0][0]
    if f == 2:
        return matriz[0][0] * matriz[1][1] - matriz[0][1] * matriz[1][0]
    
    det = 0.0
    for j in range(c):
        submatriz = obtener_submatriz(matriz, 0, j)
        cofactor = ((-1) ** j) * calcular_determinante(submatriz)
        det += matriz[0][j] * cofactor
    return det

def calcular_inversa(matriz):
    """Calcula la matriz inversa utilizando la matriz adjunta y el determinante."""
    f, c = obtener_dimensiones(matriz)
    if f != c:
        raise ValueError(f"La matriz inversa requiere una matriz cuadrada. Dimensión actual: ({f}x{c}).")
    
    det = calcular_determinante(matriz)
    if abs(det) < 1e-9:
        raise ValueError("La matriz es singular (determinante = 0), por lo que NO tiene inversa.")
    
    if f == 1:
        return [[1.0 / matriz[0][0]]]
    
    # Matriz de cofactores
    matriz_cofactores = []
    for i in range(f):
        fila_cofactores = []
        for j in range(c):
            submatriz = obtener_submatriz(matriz, i, j)
            cofactor = ((-1) ** (i + j)) * calcular_determinante(submatriz)
            fila_cofactores.append(cofactor)
        matriz_cofactores.append(fila_cofactores)
    
    # Adjunta es la transpuesta de la matriz de cofactores
    matriz_adjunta = obtener_transpuesta(matriz_cofactores)
    
    # Inversa = (1/det) * Adjunta
    matriz_inversa = [[round(matriz_adjunta[i][j] / det, 4) for j in range(c)] for i in range(f)]
    return matriz_inversa


# ==========================================
# MÓDULO 2: PERSISTENCIA DEL HISTORIAL (.TXT)
# ==========================================

NOMBRE_ARCHIVO_HISTORIAL = "historial_matrices.txt"

def registrar_en_historial(tipo_operacion, detalles_operacion, resultado):
    """Guarda en un archivo log.txt la fecha, tipo de operación y el resultado."""
    fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    contenido = f"[{fecha_hora}] OPERACIÓN: {tipo_operacion}\n"
    contenido += f"Detalles: {detalles_operacion}\n"
    contenido += f"Resultado:\n{formatear_matriz_string(resultado)}\n"
    contenido += "-" * 50 + "\n\n"
    
    try:
        with open(NOMBRE_ARCHIVO_HISTORIAL, "a", encoding="utf-8") as archivo:
            archivo.write(contenido)
    except Exception as e:
        print(f"Error al escribir en el historial: {e}")

def formatear_matriz_string(matriz):
    """Formatea la matriz o valor para guardarlo en texto plano."""
    if isinstance(matriz, (int, float)):
        return f"  {matriz}\n"
    if not isinstance(matriz, list):
        return f"  {str(matriz)}\n"
    lines = []
    for fila in matriz:
        lines.append("  [ " + "  ".join(f"{val:8.2f}" if isinstance(val, float) else f"{val:4}" for val in fila) + " ]")
    return "\n".join(lines)

def vaciar_historial_txt():
    """Borra todo el contenido del archivo de historial (.txt)."""
    try:
        with open(NOMBRE_ARCHIVO_HISTORIAL, "w", encoding="utf-8") as archivo:
            archivo.write("")
    except Exception as e:
        print(f"Error al borrar el historial: {e}")

# ==========================================
# MÓDULO 3: INTERFAZ GRÁFICA DE USUARIO (GUI)
# ==========================================

class CalculadoraMatricesGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Matrices - Programación Avanzada")
        self.root.geometry("850x650")
        self.root.minsize(800, 600)
        
        # Celdas dinámicas para la entrada
        self.celdas_a = []
        self.celdas_b = []
        
        self.crear_interfaz()

    def crear_interfaz(self):
        # Notebook (Pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

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

        # Panel Botones de Operación
        frame_acciones = ttk.LabelFrame(self.tab_operaciones, text=" Operaciones Disponibles ", padding=10)
        frame_acciones.pack(fill="x", padx=10, pady=5)

        # Botones Binarios
        ttk.Button(frame_acciones, text="A + B", command=lambda: self.ejecutar_operacion("Suma")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frame_acciones, text="A - B", command=lambda: self.ejecutar_operacion("Resta")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame_acciones, text="A * B", command=lambda: self.ejecutar_operacion("Multiplicacion")).grid(row=0, column=2, padx=5, pady=5)

        # Escalar
        ttk.Label(frame_acciones, text="Escalar k : ").grid(row=0, column=3, padx=(15, 2), pady=5)
        self.ent_escalar = ttk.Entry(frame_acciones, width=6)
        self.ent_escalar.insert(0, "2")
        self.ent_escalar.grid(row=0, column=4, padx=2, pady=5)
        ttk.Button(frame_acciones, text="k * A", command=lambda: self.ejecutar_operacion("EscalarA")).grid(row=0, column=5, padx=2, pady=5)

        # Botones Unarios para las dos matrices
        # para matriz A
        ttk.Button(frame_acciones, text="k * A", command=lambda: self.ejecutar_operacion("EscalarA")).grid(row=0, column=5, padx=2, pady=2)
        ttk.Button(frame_acciones, text="Transpuesta A", command=lambda: self.ejecutar_operacion("TranspuestaA")).grid(row=0, column=6, padx=5, pady=5)
        ttk.Button(frame_acciones, text="Det(A)", command=lambda: self.ejecutar_operacion("DetA")).grid(row=0, column=7, padx=5, pady=5)
        ttk.Button(frame_acciones, text="Inversa A (A⁻¹)", command=lambda: self.ejecutar_operacion("InversaA")).grid(row=0, column=8, padx=5, pady=5)

        # para matriz B
        ttk.Button(frame_acciones, text="k * B", command=lambda: self.ejecutar_operacion("EscalarB")).grid(row=1, column=5, padx=2, pady=2)
        ttk.Button(frame_acciones, text="Transpuesta B", command=lambda: self.ejecutar_operacion("TranspuestaB")).grid(row=1, column=6, padx=2, pady=2)
        ttk.Button(frame_acciones, text="Det(B)", command=lambda: self.ejecutar_operacion("DetB")).grid(row=1, column=7, padx=2, pady=2)
        ttk.Button(frame_acciones, text="Inversa B (B⁻¹)", command=lambda: self.ejecutar_operacion("InversaB")).grid(row=1, column=8, padx=2, pady=2)

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
            vaciar_historial_txt()
            self.cargar_historial_txt()
            messagebox.showinfo("Historial Eliminado", "El registro de operaciones ha sido borrado con éxito.")

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
                fila_entries.append(entry)
            self.celdas_a.append(fila_entries)

        self.celdas_b = []
        for i in range(f_b):
            fila_entries = []
            for j in range(c_b):
                entry = ttk.Entry(self.lbl_frame_b, width=6, justify="center")
                entry.grid(row=i, column=j, padx=2, pady=2)
                entry.insert(0, "0")
                fila_entries.append(entry)
            self.celdas_b.append(fila_entries)

    def obtener_matriz_gui(self, celdas):
        """Extrae y valida numéricamente los datos ingresados en las celdas de la interfaz."""
        matriz = []
        for i, fila_entries in enumerate(celdas):
            fila = []
            for j, entry in enumerate(fila_entries):
                val_str = entry.get().strip()
                try:
                    val = float(val_str)
                    fila.append(val)
                except ValueError:
                    raise ValueError(f"Fila {i+1}, Columna {j+1}: '{val_str}' no es un número válido.")
            matriz.append(fila)
        return matriz

    def llenar_aleatorio(self):
        """Rena las celdas activas con enteros aleatorios."""
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
        self.txt_resultado.insert(tk.END, formatear_matriz_string(resultado))

    def cargar_historial_txt(self):
        """Carga el contenido guardado en el archivo de texto en la pestaña de historial."""
        self.txt_historial_view.delete("1.0", tk.END)
        try:
            with open(NOMBRE_ARCHIVO_HISTORIAL, "r", encoding="utf-8") as archivo:
                self.txt_historial_view.insert(tk.END, archivo.read())
        except FileNotFoundError:
            self.txt_historial_view.insert(tk.END, "Aún no se han guardado operaciones en el historial.")

    def ejecutar_operacion(self, operacion):
        """Controlador central que ejecuta las operaciones solicitadas con captura de excepciones."""
        try:
            matriz_a = self.obtener_matriz_gui(self.celdas_a)
            matriz_resultado = None
            detalles = ""

            if operacion == "Suma":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = sumar_matrices(matriz_a, matriz_b)
                detalles = f"Suma de A {obtener_dimensiones(matriz_a)} + B {obtener_dimensiones(matriz_b)}"
                
            elif operacion == "Resta":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = restar_matrices(matriz_a, matriz_b)
                detalles = f"Resta de A {obtener_dimensiones(matriz_a)} - B {obtener_dimensiones(matriz_b)}"
                
            elif operacion == "Multiplicacion":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = multiplicar_matrices(matriz_a, matriz_b)
                detalles = f"Multiplicación de A {obtener_dimensiones(matriz_a)} * B {obtener_dimensiones(matriz_b)}"

            # Operaciones unarias sobre la matriz A
            elif operacion == "EscalarA":
                try:
                    k = float(self.ent_escalar.get())
                except ValueError:
                    raise ValueError("El valor del escalar 'k' debe ser un número entero o decimal válido.")
                matriz_resultado = multiplicar_por_escalar(matriz_a, k)
                detalles = f"Multiplicación de A por Escalar k={k}"

            elif operacion == "TranspuestaA":
                matriz_resultado = obtener_transpuesta(matriz_a)
                detalles = f"Transpuesta de A {obtener_dimensiones(matriz_a)}"

            elif operacion == "DetA":
                matriz_resultado = calcular_determinante(matriz_a)
                detalles = f"Determinante de A {obtener_dimensiones(matriz_a)}"

            elif operacion == "InversaA":
                matriz_resultado = calcular_inversa(matriz_a)
                detalles = f"Matriz Inversa de A {obtener_dimensiones(matriz_a)}"

            # Operaciones unarias sobre la matriz B
            elif operacion == "EscalarB":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                try:
                    k = float(self.ent_escalar.get())
                except ValueError:
                    raise ValueError("El valor del escalar 'k' debe ser un número entero o decimal válido.")
                matriz_resultado = multiplicar_por_escalar(matriz_b, k)
                detalles = f"Multiplicación de B por Escalar k={k}"

            elif operacion == "TranspuestaB":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = obtener_transpuesta(matriz_b)
                detalles = f"Transpuesta de B {obtener_dimensiones(matriz_b)}"

            elif operacion == "DetB":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = calcular_determinante(matriz_b)
                detalles = f"Determinante de B {obtener_dimensiones(matriz_b)}"

            elif operacion == "InversaB":
                matriz_b = self.obtener_matriz_gui(self.celdas_b)
                matriz_resultado = calcular_inversa(matriz_b)
                detalles = f"Matriz Inversa de B {obtener_dimensiones(matriz_b)}"
            
            # Mostrar resultado y registrar en persistencia
            self.mostrar_resultado(operacion, matriz_resultado)
            registrar_en_historial(operacion, detalles, matriz_resultado)
            self.cargar_historial_txt()

        except ValueError as err:
            messagebox.showerror("Error de Operación / Validación", str(err))


# ==========================================
# PUNTO DE ENTRADA PRINCIPAL
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = CalculadoraMatricesGUI(root)
    root.mainloop()
