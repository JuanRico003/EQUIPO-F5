import random

from algoritmos.base import AlgoritmoOrdenamiento

class Burbuja(AlgoritmoOrdenamiento):
    """
    Compara elementos adyacentes
    y los intercambia si están en el orden incorrecto, repite esto
    hasta que no haya más intercambios que hacer
    """

    def ordenar(self, lista, criterio, ascendente=True):
        datos = lista.copy()  # no modificamos la lista original
        n = len(datos)

        for i in range(n):
            hubo_intercambio = False

            for j in range(0, n - i - 1):
                valor_actual = self.obtener_valor(datos[j], criterio)
                valor_siguiente = self.obtener_valor(datos[j + 1], criterio)

                # Decidimos si hay que intercambiar según el orden pedido
                debe_intercambiar = (
                    valor_actual > valor_siguiente if ascendente
                    else valor_actual < valor_siguiente
                )

                if debe_intercambiar:
                    datos[j], datos[j + 1] = datos[j + 1], datos[j]
                    hubo_intercambio = True

            # Optimización: si en una vuelta completa no hubo intercambios,
            # la lista ya está ordenada, no hace falta seguir
            if not hubo_intercambio:
                break

        return datos


class Seleccion(AlgoritmoOrdenamiento):
    """
    En cada vuelta, busca el elemento más pequeño (o más grande) de 
    la parte no ordenada, y lo coloca en su posición correcta.
    """

    def ordenar(self, lista, criterio, ascendente=True):
        datos = lista.copy()
        n = len(datos)

        for i in range(n):
            indice_elegido = i

            for j in range(i + 1, n):
                valor_actual = self.obtener_valor(datos[j], criterio)
                valor_elegido = self.obtener_valor(datos[indice_elegido], criterio)

                es_mejor_candidato = (
                    valor_actual < valor_elegido if ascendente
                    else valor_actual > valor_elegido
                )

                if es_mejor_candidato:
                    indice_elegido = j

            # Intercambiamos el elemento elegido a su posición correcta
            datos[i], datos[indice_elegido] = datos[indice_elegido], datos[i]

        return datos

    
class Insercion(AlgoritmoOrdenamiento):
    """
    Construye la lista ordenada de a un elemento a la vez, 
    tomando cada elemento e insertándolo en la
    posición correcta dentro de la parte ya ordenada
    """

    def ordenar(self, lista, criterio, ascendente=True):
        datos = lista.copy()
        n = len(datos)

        for i in range(1, n):
            elemento_actual = datos[i]
            valor_actual = self.obtener_valor(elemento_actual, criterio)
            j = i - 1

            # Desplazamos los elementos mayores (o menores) hacia adelante
            while j >= 0:
                valor_comparado = self.obtener_valor(datos[j], criterio)

                debe_desplazar = (
                    valor_comparado > valor_actual if ascendente
                    else valor_comparado < valor_actual
                )

                if not debe_desplazar:
                    break

                datos[j + 1] = datos[j]
                j -= 1

            datos[j + 1] = elemento_actual

        return datos


class Merge(AlgoritmoOrdenamiento):
    """
    Divide la lista a la mitad recursivamente hasta tener listas de un solo elemento,
    y luego las combina (mezcla) de forma ordenada
    """

    def ordenar(self, lista, criterio, ascendente=True):
        datos = lista.copy()
        return self._dividir_y_ordenar(datos, criterio, ascendente)

    def _dividir_y_ordenar(self, datos, criterio, ascendente):
        # Caso base: una lista de 0 o 1 elementos ya está ordenada
        if len(datos) <= 1:
            return datos

        # Dividimos la lista por la mitad
        medio = len(datos) // 2
        mitad_izquierda = datos[:medio]
        mitad_derecha = datos[medio:]

        # Ordenamos cada mitad recursivamente
        izquierda_ordenada = self._dividir_y_ordenar(mitad_izquierda, criterio, ascendente)
        derecha_ordenada = self._dividir_y_ordenar(mitad_derecha, criterio, ascendente)

        # Combinamos las dos mitades ya ordenadas
        return self._combinar(izquierda_ordenada, derecha_ordenada, criterio, ascendente)

    def _combinar(self, izquierda, derecha, criterio, ascendente):
        resultado = []
        i, j = 0, 0

        # Vamos comparando el primero de cada mitad, y tomamos el "mejor"
        while i < len(izquierda) and j < len(derecha):
            valor_izq = self.obtener_valor(izquierda[i], criterio)
            valor_der = self.obtener_valor(derecha[j], criterio)

            va_primero_izquierda = (
                valor_izq <= valor_der if ascendente
                else valor_izq >= valor_der
            )

            if va_primero_izquierda:
                resultado.append(izquierda[i])
                i += 1
            else:
                resultado.append(derecha[j])
                j += 1

        # Agregamos lo que haya quedado sin comparar en cualquiera de las dos mitades
        resultado.extend(izquierda[i:])
        resultado.extend(derecha[j:])

        return resultado


