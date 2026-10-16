import requests
from json import JSONDecodeError
from api.modelo import RegistroBeneficiario


class ClienteAPI:
    """
    Se encarga de conectarse a la API de datos.gov.co y traer
    los registros de beneficiarios ya convertidos a objetos.
    """

    TAMANO_PAGINA = 1000  # registros que se piden por petición

    def __init__(self, url_api, limite_total=None):
        """
        limite_total: máximo de registros a descargar (None = todos).
        """
        self.url_api = url_api
        self.limite_total = limite_total

    def _descargar_todo(self):
        """
        Descarga los registros página por página. Socrata devuelve solo 1000
        por petición, así que se usa $limit/$offset hasta que no queden más.
        """
        datos_json = []
        desplazamiento = 0

        while True:
            tamano = self.TAMANO_PAGINA
            if self.limite_total is not None:
                faltan = self.limite_total - len(datos_json)
                if faltan <= 0:
                    break
                tamano = min(tamano, faltan)

            respuesta = requests.get(
                self.url_api,
                params={
                    "$limit": tamano,
                    "$offset": desplazamiento,
                    "$order": ":id",  # orden estable para que las páginas no se repitan
                },
                timeout=10,
            )
            respuesta.raise_for_status()
            pagina = respuesta.json()

            if not isinstance(pagina, list):
                raise ValueError("La API devolvió un formato inesperado.")

            datos_json.extend(pagina)

            # Si llegó una página incompleta, ya no hay más datos
            if len(pagina) < tamano:
                break

            desplazamiento += tamano

        return datos_json

    def obtener_beneficiarios(self):

        try:
            datos_json = self._descargar_todo()

            if not datos_json:
                print("La API respondió correctamente, pero no trajo datos.")
                return []

            beneficiarios = []
            for registro in datos_json:
                try:
                    beneficiario = RegistroBeneficiario.desde_json(registro)
                    beneficiarios.append(beneficiario)
                except (ValueError, KeyError) as e:
                    print(f"Se omitió un registro con datos inválidos: {e}")
                    continue

            return beneficiarios
        except (JSONDecodeError, ValueError):
            print("Error, la API respondió, pero el contenido no es JSON válido o no tiene el formato esperado.")
            return []
        except requests.exceptions.Timeout:
            print("Error, la API tardó demasiado en responder. Intenta de nuevo más tarde.")
            return []
        except requests.exceptions.ConnectionError:
            print("Error, no hay conexión a internet o la API no está disponible.")
            return []
        
        except requests.exceptions.RequestException as e:
            print(f"Error inesperado al conectar con la API: {e}")
            return []