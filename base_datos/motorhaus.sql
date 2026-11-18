/* =============================================================
   MOTORHAUS — base de datos compartida por la tienda web
   y la aplicación de escritorio.

   El script se puede ejecutar varias veces: solo crea lo que
   falta y solo inserta los datos de ejemplo si las tablas
   están vacías. Lo ejecutan automáticamente el servidor web y
   la app de escritorio al arrancar; también puedes abrirlo en
   SQL Server Management Studio y ejecutarlo a mano.
   ============================================================= */

IF DB_ID('MOTORHAUS') IS NULL
    CREATE DATABASE MOTORHAUS;
GO

USE MOTORHAUS;
GO

/* ---------- Catálogo ---------- */

IF OBJECT_ID('dbo.Marcas', 'U') IS NULL
CREATE TABLE dbo.Marcas (
    ID_Marca      INT IDENTITY(1,1) PRIMARY KEY,
    Nombre_Marca  VARCHAR(50)  NOT NULL UNIQUE,
    Pais_Origen   VARCHAR(50)  NULL
);
GO

IF OBJECT_ID('dbo.Vehiculos', 'U') IS NULL
CREATE TABLE dbo.Vehiculos (
    ID_Vehiculo   INT IDENTITY(1,1) PRIMARY KEY,
    ID_Marca      INT            NOT NULL REFERENCES dbo.Marcas(ID_Marca),
    Modelo        VARCHAR(100)   NOT NULL,
    Version       VARCHAR(100)   NULL,
    Tipo          VARCHAR(30)    NOT NULL DEFAULT 'Sedán',
    Anio          INT            NOT NULL,
    Color         VARCHAR(30)    NULL,
    Kilometraje   INT            NOT NULL DEFAULT 0,
    Combustible   VARCHAR(30)    NOT NULL DEFAULT 'Gasolina',
    Precio        DECIMAL(12,2)  NOT NULL,
    Descripcion   VARCHAR(500)   NULL,
    Estado        VARCHAR(30)    NOT NULL DEFAULT 'Disponible'
                  CHECK (Estado IN ('Disponible', 'Reservado', 'Vendido')),
    Etiqueta      VARCHAR(30)    NULL,
    Fecha_Alta    DATETIME2      NOT NULL DEFAULT SYSDATETIME()
);
GO

IF OBJECT_ID('dbo.Fotos_Vehiculos', 'U') IS NULL
CREATE TABLE dbo.Fotos_Vehiculos (
    ID_Foto       INT IDENTITY(1,1) PRIMARY KEY,
    ID_Vehiculo   INT           NOT NULL REFERENCES dbo.Vehiculos(ID_Vehiculo) ON DELETE CASCADE,
    Foto_URL      VARCHAR(500)  NOT NULL,
    Descripcion   VARCHAR(150)  NULL
);
GO

/* ---------- Personas ---------- */

-- Cuentas: clientes que se registran en la web y administradores del panel.
IF OBJECT_ID('dbo.Usuarios', 'U') IS NULL
CREATE TABLE dbo.Usuarios (
    ID_Usuario      INT IDENTITY(1,1) PRIMARY KEY,
    Nombre          VARCHAR(100)  NOT NULL,
    Correo          VARCHAR(150)  NOT NULL UNIQUE,
    Clave_Hash      VARCHAR(255)  NOT NULL,
    Rol             VARCHAR(20)   NOT NULL DEFAULT 'cliente'
                    CHECK (Rol IN ('cliente', 'admin')),
    Fecha_Registro  DATETIME2     NOT NULL DEFAULT SYSDATETIME()
);
GO

