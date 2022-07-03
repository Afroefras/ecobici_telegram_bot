# Ingeniería de variables
from numpy import nan
from re import sub, UNICODE
from pandas import DataFrame
from unicodedata import normalize
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

    
    def give_options(self, text: str, valid_options: list, **kwargs) -> list:
        clean = self.clean_text(text)
        clean_options = list(map(self.clean_text, valid_options))
        options_dict = dict(zip(clean_options, valid_options))
        closest_clean_options = get_close_matches(clean, clean_options, **kwargs)
        closest_options = [options_dict[x] for x in closest_clean_options]
        if SequenceMatcher(None, text, closest_options[0]).ratio() > 0.95: return [closest_options[0]]
        else: return closest_options

    
    def show_grouped(self, df: DataFrame, to_group: str, to_agg:str) -> tuple:
        df = df[[to_group,to_agg]].drop_duplicates().sort_values(to_agg)
        df = df.astype(str).pivot_table(index=to_group, values=to_agg, aggfunc=', '.join)
        return df.index, df[to_agg].values