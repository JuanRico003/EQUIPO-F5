from api.cliente_api import ClienteAPI
from ui.menu import MenuConsola

URL_API = "https://www.datos.gov.co/resource/hibb-cqit.json"


def main():
    cliente = ClienteAPI(URL_API)
    beneficiarios = cliente.obtener_beneficiarios()

    menu = MenuConsola(beneficiarios)
    menu.iniciar()


if __name__ == "__main__":
    main()