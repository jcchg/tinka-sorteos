"""
---------------------------------------------------------
Tinka Auto Update
Versión : 1.2.0

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
    """
    Busca el bloque principal del sorteo usando como bandera el texto
    'Tinka Sorteo'. Luego extrae:
        - número de sorteo
        - fecha del sorteo

    Acepta fechas con día/mes de 1 o 2 dígitos:
        1/07/2026
        01/07/2026
        1/7/2026
        01/07/2026
    """
    soup = BeautifulSoup(html, "html.parser")

    # Buscar todos los h3 y quedarnos con el que realmente contiene
    # el encabezado del sorteo.
    titulos = soup.find_all("h3")

    for titulo in titulos:
        texto = titulo.get_text(" ", strip=True)

        if "Tinka Sorteo" not in texto:
            continue

        # Permitir día y mes de 1 o 2 dígitos.
        patron = r"Tinka Sorteo\s+(\d+),\s*Fecha:\s*(\d{1,2}/\d{1,2}/\d{4})"
        resultado = re.search(patron, texto)

        if resultado:
            numero_sorteo = int(resultado.group(1))
            fecha = resultado.group(2)
            return numero_sorteo, fecha

    return None, None


def obtener_numeros(html):
    """
    Obtiene los 6 números de la jugada ganadora.

    Estrategia:
    1. Buscar el h3 que contiene 'Tinka Sorteo'.
    2. Ir al primer <p> que viene después de ese h3.
       Ese <p> contiene únicamente los 6 números de la jugada ganadora.
    3. Ignorar los números del bloque 'Sí o Sí' y 'Boliyapa'.
    """
    soup = BeautifulSoup(html, "html.parser")

    titulos = soup.find_all("h3")

    for titulo in titulos:
        texto = titulo.get_text(" ", strip=True)

        if "Tinka Sorteo" not in texto:
            continue

        # El primer <p> después del título contiene los 6 números
        # de la jugada ganadora.
        parrafo = titulo.find_next("p")
        if parrafo is None:
            return None

        numeros = []

        for span in parrafo.find_all("span"):
            t = span.get_text(strip=True)

            # Aceptar números como 06, 03, etc.
            if t.isdigit():
                numeros.append(int(t))

        if len(numeros) != 6:
            return None

        numeros.sort()
        return numeros

    return None


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


def normalizar_fecha(fecha):
    """
    Convierte una fecha como:
        1/7/2026
        1/07/2026
        01/7/2026
        01/07/2026

    al formato fijo:
        dd/mm/yyyy
    """
    try:
        partes = fecha.strip().split("/")
        if len(partes) != 3:
            return fecha.strip()

        dia = partes[0].zfill(2)
        mes = partes[1].zfill(2)
        anio = partes[2]

        return f"{dia}/{mes}/{anio}"
    except Exception:
        return fecha


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

    fecha = normalizar_fecha(fecha)
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

    # Normalizar ambas fechas antes de compararlas
    fecha_archivo_normalizada = normalizar_fecha(fecha_archivo) if fecha_archivo else None
    fecha_web_normalizada = normalizar_fecha(fecha)

    print(f"Última fecha del archivo : {fecha_archivo_normalizada}")
    print(f"Fecha encontrada en web  : {fecha_web_normalizada}")

    if fecha_archivo_normalizada is None:
        error("No fue posible obtener la última fecha de sorteos.txt.")
        return

    if fecha_web_normalizada == fecha_archivo_normalizada:
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
