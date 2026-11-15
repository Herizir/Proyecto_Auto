CREATE DATABASE MOTORHAUS;
GO

USE MOTORHAUS;
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

CREATE DATABASE RegistroPersonas;
GO

USE RegistroPersonas;
GO
CREATE TABLE Personas (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    Numero_Telefono VARCHAR(15) NOT NULL,
    Correo_Electronico VARCHAR(100) NOT NULL
);
GO
INSERT INTO Personas (Nombre, Numero_Telefono, Correo_Electronico)
VALUES
('Juan Pérez López', '6311000001', 'juan.perez@gmail.com'),
('María González Ruiz', '6311000002', 'maria.gonzalez@gmail.com'),
('Carlos Rodríguez Díaz', '6311000003', 'carlos.rodriguez@gmail.com'),
('Ana Martínez Torres', '6311000004', 'ana.martinez@gmail.com'),
('José Hernández Cruz', '6311000005', 'jose.hernandez@gmail.com'),
('Laura Sánchez Flores', '6311000006', 'laura.sanchez@gmail.com'),
('Miguel Ramírez Soto', '6311000007', 'miguel.ramirez@gmail.com'),
('Fernanda López García', '6311000008', 'fernanda.lopez@gmail.com'),
('Roberto Torres Medina', '6311000009', 'roberto.torres@gmail.com'),
('Daniela Flores Castro', '6311000010', 'daniela.flores@gmail.com'),
('Pedro Morales Reyes', '6311000011', 'pedro.morales@gmail.com'),
('Gabriela Jiménez Ortiz', '6311000012', 'gabriela.jimenez@gmail.com'),
('Fernando Castillo Vega', '6311000013', 'fernando.castillo@gmail.com'),
('Sofía Mendoza Ríos', '6311000014', 'sofia.mendoza@gmail.com'),
('Ricardo Aguilar Luna', '6311000015', 'ricardo.aguilar@gmail.com'),
('Valeria Romero Silva', '6311000016', 'valeria.romero@gmail.com'),
('Andrés Navarro Peña', '6311000017', 'andres.navarro@gmail.com'),
('Camila Ortega Díaz', '6311000018', 'camila.ortega@gmail.com'),
('Eduardo Vargas León', '6311000019', 'eduardo.vargas@gmail.com'),
('Paola Rojas Méndez', '6311000020', 'paola.rojas@gmail.com'),
('Alejandro Cruz Ramírez', '6311000021', 'alejandro.cruz@gmail.com'),
('Natalia Herrera Soto', '6311000022', 'natalia.herrera@gmail.com'),
('Francisco Medina López', '6311000023', 'francisco.medina@gmail.com'),
('Daniela Reyes Torres', '6311000024', 'daniela.reyes@gmail.com'),
('Jorge Silva Morales', '6311000025', 'jorge.silva@gmail.com'),
('Andrea Castro Jiménez', '6311000026', 'andrea.castro@gmail.com'),
('Luis Peña Vargas', '6311000027', 'luis.pena@gmail.com'),
('Regina León Navarro', '6311000028', 'regina.leon@gmail.com'),
('Manuel Díaz Romero', '6311000029', 'manuel.diaz@gmail.com'),
('Alejandra Soto Aguilar', '6311000030', 'alejandra.soto@gmail.com'),
('Diego Méndez Ortiz', '6311000031', 'diego.mendez@gmail.com'),
('Mariana Vega Ríos', '6311000032', 'mariana.vega@gmail.com'),
('Óscar Luna Herrera', '6311000033', 'oscar.luna@gmail.com'),
('Isabella Flores Reyes', '6311000034', 'isabella.flores@gmail.com'),
('Raúl Ortiz Castillo', '6311000035', 'raul.ortiz@gmail.com'),
('Ximena García Sánchez', '6311000036', 'ximena.garcia@gmail.com'),
('Héctor Ruiz Martínez', '6311000037', 'hector.ruiz@gmail.com'),
('Lucía Torres González', '6311000038', 'lucia.torres@gmail.com'),
('Emilio Ramírez Cruz', '6311000039', 'emilio.ramirez@gmail.com'),
('Renata Morales Peña', '6311000040', 'renata.morales@gmail.com'),
('Arturo Navarro Silva', '6311000041', 'arturo.navarro@gmail.com'),
('Elena Jiménez Vega', '6311000042', 'elena.jimenez@gmail.com'),
('Gabriel Reyes Medina', '6311000043', 'gabriel.reyes@gmail.com'),
('Victoria Castillo Rojas', '6311000044', 'victoria.castillo@gmail.com'),
('Adrián Herrera López', '6311000045', 'adrian.herrera@gmail.com'),
('Carolina Aguilar Díaz', '6311000046', 'carolina.aguilar@gmail.com'),
('Iván Romero Flores', '6311000047', 'ivan.romero@gmail.com'),
('Melissa Ortega Cruz', '6311000048', 'melissa.ortega@gmail.com'),
('Sebastián Vargas Ruiz', '6311000049', 'sebastian.vargas@gmail.com'),
('Daniela Mendoza Castro', '6311000050', 'daniela.mendoza@gmail.com');
GO
SELECT * FROM Personas;
SELECT Nombre FROM Personas;
SELECT * FROM Personas
WHERE Nombre = 'Juan Pérez López';
SELECT COUNT(*) AS Total_Personas
FROM Personas;
SELECT * FROM Personas
ORDER BY Nombre ASC;  