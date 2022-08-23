# Ingeniería de variables
from numpy import nan
from pandas import DataFrame
from unicodedata import normalize
from re import sub, UNICODE, search as re_search
from difflib import SequenceMatcher, get_close_matches

class UtilClass:
    def __init__(self) -> None:
        pass

    def clean_text(self, text: str, pattern: str="[^a-zA-Z0-9\s]", lower: bool=True) -> str: 
        '''
        Limpieza de texto
        '''
        # Reemplazar acentos: áàäâã --> a
        clean = normalize('NFD', str(text).replace('\n', ' \n ')).encode('ascii', 'ignore')
        # Omitir caracteres especiales !"#$%&/()=...
        clean = sub(pattern, ' ', clean.decode('utf-8'), flags=UNICODE)
        # Mantener sólo un espacio
        clean = sub(r'\s{2,}', ' ', clean.strip())
        # Minúsculas si el parámetro lo indica
        if lower: clean = clean.lower()
        # Si el registro estaba vacío, indicar nulo
        if clean in ('','nan'): clean = nan
        return clean

    
    def give_options(self, text: str, valid_options: list, max_options: int, **kwargs) -> list:
        '''
        Compara el texto recibido vs una lista con las opciones válidas, 
        devolviendo la(s) opcion(es) más parecida(s)
        '''
        # Limpia el texto recibido
        clean = self.clean_text(text)
        # Limpia el texto de cada opción válida
        clean_options = list(map(self.clean_text, valid_options))
        # Crea un catálogo de opciones limpias junto con la opción sin limpiar
        options_dict = dict(zip(clean_options, valid_options))

        # Obtiene las opciones más parecidas al texto recibido
        closest_clean_options = get_close_matches(clean, clean_options, **kwargs)
        # Agrega las opciones donde el texto recibido está dentro del texto comparado
        closest_clean_options.extend([x for x in clean_options if re_search(f'.*{clean}.*', x)])

        closest_options = []
        for x in closest_clean_options:
            # Acumula las opciones más parecidas en orden de similitud
            if x not in map(self.clean_text, closest_options): closest_options.append(options_dict[x])
        
        # Si la primera opción tiene más de 95% de similitud, sólo devuelve dicha opción
        if SequenceMatcher(None, text, closest_options[0]).ratio() > 0.95: return [closest_options[0]]
        # De otro modo, devuelve el número de opciones máximas indicadas
        else: return closest_options[:max_options]

    
    def show_grouped(self, df: DataFrame, to_group: str, to_agg:str) -> tuple:
        '''
        Agrupa el texto de dos columnas tal que cada opción de 
        la columna A tenga la lista de elementos de la columna B 
        (de todos los renglones donde ocurre la opción de A) separados por coma
        '''
        # Sin duplicados, ordena la columna A y B ascendentemente
        df = df[[to_group,to_agg]].drop_duplicates().sort_values(to_agg)
        # Agrupa los elementos separados por coma
        df = df.astype(str).pivot_table(index=to_group, values=to_agg, aggfunc=', '.join)

        # Devuelve tanto el índice (opciones de col A) como las opciones separadas por coma de col B
        return df.index, df[to_agg].values