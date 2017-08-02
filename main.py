#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rutina de actualización diaria del repositorio libreria-catalogos."""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import os
import sys
import glob
import filecmp
import logging
import arrow
import requests
import yaml
import sh
import urllib3

from pydatajson.readers import read_catalog, read_ckan_catalog
from pydatajson.writers import write_json_catalog
from pydatajson import DataJson

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT_DIR = os.getcwd()
ARCHIVE_DIR = 'archivo'
TODAY = arrow.now()
DATE_TODAY = TODAY.format('YYYY-MM-DD')
TODAY_DIR = os.path.join(ARCHIVE_DIR, DATE_TODAY)
INDEX = os.path.join(ROOT_DIR, 'indice.yml')
with open(INDEX) as config_file:
    ORGANISMS = yaml.load(config_file)

GIT = sh.git.bake(_cwd=ROOT_DIR)

# Logging config
logger = logging.getLogger("libreria-catalogos")
logger.setLevel(logging.INFO)
FORMAT = logging.Formatter(
    fmt=u'%(asctime)s [%(levelname)s]: %(message)s',
    datefmt=u'%m/%d/%Y %I:%M:%S'
)
HANDLER = logging.FileHandler(
    filename='logs/{}-rutina_diaria.log'.format(DATE_TODAY)
)
HANDLER.setFormatter(FORMAT)
logger.addHandler(HANDLER)
logger.propagate = False


def ensure_dir_exists(target_dir):
    """Crea el directorio que llega como parámetro si no existe."""
    start_dir = os.getcwd()

    if not os.path.isdir(target_dir):
        for dirr in target_dir.split(os.path.sep):
            if not os.path.isdir(dirr):
                os.mkdir(dirr)
            os.chdir(dirr)

    os.chdir(start_dir)


def catalog_name(org_alias):
    """Devuelve el nombre local dado al catálogo de un organismo. Puede ser
    'data.xlsx' o 'data.json', según sea su 'formato'."""
    extension = ORGANISMS[org_alias].get('formato')
    assert_msg = """
ERROR: {} no define un 'formato' para su catálogo""".format(org_alias)
    assert extension is not None, assert_msg
    name = 'data.{}'.format(extension)

    return name


def versioning_assistant(daily_file):
    """Devuelve la información de un archivo diario necesaria para actualizar
    las carpetas bajo control de versiones.

    Args:
        daily_file (str): Versión descargada diariamente de un archivo.

    Returns:
        version_file (str): Ubicación bajo control de versiones de ese
            mismo archivo.
        organism (str): Nombre del organismo al que pertenece el archivo.
        file_date (str): Fecha en la que se generó el archivo diario.

    Examples:
        ubicacion_versionada("archivo/2020-12-25/justicia/data.xlsx")
        > "justicia/data.xlsx"
    """
    parts = daily_file.split('/')

    version_file = '/'.join(parts[-2:])
    organism = parts[-2]
    file_date = parts[-3]

    return version_file, organism, file_date


def update_versioning(daily_file):
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

    version_file, _, file_date = versioning_assistant(daily_file)

    if not os.path.isfile(version_file):
        # File is not on version control.
        commit_msg = 'Agrego archivo {} encontrado el {}'.format(
            version_file, file_date)
    elif not filecmp.cmp(daily_file, version_file):
        # daily_file and version_file differ.
        commit_msg = 'Modifico archivo {} según cambios del {}'.format(
            version_file, file_date)
    else:
        # No changes between daily_file and version_file.
        commit_msg = None

    # Commit if appropriate.
    if commit_msg:
        sh.cp(daily_file, version_file)
        GIT.add(version_file)
        GIT.commit(m=commit_msg)


def process_catalog(org, datajson):
    """Descarga y procesa el catálogo correspondiente a la organización."""
    logger.info('=== Catálogo %s ===', org.upper())
    os.chdir(org)
    try:
        config = ORGANISMS[org]

        logger.info('- Lectura de catálogo')
        # For XLSX catalogs, creates corresponding JSON
        file_ext = config["formato"]
        if file_ext == 'xlsx':
            res = requests.get(config['url'])
            with open('data.xlsx', 'w') as xlsx_file:
                xlsx_file.write(res.content)
            logger.info('- Transformación de XLSX a JSON')
            catalog = read_catalog('data.xlsx')

        elif file_ext == 'json':
            catalog = read_catalog(config['url'])

        elif file_ext == 'ckan':
            catalog = read_ckan_catalog(config['url'])

        else:
            raise ValueError(
                '%s no es una extension valida para un catalogo.', file_ext)

        logger.info('- Escritura de catálogo')
        write_json_catalog(catalog, 'data.json')

        # Creates README and auxiliary reports
        logger.info('- Generación de reportes')
        datajson.generate_catalog_readme(catalog, export_path='README.md')
        datajson.generate_datasets_summary(catalog, export_path='datasets.csv')
    except:
        logger.error(
            'Error al procesar el catálogo de %s', org, exc_info=True)
    finally:
        os.chdir('..')  # Returns to parent dir.


def daily_routine():
    """Rutina a ser ejecutada cada mañana por cron."""

    logger.info('>>> COMIENZO DE LA RUTINA <<<')

    # Creates DataJson object to validate oragnisms
    logger.info('Instanciación DataJson')
    datajson = DataJson()

    logger.info('Creación de carpetas necesarias (de archivo y versionadas).')
    for org in ORGANISMS:
        ensure_dir_exists(org)
        ensure_dir_exists(os.path.join(TODAY_DIR, org))

    logger.info('Procesamiento de cada organismo:')
    os.chdir(TODAY_DIR)

    for org in ORGANISMS:
        process_catalog(org, datajson)

    os.chdir(ROOT_DIR)

    logger.info('Actualizo los archivos bajo control de versiones:')
    files_of_day = glob.glob('{}/*/*'.format(TODAY_DIR))
    for filename in files_of_day:
        logger.debug('- %s', filename)
        update_versioning(filename)

    logger.info('Push de los cambios encontrados.')
    GIT.push('origin', 'master')

    logger.info('>>> FIN DE LA RUTINA <<<')


if __name__ == '__main__':
    daily_routine()
