# Control de datos
from io import BytesIO
from dateutil import tz
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
from json import loads as loads_json
from PIL.Image import open as open_image
from requests import get as get_request

# Ingeniería de variables
from geopandas import read_file
from pandas import DataFrame, json_normalize

# Gráficas
from seaborn import scatterplot
from matplotlib.lines import Line2D
from contextily import add_basemap, providers
from matplotlib.pyplot import Axes, Figure, get_cmap, switch_backend
switch_backend('Agg')

# Clase madre para métodos como limpieza de texto
from util import UtilClass

# # Modelo
# import ecoTad, ecoPredict

class EcoBiciMap(UtilClass):
    def __init__(self, client_id: str, client_secret: str, is_local: bool=True) -> None:
        '''
        Define el directorio base, la URL base y las credenciales para el acceso a la API Ecobici
        :client_id: user_uuid proporcionado por Ecobici. Más info en: https://www.ecobici.cdmx.gob.mx/sites/default/files/pdf/manual_api_opendata_esp_final.pdf 
        :secret_id: contraseña propoprcionada por Ecobici, en un correo aparte para mayor seguridad
        '''
        # Obtiene el directorio actual
        if is_local: self.base_dir = Path('/Users/efrain.flores/Desktop/hub/ecobici_telegram_bot')
        else: self.base_dir = Path().cwd()
        self.shapefile_dir = self.base_dir.joinpath('data','shp')
        self.media_dir = self.base_dir.joinpath('media')
        for use_directory in [self.shapefile_dir, self.media_dir]: use_directory.mkdir(exist_ok=True)

        # Dominio web base, de donde se anexarán rutas y parámetros
        self.base_url = "https://pubsbapi-latam.smartbike.com"
        # Ruta con las credenciales de acceso
        self.user_credentials = f"oauth/v2/token?client_id={client_id}&client_secret={client_secret}"


        self.started_at = datetime.now().astimezone(tz.gettz('America/Mexico_City'))
        self.started_at_format = self.started_at.strftime(r'%d/%b/%Y %H:%M')
        self.is_local = is_local
        self.eb_map = {}

    def __str__(self) -> str:
        return f'''
        {self.started_at_format}
        Clase para extraer información de la API Ecobici (https://www.ecobici.cdmx.gob.mx/sites/default/files/pdf/manual_api_opendata_esp_final.pdf)
        transformar, graficar la disponibilidad en un mapa de calor, exportar los datos y crear un tweet con el mapa.
        '''


    def get_token(self, first_time: bool=False) -> None:
        '''
        Guarda los tokens de acceso, necesarios para solicitar la información de estaciones y disponibilidad
        :first_time: 
            - True para obtener ACCESS_TOKEN y REFRESH_TOKEN usando las credenciales por primera vez
            - False para continuar con acceso a la API (después de 60min) y renovar ACCESS_TOKEN a través del REFRESH_TOKEN
        '''
        # URL completa para recibir el token de acceso y el token de actualización (se ocupa si la sesión dura más de 60min)
        if first_time: 
            URL = f"{self.base_url}/{self.user_credentials}&grant_type=client_credentials"
        # En el caso que se accese por 2a ocasión o más, se llama al token de actualización
        else: 
            URL = f"{self.base_url}/{self.user_credentials}&grant_type=refresh_token&refresh_token={self.REFRESH_TOKEN}"

        # Obtiene la respuesta a la solicitud de la URL, los datos vienen en bits
        req_text = get_request(URL).text
        # Convierte los bits a formato json para guardar los tokens
        data = loads_json(req_text)

        # Guarda los tokens como atributos
        self.ACCESS_TOKEN = data['access_token']
        self.REFRESH_TOKEN = data['refresh_token']


    def get_data(self, availability: bool=False) -> DataFrame:
        '''
        Obtiene la información de estaciones y disponibilidad al momento
        :availabilty:
            - True para obtener los datos de disponibilidad
            - False para obtener la información respecto a las estaciones
        '''
        # URL para obtener la información en tiempo real, ya sea la info de las estaciones y/o la disponibilidad de las mismas
        stations_url = f"{self.base_url}/api/v1/stations{'/status' if availability else ''}.json?access_token={self.ACCESS_TOKEN}"
        req_text = get_request(stations_url).text
        data = loads_json(req_text)

        # El json resultado tiene la data encapsulada en la primer llave
        first_key = list(data.keys())[0]
        # Se estructura como tabla 
        df = json_normalize(data[first_key])
        self.got_data_at = datetime.now().astimezone(tz.gettz('America/Mexico_City')).strftime(r'%d/%b/%Y %H:%M')
        return df


    def get_shapefile(self, first_time: bool=False, shapefile_url: str='https://datos.cdmx.gob.mx/dataset/7abff432-81a0-4956-8691-0865e2722423/resource/8ee17d1b-2d65-4f23-873e-fefc9e418977/download/cp_cdmx.zip') -> None:
        '''
        Obtiene y descomprime el zip que contiene el shapefile 
        (varias carpetas que en conjunto, definen una zona geográfica)
        :shapefile_url: liga gubernamental y oficial respecto a la delimitación de colonias en CDMX
        '''
        if first_time:
            # Obtener los datos de la URL
            req_data = get_request(shapefile_url).content
            # Extraer la información del ZIP, que es un SHP file 
            zipfile = ZipFile(BytesIO(req_data))
            zipfile.extractall(self.shapefile_dir)
        # Se estructura como tabla, para poder gráficar las colonias de la CDMX
        self.gdf = read_file(self.shapefile_dir).to_crs(epsg=4326)


    def transform(self, filter_col: str=None, filter_value: str=None, station_cols: list=['id','zipCode','location.lat','location.lon'], id_col: str='id', status_col: str='status', bikes_col: str='availability.bikes', slots_col: str='availability.slots') -> None:
        '''
        Une las tablas de estaciones y disponibilidad. Crea las variables de proporción en bicicletas y slots vacíos
        :station_cols:  columnas de interés respecto a la tabla de estaciones
        :id_col:        identificación de la estación Ecobici
        :status_col:    columna que indica el estatus de la estación, sólo se mantendrá estaciones abiertas
        :bikes_col:     columna que indica las bicicletas disponibles
        :slots_col:     columna que indica los slots vacíos
        '''
        # Filtra un subconjunto si es indicado
        if filter_col is None or filter_value is None: df = self.st.copy()
        else: df = self.st[self.st[filter_col]==filter_value].copy()
        # Une la información de estaciones con la disponibilidad de las mismas
        df = df[station_cols].merge(self.av, on=id_col)
        # Sólo las estaciones con estatus disponible
        df = df[df[status_col]=='OPN'].copy()
        # Calcula la proporción de disponibilidad, tanto de bicicletas, como de slots vacíos
        df['slots_proportion'] = df[slots_col] / (df[slots_col] + df[bikes_col])
        df['bikes_proportion'] = 1 - df['slots_proportion']
        return df


    def set_custom_legend(self, ax, cmap, values: list) -> None:
        ''''
        Modifica las etiquetas para un mapa de calor
        '''
        legend_elements = []
        for gradient, label in values:
            color = cmap(gradient)
            legend_elements.append(Line2D([0], [0], marker="o", color="w", label=label, markerfacecolor=color, markeredgewidth=0.5, markeredgecolor="k"))
        ax.legend(handles=legend_elements, loc="upper left", prop={"size": 4}, ncol=len(values))


    def plot_map(self, data: DataFrame, col_to_plot='slots_proportion', img_name='map', padding=0.006, points_palette='Blues', lat_col: str='location.lat', lon_col: str='location.lon', **kwargs) -> None:
        
        # Crea el lienzo para graficar el mapa
        fig = Figure(figsize=(5, 4), dpi=200, frameon=False)
        ax = Axes(fig, [0.0, 0.0, 1.0, 1.0])
        fig.add_axes(ax)
        ax.set_axis_off()
        
        # Delimita el tamaño dependiendo el rango de las coordenadas
        
        ax.set_ylim((data[lat_col].min() - padding, data[lat_col].max() + padding))
        ax.set_xlim((data[lon_col].min() - padding, data[lon_col].max() + padding))
        # except: pass

        # Grafica el mapa de las colonias en CDMX
        self.gdf.plot(ax=ax, figsize=(8, 8), linewidth=0.5, **kwargs)
        # Agrega etiquetas de calles/colonias
        add_basemap(ax, crs=self.gdf.crs, source=providers.Stamen.TonerLabels, interpolation='sinc', aspect='equal')

        # Grafica cada estación, asignando el color dependiendo la disponibilidad
        cmap = get_cmap(points_palette)
        scatterplot(y=lat_col, x=lon_col, data=data, ax=ax, palette=cmap, hue=col_to_plot)

        # Modifica las etiquetas para indicar el significado del color en las estaciones
        self.set_custom_legend(ax, cmap, values=[(0.0, 'Sin bicis'), (0.5, 'Algunas bicis'), (1.0, 'Muchas bicis')])
        # Guarda la imagen
        self.eb_map[img_name] = fig
        self.eb_map[img_name].savefig(self.media_dir.joinpath(f'{img_name}.png'))
        img = open_image(self.media_dir.joinpath(f'{img_name}.png'))
        return img


    # def prediction_data(self, file_name: str, is_local:bool) -> None:
    #     ecoTad.run_ecotad(is_local=is_local)
    #     ecoPredict.run_ecopredict(is_local=is_local)
    #     self.pred = read_csv(self.base_dir.joinpath('data','for_map',file_name))
    #     print(self.pred.shape)
    #     self.pred = self.pred.merge(self.av[['id', 'availability.bikes', 'availability.slots']], on='id')
    #     print(self.pred.shape)
    #     self.pred['prediction'] = self.pred['prediction'].map(lambda x: 0 if x<0 else x)
    #     self.pred['bikes_proportion'] = 1 - self.pred['prediction'] / (self.pred['availability.bikes'] + self.pred['availability.slots'])
    #     self.pred['bikes_proportion'] = self.pred['bikes_proportion'].map(lambda x: 0 if x<0 else x)