class Quick(AlgoritmoOrdenamiento):
    """
    Elige un pivote y reorganiza la lista en tres zonas: menores, iguales y
    mayores que el pivote. Luego repite el proceso en las zonas de menores
    y mayores.

    Mejoras frente a la versión clásica:
    - Pivote aleatorio: evita el peor caso con listas ya ordenadas.
    - Partición en tres zonas: los valores repetidos (por ejemplo, el mismo
      departamento en todos los registros) quedan juntos y no se vuelven a
      procesar, así que no hay recursión excesiva ni lentitud.
    - Se recurre solo sobre la zona más pequeña y se itera sobre la grande,
      por lo que la profundidad de la recursión es de O(log n).
    """

    def ordenar(self, lista, criterio, ascendente=True):
        datos = lista.copy()
        self._quicksort(datos, 0, len(datos) - 1, criterio, ascendente)
        return datos

    def _quicksort(self, datos, inicio, fin, criterio, ascendente):
        while inicio < fin:
            limite_menores, limite_mayores = self._particionar(
                datos, inicio, fin, criterio, ascendente
            )

            # Recursión sobre la zona más pequeña; la grande se sigue en el while
            if limite_menores - inicio < fin - limite_mayores:
                self._quicksort(datos, inicio, limite_menores - 1, criterio, ascendente)
                inicio = limite_mayores + 1
            else:
                self._quicksort(datos, limite_mayores + 1, fin, criterio, ascendente)
                fin = limite_menores - 1

    def _particionar(self, datos, inicio, fin, criterio, ascendente):
        """
        Deja la lista así:  [ antes del pivote | iguales al pivote | después ]
        y devuelve (primer_indice_de_iguales, ultimo_indice_de_iguales).
        """
        pivote = self.obtener_valor(datos[random.randint(inicio, fin)], criterio)

        menor = inicio   # frontera de la zona "antes del pivote"
        actual = inicio  # elemento que se está revisando
        mayor = fin      # frontera de la zona "después del pivote"

        while actual <= mayor:
            valor = self.obtener_valor(datos[actual], criterio)

            if valor == pivote:
                actual += 1
                continue

            va_antes = valor < pivote if ascendente else valor > pivote

            if va_antes:
                datos[menor], datos[actual] = datos[actual], datos[menor]
                menor += 1
                actual += 1
            else:
                datos[actual], datos[mayor] = datos[mayor], datos[actual]
                mayor -= 1

        return menor, mayor


class Counting(AlgoritmoOrdenamiento):
    """
    Cuenta cuántas veces aparece cada valor entero, y usa esas cuentas 
    para reconstruir la lista ya ordenada, solo funciona con criterios numéricos enteros.

    Como crea una lista del tamaño del rango de valores (máximo - mínimo),
    se rechaza si ese rango es demasiado grande para no agotar la memoria.
    """

    RANGO_MAXIMO = 1_000_000

    def ordenar(self, lista, criterio, ascendente=True):
        datos = lista.copy()
        if not datos:
            return datos

        valores = [self.obtener_valor(obj, criterio) for obj in datos]

        if not all(isinstance(v, int) for v in valores):
            raise TypeError(
                f"Counting Sort solo funciona con valores enteros. "
                f"El criterio '{criterio}' no es de tipo entero."
            )

        valor_min = min(valores)
        valor_max = max(valores)
        rango = valor_max - valor_min + 1

        if rango > self.RANGO_MAXIMO:
            raise ValueError(
                f"Counting Sort no es adecuado para '{criterio}': los valores "
                f"van de {valor_min} a {valor_max} (rango de {rango:,}), "
                f"demasiado amplio. Usa otro algoritmo, como Merge o Heap."
            )

        # Conteo: cuántas veces aparece cada valor
        conteo = [0] * rango
        for v in valores:
            conteo[v - valor_min] += 1

        # Sumas acumuladas: nos dicen en qué posición final va cada valor
        for i in range(1, rango):
            conteo[i] += conteo[i - 1]

        # Construimos el resultado recorriendo de atrás hacia adelante
        # (esto mantiene el orden relativo de elementos con el mismo valor)
        resultado = [None] * len(datos)
        for i in range(len(datos) - 1, -1, -1):
            valor = valores[i]
            posicion = conteo[valor - valor_min] - 1
            resultado[posicion] = datos[i]
            conteo[valor - valor_min] -= 1

        if not ascendente:
            resultado.reverse()

        return resultado


