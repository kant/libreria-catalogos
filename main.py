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
ARCHIVE_DIR = 'archivo'
TODAY = arrow.now()
DATE_TODAY = TODAY.format('YYYY-MM-DD')
TODAY_DIR = os.path.join(ARCHIVE_DIR, DATE_TODAY)
INDEX = os.path.join(ROOT_DIR, 'indice.yml')
with open(INDEX) as config_file:
    ORGANISMS = yaml.load(config_file)

GIT = sh.git.bake(_cwd=ROOT_DIR)
# Logging config
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S',
                    filename='logs/{}-rutina_diaria.log'.format(DATE_TODAY))


def ensure_dir_exists(target_dir):
    """Crea el directorio que llega como parámetro si no existe."""
    start_dir = os.getcwd()

    if not os.path.isdir(target_dir):
        for dirr in target_dir.split(os.path.sep):
            if not os.path.isdir(dirr):
                os.mkdir(dirr)
            os.chdir(dirr)

    os.chdir(start_dir)


def save_get_result(url, file_name=None):
    """Guarda el resultado de un request GET a disco."""
    file_name = file_name or url.split('/')[-1]
    res = requests.get(url)
    with open(file_name, 'w') as file:
        file.write(res.content)


def catalog_name(org_alias):
    """Devuelve el nombre local dado al catálogo de un organismo. Puede ser
    'data.xlsx' o 'data.json', según sea su 'formato'."""
    extension = ORGANISMS[org_alias].get('formato')
    assert_msg = """
ERROR: {} no define un 'formato' para su catálogo""".format(org_alias)
    assert extension is not None, assert_msg
    name = 'data.{}'.format(extension)

    return name


def download_catalog(org_alias):
    """Descarga el catálogo de un organismo según especifican sus variables de
    configuración."""
    config = ORGANISMS[org_alias]
    local_file = catalog_name(org_alias)

    method = config.get('metodo')
    if method is None or method == 'get':
        save_get_result(config['url'], local_file)
    else:
        warnings.warn('{} no es un `metodo` valido.'.format(method))


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


def process_catalog(org, config, datajson):
    """Descarga y procesa el catálogo correspondiente a la organización."""
    logging.info('=== {} ==='.format(org.upper()))
    os.chdir(org)
    try:
        download_catalog(org)
        logging.info('- Descarga de catálogo')
        if org == 'justicia':
            raise AssertionError
        # For XLSX catalogs, creates corresponding JSON
        if config['formato'] == 'xlsx':
            logging.info('- Transformación de XLSX a JSON')
            catalog = read_catalog(catalog_name(org))
            write_json_catalog(catalog, 'data.json')

        # Creates README and auxiliary reports
        logging.info('- Generación de reportes')
        datajson.generate_catalog_readme(catalog, export_path='README.md')
        datajson.generate_datasets_summary(catalog, export_path='datasets.csv')
    except:
        logging.error('Error al procesar el catálogo de %s', org)
    finally:
        os.chdir('..')  # Returns to parent dir.


def daily_routine():
    """Rutina a ser ejecutada cada mañana por cron."""

    def my_handler(type, value, tb):
        logger.exception('Uncaught exception: {0}'.format(str(value)))

    # Install exception handler
    sys.excepthook = my_handler

    logging.info('COMIENZO de la rutina.')

    # Creates DataJson object to validate oragnisms
    logging.info('Instanciación DataJson')
    datajson = DataJson()

    logging.info('Creación de carpetas necesarias (de archivo y versionadas).')
    for org in ORGANISMS:
        ensure_dir_exists(org)
        ensure_dir_exists(os.path.join(TODAY_DIR, org))

    logging.info('Procesamiento de cada organismo:')
    os.chdir(TODAY_DIR)

    for org, config in ORGANISMS.iteritems():
        process_catalog(org, config, datajson)

    os.chdir(ROOT_DIR)

    logging.info('Actualizo los archivos bajo control de versiones:')
    files_of_day = glob.glob('{}/*/*'.format(TODAY_DIR))
    for filename in files_of_day:
        logging.debug('- %s', filename)
        update_versioning(filename)

    logging.info('Push de los cambios encontrados.')
    GIT.push('origin', 'master')

    logging.info('FIN de la rutina.')


if __name__ == '__main__':
    daily_routine()
