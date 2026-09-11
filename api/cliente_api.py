import requests
from json import JSONDecodeError
from api.modelo import RegistroBeneficiario


class ClienteAPI:
    """
    Se encarga de conectarse a la API de datos.gov.co y traer
    los registros de beneficiarios ya convertidos a objetos.
    """

    def __init__(self, url_api):
        self.url_api = url_api

    def obtener_beneficiarios(self):
    
        try:
            respuesta = requests.get(self.url_api, timeout=10)
            respuesta.raise_for_status()
            datos_json = respuesta.json()

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
        except JSONDecodeError:
            print("Error, la API respondió, pero el contenido no es JSON válido.")
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