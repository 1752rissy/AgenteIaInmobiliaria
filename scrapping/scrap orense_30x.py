import requests
from bs4 import BeautifulSoup

# URL de la página a scrapear
url = "https://www.orensepropiedades.com/orense-305"

# Realiza la petición HTTP
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Extraer la descripción corta
descripcion_corta = soup.find('p', class_='text-muted p-0 m-0 zone')
if descripcion_corta:
    print("Descripción corta:", descripcion_corta.text.strip())
else:
    print("No se encontró la descripción corta.")

# Extraer la descripción completa
descripcion_completa = soup.find('p', class_='p-0 m-0')
if descripcion_completa:
    texto_completo = descripcion_completa.get_text(separator="\n").strip()
    print("\nDescripción completa:\n", texto_completo)
else:
    print("No se encontró la descripción completa.")

# Extraer las propiedades adicionales
propiedades = soup.find_all('div', class_='mb-3 item d-inline-flex align-items-center col-md-3 col-6')
print("\nPropiedades:")
for prop in propiedades:
    titulo = prop.get('title')
    if titulo:
        print("-", titulo)

# Extraer el precio
precio = soup.find('h2', class_='d-inline-block fw-bold mb-0 p-0 price')
if precio:
    precio_texto = precio.get_text(strip=True)
    print("\nPrecio:", precio_texto)
else:
    print("\nNo se encontró el precio.")

# Extraer la dirección
direccion = None
ubicacion_section = soup.find('h3', class_='mb-4 fw-bold section-title', string="Ubicación")
if ubicacion_section:
    # Busca el siguiente <p> después del título "Ubicación"
    direccion_tag = ubicacion_section.find_next('p')
    if direccion_tag:
        direccion = direccion_tag.get_text(strip=True)
        print("\nDirección:", direccion)
    else:
        print("\nNo se encontró la dirección.")
else:
    print("\nNo se encontró la sección de ubicación.")

# Obtener latitud y longitud usando Nominatim
if direccion:
    url_nominatim = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': direccion,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'MiAppWebScraping/1.0 (tu_email@dominio.com)'
    }
    response_geo = requests.get(url_nominatim, params=params, headers=headers)
    try:
        data = response_geo.json()
        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            print("Latitud:", lat)
            print("Longitud:", lon)
        else:
            print("No se encontraron coordenadas para la dirección.")
    except Exception as e:
        print("Error al decodificar JSON:", e)
        print("Respuesta recibida:", response_geo.text)