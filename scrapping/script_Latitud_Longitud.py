# -*- coding: utf-8 -*-
"""
Created on Mon Oct 27 21:29:08 2025

@author: agutierrez752
"""

import requests

direccion = "Sargento Cabral 100, Posadas, Misiones, Argentina"  # Cambia por la dirección que necesites

url = "https://nominatim.openstreetmap.org/search"
params = {
    'q': direccion,
    'format': 'json',
    'limit': 1
}
headers = {
    'User-Agent': 'MiAppWebScraping/1.0 (tu_email@dominio.com)'  # Cambia el email por el tuyo
}

response = requests.get(url, params=params, headers=headers)
data = response.json()
print(data)
if data:
    lat = data[0]['lat']
    lon = data[0]['lon']
    print("Latitud:", lat)
    print("Longitud:", lon)
else:
    print("No se encontraron coordenadas para la dirección.")