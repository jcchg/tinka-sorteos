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
    Busca el texto que contiene 'Tinka Sorteo' sin depender
    de una etiqueta HTML específica.

    Extrae:
        - número de sorteo
        - fecha del sorteo
    """

    soup = BeautifulSoup(html, "html.parser")

    print()
    info("Buscando número y fecha del sorteo...")

    elementos = soup.find_all(
        string=lambda texto: texto and "Tinka Sorteo" in texto
    )

    for elemento in elementos:

        texto = elemento.strip()

        print(f"[DEBUG] Texto encontrado: {texto}")

        # Buscar el número del sorteo
        resultado_sorteo = re.search(
            r"Tinka\s+Sorteo\s+(\d+)",
            texto,
            re.IGNORECASE
        )

        if not resultado_sorteo:
            print(
                "[DEBUG] Se encontró 'Tinka Sorteo', "
                "pero no se pudo obtener el número."
            )
            continue

        numero_sorteo = int(resultado_sorteo.group(1))

        # La fecha está actualmente dentro de una etiqueta <time>
        fecha_elemento = elemento.parent.find("time")

        if fecha_elemento is None:
            print("[DEBUG] No se encontró la etiqueta <time>.")
            continue

        fecha = fecha_elemento.get_text(strip=True)

        print(
            f"[DEBUG] Coincidencia encontrada: "
            f"sorteo={numero_sorteo}, fecha={fecha}"
        )

        return numero_sorteo, fecha

    return None, None


def obtener_numeros(html):
    """
    Obtiene los 6 números de la jugada ganadora.

    Busca el elemento que contiene 'Tinka Sorteo' y,
    dentro de la misma tarjeta de resultados, busca
    el párrafo con clase 'balls'.
    """

    soup = BeautifulSoup(html, "html.parser")

    elementos = soup.find_all(
        string=lambda texto: texto and "Tinka Sorteo" in texto
    )

    for elemento in elementos:

        tarjeta = elemento.find_parent("section", class_="result-card")

        if tarjeta is None:
            print("[DEBUG] No se encontró la tarjeta de resultados.")
            continue

        parrafo = tarjeta.find("p", class_="balls")

        if parrafo is None:
            print("[DEBUG] No se encontró el bloque de números.")
            continue

        numeros = []

        for span in parrafo.find_all("span", class_="ball"):
            texto_numero = span.get_text(strip=True)

            if texto_numero.isdigit():
                numeros.append(int(texto_numero))

        print(f"[DEBUG] Números encontrados: {numeros}")

        if len(numeros) != 6:
            print(
                f"[DEBUG] Se esperaban 6 números, "
                f"pero se encontraron {len(numeros)}."
            )
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
        with open(RUTA_ARCHIVO, "a+", encoding="utf-8") as archivo:
            archivo.seek(0, 2)  # ir al final del archivo
            tamaño = archivo.tell()

            # Solo agregar salto de línea si el archivo no está vacío
            # y no termina ya con salto de línea.
            if tamaño > 0:
                archivo.seek(tamaño - 1)
                ultimo = archivo.read(1)
                if ultimo != "\n":
                    archivo.write("\n")

            archivo.write("\n".join(lineas))

        print()
        ok("Nuevo sorteo agregado a sorteos.txt.")

    except Exception as e:
        print()
        error(f"No se pudo actualizar sorteos.txt: {e}")
        return


if __name__ == "__main__":
    main()
