# -*- coding: utf-8 -*-
"""
Created on Sat Nov 1 17:34:09 2025

@author: agutierrez752
"""

import asyncpg
from dotenv import load_dotenv
import os
from google import genai
from google.genai import types 
from google.genai.errors import APIError
import numpy as np
import asyncio 

# Cargar variables de entorno (usamos 'cred.env' como en main.py)
load_dotenv('cred.env')

# --- Configuración de BD y Gemini ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Modelo de embeddings de Google con 768 dimensiones
EMBEDDING_MODEL = 'text-embedding-004'

# --- Inicialización del Cliente Gemini ---
try:
    # Usamos el Cliente Síncrono estándar
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Cliente Gemini Síncrono inicializado.")
except Exception as e:
    print(f"❌ Error al inicializar cliente Gemini: {e}")
    exit()

# --- Función Principal de Procesamiento ---
async def generate_and_update_vectors():
    conn = None
    try:
        # Conexión directa (no usamos pool porque es un script de una sola corrida)
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=int(DB_PORT)
        )
        print("✅ Conexión a PostgreSQL establecida.")

        # 1. Seleccionar propiedades pendientes:
        properties_to_process = await conn.fetch("""
            SELECT id_propiedad, descripcion_ia
            FROM Propiedad
            WHERE descripcion_ia IS NOT NULL 
            AND embedding IS NULL;
        """)
        
        if not properties_to_process:
            print("✅ No hay propiedades pendientes de vectorización. Tarea completa.")
            return

        print(f"Encontradas {len(properties_to_process)} propiedades para vectorizar...")
        
        # 2. Generar y actualizar vector por vector:
        processed_count = 0
        
        for record in properties_to_process:
            prop_id = record['id_propiedad']
            desc_ia = record['descripcion_ia']
            
            try:
                # Llamada a la API (todos los argumentos han sido corregidos)
                response = await asyncio.to_thread(
                    client.models.embed_content,
                    model=EMBEDDING_MODEL,
                    contents=[desc_ia], 
                    config=types.EmbedContentConfig( 
                        task_type="RETRIEVAL_DOCUMENT",
                    ),
                )
                
                # CORRECCIÓN FINAL: Acceder al atributo .values (plural)
                # 1. Obtenemos el objeto Embedding (el primero y único)
                embedding_object = response.embeddings[0] 
                # 2. Extraemos la lista de flotantes del atributo '.values'
                embedding_vector_list = embedding_object.values # <--- CORRECCIÓN CLAVE: .values
                
                vector_str = "[" + ",".join(map(str, embedding_vector_list)) + "]"
                
                # 3. Actualizar la base de datos
                await conn.execute("""
                    UPDATE Propiedad
                    SET embedding = $1
                    WHERE id_propiedad = $2;
                """, vector_str, prop_id)
                
                processed_count += 1
                print(f"  [ID {prop_id}] Vector generado y actualizado (Dim: {len(embedding_vector_list)}).")
                
            except APIError as e:
                print(f"  ❌ Error de API en ID {prop_id}: {e}")
            except Exception as e:
                print(f"  ❌ Error desconocido al procesar ID {prop_id}: {e}")

        print(f"\n--- Proceso finalizado. Total de propiedades vectorizadas: {processed_count} ---")

    except Exception as e:
        print(f"❌ Error fatal en el script: {e}")
    finally:
        if conn:
            await conn.close()
            print("🔌 Conexión a PostgreSQL cerrada.")


# Ejecución del script asíncrono
if __name__ == '__main__':
    import asyncio
    try:
        # Intenta la ejecución estándar
        asyncio.run(generate_and_update_vectors())
    except RuntimeError as e:
        # Si el loop ya está corriendo (típico en entornos IDE/notebook), usa el loop existente
        if "loop is already running" in str(e) or "cannot be called from a running event loop" in str(e):
            loop = asyncio.get_event_loop()
            print("⚠️ Advertencia: Loop existente detectado. Ejecutando en loop actual.")
            loop.run_until_complete(generate_and_update_vectors())
        else:
            raise e