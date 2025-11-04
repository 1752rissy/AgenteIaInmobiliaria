CREATE TABLE Propiedad (
    -- ID y Referencias
    id_propiedad SERIAL PRIMARY KEY,
    -- Aquí podrías añadir una tabla 'Agente' y referenciarla, pero la omitiremos por ahora para simplificar el MVP
    agente_nombre VARCHAR(100), -- Nombre del agente/inmobiliaria que sube la propiedad

    -- Datos de Identificación y Ubicación
    titulo VARCHAR(255) NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    ciudad VARCHAR(100) NOT NULL,

    -- **GEOLOCALIZACIÓN (Usando PostGIS)**
    -- geometry(Point) almacena la latitud y longitud, permitiendo consultas espaciales
    ubicacion GEOMETRY(Point, 4326) NOT NULL, 

    -- Características Básicas
    tipo_propiedad VARCHAR(50) NOT NULL, -- Ej: 'Departamento', 'Casa'
    ambientes INT NOT NULL,
    metros_cuadrados INT NOT NULL,

    -- Financiero y Operacional
    precio_alquiler DECIMAL(10, 2) NOT NULL,
    moneda VARCHAR(3) NOT NULL DEFAULT 'ARS',

    -- **Datos de Texto y IA**
    descripcion_manual TEXT, -- Texto base que sube el agente.
    descripcion_ia TEXT,     -- Campo para guardar el texto optimizado por la IA.

    -- **Amenities y Filtros Inteligentes**
    -- JSONB es crucial para almacenar los detalles flexibles que la IA usará
    amenities JSONB,         -- Ejemplo: {"pileta": true, "mascotas_permitidas": false, "seguridad_24h": true}
    
    -- Metadatos
    fecha_publicacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    esta_disponible BOOLEAN DEFAULT TRUE
);