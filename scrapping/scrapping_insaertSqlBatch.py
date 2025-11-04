import requests
from bs4 import BeautifulSoup
import json
import re

urls = [
   "https://www.orensepropiedades.com/orense-302",
       "https://www.orensepropiedades.com/orense-301",
       "https://www.orensepropiedades.com/orense-300",
       "https://www.orensepropiedades.com/orense-298",
       "https://www.orensepropiedades.com/orense-297",
       "https://www.orensepropiedades.com/orense-296",
       "https://www.orensepropiedades.com/orense-295",
       "https://www.orensepropiedades.com/orense-294",
       "https://www.orensepropiedades.com/orense-293",
       "https://www.orensepropiedades.com/orense-292",
       "https://www.orensepropiedades.com/orense-291",
       "https://www.orensepropiedades.com/orense-289",
       "https://www.orensepropiedades.com/orense-284",
       "https://www.orensepropiedades.com/orense-279",
       "https://www.orensepropiedades.com/orense-278",
       "https://www.orensepropiedades.com/orense-276",
       "https://www.orensepropiedades.com/orense-246",
       "https://www.orensepropiedades.com/orense-244",
       "https://www.orensepropiedades.com/orense-110",
       "https://www.orensepropiedades.com/orense-100",
       "https://www.orensepropiedades.com/orense-303",
       "https://www.orensepropiedades.com/orense-257",
       "https://www.orensepropiedades.com/orense-112",
       "https://www.orensepropiedades.com/orense-274",
       "https://www.orensepropiedades.com/orense-245",
       "https://www.orensepropiedades.com/orense-225",
       "https://www.orensepropiedades.com/orense-224",
       "https://www.orensepropiedades.com/orense-222",
       "https://www.orensepropiedades.com/orense-221",
       "https://www.orensepropiedades.com/orense-220",
       "https://www.orensepropiedades.com/orense-219",
       "https://www.orensepropiedades.com/orense-218",
       "https://www.orensepropiedades.com/orense-217",
       "https://www.orensepropiedades.com/orense-216",
       "https://www.orensepropiedades.com/orense-215",
       "https://www.orensepropiedades.com/orense-214",
       "https://www.orensepropiedades.com/orense-213",
       "https://www.orensepropiedades.com/orense-206"
]

output_file = "inserts_propiedades.txt"
with open(output_file, "w", encoding="utf-8") as f:
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        agente_nombre = "Orense Propiedades"
        titulo_tag = soup.find('h6', class_='fw-bold')
        titulo = titulo_tag.text.strip() if titulo_tag else "Sin título"

        direccion = None
        ciudad = "Posadas"
        ubicacion_section = soup.find('h3', class_='mb-4 fw-bold section-title', string="Ubicación")
        if ubicacion_section:
            direccion_tag = ubicacion_section.find_next('p')
            if direccion_tag:
                direccion = direccion_tag.get_text(strip=True)
        if not direccion:
            direccion = "Sin dirección"

        lat, lon = None, None
        if direccion:
            url_nominatim = "https://nominatim.openstreetmap.org/search"
            params = {'q': direccion + ", " + ciudad, 'format': 'json', 'limit': 1}
            headers = {'User-Agent': 'MiAppWebScraping/1.0 (tu_email@dominio.com)'}
            response_geo = requests.get(url_nominatim, params=params, headers=headers)
            data = response_geo.json()
            if data:
                lat = data[0]['lat']
                lon = data[0]['lon']

        tipo_propiedad = "Departamento"
        ambientes = 0
        metros_cuadrados = 0
        for prop in soup.find_all('div', class_='mb-3 item d-inline-flex align-items-center col-md-3 col-6'):
            titulo_prop = prop.get('title', '').lower()
            if "dormitorio" in titulo_prop:
                ambientes = int(re.sub(r'\D', '', titulo_prop))
            if "sup. total" in titulo_prop or "sup. cubierta" in titulo_prop:
                metros_cuadrados = int(re.sub(r'\D', '', titulo_prop))

        precio = 0
        precio_tag = soup.find('h2', class_='d-inline-block fw-bold mb-0 p-0 price')
        if precio_tag:
            precio_texto = precio_tag.get_text(separator=" ", strip=True)
            match = re.search(r'([0-9][0-9\.,]*)', precio_texto)
            if match:
                precio_limpio = match.group(1).replace('.', '').replace(',', '.')
                try:
                    precio = float(precio_limpio)
                except:
                    precio = 0

        moneda = "ARS"
        descripcion_manual = ""
        descripcion_completa = soup.find('p', class_='p-0 m-0')
        if descripcion_completa:
            descripcion_manual = descripcion_completa.get_text(separator="\n").strip()
        descripcion_ia = ""
        amenities = {
            "pileta": False,
            "mascotas_permitidas": True,
            "seguridad_24h": False
        }

        insert_sql = f"""----- QUERY PARA URL: {url} -----
INSERT INTO Propiedad (
    agente_nombre, titulo, direccion, ciudad, ubicacion, tipo_propiedad, ambientes, metros_cuadrados,
    precio_alquiler, moneda, descripcion_manual, descripcion_ia, amenities
) VALUES (
    '{agente_nombre}',
    '{titulo}',
    '{direccion}',
    '{ciudad}',
    ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326),
    '{tipo_propiedad}',
    {ambientes},
    {metros_cuadrados},
    {precio},
    '{moneda}',
    $$ {descripcion_manual} $$,
    $$ {descripcion_ia} $$,
    '{json.dumps(amenities)}'
);
----- FIN QUERY -----

"""
        f.write(insert_sql)
print(f"Todas las queries fueron exportadas a {output_file}")