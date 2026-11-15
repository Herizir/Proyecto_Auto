CREATE DATABASE MOTORHAUS_AUTOMOTIVE_CLUB;
GO

USE MOTORHAUS_AUTOMOTIVE_CLUB;
GO
CREATE TABLE Marcas (
    ID_Marca INT IDENTITY(1,1) PRIMARY KEY,
    Nombre_Marca VARCHAR(50) NOT NULL,
    Pais_Origen VARCHAR(50)
);
CREATE TABLE Vehiculos (
    ID_Vehiculo INT IDENTITY(1,1) PRIMARY KEY,
    ID_Marca INT NOT NULL,
    Modelo VARCHAR(100) NOT NULL,
    Anio INT NOT NULL,
    Color VARCHAR(30),
    Kilometraje INT,
    Precio DECIMAL(12,2) NOT NULL,
    Descripcion VARCHAR(500),
    Estado VARCHAR(30),

    FOREIGN KEY (ID_Marca)
    REFERENCES Marcas(ID_Marca)
);
CREATE TABLE Fotos_Vehiculos (
    ID_Foto INT IDENTITY(1,1) PRIMARY KEY,
    ID_Vehiculo INT NOT NULL,
    Foto_URL VARCHAR(500) NOT NULL,
    Descripcion VARCHAR(150),

    FOREIGN KEY (ID_Vehiculo)
    REFERENCES Vehiculos(ID_Vehiculo)
);
INSERT INTO Marcas (Nombre_Marca, Pais_Origen)
VALUES
('BMW', 'Alemania'),
('Mercedes-Benz', 'Alemania'),
('Audi', 'Alemania'),
('Ford', 'Estados Unidos'),
('Chevrolet', 'Estados Unidos'),
('Toyota', 'Japón');
INSERT INTO Vehiculos
(ID_Marca, Modelo, Anio, Color, Kilometraje, Precio, Descripcion, Estado)
VALUES
(1, 'BMW M4 Competition', 2024, 'Negro', 5000, 1850000, 'Deportivo de lujo', 'Disponible'),

(2, 'Mercedes-Benz C300', 2023, 'Blanco', 8000, 1150000, 'Sedán de lujo', 'Disponible'),

(3, 'Audi RS5', 2024, 'Gris', 3000, 1750000, 'Deportivo premium', 'Disponible'),

(4, 'Ford Mustang GT', 2022, 'Rojo', 12000, 950000, 'Motor V8 deportivo', 'Disponible'),

(5, 'Chevrolet Camaro SS', 2023, 'Amarillo', 7000, 1100000, 'Muscle car deportivo', 'Disponible'),

(6, 'Toyota Supra', 2024, 'Azul', 4000, 1450000, 'Deportivo japonés', 'Disponible');
INSERT INTO Fotos_Vehiculos
(ID_Vehiculo, Foto_URL, Descripcion)
VALUES
(1, 'fotos/bmw_m4.jpg', 'Fotografía BMW M4'),

(2, 'fotos/mercedes_c300.jpg', 'Fotografía Mercedes C300'),

(3, 'fotos/audi_rs5.jpg', 'Fotografía Audi RS5'),

(4, 'fotos/mustang_gt.jpg', 'Fotografía Ford Mustang'),

(5, 'fotos/camaro_ss.jpg', 'Fotografía Chevrolet Camaro'),

(6, 'fotos/toyota_supra.jpg', 'Fotografía Toyota Supra');
SELECT
    V.ID_Vehiculo,
    M.Nombre_Marca,
    V.Modelo,
    V.Anio,
    V.Color,
    V.Kilometraje,
    V.Precio,
    V.Estado,
    F.Foto_URL
FROM Vehiculos V
INNER JOIN Marcas M
ON V.ID_Marca = M.ID_Marca
LEFT JOIN Fotos_Vehiculos F
ON V.ID_Vehiculo = F.ID_Vehiculo;
SELECT * FROM Vehiculos
WHERE Anio = 2024;
SELECT * FROM Vehiculos
ORDER BY Precio ASC;
SELECT * FROM Vehiculos
WHERE Estado = 'Disponible';
SELECT V.Modelo, M.Nombre_Marca, V.Precio
FROM Vehiculos V
INNER JOIN Marcas M
ON V.ID_Marca = M.ID_Marca
WHERE M.Nombre_Marca = 'BMW';
