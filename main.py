from api.cliente_api import ClienteAPI
from ui.menu import MenuConsola

URL_API = "https://www.datos.gov.co/resource/hibb-cqit.json"

# Máximo de registros a descargar (None = todos). Los algoritmos O(n²)
# (Burbuja, Selección, Inserción) se vuelven lentos con decenas de miles.
LIMITE_REGISTROS = 50000


def main():
    cliente = ClienteAPI(URL_API, LIMITE_REGISTROS)
    beneficiarios = cliente.obtener_beneficiarios()

    menu = MenuConsola(beneficiarios)
    menu.iniciar()


if __name__ == "__main__":
    main()