-- Clientes / prospectos. Pueden venir de la web (registro o consulta)
-- o darse de alta desde el escritorio.
IF OBJECT_ID('dbo.Clientes', 'U') IS NULL
CREATE TABLE dbo.Clientes (
    ID_Cliente   INT IDENTITY(1,1) PRIMARY KEY,
    ID_Usuario   INT           NULL REFERENCES dbo.Usuarios(ID_Usuario) ON DELETE SET NULL,
    Nombre       VARCHAR(100)  NOT NULL,
    Correo       VARCHAR(150)  NULL,
    Telefono     VARCHAR(20)   NULL,
    Interes      VARCHAR(100)  NULL,
    Notas        VARCHAR(500)  NULL,
    Estado       VARCHAR(30)   NOT NULL DEFAULT 'Nuevo contacto',
    Origen       VARCHAR(20)   NOT NULL DEFAULT 'Escritorio',
    Fecha_Alta   DATETIME2     NOT NULL DEFAULT SYSDATETIME()
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_Clientes_Correo')
    CREATE UNIQUE INDEX UX_Clientes_Correo ON dbo.Clientes(Correo) WHERE Correo IS NOT NULL;
GO

/* ---------- Actividad ---------- */

IF OBJECT_ID('dbo.Favoritos', 'U') IS NULL
CREATE TABLE dbo.Favoritos (
    ID_Usuario   INT        NOT NULL REFERENCES dbo.Usuarios(ID_Usuario) ON DELETE CASCADE,
    ID_Vehiculo  INT        NOT NULL REFERENCES dbo.Vehiculos(ID_Vehiculo) ON DELETE CASCADE,
    Fecha        DATETIME2  NOT NULL DEFAULT SYSDATETIME(),
    PRIMARY KEY (ID_Usuario, ID_Vehiculo)
);
GO

-- Mensajes que llegan desde la web (contacto, consulta de un auto, recuperación).
IF OBJECT_ID('dbo.Consultas', 'U') IS NULL
CREATE TABLE dbo.Consultas (
    ID_Consulta  INT IDENTITY(1,1) PRIMARY KEY,
    ID_Cliente   INT            NOT NULL REFERENCES dbo.Clientes(ID_Cliente) ON DELETE CASCADE,
    ID_Vehiculo  INT            NULL REFERENCES dbo.Vehiculos(ID_Vehiculo) ON DELETE SET NULL,
    Tipo         VARCHAR(30)    NOT NULL DEFAULT 'Contacto',
    Mensaje      VARCHAR(1000)  NULL,
    Atendida     BIT            NOT NULL DEFAULT 0,
    Fecha        DATETIME2      NOT NULL DEFAULT SYSDATETIME()
);
GO

IF OBJECT_ID('dbo.Ventas', 'U') IS NULL
CREATE TABLE dbo.Ventas (
    ID_Venta         INT IDENTITY(1,1) PRIMARY KEY,
    ID_Cliente       INT            NOT NULL REFERENCES dbo.Clientes(ID_Cliente),
    ID_Vehiculo      INT            NOT NULL REFERENCES dbo.Vehiculos(ID_Vehiculo),
    Precio_Acordado  DECIMAL(12,2)  NOT NULL,
    Estado           VARCHAR(30)    NOT NULL DEFAULT 'En seguimiento'
                     CHECK (Estado IN ('En seguimiento', 'Reservado', 'Cerrada', 'Cancelada')),
    Notas            VARCHAR(500)   NULL,
    Fecha            DATETIME2      NOT NULL DEFAULT SYSDATETIME()
);
GO

/* ---------- Datos de ejemplo (solo si está vacío) ---------- */

IF NOT EXISTS (SELECT 1 FROM dbo.Marcas)
INSERT INTO dbo.Marcas (Nombre_Marca, Pais_Origen) VALUES
('BMW', 'Alemania'),
('Mercedes-Benz', 'Alemania'),
('Audi', 'Alemania'),
('Ford', 'Estados Unidos'),
('Chevrolet', 'Estados Unidos'),
('Toyota', 'Japón'),
('Porsche', 'Alemania');
GO

IF NOT EXISTS (SELECT 1 FROM dbo.Vehiculos)
BEGIN
    INSERT INTO dbo.Vehiculos
        (ID_Marca, Modelo, Version, Tipo, Anio, Color, Kilometraje, Combustible, Precio, Descripcion, Estado, Etiqueta)
    SELECT M.ID_Marca, V.Modelo, V.Version, V.Tipo, V.Anio, V.Color, V.Km, 'Gasolina', V.Precio, V.Descripcion, 'Disponible', V.Etiqueta
    FROM (VALUES
        ('BMW',           'M4 Competition', 'Coupé · xDrive',     'Deportivo', 2024, 'Negro',    5000,  1850000, 'Deportivo de lujo',     'DESTACADO'),
        ('Mercedes-Benz', 'C300',           'AMG Line',           'Sedán',     2023, 'Blanco',   8000,  1150000, 'Sedán de lujo',         'RECIÉN LLEGADO'),
        ('Audi',          'RS5',            'Sportback quattro',  'Deportivo', 2024, 'Gris',     3000,  1750000, 'Deportivo premium',     'SELECCIÓN'),
        ('Ford',          'Mustang GT',     '5.0 V8 · Fastback',  'Deportivo', 2022, 'Rojo',     12000,  950000, 'Motor V8 deportivo',    'SELECCIÓN'),
        ('Chevrolet',     'Camaro SS',      '6.2 V8',             'Deportivo', 2023, 'Amarillo', 7000,  1100000, 'Muscle car deportivo',  'SELECCIÓN'),
        ('Toyota',        'Supra',          'GR 3.0',             'Deportivo', 2024, 'Azul',     4000,  1450000, 'Deportivo japonés',     'RECIÉN LLEGADO'),
        ('Porsche',       '911 Carrera',    '3.0 Turbo · Coupé',  'Deportivo', 2023, 'Gris',     8200,  2450000, 'Ícono deportivo',       'DESTACADO'),
        ('BMW',           'X5',             'xDrive40i · M Sport','SUV',       2023, 'Negro',    12300, 1490000, 'SUV de lujo',           'DESTACADO'),
        ('Audi',          'Q5',             '45 TFSI · S line',   'SUV',       2022, 'Blanco',   21000,  895000, 'SUV premium',           'SELECCIÓN'),
        ('BMW',           'Serie 3',        '330i · Sport Line',  'Sedán',     2023, 'Azul',     14600,  920000, 'Sedán deportivo',       'SELECCIÓN')
    ) AS V(Marca, Modelo, Version, Tipo, Anio, Color, Km, Precio, Descripcion, Etiqueta)
    INNER JOIN dbo.Marcas M ON M.Nombre_Marca = V.Marca;

    INSERT INTO dbo.Fotos_Vehiculos (ID_Vehiculo, Foto_URL, Descripcion)
    SELECT V.ID_Vehiculo, F.Url, CONCAT('Fotografía ', V.Modelo)
    FROM (VALUES
        ('911 Carrera', 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=900&q=80'),
        ('C300',        'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=900&q=80'),
        ('X5',          'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=900&q=80'),
        ('Q5',          'https://images.unsplash.com/photo-1606152421802-db97b9c7a11b?auto=format&fit=crop&w=900&q=80'),
        ('Serie 3',     'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=900&q=80')
    ) AS F(Modelo, Url)
    INNER JOIN dbo.Vehiculos V ON V.Modelo = F.Modelo;
END
GO
