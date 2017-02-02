#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rutina de actualización diaria del repositorio libreria-catalogos."""
import os
import sys
import warnings
import glob
import filecmp
import arrow
import requests
import yaml
import sh
from pydatajson.readers import read_catalog
from pydatajson.writers import write_json_catalog
from pydatajson import DataJson

DIR_RAIZ = os.getcwd()
DIR_ARCHIVO = os.path.join(DIR_RAIZ, "archivo/")
HOY = arrow.now()
FECHA_HOY = HOY.format("YYYY-MM-DD")
DIR_HOY = os.path.join(DIR_ARCHIVO, FECHA_HOY)
INDICE = os.path.join(DIR_RAIZ, "indice.yml")
with open(INDICE) as config_file:
    ORGANISMOS = yaml.load(config_file)
GIT = sh.git.bake(_cwd=DIR_RAIZ)


def crear_dirs_organismos():
    """Para cada organismo del indice, crear un directorio si no existe."""
    for organismo in ORGANISMOS.keys():
        if not os.path.isdir(organismo):
            os.mkdir(organismo)


def crear_dir_hoy():
    """Creo el directorio para descargar los archivos diarios."""
    if not os.path.isdir(DIR_ARCHIVO):
        os.mkdir(DIR_ARCHIVO)

    os.chdir(DIR_ARCHIVO)

    if not os.path.isdir(FECHA_HOY):
        os.mkdir(FECHA_HOY)


def guardar_resultado_get(url, nombre_archivo=None):
    """Guardo el resultado de un request GET a disco."""
    nombre_archivo = nombre_archivo or url.split("/")[-1]
    res = requests.get(url)
    with open(nombre_archivo, 'w') as archivo:
        archivo.write(res.content)


def nombre_catalogo(alias_organismo):
    """Devuelve el nombre local dado al catálogo de un organismo. Puede ser
    'data.xlsx' o 'data.json', según sea su 'formato'."""
    formato = ORGANISMOS[alias_organismo].get("formato")
    assert_msg = """
ERROR: {} no define un 'formato' para su catálogo""".format(alias_organismo)
    assert formato is not None, assert_msg
    nombre = "data.{}".format(formato)

    return nombre


def descargar_catalogo(alias_organismo):
    """Descarga el catálogo de un organismo según especifican sus variables de
    configuración."""
    config = ORGANISMOS[alias_organismo]
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
    os.chdir(DIR_RAIZ)

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
    # Creo un objeto DataJson para ejecutar validaciones por organismo:
    dj = DataJson()

    # Si un organismo no tiene directorio bajo control de versiones, lo creo
    crear_dirs_organismos()

    # Creo el archivo para el día de hoy, con sus directorios por organismo
    crear_dir_hoy()
    os.chdir(DIR_HOY)
    crear_dirs_organismos()

    # Descargo los catálogos de cada organismo
    for (organismo, config) in ORGANISMOS.iteritems():
        os.chdir(organismo)
        descargar_catalogo(organismo)

        # Para los catálogos en formato XLSX, genero el JSON correspondiente
        if config["formato"] == "xlsx":
            catalogo = read_catalog(nombre_catalogo(organismo))
            write_json_catalog(catalogo, "data.json")

        # Genero el README y los reportes auxiliares
        dj.generate_catalog_readme(catalogo, export_path="README.md")
        dj.generate_datasets_summary(catalogo, export_path="datasets.csv")

        # Retorno a la raíz antes de comenzar con el siguiente organismo
        os.chdir("..")

    os.chdir(DIR_RAIZ)

    # Actualizo las carpetas bajo control de versiones
    archivos_del_dia = glob.glob("{}/*/*".format(DIR_HOY))
    for archivo in archivos_del_dia:
        actualizar_versionado(archivo)

    # Pusheo los cambios encontrados.
    GIT.push("origin", "master")

if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        rutina = args.pop(0)
        if rutina == "rutina_diaria":
            rutina_diaria()
        else:
            warnings.warn("No se reconoce el argumento {}".format(rutina))
