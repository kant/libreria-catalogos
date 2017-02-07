#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rutina de actualización diaria del repositorio libreria-catalogos."""
import os
import sys
import warnings
import glob
import filecmp
import logging
import arrow
import requests
import yaml
import sh
from pydatajson.readers import read_catalog
from pydatajson.writers import write_json_catalog
from pydatajson import DataJson


ROOT_DIR = os.getcwd()
ARCHIVO_DIR = "archivo"
TODAY = arrow.now()
DATE_TODAY = TODAY.format("YYYY-MM-DD")
TODAY_DIR = os.path.join(ARCHIVO_DIR, DATE_TODAY)
INDEX = os.path.join(ROOT_DIR, "indice.yml")
with open(INDEX) as config_file:
    ORGANISMS = yaml.load(config_file)

GIT = sh.git.bake(_cwd=ROOT_DIR)


def ensure_dir_exists(target_dir):
    start_dir = os.getcwd()

    if not os.path.isdir(target_dir):
        for dirr in target_dir.split(os.path.sep):
            if not os.path.isdir(dirr):
                os.mkdir(dirr)
            os.chdir(dirr)

    os.chdir(start_dir)


def guardar_resultado_get(url, nombre_archivo=None):
    """Guardo el resultado de un request GET a disco."""
    nombre_archivo = nombre_archivo or url.split("/")[-1]
    res = requests.get(url)
    with open(nombre_archivo, 'w') as archivo:
        archivo.write(res.content)


def nombre_catalogo(alias_organismo):
    """Devuelve el nombre local dado al catálogo de un organismo. Puede ser
    'data.xlsx' o 'data.json', según sea su 'formato'."""
    formato = ORGANISMS[alias_organismo].get("formato")
    assert_msg = """
ERROR: {} no define un 'formato' para su catálogo""".format(alias_organismo)
    assert formato is not None, assert_msg
    nombre = "data.{}".format(formato)

    return nombre


def descargar_catalogo(alias_organismo):
    """Descarga el catálogo de un organismo según especifican sus variables de
    configuración."""
    config = ORGANISMS[alias_organismo]
    archivo_local = nombre_catalogo(alias_organismo)

    metodo = config.get("metodo")
    if metodo is None or metodo == "get":
        guardar_resultado_get(config["url"], archivo_local)
    else:
        warnings.warn("{} no es un `metodo` valido.".format(metodo))


def generar_json(catalogo_xlsx):
    """ Toma un catálogo en formato XLSX y genera un catálogo con el mismo
    nombre y ubicación, pero extensión y formato JSON."""
    catalogo = read_catalog(catalogo_xlsx)
    with open(catalogo_xlsx.replace("xlsx", "json"), 'w') as catalogo_json:
        write_json_catalog(catalogo, catalogo_json)


def asistente_versionado(archivo_diario):
    """Devuelve la información de un archivo diario necesaria para actualizar
    las carpetas bajo control de versiones.

    Args:
        archivo_diario (str): Versión descargada diariamente de un archivo.

    Returns:
        archivo_versionado (str): Ubicación bajo control de versiones de ese
            mismo archivo.
        organismo (str): Nombre del organismo al que pertenece el archivo.
        fecha (str): Fecha en la que se generó el archivo diario.

    Examples:
        ubicacion_versionada("archivo/2020-12-25/justicia/data.xlsx")
        > "justicia/data.xlsx"
    """
    lista = archivo_diario.split("/")

    archivo_versionado = "/".join(lista[-2:])
    organismo = lista[-2]
    fecha = lista[-3]

    return archivo_versionado, organismo, fecha


def actualizar_versionado(archivo_diario):
    """Actualiza las carpetas bajo control de versiones a partir de los cambios
    existentes entre éstas y el archivo_diario entregado.

    - Si el archivo no existe bajo control de versiones, lo agrega y commitea
        con un mensaje relevante.
    - Si el archivo versionado y el diario son distintos, "pisa" el versionado
    con el diario y commitea los cambios con un mensaje relevante.
    - Si ambos archivos son iguales, no hace nada.

    NOTA: Esta función debe ejecutarse desde la raíz del repositorio.
    """
    # Me aseguro estar ubicado en la raíz del repositorio.
    os.chdir(ROOT_DIR)

    archivo_versionado, _, fecha = asistente_versionado(archivo_diario)

    if not os.path.isfile(archivo_versionado):
        # El archivo no existe bajo control de versiones.
        commit_msg = "Agrego archivo {} encontrado el {}".format(
            archivo_versionado, fecha)
    elif not filecmp.cmp(archivo_diario, archivo_versionado):
        # Las variante diaria y la versionada difieren en su contenido.
        commit_msg = "Modifico archivo {} según cambios del {}".format(
            archivo_versionado, fecha)
    else:
        # No hay cambios entre el archivo diario y el versionado.
        commit_msg = None

    # Si corresponde, genero un commit.
    if commit_msg:
        sh.cp(archivo_diario, archivo_versionado)
        GIT.add(archivo_versionado)
        GIT.commit(m=commit_msg)


def rutina_diaria():
    """Rutina a ser ejecutada cada mañana por cron."""

    # Configuro logging de la sesión
    TODAY = arrow.now().format('YYYY-MM-DD')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S',
                        filename='logs/{}-rutina_diaria.log'.format(TODAY))

    def my_handler(type, value, tb):
        logger.exception("Uncaught exception: {0}".format(str(value)))

    # Install exception handler
    sys.excepthook = my_handler

    logging.info("COMIENZO de la rutina.")

    # Creo un objeto DataJson para ejecutar validaciones por organismo:
    logging.info('Instanciación DataJson')
    dj = DataJson()

    logging.info('Creación de carpetas necesarias (de archivo y versionadas).')
    for organismo in ORGANISMS:
        ensure_dir_exists(organismo)
        ensure_dir_exists(os.path.join(TODAY_DIR, organismo))

    logging.info('Procesamiento de cada organismo:')
    os.chdir(TODAY_DIR)

    for (organismo, config) in ORGANISMS.iteritems():
        # Descargo el catálogo del organismo
        logging.info("=== {} ===".format(organismo.upper()))
        logging.info("- Descarga de catálogo")
        os.chdir(organismo)
        descargar_catalogo(organismo)
        if organismo == "justicia":
            raise AssertionError
        # Para los catálogos en formato XLSX, genero el JSON correspondiente
        if config["formato"] == "xlsx":
            logging.info("- Transformación de XLSX a JSON")
            catalogo = read_catalog(nombre_catalogo(organismo))
            write_json_catalog(catalogo, "data.json")

        # Genero el README y los reportes auxiliares

        logging.info("- Generación de reportes")
        dj.generate_catalog_readme(catalogo, export_path="README.md")
        dj.generate_datasets_summary(catalogo, export_path="datasets.csv")
        # Retorno a la raíz antes de comenzar con el siguiente organismo
        os.chdir("..")

    os.chdir(ROOT_DIR)

    logging.info("Actualizo los archivos bajo control de versiones:")
    archivos_del_dia = glob.glob("{}/*/*".format(TODAY_DIR))
    for archivo in archivos_del_dia:
        logging.debug("- {}".format(archivo))
        actualizar_versionado(archivo)

    logging.info("Pusheo los cambios encontrados.")
    GIT.push("origin", "master")

    logging.info("FIN de la rutina.")


if __name__ == "__main__":
    rutina_diaria()
