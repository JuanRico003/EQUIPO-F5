from abc import ABC, abstractmethod


class AlgoritmoOrdenamiento(ABC):
    """
    Clase base abstracta para todos los algoritmos de ordenamiento.
    """

    @abstractmethod
    def ordenar(self, lista, criterio, ascendente=True):
        """
        Ordena 'lista' (de objetos RegistroBeneficiario) según el
        atributo indicado en 'criterio'
        """
        pass

    def obtener_valor(self, objeto, criterio):
        """
        Método auxiliar compartido por todos los algoritmos
        """
        return getattr(objeto, criterio)