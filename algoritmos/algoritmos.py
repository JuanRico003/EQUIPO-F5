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
    Elige un pivote, reorganiza la lista para que los menores queden a la izquierda
    y los mayores a la derecha, y repite recursivamente en cada mitad.
    """

    def ordenar(self, lista, criterio, ascendente=True):
        datos = lista.copy()
        self._quicksort(datos, 0, len(datos) - 1, criterio, ascendente)
        return datos

    def _quicksort(self, datos, inicio, fin, criterio, ascendente):
        if inicio < fin:
            posicion_pivote = self._particionar(datos, inicio, fin, criterio, ascendente)

            # Ordenamos recursivamente lo que quedó antes y después del pivote
            self._quicksort(datos, inicio, posicion_pivote - 1, criterio, ascendente)
            self._quicksort(datos, posicion_pivote + 1, fin, criterio, ascendente)

    def _particionar(self, datos, inicio, fin, criterio, ascendente):
        # Elegimos el último elemento como pivote
        pivote = self.obtener_valor(datos[fin], criterio)
        i = inicio - 1  # marca el límite de "los menores que el pivote"

        for j in range(inicio, fin):
            valor_actual = self.obtener_valor(datos[j], criterio)

            pertenece_a_la_izquierda = (
                valor_actual <= pivote if ascendente
                else valor_actual >= pivote
            )

            if pertenece_a_la_izquierda:
                i += 1
                datos[i], datos[j] = datos[j], datos[i]

        # Colocamos el pivote en su posición final correcta
        datos[i + 1], datos[fin] = datos[fin], datos[i + 1]
        return i + 1


class Counting(AlgoritmoOrdenamiento):
    """
    Cuenta cuántas veces aparece cada valor entero, y usa esas cuentas 
    para reconstruir la lista ya ordenada, solo funciona con criterios numéricos enteros
    """

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
