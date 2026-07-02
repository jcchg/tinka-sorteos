"""
---------------------------------------------------------
Tinka Auto Update
Versión : 1.1.0

Autor : Carlos + ChatGPT
---------------------------------------------------------
"""

import requests
from bs4 import BeautifulSoup
import re

VERSION = "1.2.0"

URL = "https://www.tinkaresultados.com/"
RUTA_ARCHIVO = "sorteos.txt"


def info(texto):
    print(f"[INFO] {texto}")


def ok(texto):
    print(f"[ OK ] {texto}")


def error(texto):
    print(f"[ERROR] {texto}")


def descargar_html():
    info("Conectando con Tinka Resultados...")
    try:
        respuesta = requests.get(URL, timeout=15)
        respuesta.raise_for_status()
        ok("Página descargada correctamente.")
        return respuesta.text
    except Exception as e:
        error(e)
        return None


def obtener_sorteo_y_fecha(html):
    soup = BeautifulSoup(html, "html.parser")
    titulo = soup.find("h3")
    if titulo is None:
        return None, None

    texto = titulo.get_text(" ", strip=True)
    patron = r"Tinka Sorteo\s+(\d+),\s*Fecha:\s*(\d{2}/\d{2}/\d{4})"
    resultado = re.search(patron, texto)

    if resultado:
        return int(resultado.group(1)), resultado.group(2)

    return None, None


def obtener_numeros(html):
    soup = BeautifulSoup(html, "html.parser")
    titulo = soup.find("h3")
    if titulo is None:
        return None

    parrafo = titulo.find_next("p")
    if parrafo is None:
        return None

    numeros = []
    for span in parrafo.find_all("span"):
        t = span.get_text(strip=True)
        if t.isdigit():
            numeros.append(int(t))

    if len(numeros) != 6:
        return None

    numeros.sort()
    return numeros


def obtener_ganador(html):
    soup = BeautifulSoup(html, "html.parser")

    for fila in soup.find_all("tr"):
        columnas = fila.find_all("td")
        if len(columnas) < 2:
            continue

        categoria = columnas[0].get_text(" ", strip=True).lower()

        if categoria == "6 aciertos":
            valor = columnas[1].get_text(strip=True)
            if valor in ("0", "1"):
                return int(valor)
            return None

    return None


def crear_lineas_sorteo(numeros, fecha, ganador):
    return [f"{n};{fecha};{ganador}" for n in numeros]


def leer_sorteos():
    try:
        with open(RUTA_ARCHIVO, "r", encoding="utf-8") as archivo:
            return [l.strip() for l in archivo if l.strip()]
    except Exception as e:
        error(e)
        return None


def obtener_ultima_fecha(lineas):
    if not lineas:
        return None

    partes = lineas[-1].split(";")
    if len(partes) != 3:
        return None

    return partes[1]


def main():
    print("=" * 50)
    print(" Tinka Auto Update")
    print(f" Versión {VERSION}")
    print("=" * 50)

    html = descargar_html()
    if html is None:
        return

    print()
    info(f"HTML recibido: {len(html)} caracteres")

    with open("pagina.html", "w", encoding="utf-8") as archivo:
        archivo.write(html)

    ok("Archivo pagina.html creado.")

    sorteo, fecha = obtener_sorteo_y_fecha(html)

    print()

    if sorteo is None:
        error("No fue posible obtener el número del sorteo.")
        return

    ok("Sorteo encontrado.")
    print(f"Número de sorteo: {sorteo}")
    print(f"Fecha: {fecha}")

    numeros = obtener_numeros(html)
    print()

    if numeros is None:
        error("No fue posible obtener los números.")
        return

    ok("Números encontrados.")
    print("Números ordenados:")
    print(" - ".join(map(str, numeros)))

    ganador = obtener_ganador(html)
    print()

    if ganador is None:
        error("No fue posible obtener el valor de 6 aciertos.")
        return

    ok("Estado del pozo encontrado.")

    if ganador == 1:
        print("Hubo ganador del pozo principal.")
    else:
        print("No hubo ganador del pozo principal.")

    lineas = crear_lineas_sorteo(numeros, fecha, ganador)
    # ==========================================================
    # Crear el mensaje que utilizará GitHub para el commit.
    #
    # Ejemplo:
    #     Tinka 1311 - 28/06/2026
    # ==========================================================
    mensaje_commit = f"Tinka {sorteo} - {fecha}"

    with open("commit_message.txt", "w", encoding="utf-8") as archivo:

        archivo.write(mensaje_commit)

    print()
    ok("Líneas generadas.")

    for linea in lineas:
        print(linea)

    print()
    lineas_existentes = leer_sorteos()
    if lineas_existentes is None:
        return

    fecha_archivo = obtener_ultima_fecha(lineas_existentes)

    print(f"Última fecha del archivo : {fecha_archivo}")
    print(f"Fecha encontrada en web  : {fecha}")

        # Si no se pudo obtener la última fecha del archivo, detener.
        if fecha_archivo is None:
            error("No fue posible obtener la última fecha de sorteos.txt.")
            return

        # Si la fecha web ya existe en el archivo, no hay nada que actualizar.
        if fecha == fecha_archivo:
            print()
            ok("El archivo ya está actualizado.")
            return

        # Si la fecha web es distinta, se agregan las 6 líneas al final del archivo.
        try:
            with open(RUTA_ARCHIVO, "a", encoding="utf-8") as archivo:
                for linea in lineas:
                    archivo.write("\n" + linea)

            print()
            ok("Nuevo sorteo agregado a sorteos.txt.")

        except Exception as e:
            print()
            error(f"No se pudo actualizar sorteos.txt: {e}")
            return


if __name__ == "__main__":
    main()
