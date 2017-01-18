#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import yaml
import arrow
import requests
import warnings
import filecmp
import sh
from pydatajson.pydatajson import read_catalog
from pydatajson.xlsx_to_json import write_json_catalog

DIR_RAIZ = os.getcwd()
DIR_ARCHIVO = os.path.join(DIR_RAIZ, "archivo/")
HOY = arrow.now()
FECHA_HOY = HOY.format("YYYY-MM-DD")
DIR_HOY = os.path.join(DIR_ARCHIVO, FECHA_HOY)
INDICE = os.path.join(DIR_RAIZ, "indice.yml")
with open(INDICE) as config:
    ORGANISMOS = yaml.load(config)


def listar_organismos():
    print ORGANISMOS


def crear_dirs_organismos():
    """Para cada organismo del indice, crear un directorio si no existe."""
    for organismo in ORGANISMOS.keys():
        if not os.path.isdir(organismo):
            os.mkdir(organismo)


def crear_dir_hoy():
    if not os.path.isdir(DIR_ARCHIVO):
        os.mkdir(DIR_ARCHIVO)

    os.chdir(DIR_ARCHIVO)

    if not os.path.isdir(FECHA_HOY):
        os.mkdir(FECHA_HOY)


def guardar_resultado_get(url, nombre_archivo=None):
    nombre_archivo = nombre_archivo or url.split("/")[-1]
    res = requests.get(url)
    with open(nombre_archivo, 'w') as archivo:
        archivo.write(res.content)


def descargar_catalogo(alias_organismo):
    org = ORGANISMOS[alias_organismo]
    if org.get("metodo") in ["get", None]:
        guardar_resultado_get(org["url"], "data.{}".format(org["formato"]))
    else:
        warnings.warn("{} no es un `metodo` valido.".format(org["metodo"]))

