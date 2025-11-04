# -*- coding: utf-8 -*-
"""
Created on Sat Nov  1 13:52:28 2025

@author: agutierrez752
"""

import psycopg2
from dotenv import load_dotenv
import os

# Cargar variables de entorno del archivo .env
load_dotenv('cred.env')


# DEBUG: Verificar directorio actual y archivos
print("📁 Directorio actual:", os.getcwd())
print("📋 Archivos en directorio:", [f for f in os.listdir('.') if f.endswith('.env') or f == '.env'])


# --- Configuración de la Base de Datos ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

print(DB_PASSWORD)

def connect_db():
    """
    Establece la conexión segura a la base de datos PostgreSQL.
    Retorna el objeto de conexión (conn) y el cursor (cur).
    """
    conn = None
    cur = None
    try:
        # Intentar la conexión usando las credenciales cargadas
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        print("✅ Conexión a PostgreSQL exitosa.")
        return conn, cur
    except psycopg2.Error as e:
        print(f"❌ Error al conectar a PostgreSQL: {e}")
        # Retorna None si hay un error
        return None, None

def close_connection(conn, cur):
    """Cierra el cursor y la conexión a la base de datos."""
    if cur:
        cur.close()
    if conn:
        conn.close()
        print("🔌 Conexión a PostgreSQL cerrada.")

if __name__ == '__main__':
    # Bloque de prueba para verificar la conexión
    conn, cur = connect_db()

    if conn and cur:
        # Prueba: Recuerdo de las 10 primeras propiedades
        try:
            cur.execute("SELECT agente_nombre,titulo from public.propiedad;")
            print("\n--- Primeros 10 Registros de Propiedad ---")
            for row in cur.fetchall():
                print(f"Título: {row[0]} | Dirección: {row[1]}")
        except Exception as e:
            print(f"Error al ejecutar la consulta de prueba: {e}")
        
        close_connection(conn, cur)