<p align="center">
  <h1>Ecobici TelegramBot</h1>
  <img src="https://github.com/Afroefras/ecobici_telegram_bot/blob/main/media/demo_halfsize.gif" />
</p>

# Índice
1. [Repositorio](#Repositorio)
2. [Extracción](#Extracción)
3. [Transformación](#Transformación)
4. [Interacción](#Interacción)
5. [Puesta en producción](#Puesta en producción) (En progreso ...)

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


2. Instanciar la clase para obtener los datos al momento
```python
from map import EcoBiciMap

ebm = EcoBiciMap(CLIENT_ID, CLIENT_SECRET)

# Con las credenciales se inicia la sesión y se obtiene el token de acceso
ebm.get_token(first_time=True)
```

<br><br>


3. Información respecto a las estaciones, incluyendo coordenadas
```python
ebm.get_data()
```
|id|name|address|addressNumber|zipCode|districtCode|districtName|altitude|nearbyStations|stationType|location.lat|location.lon|
|---|---|---|---|---|---|---|---|---|---|---|---|
|55|55 5 DE MAYO-BOLIVAR|055 - 5 de Mayo - Bolívar|S/N|6700|1|Ampliación Granada|None|[65, 87]|BIKE,TPV|19.434356|-99.138064|
|124|124 CLAUDIO BERNARD-DR. LICEAGA|124 - Claudio Bernard-Dr. Liceaga|S/N|6500|1|Ampliación Granada|None|[119, 123, 133]|BIKE|19.422392|-99.150358|
|159|159 HUATABAMPO-EJE 1 PTE. AV. CUAUHTÉMOC|159 - Huatabampo-Eje 1 Pte. Av. Cuauhtémoc|S/N|6760|1|Ampliación Granada|None|[155, 158, 163]|BIKE|19.407517|-99.155373|

<br><br>


4. Disponibilidad de las estaciones (mismo método pero especificando un parámetro)
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

5. Filtrar las estaciones con estatus activo, unir ambas tablas y calcular la proporción de bicicletas y slots
```python
ebm.transform()
```
|id|zipCode|location.lat|location.lon|status|availability.bikes|availability.slots|slots_proportion|bikes_proportion|
|---|---|---|---|---|---|---|---|---|
|55|6700|19.434356|-99.138064|OPN|11|4|0.27|0.73|
|124|6500|19.422392|-99.150358|OPN|0|34|1.00|0.00|
|159|6760|19.407517|-99.155373|OPN|12|24|0.67|0.33|

<br><br>


6. Se utiliza el shapefile de los [Códigos Postales CDMX](https://datos.cdmx.gob.mx/dataset/7abff432-81a0-4956-8691-0865e2722423/resource/8ee17d1b-2d65-4f23-873e-fefc9e418977) para definir los límites en el mapa

![](media/cdmx.png?raw=true "Mexico City by zipcodes") 

<br><br>


7. Unir ambos mapas, utilizando las coordenadas y disponibilidad de las estaciones
```python
ebm.plot_map(
    data=ebm.df,
    col_to_plot='slots_proportion',
    padding=0.006,
    color='#ffffff',
    edgecolor='#00acee', 
    points_palette='Blues')
```
![](media/map.png?raw=true "Ecobici Map")

<br><br>


# Interacción
8. Al [iniciar un chat con Ecobici TelegramBot](t.me/EcobicimapBot) 


# Puesta en producción 

(en progreso ...)


Quieres comprobarlo?

