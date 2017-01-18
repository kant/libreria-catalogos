# Propuesta para mantenimiento de una librería de catálogos
- Gonzalo Barrera Borla
- 16 de Enero de 2017

## Contexto
El Plan de Apertura de Datos (PAD) contempla que los datasets considerados como valiosos presentes en Portales de datos de la APN ("portales externos") sean federados en el Portal Nacional de Datos Abiertos ("portal nacional", o "datos.gob.ar"). 
A tal fin, se espera que un "operador" del Portal Nacional cuente con versiones actualizadas de los catálogos de todos los portales externos en formato JSON, que es el estándar común que entienden todas las herramientas de manipulación de datasets enmarcadas en el PAD.

## Problema
Se espera que al menos inicialmente, algunos organismos de la APN que ya cuentan con portales externos, 
- no provean un catálogo de metadatos, o
- lo provean en formato XLSX en vez de JSON, o
- lo provean en formato JSON pero en una ubicación no-estándar (es decir, distinta al recurso "http://portalexterno.gob.ar/data.json").

Cuando la cantidad organismos externos participantes del PAD crezca lo suficiente, es de esperar que resulte difícil al operador mantener manualmente una lista exhaustiva de catálogos y sus ubicaciones. Además, cuando un catálogo supera cierta longitud, notar los cambios introducidos en sucesivas actualizaciones sin ayuda de un resumen programático de éstos puede resultar engorroso y propenso a errores.

## Solución Propuesta
Construir una **librería de catálogos**, en la que el operador del Portal Nacional tenga a su disposición **localmente**, por cada organismo participante,

1. `data.XXX`: la última versión del archivo de metadatos mantenido por el organismo, en su formato original,
2. `data.json`: (cuando (1) no esté en formato JSON), el archivo de metadatos en formato JSON que se deriva de procesar (1),

Adicionalmente, y en función de los requerimientos delineados por el operador y su discusión con la dirección del equipo, se agregarán por cada catálogo una serie de reportes auxiliares que faciliten la tarea de decidir qué datasets cosechar. Algunos posibles son:

1. `validacion.json`: el resultado _completo_ de la validación del archivo de metadatos (2), según `DataJson.validate_catalog`, y
2. `errores.csv`: un informe en formato tabular con la lista completa de errores surgidos de `DataJson.validate_catalog`
3. `README.md`: un resumen humanamente legible con la metadata a nivel catálogo, y la cantidad de datasets y distribuciones presentes en el catálogo,
4. `datasets.csv`: un informe en formato tabular que incluya, junto con algunos valores claves de la metadata de cada dataset, estadísticas básicas sobre:
  - cantidad de distribuciones
  - resultado de la validación de sus metadatos
  - una bandera (*flag*) que indique si el dataset es nuevo (i.e., fue incluido en el catálogo en la última actualización).

### Estructura
Esta librería de catálogos consiste en un directorio bajo control de versiones (a través de `git`, en un repositorio remoto o local, público o privado según se decida), con la siguiente estructura de archivos y carpetas:
```
indice.yaml
archivo/YYYY-MM-DD/
organismo1/data.xlsx
organismo1/data.json
organismo1/validacion.json
organismo1/resumen.md
organismo2/...
```
#### `indice.yaml`
Contiene un diccionario en formato YAML, cuyas claves son "nombres cortos" de los organismos participantes del PAD, y sus valores son diccionarios con los parámetros necesarios para identificar la ubicación en la cual mantienen sus catálogos externos:
  - "url": URL de donde descargar (idealmente mediante descarga directa) el catálogo del portal externo del organismo en cuestión,
  - "formato": Formato en que se encuentra el archivo de metadatos ubicado en URL. En principio, podrá ser "xlsx" o "json".
  - "metodo": Método a utiliZar para descargar el archivo ubicado en URL. Por default, es "wget".

Ejemplo de `indice.yaml`:
```yaml
justicia:
  url: "http://datos.jus.gob.ar/data.json"
  formato: "json"
  metodo: "wget"
energia:
  url: "https://www.dropbox.com/s/grnsgcgjo3dl0LU/catalogo_energia.xlsx"
  formato: "xlsx"
  # Si no se especifica un 'metodo', se asume "wget" por omisión.
```
#### `organismoX/`
Por cada organismo presente en `indice.yaml`, existirá una carpeta con su nombre, en la que se incluyen los 3 (o 4, si el catálogo externo se mantiene en un formato distinto a JSON) archivos indicados anteriormente: `data.json`, `validacion.json`, `resumen.md`, y si corresponde, `data.xlsx`.

#### `archivo/YYYY-MM-DD/`
A pesar de que el directorio completo `libreria-catalogos` estará bajo control de versiones, y por tanto en cualquier momento uno puede devolverlo a un estado anterior, la carpeta `archivo/` contendrá el archivo histórico de los estados de la librería con granularidad diaria. Así, por ejempllo, la carpeta `archivo/2017-01-15/` tendrá la misma estructura que la raíz del repositorio (exceptuando la carpeta `archivo/` en sí), al día 15 de Enero de 2017.

**La carpeta `archivo/` NO se encontrará bajo control de versiones** por razones obvias, pero se incluye para comodidad del operador que necesite referenciar archivos viejos en detalle.

### Proceso de actualización

Todas las mañanas, en un horario predeterminado antes del comienzo de la jornada laboral (e.g., 7AM), correrá una rutina que realiza los siguientes pasos:

1. Crea en `archivo/` una nueva carpeta con la fecha corriente, y la usa como directorio de trabajo.
2. Por cada `organismo` presente en `indice.yaml`, genera una carpeta a su nombre, y descarga a ella el catálogo mantenido externamente por el organismo, según especifiquen las variables "url", "formato" y "metodo". El archivo se guardará con el nombre `data.XXX`, donde "XXX" es la extensión especificada en "formato".
3. Por cada `organismo` presente en `indice.yaml` cuyo "formato" es distinto a JSON, se ejecutará la rutina adecuada del módulo `pydatajson` para tansformar `data.XXX` a formato JSON. Su resultado será guardado con el nombre `data.json`.
4. Sobre los catálogos en formato JSON de cada organismo, se ejecutarán las rutinas necesarias para generar los informes auxiliares que el operador requiera.

Finalmente, para cada organismo, los contenidos de `archivo/fecha-corriente/organismoX` se copiarán en su totalidad a la carpeta bajo control de versiones correspondiente al organismo en la raíz del repositorio. De haber algún cambio según `git status`, dichos cambios se "commitearán" al control de versiones, de manera que el operador pueda revisar los cambios entre la última versión y la actual de manera sucinta, utilizando, según le convenga al nivel de desagregación buscado, `data.json`, `validacion.json` o `resumen.md`.
