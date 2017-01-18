#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setup import *
git = sh.git.bake(_cwd=DIR_RAIZ)

crear_dir_hoy()
os.chdir(DIR_HOY)
crear_dirs_organismos()

for (alias, conf) in ORGANISMOS.iteritems():
    os.chdir(alias)
    archivo_catalogo = "data.{}".format(conf["formato"])
    descargar_catalogo(alias)

    version_actual = os.path.join(DIR_RAIZ, alias, archivo_catalogo)
    if not os.path.isfile(version_actual):
        sh.cp(archivo_catalogo, version_actual)
        git.add(version_actual)
        commit_msg = " Agrego archivo {} encontrado el {}".format(
            archivo_catalogo, FECHA_HOY)
        git.commit(m=commit_msg)
    elif not filecmp.cmp(archivo_catalogo, version_actual):
        sh.cp(archivo_catalogo, version_actual)
        git.add(version_actual)
        commit_msg = "Actualizo modificaciones del {} a {}".format(
            FECHA_HOY, archivo_catalogo)
        git.commit(m=commit_msg)

    if conf["formato"] == "xlsx":
        catalogo = read_catalog(archivo_catalogo)
        write_json_catalog(catalogo, "data.json")

        version_actual = os.path.join(DIR_RAIZ, alias, "data.json")
        if not os.path.isfile(version_actual):
            sh.cp(archivo_catalogo, version_actual)
            git.add(version_actual)
            commit_msg = " Agrego archivo {} encontrado el {}".format(
                archivo_catalogo, FECHA_HOY)
            git.commit(m=commit_msg)
        if not filecmp.cmp("data.json", version_actual):
            sh.cp("data.json", version_actual)
            git.add(version_actual)
            commit_msg = "Actualizo modificaciones del {} a {}".format(
                FECHA_HOY, "data.json")
            git.commit(m=commit_msg)
    os.chdir("..")

os.chdir(DIR_RAIZ)
git.push("origin", "master")
