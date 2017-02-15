# librería de catálogos

## Contexto
El Plan de Apertura de Datos (PAD) contempla que los datasets relevantes de Portales de datos de la Administración Pública Nacional (APN) sean federados en el Portal Nacional de Datos Abiertos ("portal nacional", o "datos.gob.ar"). 
A tal fin, el mantenedor del Portal Nacional debe contar con versiones actualizadas de los catálogos de todos los portales externos en formato JSON, que es el estándar común que entienden todas las herramientas de manipulación de datasets enmarcadas en el PAD.

## Problema
Se espera que al menos inicialmente, algunos organismos de la APN que ya cuentan con portales externos, 
- provean sus metadatos a través del API de su portal (comúnmente CKAN),
- provean un catálogo de metadatos en formato XLSX en vez de JSON, o
- lo provean en formato JSON pero en una ubicación no-estándar (es decir, distinta al recurso "http://portalexterno.gob.ar/data.json").

Cuando la cantidad organismos externos participantes del PAD crezca lo suficiente, es de esperar que resulte difícil al operador mantener manualmente una lista exhaustiva de catálogos y sus ubicaciones. Además, cuando un catálogo supera cierta longitud, notar los cambios introducidos en sucesivas actualizaciones sin ayuda de un resumen programático de éstos puede resultar engorroso y propenso a errores.

## Solución
Este repositorio implementa una **librería de catálogos**, en la que el operador del Portal Nacional tiene a su disposición, por cada organismo participante,

1. `data.XXX`: la última versión del archivo de metadatos mantenido por el organismo, en su formato original,
2. `data.json`: (cuando (1) no esté en formato JSON), el archivo de metadatos en formato JSON que se deriva de procesar (1),

Adicionalmente, y en función de los requerimientos delineados por el operador y su discusión con la dirección del equipo, se agregarán por cada catálogo una serie de reportes auxiliares que faciliten la tarea de decidir qué datasets cosechar. Actualmente, éstos son:

1. `README.md`: un resumen humanamente legible con la metadata a nivel catálogo, y la cantidad de datasets y distribuciones presentes en el catálogo,
2. `datasets.csv`: un informe en formato tabular que incluya, junto con algunos valores claves de la metadata de cada dataset, estadísticas básicas sobre:
  - cantidad de distribuciones
  - resultado de la validación de sus metadatos
  - una bandera (*flag*) que indique si el dataset es nuevo (i.e., fue incluido en el catálogo en la última actualización).

### Estructura
Esta librería de catálogos (es decir, este repositorio), cuenta con la siguiente estructura de archivos y carpetas:
```
indice.yaml
archivo/YYYY-MM-DD/
organismo1/data.xlsx
organismo1/data.json
organismo1/README.md
organismo1/datasets.csv
organismo2/...
```
#### `indice.yaml`
Contiene un diccionario en formato YAML, cuyas claves son "nombres cortos" de los organismos participantes del PAD, y sus valores son diccionarios con los parámetros necesarios para identificar la ubicación en la cual mantienen sus catálogos externos:
  - "url": URL de donde descargar (idealmente mediante descarga directa) el catálogo del portal externo del organismo en cuestión,
  - "formato": Formato en que se encuentra el archivo de metadatos ubicado en URL. Podrá ser "xlsx", "json" o "ckan".

Ejemplo de `indice.yaml`:
```yaml
justicia:
  url: "http://datos.jus.gob.ar"
  formato: "ckan"

datosgobar:
  url: "http://datos.gob.ar/data.json"
  formato: "json"
```

#### `organismoX/`
Por cada organismo presente en `indice.yaml`, existe una carpeta con su nombre, en la que se incluyen los 3 (o 4, si el catálogo externo se mantiene en un formato distinto a JSON) archivos indicados anteriormente: `data.json`, `README.md`, `datasets.csv`, y si corresponde, `data.xlsx`.

#### `archivo/YYYY-MM-DD/`
A pesar de que el directorio completo `libreria-catalogos` estará bajo control de versiones, y por tanto en cualquier momento uno puede devolverlo a un estado anterior, la carpeta `archivo/` contiene el archivo histórico de los estados de la librería con granularidad diaria. Así, por ejemplo, la carpeta `archivo/2017-01-15/` tendrá la misma estructura que la raíz del repositorio (exceptuando la carpeta `archivo/` en sí), al día 15 de Enero de 2017.

**La carpeta `archivo/` NO se encontrará bajo control de versiones** por razones obvias, pero se incluye para comodidad del operador que necesite referenciar archivos viejos en detalle, en el servidor en que corre regularmente esta rutina.

### Proceso de actualización

Todas las mañanas, en un horario predeterminado antes del comienzo de la jornada laboral (e.g., 7AM), correrá una rutina que realiza los siguientes pasos:

1. Crea en `archivo/` una nueva carpeta con la fecha corriente, y la usa como directorio de trabajo.
2. Por cada `organismo` presente en `indice.yaml`, genera una carpeta a su nombre, y descarga a ella el catálogo mantenido externamente por el organismo, según especifiquen las variables "url" y "formato". El archivo se guardará con el nombre `data.XXX`, donde "XXX" es la extensión especificada en "formato".
3. Por cada `organismo` presente en `indice.yaml` cuyo "formato" es distinto a JSON, se ejecutará la rutina adecuada del módulo `pydatajson` para tansformar `data.XXX` a formato JSON. Su resultado será guardado con el nombre `data.json`.
4. Sobre los catálogos en formato JSON de cada organismo, se ejecutarán las rutinas necesarias para generar los informes auxiliares que el operador requiera.

Finalmente, para cada organismo, los contenidos de `archivo/fecha-corriente/organismoX` se copiarán en su totalidad a la carpeta bajo control de versiones correspondiente al organismo en la raíz del repositorio. De haber algún cambio según `git status`, dichos cambios se empujarán al control de versiones, de manera que el operador pueda revisar los cambios entre la última versión y la actual de manera sucinta, utilizando, según le convenga al nivel de desagregación buscado, `data.json`, `datasets.csv` o `README.md`.
