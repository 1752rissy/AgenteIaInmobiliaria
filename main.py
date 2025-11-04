from fastapi import FastAPI, HTTPException
import asyncpg
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel # <-- NUEVO
import asyncio # <-- NUEVO
import logging
from google import genai # <-- NUEVO
from google.genai import types # <-- NUEVO (Para EmbedContentConfig)
import logging


# Cargar variables de entorno
load_dotenv('cred.env')

EMBEDDING_MODEL = 'text-embedding-004'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    # Usamos el Cliente Síncrono estándar, la sintaxis que funcionó en vector_generator.py
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Cliente Gemini Síncrono inicializado para búsquedas.")
except Exception as e:
    print(f"❌ Error al inicializar cliente Gemini en main.py: {e}")
    

# --- Configuración de la Base de Datos ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT") 

app = FastAPI(title="MVP Búsqueda Inmobiliaria IA")

# Variable global para el pool de conexiones (FastAPI la inicializa)
db_pool = None 


    
    

# ----------------------------------------------------
# 1. Funciones de Startup/Shutdown de FastAPI
# ----------------------------------------------------
# Se ejecuta antes de que Uvicorn acepte solicitudes
@app.on_event("startup")
async def startup_db_pool():
    global db_pool
    try:
        # Crea el pool de conexiones asíncrono
        db_pool = await asyncpg.create_pool(
            timeout=5.0,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=int(DB_PORT),
            min_size=1, 
            max_size=10
        )
        print("✅ Pool de conexiones a PostgreSQL (asyncpg) creado.")
    except Exception as e:
        print(f"❌ Error al crear el pool de BD: {e}")
        raise RuntimeError("No se pudo iniciar la conexión a la base de datos.")


# Se ejecuta cuando Uvicorn se detiene
@app.on_event("shutdown")
async def shutdown_db_pool():
    if db_pool:
        await db_pool.close()
        print("🔌 Pool de conexiones a PostgreSQL cerrado.")

# ----------------------------------------------------
# 2. Endpoint de Propiedades (Consulta Real a BD)
# ----------------------------------------------------
@app.get("/propiedades/top")
async def get_top_properties():
    """
    Recupera el título, la dirección y las coordenadas geográficas 
    (obtenidas de PostGIS) de las 5 primeras propiedades.
    """
    
    # Adquiere una conexión del pool y la libera al salir del bloque 'async with'
    async with db_pool.acquire() as conn:
        # Ejecuta la consulta SQL, incluyendo las funciones de PostGIS
        results = await conn.fetch("""
            SELECT 
                titulo, 
                direccion, 
                ST_X(ubicacion) AS longitud, 
                ST_Y(ubicacion) AS latitud
            FROM Propiedad 
            LIMIT 5;
        """)

    # Transforma los resultados (objetos Record) en una lista de diccionarios
    data = [dict(row) for row in results]
    
    return {
        "status": "success",
        "count": len(data),
        "data": data
    }


# ----------------------------------------------------
# 3. Lógica de Búsqueda Semántica
# ----------------------------------------------------



async def search_properties_semantic(pool: asyncpg.Pool, query: str, limit: int = 5):
    """Genera el embedding de la consulta y ejecuta la búsqueda de similitud en PostgreSQL."""
    
    # 1. Generar embedding de la consulta del usuario
    try:
        # Usamos asyncio.to_thread para correr la función síncrona en un hilo
        response = await asyncio.to_thread(
            gemini_client.models.embed_content,
            model=EMBEDDING_MODEL,
            contents=[query], 
            config=types.EmbedContentConfig( 
                task_type="RETRIEVAL_QUERY", # Usamos RETRIEVAL_QUERY para la consulta
            ),
        )
        # Accedemos al valor de la lista de flotantes (la sintaxis que encontramos)
        embedding_object = response.embeddings[0] 
        query_vector_list = embedding_object.values # <-- .values (en plural)
        
        # Convertimos la lista de Python al formato vector de PostgreSQL
        query_vector_str = "[" + ",".join(map(str, query_vector_list)) + "]"
        
    except Exception as e:
        # Retornamos un diccionario con el error para manejarlo en el endpoint
        return {"error": f"Error al generar embedding de la consulta: {e}"}

    # 2. Ejecutar búsqueda de similitud de coseno
    # 'embedding' <=> $1' calcula la distancia de coseno. Cuanto menor el valor, más similar.
    results = await pool.fetch("""
        SELECT 
            id_propiedad, 
            titulo, 
            precio_alquiler, 
            descripcion_ia,
            embedding <=> $1 AS distance
        FROM 
            Propiedad
        ORDER BY 
            distance ASC
        LIMIT $2;
    """, query_vector_str, limit)

    return [{
        'id_propiedad': r['id_propiedad'],
        'titulo': r['titulo'],
        'precio': float(r['precio_alquiler']),
        'descripcion_ia': r['descripcion_ia'],
        'distance': r['distance']
    } for r in results]


class SearchQuery(BaseModel):
    query: str
    limit: int = 5



# Función de dependencia de FastAPI
def get_db_pool():
    """Retorna el pool global de conexiones a la BD para inyección de dependencias."""
    global db_pool
    if db_pool is None:
        # En caso de que el pool no esté inicializado (debería estarlo después de startup)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La conexión a la base de datos no está disponible."
        )
    return db_pool

# ... (Antes de tus endpoints)

# ----------------------------------------------------
# 4. Endpoint de Búsqueda Semántica
# ----------------------------------------------------
@app.post("/propiedades/search/semantic", summary="Búsqueda Semántica de Propiedades")
async def search_properties(
    data: SearchQuery,
    pool:asyncpg.Pool = Depends(get_db_pool)
    ):
    """
    Busca propiedades en la base de datos utilizando embeddings vectoriales (pgvector).
    La búsqueda se realiza basándose en la similitud de significado (semántica) de la consulta.
    """
    try:
        results = await search_properties_semantic(
            pool, 
            query=data.query, 
            limit=data.limit
        )
        
        if 'error' in results:
            raise HTTPException(status_code=500, detail=results['error'])
            
        return {
            "query": data.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")
    



# ----------------------------------------------------
# 3. Endpoint Raíz
# ----------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "API de Búsqueda Inmobiliaria (MVP) - ¡Lista para la IA!"}