class Radix(AlgoritmoOrdenamiento):
    """
    Ordena números enteros dígito por dígito,
    de menos a más significativo, usando Counting Sort como paso interno
    """

    def ordenar(self, lista, criterio, ascendente=True):
        datos = lista.copy()
        if not datos:
            return datos

        valores = [self.obtener_valor(obj, criterio) for obj in datos]

        if not all(isinstance(v, int) and v >= 0 for v in valores):
            raise TypeError(
                f"Radix Sort solo funciona con enteros no negativos. "
                f"El criterio '{criterio}' no cumple esa condición."
            )

        valor_maximo = max(valores)
        exp = 1  # posición del dígito actual: 1=unidades, 10=decenas, 100=centenas...

        # Repetimos mientras queden dígitos por revisar en el número más grande
        while valor_maximo // exp > 0:
            datos = self._counting_sort_por_digito(datos, criterio, exp)
            exp *= 10

        if not ascendente:
            datos.reverse()

        return datos

    def _counting_sort_por_digito(self, datos, criterio, exp):
        n = len(datos)
        resultado = [None] * n
        conteo = [0] * 10  # los dígitos van de 0 a 9

        # Contamos cuántas veces aparece cada dígito en esta posición
        for obj in datos:
            valor = self.obtener_valor(obj, criterio)
            digito = (valor // exp) % 10
            conteo[digito] += 1

        # Sumas acumuladas
        for i in range(1, 10):
            conteo[i] += conteo[i - 1]

        # Construimos el resultado de atrás hacia adelante (estabilidad)
        for i in range(n - 1, -1, -1):
            valor = self.obtener_valor(datos[i], criterio)
            digito = (valor // exp) % 10
            resultado[conteo[digito] - 1] = datos[i]
            conteo[digito] -= 1

        return resultado


class Heap(AlgoritmoOrdenamiento):
    """
    Construye un montículo (heap) binario con
    los datos, y extrae repetidamente el elemento máximo (o mínimo)
    para construir la lista ordenada
    """

    def ordenar(self, lista, criterio, ascendente=True):
        datos = lista.copy()
        n = len(datos)

        # Construimos el heap inicial (reorganizamos todos los "padres")
        for i in range(n // 2 - 1, -1, -1):
            self._hundir(datos, n, i, criterio, ascendente)

        # Extraemos el elemento raíz uno por uno
        for i in range(n - 1, 0, -1):
            datos[0], datos[i] = datos[i], datos[0]
            self._hundir(datos, i, 0, criterio, ascendente)

        return datos

    def _hundir(self, datos, n, raiz, criterio, ascendente):
        """
        Reorganiza el heap para que el nodo 'raiz' quede en su
        posición correcta respecto a sus hijos (izquierdo y derecho).
        """
        mejor = raiz
        izquierdo = 2 * raiz + 1
        derecho = 2 * raiz + 2

        def es_mejor(indice_a, indice_b):
            valor_a = self.obtener_valor(datos[indice_a], criterio)
            valor_b = self.obtener_valor(datos[indice_b], criterio)
            return valor_a > valor_b if ascendente else valor_a < valor_b

        if izquierdo < n and es_mejor(izquierdo, mejor):
            mejor = izquierdo

        if derecho < n and es_mejor(derecho, mejor):
            mejor = derecho

        if mejor != raiz:
            datos[raiz], datos[mejor] = datos[mejor], datos[raiz]
            self._hundir(datos, n, mejor, criterio, ascendente)


class Bucket(AlgoritmoOrdenamiento):
    """
    Este algoritmo distribuye los elementos en "baldes" según
    su rango de valores, ordena cada balde individualmente, y luego
    concatena todos los baldes en orden.
    """

    def ordenar(self, lista, criterio, ascendente=True, num_baldes=10):
        datos = lista.copy()
        if not datos:
            return datos

        valores = [self.obtener_valor(obj, criterio) for obj in datos]

        if not all(isinstance(v, (int, float)) for v in valores):
            raise TypeError(
                f"Bucket Sort solo funciona con valores numéricos. "
                f"El criterio '{criterio}' no es de tipo numérico."
            )

        valor_min = min(valores)
        valor_max = max(valores)

        # Si todos los valores son iguales, ya está "ordenado"
        if valor_min == valor_max:
            return datos

        rango = valor_max - valor_min
        baldes = [[] for _ in range(num_baldes)]

        # Distribuimos cada elemento en su balde correspondiente
        for obj in datos:
            valor = self.obtener_valor(obj, criterio)
            indice_balde = int((valor - valor_min) / rango * (num_baldes - 1))
            baldes[indice_balde].append(obj)

        # Ordenamos cada balde individualmente (con inserción, son pocos elementos)
        for balde in baldes:
            self._ordenar_balde(balde, criterio, ascendente)

        # Concatenamos todos los baldes en orden
        resultado = []
        for balde in baldes:
            resultado.extend(balde)

        if not ascendente:
            resultado.reverse()

        return resultado

    def _ordenar_balde(self, balde, criterio, ascendente):
        """Ordena un balde individual usando inserción (son pocos elementos)."""
        for i in range(1, len(balde)):
            actual = balde[i]
            valor_actual = self.obtener_valor(actual, criterio)
            j = i - 1

            while j >= 0:
                valor_comparado = self.obtener_valor(balde[j], criterio)
                if valor_comparado <= valor_actual:
                    break
                balde[j + 1] = balde[j]
                j -= 1

            balde[j + 1] = actual
