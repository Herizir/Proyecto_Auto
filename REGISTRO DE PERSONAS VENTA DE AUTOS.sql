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