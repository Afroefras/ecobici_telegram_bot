<h1 align='center'>Ecobici TelegramBot</h1>

<p align="center">
  <img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/for_readme/demo_halfsize.gif" />
</p>

# Índice
1. [Repositorio](#Repositorio)
2. [Extracción](#Extracción)
3. [Transformación](#Transformación)
4. [Interacción](#Interacción)
5. [Puesta en producción](#Puesta-en-producción) (En progreso ...)

<br>
--------------------------------------------------------------------------------------------
<br>

# Repositorio:
    .
    ├── data/shp                      # Archivos necesarios para desplegar los límites por Código Postal en CDMX
    │
    ├── media
    │   └── demo_halfsize.gif         # GIF al inicio de este README.md, para mostrar las capacidades del bot
    │   └── map.png                   # Última magen solicitada del mapa de disponibilidad
    │
    ├── scripts
    │   ├── __init__.py               # Para que el directorio se trabaje de forma modular
    │   ├── etl.py                    # Cuenta con la clase EcoBiciMap para importar datos desde API, hereda la clase util.UtilClass
    │   └── main.py                   # Al correr este archivo, el TelegramBot está listo para interactuar con el usuario
    │   └── util.py                   # Cuenta con la clase UtilClass con métodos generales para limpieza de texto y otros
    │
    └── requirements.txt              # Instalar las librerías necesarias con el comando: pip install -r requirements.txt

<br>


# Extracción

1. El primer paso es registrarte para la API [aquí](https://www.ecobici.cdmx.gob.mx/es/informacion-del-servicio/open-data), recibirás un correo con tus credenciales: CLIENT_ID y CLIENT_SECRET (guárdalas muy bien, donde nadie las encuentre)

([este artículo](https://canovasjm.netlify.app/2021/01/12/github-secrets-from-python-and-r/) me ayudó mucho a entender GitHub Secrets, para guardar y usar credenciales automáticamente mediante un workflow .yml, si fuera el caso)

<br><br>


2. Así, puedes instanciar la clase para obtener los datos al momento
```python
from map import EcoBiciMap

ebm = EcoBiciMap(CLIENT_ID, CLIENT_SECRET)

# Con las credenciales se inicia la sesión y se obtiene el token de acceso
ebm.get_token(first_time=True)
```

<br><br>


3. Se puede extraer información respecto a las estaciones, incluyendo coordenadas
```python
ebm.get_data()
```
|id|name|address|addressNumber|zipCode|districtCode|districtName|altitude|nearbyStations|stationType|location.lat|location.lon|
|---|---|---|---|---|---|---|---|---|---|---|---|
|55|55 5 DE MAYO-BOLIVAR|055 - 5 de Mayo - Bolívar|S/N|6700|1|Ampliación Granada|None|[65, 87]|BIKE,TPV|19.434356|-99.138064|
|124|124 CLAUDIO BERNARD-DR. LICEAGA|124 - Claudio Bernard-Dr. Liceaga|S/N|6500|1|Ampliación Granada|None|[119, 123, 133]|BIKE|19.422392|-99.150358|
|159|159 HUATABAMPO-EJE 1 PTE. AV. CUAUHTÉMOC|159 - Huatabampo-Eje 1 Pte. Av. Cuauhtémoc|S/N|6760|1|Ampliación Granada|None|[155, 158, 163]|BIKE|19.407517|-99.155373|

<br><br>


4. Y también la disponibilidad de las estaciones (mismo método pero especificando un parámetro)
```python
ebm.get_data(availability=True)
```
|id|status|availability.bikes|availability.slots|
|---|---|---|---|
|55|OPN|13|10|
|124|OPN|0|21|
|159|OPN|1|34|

<br><br>


# Transformación

5. Es importante filtrar las estaciones con estatus activo, unir ambas tablas y calcular la proporción de bicicletas y slots
```python
ebm.transform()
```
|id|zipCode|location.lat|location.lon|status|availability.bikes|availability.slots|slots_proportion|bikes_proportion|
|---|---|---|---|---|---|---|---|---|
|55|6700|19.434356|-99.138064|OPN|11|4|0.27|0.73|
|124|6500|19.422392|-99.150358|OPN|0|34|1.00|0.00|
|159|6760|19.407517|-99.155373|OPN|12|24|0.67|0.33|

<br><br>


6. Se utilizará el shapefile de los [Códigos Postales CDMX](https://datos.cdmx.gob.mx/dataset/7abff432-81a0-4956-8691-0865e2722423/resource/8ee17d1b-2d65-4f23-873e-fefc9e418977) para definir los límites en el mapa

![](media/for_readme/cdmx.png?raw=true "Mexico City by zipcodes") 

<br><br>


7. Al unir ambos mapas, utilizando las coordenadas y disponibilidad de las estaciones, este es el resultado:
```python
ebm.plot_map(
    data=ebm.df,
    col_to_plot='slots_proportion',
    padding=0.006,
    color='#ffffff',
    edgecolor='#00acee', 
    points_palette='Blues')
```

<img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/for_readme/full_map.jpeg" width=50% height=50%>

<br><br>


# Interacción

8. Al [iniciar un chat con Ecobici TelegramBot](t.me/EcobicimapBot) te muestra las instrucciones del chat
<img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/for_readme/01_start.png" width=50% height=50%>
Todas las opciones que comienzan con "\" pueden ser presionadas y son inmediatamente enviadas.

<br><br>

9. Tal como en [Ecobici TwitterBot](https://twitter.com/EcobiciMapBot), este bot puede mostrar la disponibilidad total de CDMX mandando el comando `\todo`
<img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/for_readme/02_todo.png" width=50% height=50%>

<br><br>

10. Incluso puedes actualizar los datos en cualquier momento mandando `\update`
<img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/for_readme/03_update.png" width=50% height=50%>

<br><br>

11. Ahora, veamos las opciones que filtran una zona en el mapa. En primer lugar está la consulta por código postal, sólo basta con ocupar la palabra `zipcode XXXX` para filtrar en el mapa la zona con código postal `XXXX`
<img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/for_readme/04_zipcode.png" width=50% height=50%>

<br><br>

12. Por otro lado, es posible filtrar zonas más específicas indicando la colonia. La manera de hacerlo es mandando `colonia XXXX` o bien la abreviatura `col XXXX`. Si el texto recibido se parece a más de una colonia, te mostrará máx 5 opciones para que elijas cuál consultar.
<img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/for_readme/05_options.jpeg" width=50% height=50%>

<br>

<img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/for_readme/06_answered.jpeg" width=50% height=50%>

<br><br>

13. Incluso, dado que utiliza [difflib.SequenceMatcher](https://docs.python.org/2/library/difflib.html#sequencematcher-objects) para comparar el texto recibido vs las opciones de colonias válidas, también "corrige" las faltas de ortografía, por ejemplo:
<img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/for_readme/07_typo.png" width=50% height=50%>

<br><br>

# Puesta en producción 

La investigación preliminar apunta que el script debe instanciarse en un servidor, cómo hacerlo está en progreso, espérenlo ...
