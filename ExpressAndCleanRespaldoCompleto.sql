-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: 10.147.17.29    Database: crystalcontrol
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('945aabf294b2');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cajas`
--

DROP TABLE IF EXISTS `cajas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cajas` (
  `id_caja` int NOT NULL AUTO_INCREMENT,
  `nombre_caja` varchar(50) DEFAULT NULL,
  `id_usuario_cajero` int DEFAULT NULL,
  `status` int DEFAULT NULL,
  PRIMARY KEY (`id_caja`),
  KEY `id_usuario_cajero` (`id_usuario_cajero`),
  CONSTRAINT `cajas_ibfk_1` FOREIGN KEY (`id_usuario_cajero`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cajas`
--

LOCK TABLES `cajas` WRITE;
/*!40000 ALTER TABLE `cajas` DISABLE KEYS */;
INSERT INTO `cajas` VALUES (1,'Caja 1',4,1);
/*!40000 ALTER TABLE `cajas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clientes`
--

DROP TABLE IF EXISTS `clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clientes` (
  `id_cliente` int NOT NULL AUTO_INCREMENT,
  `id_usuario` int NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_cliente`),
  KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `clientes_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clientes`
--

LOCK TABLES `clientes` WRITE;
/*!40000 ALTER TABLE `clientes` DISABLE KEYS */;
INSERT INTO `clientes` VALUES (1,3,'1234567890'),(2,5,'+524777230730'),(3,6,'+52477 723073');
/*!40000 ALTER TABLE `clientes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compras`
--

DROP TABLE IF EXISTS `compras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compras` (
  `id_compra` int NOT NULL AUTO_INCREMENT,
  `folio_compra` varchar(20) DEFAULT NULL,
  `id_usuario_solicita` int NOT NULL,
  `fecha_solicitud` datetime DEFAULT NULL,
  `fecha_generada` datetime DEFAULT NULL,
  `status_general` int DEFAULT NULL,
  `observaciones_admin` text,
  PRIMARY KEY (`id_compra`),
  UNIQUE KEY `folio_compra` (`folio_compra`),
  KEY `id_usuario_solicita` (`id_usuario_solicita`),
  CONSTRAINT `compras_ibfk_1` FOREIGN KEY (`id_usuario_solicita`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compras`
--

LOCK TABLES `compras` WRITE;
/*!40000 ALTER TABLE `compras` DISABLE KEYS */;
INSERT INTO `compras` VALUES (2,'PUR-2026-0002',1,'2026-04-13 00:00:00',NULL,2,'aprove');
/*!40000 ALTER TABLE `compras` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tg_generar_folio_compra` BEFORE INSERT ON `compras` FOR EACH ROW BEGIN
    DECLARE next_id INT;
    SET next_id = (SELECT AUTO_INCREMENT FROM information_schema.TABLES 
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'Compras');
    SET NEW.folio_compra = CONCAT('PUR-', YEAR(CURDATE()), '-', LPAD(next_id, 4, '0'));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `cortes_cajas`
--

DROP TABLE IF EXISTS `cortes_cajas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cortes_cajas` (
  `id_corte` int NOT NULL AUTO_INCREMENT,
  `id_caja` int NOT NULL,
  `fecha_apertura` datetime DEFAULT (now()),
  `fecha_cierre` datetime DEFAULT NULL,
  `monto_apertura` decimal(10,2) NOT NULL,
  `monto_cierre_esperado` decimal(10,2) DEFAULT NULL,
  `monto_cierre_real` decimal(10,2) DEFAULT NULL,
  `diferencia` decimal(10,2) DEFAULT NULL,
  `estatus` int DEFAULT NULL,
  PRIMARY KEY (`id_corte`),
  KEY `id_caja` (`id_caja`),
  CONSTRAINT `cortes_cajas_ibfk_1` FOREIGN KEY (`id_caja`) REFERENCES `cajas` (`id_caja`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cortes_cajas`
--

LOCK TABLES `cortes_cajas` WRITE;
/*!40000 ALTER TABLE `cortes_cajas` DISABLE KEYS */;
INSERT INTO `cortes_cajas` VALUES (1,1,'2026-04-13 18:40:41',NULL,200.00,NULL,NULL,NULL,1);
/*!40000 ALTER TABLE `cortes_cajas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_compras`
--

DROP TABLE IF EXISTS `detalle_compras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_compras` (
  `id_detalle_compra` int NOT NULL AUTO_INCREMENT,
  `id_compra` int NOT NULL,
  `id_materia` int NOT NULL,
  `id_proveedor_seleccionado` int DEFAULT NULL,
  `cantidad_solicitada` decimal(10,2) NOT NULL,
  `cantidad_aprobada` decimal(10,2) DEFAULT NULL,
  `cantidad_recibida` decimal(10,2) DEFAULT '0.00',
  `precio_unitario_final` decimal(10,2) DEFAULT NULL,
  `dias_entrega` int DEFAULT NULL,
  `status_item` int DEFAULT NULL,
  PRIMARY KEY (`id_detalle_compra`),
  KEY `id_compra` (`id_compra`),
  KEY `id_materia` (`id_materia`),
  KEY `id_proveedor_seleccionado` (`id_proveedor_seleccionado`),
  CONSTRAINT `detalle_compras_ibfk_1` FOREIGN KEY (`id_compra`) REFERENCES `compras` (`id_compra`) ON DELETE CASCADE,
  CONSTRAINT `detalle_compras_ibfk_2` FOREIGN KEY (`id_materia`) REFERENCES `materiaprima` (`id_materia`),
  CONSTRAINT `detalle_compras_ibfk_3` FOREIGN KEY (`id_proveedor_seleccionado`) REFERENCES `proveedores` (`id_proveedor`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_compras`
--

LOCK TABLES `detalle_compras` WRITE;
/*!40000 ALTER TABLE `detalle_compras` DISABLE KEYS */;
INSERT INTO `detalle_compras` VALUES (1,2,16,NULL,30.00,0.00,0.00,0.00,NULL,2),(2,2,20,NULL,200.00,0.00,0.00,0.00,NULL,2),(3,2,21,NULL,100.00,0.00,0.00,0.00,NULL,2);
/*!40000 ALTER TABLE `detalle_compras` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_venta`
--

DROP TABLE IF EXISTS `detalle_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_venta` (
  `id_detalle_venta` int NOT NULL AUTO_INCREMENT,
  `id_venta` int NOT NULL,
  `id_producto` int NOT NULL,
  `id_presentacion` int DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `precio_unitario_momento` decimal(10,2) DEFAULT NULL,
  `utilidad_momento` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id_detalle_venta`,`id_venta`,`id_producto`),
  KEY `id_presentacion` (`id_presentacion`),
  KEY `id_producto` (`id_producto`),
  KEY `id_venta` (`id_venta`),
  CONSTRAINT `detalle_venta_ibfk_1` FOREIGN KEY (`id_presentacion`) REFERENCES `producto_presentación_precio` (`id_presentacion_precio`),
  CONSTRAINT `detalle_venta_ibfk_2` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`),
  CONSTRAINT `detalle_venta_ibfk_3` FOREIGN KEY (`id_venta`) REFERENCES `ventas` (`id_venta`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_venta`
--

LOCK TABLES `detalle_venta` WRITE;
/*!40000 ALTER TABLE `detalle_venta` DISABLE KEYS */;
INSERT INTO `detalle_venta` VALUES (1,2,6,5,3,30.00,0.00),(5,6,2,2,1,25.00,7.50),(6,6,4,4,1,12.00,3.60),(7,9,3,19,10,15.00,0.00),(8,9,3,2,10,25.00,0.00);
/*!40000 ALTER TABLE `detalle_venta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `direcciones`
--

DROP TABLE IF EXISTS `direcciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `direcciones` (
  `id_direccion` int NOT NULL AUTO_INCREMENT,
  `direccion` varchar(255) NOT NULL,
  `id_client` int NOT NULL,
  PRIMARY KEY (`id_direccion`),
  KEY `id_client` (`id_client`),
  CONSTRAINT `direcciones_ibfk_1` FOREIGN KEY (`id_client`) REFERENCES `clientes` (`id_cliente`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `direcciones`
--

LOCK TABLES `direcciones` WRITE;
/*!40000 ALTER TABLE `direcciones` DISABLE KEYS */;
INSERT INTO `direcciones` VALUES (1,'Joyas #50 col. Leon 2, Salamanca, 34600',3);
/*!40000 ALTER TABLE `direcciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `favoritos`
--

DROP TABLE IF EXISTS `favoritos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `favoritos` (
  `id_favorito` int NOT NULL AUTO_INCREMENT,
  `id_producto` int DEFAULT NULL,
  `id_cliente` int DEFAULT NULL,
  PRIMARY KEY (`id_favorito`),
  UNIQUE KEY `_customer_product_uc` (`id_producto`,`id_cliente`),
  KEY `id_cliente` (`id_cliente`),
  CONSTRAINT `favoritos_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id_cliente`),
  CONSTRAINT `favoritos_ibfk_2` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `favoritos`
--

LOCK TABLES `favoritos` WRITE;
/*!40000 ALTER TABLE `favoritos` DISABLE KEYS */;
/*!40000 ALTER TABLE `favoritos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lotesproduccion`
--

DROP TABLE IF EXISTS `lotesproduccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lotesproduccion` (
  `id_lote` int NOT NULL AUTO_INCREMENT,
  `codigo_lote` varchar(50) NOT NULL,
  `id_producto` int NOT NULL,
  `nombre_producto` varchar(100) DEFAULT NULL,
  `folio_orden_ref` varchar(20) DEFAULT NULL,
  `cantidad_producida` decimal(10,2) DEFAULT NULL,
  `unidad_medida` varchar(20) DEFAULT NULL,
  `costo_unitario_produccion` decimal(10,2) DEFAULT NULL,
  `fecha_fabricacion` datetime DEFAULT NULL,
  `fecha_caducidad_estimada` datetime DEFAULT NULL,
  `ubicacion_almacen` varchar(50) DEFAULT NULL,
  `stock_actual` decimal(10,2) DEFAULT NULL,
  `status` int DEFAULT NULL,
  PRIMARY KEY (`id_lote`),
  UNIQUE KEY `codigo_lote` (`codigo_lote`),
  KEY `id_producto` (`id_producto`),
  CONSTRAINT `lotesproduccion_ibfk_1` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lotesproduccion`
--

LOCK TABLES `lotesproduccion` WRITE;
/*!40000 ALTER TABLE `lotesproduccion` DISABLE KEYS */;
INSERT INTO `lotesproduccion` VALUES (1,'LOT-OP-20260413171716-2604131720',6,'Gel Quitacochambre','OP-20260413171716',113.74,'1',0.00,'2026-04-13 23:20:26','2027-04-13 00:00:00','Almacén de Cuarentena',113.74,5),(2,'LOT-OP-20260413171531-2604131734',3,'Limpia Pisos tipo Fabuloso','OP-20260413171531',92.80,'2',0.00,'2026-04-13 23:34:39','2027-04-13 00:00:00','Almacén de Cuarentena',92.80,5),(3,'LOT-OP-20260413175223-2604131756',7,'Cloro Blanqueador y Desinfectante','OP-20260413175223',96.67,'1',0.00,'2026-04-13 23:56:45','2027-04-13 00:00:00','Almacén de Cuarentena',76.67,6),(4,'LOT-OP-20260413182607-2604131828',4,'Jabón Líquido Lavamanos','OP-20260413182607',141.22,'1',0.00,'2026-04-14 00:28:24','2027-04-13 00:00:00','Almacén de Cuarentena',111.22,6),(5,'LOT-OP-20260413200652-2604132008',3,'Limpia Pisos tipo Fabuloso','OP-20260413200652',92.80,'2',0.00,'2026-04-14 02:08:33','2027-04-13 00:00:00','Almacén de Cuarentena',48.30,6);
/*!40000 ALTER TABLE `lotesproduccion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lotesproduccion_calidad`
--

DROP TABLE IF EXISTS `lotesproduccion_calidad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lotesproduccion_calidad` (
  `id_control` int NOT NULL AUTO_INCREMENT,
  `id_lote` int DEFAULT NULL,
  `parametro` varchar(50) DEFAULT NULL,
  `valor_obtenido` varchar(50) DEFAULT NULL,
  `aprobado` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id_control`),
  KEY `id_lote` (`id_lote`),
  CONSTRAINT `lotesproduccion_calidad_ibfk_1` FOREIGN KEY (`id_lote`) REFERENCES `lotesproduccion` (`id_lote`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lotesproduccion_calidad`
--

LOCK TABLES `lotesproduccion_calidad` WRITE;
/*!40000 ALTER TABLE `lotesproduccion_calidad` DISABLE KEYS */;
INSERT INTO `lotesproduccion_calidad` VALUES (2,1,'Calidad Fisicoquímica','pH: 7% | Asp: Correcto | Dens: 10',1),(3,2,'Calidad Fisicoquímica','pH: 5% | Asp: Correcto | Dens: 20',1),(4,3,'Calidad Fisicoquímica','pH: 7% | Asp: Correcto | Dens: 10',1),(5,4,'Calidad Fisicoquímica','pH: 7 | Asp: Correcto | Dens: 10',1),(6,5,'Calidad Fisicoquímica','pH: 7 | Asp: Correcto | Dens: 10',1);
/*!40000 ALTER TABLE `lotesproduccion_calidad` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `materia_prima_proveedor`
--

DROP TABLE IF EXISTS `materia_prima_proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `materia_prima_proveedor` (
  `id_materia` int NOT NULL,
  `id_proveedor` int NOT NULL,
  `precio_referencia` decimal(10,2) NOT NULL,
  `unidad_medida` int NOT NULL,
  PRIMARY KEY (`id_materia`,`id_proveedor`),
  KEY `id_proveedor` (`id_proveedor`),
  CONSTRAINT `materia_prima_proveedor_ibfk_1` FOREIGN KEY (`id_materia`) REFERENCES `materiaprima` (`id_materia`),
  CONSTRAINT `materia_prima_proveedor_ibfk_2` FOREIGN KEY (`id_proveedor`) REFERENCES `proveedores` (`id_proveedor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `materia_prima_proveedor`
--

LOCK TABLES `materia_prima_proveedor` WRITE;
/*!40000 ALTER TABLE `materia_prima_proveedor` DISABLE KEYS */;
INSERT INTO `materia_prima_proveedor` VALUES (1,1,34.00,1),(2,2,24.00,1),(3,3,45.00,1),(4,4,35.00,2),(5,5,45.00,1),(6,1,4.00,1),(6,2,4.00,1),(6,4,4.00,2),(8,3,1500.00,2),(8,5,12.00,2),(9,3,60.00,1),(10,2,70.00,1),(11,1,60.00,1),(12,5,1000.00,1),(13,1,500.00,1),(14,5,800.00,1),(15,3,100.00,1),(16,2,200.00,1),(18,8,5.00,4),(19,7,8.00,4),(20,1,20.00,2),(21,1,15.00,1),(22,1,20.00,1),(23,1,21.00,2),(24,1,19.00,1),(25,1,25.00,2),(26,1,35.00,1),(28,1,22.00,2),(29,2,19.00,1),(30,1,20.00,1),(31,3,32.00,1),(32,5,20.00,1),(33,7,10.00,4);
/*!40000 ALTER TABLE `materia_prima_proveedor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `materiaprima`
--

DROP TABLE IF EXISTS `materiaprima`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `materiaprima` (
  `id_materia` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  `stock_min` decimal(10,2) DEFAULT NULL,
  `stock_max` decimal(10,2) DEFAULT NULL,
  `unidad_medida` int NOT NULL,
  `stock_real` decimal(10,2) DEFAULT NULL,
  `stock_disponible` decimal(10,2) DEFAULT NULL,
  `estatus` enum('Activo','Inactivo') DEFAULT NULL,
  PRIMARY KEY (`id_materia`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `materiaprima`
--

LOCK TABLES `materiaprima` WRITE;
/*!40000 ALTER TABLE `materiaprima` DISABLE KEYS */;
INSERT INTO `materiaprima` VALUES (1,'Ácido sulfónico',50.00,200.00,1,320.50,120.50,'Activo'),(2,'Sosa cáustica (hidróxido de sodio)',40.00,150.00,1,260.00,70.00,'Activo'),(3,'Lauril éter sulfato de sodio (LESS)',60.00,250.00,1,350.00,70.00,'Activo'),(4,'Alcohol etílico',30.00,120.00,2,232.00,108.00,'Activo'),(5,'Glicerina',20.00,80.00,1,160.00,75.00,'Activo'),(6,'Agua desmineralizada',100.00,500.00,2,600.00,100.00,'Activo'),(7,'Botellas 1 Galón',50.00,200.00,4,0.00,0.00,'Activo'),(8,'Hipoclorito de sodio líquido',100.00,500.00,2,472.50,302.75,'Activo'),(9,'Conservador (benzoato de sodio)',10.00,40.00,1,40.00,0.00,'Activo'),(10,'EDTA (estabilizante)',15.00,60.00,1,60.00,0.00,'Activo'),(11,'Nonilfenol (tensioactivo)',20.00,50.00,1,80.00,24.00,'Activo'),(12,'Harina de trigo',50.00,100.00,1,200.00,68.00,'Activo'),(13,'Alcohol isopropílico',50.00,200.00,2,300.00,100.00,'Activo'),(14,'Hidróxido de amonio',20.00,150.00,2,250.00,100.00,'Activo'),(15,'Formol',50.00,150.00,2,159.00,108.50,'Activo'),(16,'Colorante azul',20.00,50.00,1,80.00,20.00,'Activo'),(17,'Agua',300.00,1000.00,2,800.00,74.00,'Activo'),(18,'Etiquetas',250.00,600.00,4,0.00,0.00,'Activo'),(19,'Botellas 1 Litro',100.00,250.00,4,52.00,52.00,'Activo'),(20,'Aceite de pino',50.00,500.00,2,100.00,100.00,'Activo'),(21,'Detercon potásico',70.00,300.00,1,100.00,100.00,'Activo'),(22,'Colorante verde',80.00,300.00,1,0.00,0.00,'Activo'),(23,'Agua Destilada',50.00,150.00,2,0.00,0.00,'Activo'),(24,'Nipagín',50.00,200.00,1,0.00,0.00,'Activo'),(25,'Esencia (Lavanda)',100.00,400.00,2,0.00,0.00,'Activo'),(26,'Jabón de tocador \"neutro\"',100.00,900.00,1,0.00,0.00,'Activo'),(27,'Fragancia (Tipo detergente)',20.00,150.00,2,0.00,0.00,'Inactivo'),(28,'Agua Suavizada',100.00,250.00,2,0.00,0.00,'Activo'),(29,'Amida de Coco (Dietanolamida)',50.00,100.00,2,0.00,0.00,'Activo'),(30,'Fragancia (Tipo Detergente)',10.00,30.00,2,0.00,0.00,'Activo'),(31,'Activo Suavizante (Cuaternario de Amonio)',25.00,250.00,1,0.00,0.00,'Activo'),(32,'Fragancia (Tipo suavizante)',50.00,190.00,1,0.00,0.00,'Activo'),(33,'Botella 500ml',50.00,200.00,4,51.00,51.00,'Activo');
/*!40000 ALTER TABLE `materiaprima` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `modulos`
--

DROP TABLE IF EXISTS `modulos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `modulos` (
  `id_modulo` int NOT NULL AUTO_INCREMENT,
  `nombre_modulo` varchar(50) NOT NULL,
  PRIMARY KEY (`id_modulo`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `modulos`
--

LOCK TABLES `modulos` WRITE;
/*!40000 ALTER TABLE `modulos` DISABLE KEYS */;
INSERT INTO `modulos` VALUES (1,'users'),(2,'suppliers'),(3,'raw_materials'),(4,'purchases'),(5,'production'),(6,'analytics'),(7,'sales'),(8,'products'),(9,'recipes');
/*!40000 ALTER TABLE `modulos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `movimientosinventariomp`
--

DROP TABLE IF EXISTS `movimientosinventariomp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `movimientosinventariomp` (
  `id_movimiento_mp` int NOT NULL AUTO_INCREMENT,
  `id_materia` int NOT NULL,
  `tipo_movimiento` int NOT NULL,
  `motivo` int NOT NULL,
  `cantidad` decimal(10,2) NOT NULL,
  `stock_resultante` decimal(10,2) DEFAULT NULL,
  `cantidad_pendiente` decimal(10,2) DEFAULT NULL,
  `status_movimiento` int DEFAULT NULL,
  `fecha_caducidad` date DEFAULT NULL,
  `id_usuario` int NOT NULL,
  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`id_movimiento_mp`),
  KEY `id_materia` (`id_materia`),
  KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `movimientosinventariomp_ibfk_1` FOREIGN KEY (`id_materia`) REFERENCES `materiaprima` (`id_materia`),
  CONSTRAINT `movimientosinventariomp_ibfk_2` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimientosinventariomp`
--

LOCK TABLES `movimientosinventariomp` WRITE;
/*!40000 ALTER TABLE `movimientosinventariomp` DISABLE KEYS */;
INSERT INTO `movimientosinventariomp` VALUES (1,17,1,3,800.00,NULL,0.00,1,NULL,1,'2026-04-13 23:06:18'),(2,11,1,3,30.00,NULL,0.00,1,NULL,1,'2026-04-13 23:06:19'),(3,17,2,2,84.00,716.00,84.00,2,NULL,1,'2026-04-13 23:15:31'),(4,11,2,2,3.00,27.00,3.00,2,NULL,1,'2026-04-13 23:15:31'),(5,15,2,2,0.25,108.75,0.25,2,NULL,1,'2026-04-13 23:15:31'),(6,4,2,2,2.00,110.00,2.00,2,NULL,1,'2026-04-13 23:15:31'),(7,17,2,2,164.00,552.00,164.00,2,NULL,1,'2026-04-13 23:16:13'),(8,2,2,2,20.00,90.00,20.00,2,NULL,1,'2026-04-13 23:16:13'),(9,12,2,2,16.00,84.00,16.00,2,NULL,1,'2026-04-13 23:16:13'),(10,17,2,2,82.00,470.00,82.00,2,NULL,1,'2026-04-13 23:17:17'),(11,2,2,2,10.00,80.00,10.00,2,NULL,1,'2026-04-13 23:17:17'),(12,12,2,2,8.00,76.00,8.00,2,NULL,1,'2026-04-13 23:17:17'),(13,17,2,2,87.00,383.00,87.00,2,NULL,1,'2026-04-13 23:52:24'),(14,8,2,2,13.00,315.75,13.00,2,NULL,1,'2026-04-13 23:52:24'),(15,17,2,2,82.00,301.00,82.00,2,NULL,1,'2026-04-13 23:53:10'),(16,2,2,2,10.00,70.00,10.00,2,NULL,1,'2026-04-13 23:53:10'),(17,12,2,2,8.00,68.00,8.00,2,NULL,1,'2026-04-13 23:53:10'),(18,17,2,2,87.00,214.00,87.00,2,NULL,1,'2026-04-13 23:53:25'),(19,8,2,2,13.00,302.75,13.00,2,NULL,1,'2026-04-13 23:53:25'),(20,19,2,2,20.00,22.00,0.00,1,NULL,1,'2026-04-14 00:05:58'),(21,18,2,2,20.00,19.00,0.00,1,NULL,1,'2026-04-14 00:05:58'),(22,16,1,3,30.00,NULL,0.00,1,NULL,1,'2026-04-14 00:23:03'),(23,19,1,3,80.00,NULL,0.00,1,NULL,1,'2026-04-14 00:23:46'),(24,18,1,3,80.00,NULL,0.00,1,NULL,1,'2026-04-14 00:24:11'),(25,20,1,3,100.00,NULL,0.00,1,NULL,1,'2026-04-14 00:25:03'),(26,21,1,3,100.00,NULL,0.00,1,NULL,1,'2026-04-14 00:25:03'),(27,17,2,2,56.00,158.00,56.00,2,NULL,1,'2026-04-14 00:26:08'),(28,3,2,2,30.00,70.00,30.00,2,NULL,1,'2026-04-14 00:26:08'),(29,5,2,2,5.00,75.00,5.00,2,NULL,1,'2026-04-14 00:26:08'),(30,16,2,2,10.00,20.00,10.00,2,NULL,1,'2026-04-14 00:26:08'),(31,19,2,2,30.00,72.00,0.00,1,NULL,1,'2026-04-14 00:30:38'),(32,18,2,2,30.00,69.00,0.00,1,NULL,1,'2026-04-14 00:30:38'),(33,17,2,2,84.00,74.00,84.00,2,NULL,1,'2026-04-14 02:06:52'),(34,11,2,2,3.00,24.00,3.00,2,NULL,1,'2026-04-14 02:06:52'),(35,15,2,2,0.25,108.50,0.25,2,NULL,1,'2026-04-14 02:06:52'),(36,4,2,2,2.00,108.00,2.00,2,NULL,1,'2026-04-14 02:06:52'),(37,19,2,2,20.00,52.00,0.00,1,NULL,1,'2026-04-14 02:11:16'),(38,18,2,2,20.00,49.00,0.00,1,NULL,1,'2026-04-14 02:11:16'),(39,33,1,3,100.00,NULL,0.00,1,NULL,1,'2026-04-14 02:13:57'),(40,33,2,2,49.00,51.00,0.00,1,NULL,1,'2026-04-14 02:15:17'),(41,18,2,2,49.00,0.00,0.00,1,NULL,1,'2026-04-14 02:15:17');
/*!40000 ALTER TABLE `movimientosinventariomp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `movimientosinventariopt`
--

DROP TABLE IF EXISTS `movimientosinventariopt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `movimientosinventariopt` (
  `id_movimiento_pt` int NOT NULL AUTO_INCREMENT,
  `id_producto` int NOT NULL,
  `tipo_movimiento` int NOT NULL,
  `motivo` int NOT NULL,
  `cantidad` decimal(10,2) NOT NULL,
  `stock_resultante` decimal(10,2) NOT NULL,
  `id_usuario` int DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `status` int NOT NULL,
  PRIMARY KEY (`id_movimiento_pt`),
  KEY `id_producto` (`id_producto`),
  KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `movimientosinventariopt_ibfk_1` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`),
  CONSTRAINT `movimientosinventariopt_ibfk_2` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimientosinventariopt`
--

LOCK TABLES `movimientosinventariopt` WRITE;
/*!40000 ALTER TABLE `movimientosinventariopt` DISABLE KEYS */;
INSERT INTO `movimientosinventariopt` VALUES (1,6,1,4,113.74,113.74,1,'2026-04-13 23:26:33',1),(2,7,2,3,97.00,0.00,1,'2026-04-13 18:02:47',1),(3,7,1,4,20.00,20.00,1,'2026-04-14 00:05:58',1),(4,4,1,4,30.00,30.00,1,'2026-04-14 00:30:38',1),(5,2,1,3,50.00,50.00,1,'2026-04-13 18:34:29',1),(6,2,1,3,90.00,90.00,1,'2026-04-13 18:35:03',1),(7,3,1,3,60.00,60.00,1,'2026-04-13 18:35:16',1),(8,2,1,3,40.00,90.00,1,'2026-04-13 18:35:33',1),(9,4,1,3,40.00,40.00,1,'2026-04-13 18:35:55',1),(10,5,1,3,70.00,70.00,1,'2026-04-13 18:36:12',1),(11,7,1,3,45.00,45.00,1,'2026-04-13 18:38:06',1),(12,8,1,3,85.00,85.00,1,'2026-04-13 18:38:45',1),(13,9,1,3,54.00,54.00,1,'2026-04-13 18:39:20',1),(14,10,1,3,62.00,62.00,1,'2026-04-13 18:39:56',1),(15,2,1,3,42.00,42.00,1,'2026-04-13 19:42:55',1),(16,2,1,3,60.00,60.00,1,'2026-04-13 19:43:21',1),(17,3,1,4,20.00,112.00,1,'2026-04-14 02:11:16',1),(18,3,1,4,49.00,109.00,1,'2026-04-14 02:15:17',1);
/*!40000 ALTER TABLE `movimientosinventariopt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ordenesproduccion`
--

DROP TABLE IF EXISTS `ordenesproduccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ordenesproduccion` (
  `id_orden_produccion` int NOT NULL AUTO_INCREMENT,
  `folio_orden` varchar(20) NOT NULL,
  `id_receta_ref` int NOT NULL,
  `cantidad_solicitada` int NOT NULL,
  `unidad_medida` int NOT NULL,
  `id_operador` int NOT NULL,
  `merma_real` decimal(10,2) DEFAULT NULL,
  `fecha_programada` datetime DEFAULT NULL,
  `fecha_inicio` datetime DEFAULT NULL,
  `fecha_cierre` datetime DEFAULT NULL,
  `status` int DEFAULT NULL,
  PRIMARY KEY (`id_orden_produccion`),
  UNIQUE KEY `folio_orden` (`folio_orden`),
  KEY `id_operador` (`id_operador`),
  KEY `id_receta_ref` (`id_receta_ref`),
  CONSTRAINT `ordenesproduccion_ibfk_1` FOREIGN KEY (`id_operador`) REFERENCES `usuarios` (`id_usuario`),
  CONSTRAINT `ordenesproduccion_ibfk_2` FOREIGN KEY (`id_receta_ref`) REFERENCES `recetas` (`id_receta`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ordenesproduccion`
--

LOCK TABLES `ordenesproduccion` WRITE;
/*!40000 ALTER TABLE `ordenesproduccion` DISABLE KEYS */;
INSERT INTO `ordenesproduccion` VALUES (1,'OP-20260413171531',2,1,2,1,7.20,NULL,'2026-04-13 17:18:09','2026-04-13 17:34:38',4),(2,'OP-20260413171612',7,2,1,1,0.00,NULL,NULL,NULL,2),(3,'OP-20260413171716',7,1,1,1,6.26,NULL,'2026-04-13 17:18:06','2026-04-13 17:20:26',4),(4,'OP-20260413175223',8,1,1,1,3.33,NULL,'2026-04-13 17:53:42','2026-04-13 17:56:45',4),(5,'OP-20260413175310',7,1,1,1,0.00,NULL,NULL,NULL,2),(6,'OP-20260413175325',8,1,1,1,0.00,NULL,'2026-04-13 18:41:05',NULL,3),(7,'OP-20260413182607',3,1,1,1,8.78,NULL,'2026-04-13 18:26:23','2026-04-13 18:28:24',4),(8,'OP-20260413200652',2,1,2,1,7.20,NULL,'2026-04-13 20:07:03','2026-04-13 20:08:33',4);
/*!40000 ALTER TABLE `ordenesproduccion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ordenesproduccion_ciclos`
--

DROP TABLE IF EXISTS `ordenesproduccion_ciclos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ordenesproduccion_ciclos` (
  `id_ciclo` int NOT NULL AUTO_INCREMENT,
  `id_orden_produccion` int NOT NULL,
  `numero_ciclo` int NOT NULL,
  `cantidad_a_producir` decimal(10,2) NOT NULL,
  `id_operador_asignado` int DEFAULT NULL,
  `id_lote_referencia` int DEFAULT NULL,
  `fecha_inicio_programada` datetime DEFAULT NULL,
  `fecha_inicio_real` datetime DEFAULT NULL,
  `fecha_fin_real` datetime DEFAULT NULL,
  `status_ciclo` int DEFAULT NULL,
  PRIMARY KEY (`id_ciclo`),
  KEY `id_lote_referencia` (`id_lote_referencia`),
  KEY `id_operador_asignado` (`id_operador_asignado`),
  KEY `id_orden_produccion` (`id_orden_produccion`),
  CONSTRAINT `ordenesproduccion_ciclos_ibfk_1` FOREIGN KEY (`id_lote_referencia`) REFERENCES `lotesproduccion` (`id_lote`),
  CONSTRAINT `ordenesproduccion_ciclos_ibfk_2` FOREIGN KEY (`id_operador_asignado`) REFERENCES `usuarios` (`id_usuario`),
  CONSTRAINT `ordenesproduccion_ciclos_ibfk_3` FOREIGN KEY (`id_orden_produccion`) REFERENCES `ordenesproduccion` (`id_orden_produccion`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ordenesproduccion_ciclos`
--

LOCK TABLES `ordenesproduccion_ciclos` WRITE;
/*!40000 ALTER TABLE `ordenesproduccion_ciclos` DISABLE KEYS */;
INSERT INTO `ordenesproduccion_ciclos` VALUES (1,1,1,100.00,1,NULL,NULL,'2026-04-13 17:33:26','2026-04-13 17:34:05',4),(2,2,1,120.00,1,NULL,NULL,NULL,NULL,1),(3,2,2,120.00,1,NULL,NULL,NULL,NULL,1),(4,3,1,120.00,1,NULL,NULL,'2026-04-13 17:18:24','2026-04-13 17:20:01',4),(5,4,1,100.00,1,NULL,NULL,'2026-04-13 17:55:52','2026-04-13 17:56:26',4),(6,5,1,120.00,1,NULL,NULL,NULL,NULL,1),(7,6,1,100.00,1,NULL,NULL,'2026-04-13 18:41:11',NULL,3),(8,7,1,150.00,1,NULL,NULL,'2026-04-13 18:26:41','2026-04-13 18:27:33',4),(9,8,1,100.00,1,NULL,NULL,'2026-04-13 20:07:10','2026-04-13 20:08:13',4);
/*!40000 ALTER TABLE `ordenesproduccion_ciclos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ordenesproduccion_insumos`
--

DROP TABLE IF EXISTS `ordenesproduccion_insumos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ordenesproduccion_insumos` (
  `id_op_insumo` int NOT NULL AUTO_INCREMENT,
  `id_orden_produccion` int DEFAULT NULL,
  `id_materia_prima` int DEFAULT NULL,
  `nombre_materia` varchar(100) DEFAULT NULL,
  `lote_proveedor` varchar(50) DEFAULT NULL,
  `cantidad_utilizada` decimal(10,2) DEFAULT NULL,
  `costo_insumo_momento` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id_op_insumo`),
  KEY `id_materia_prima` (`id_materia_prima`),
  KEY `id_orden_produccion` (`id_orden_produccion`),
  CONSTRAINT `ordenesproduccion_insumos_ibfk_1` FOREIGN KEY (`id_materia_prima`) REFERENCES `materiaprima` (`id_materia`),
  CONSTRAINT `ordenesproduccion_insumos_ibfk_2` FOREIGN KEY (`id_orden_produccion`) REFERENCES `ordenesproduccion` (`id_orden_produccion`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ordenesproduccion_insumos`
--

LOCK TABLES `ordenesproduccion_insumos` WRITE;
/*!40000 ALTER TABLE `ordenesproduccion_insumos` DISABLE KEYS */;
/*!40000 ALTER TABLE `ordenesproduccion_insumos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ordenesproduccion_insumos_ciclo`
--

DROP TABLE IF EXISTS `ordenesproduccion_insumos_ciclo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ordenesproduccion_insumos_ciclo` (
  `id_insumo_ciclo` int NOT NULL AUTO_INCREMENT,
  `id_ciclo` int NOT NULL,
  `id_materia_prima` int NOT NULL,
  `cantidad_estimada` decimal(10,2) NOT NULL,
  `cantidad_real_utilizada` decimal(10,2) DEFAULT NULL,
  `lote_proveedor_usado` varchar(50) DEFAULT NULL,
  `costo_unitario_momento` decimal(10,2) DEFAULT NULL,
  `id_movimiento_inv_ref` int DEFAULT NULL,
  PRIMARY KEY (`id_insumo_ciclo`),
  KEY `id_ciclo` (`id_ciclo`),
  KEY `id_materia_prima` (`id_materia_prima`),
  KEY `id_movimiento_inv_ref` (`id_movimiento_inv_ref`),
  CONSTRAINT `ordenesproduccion_insumos_ciclo_ibfk_1` FOREIGN KEY (`id_ciclo`) REFERENCES `ordenesproduccion_ciclos` (`id_ciclo`) ON DELETE CASCADE,
  CONSTRAINT `ordenesproduccion_insumos_ciclo_ibfk_2` FOREIGN KEY (`id_materia_prima`) REFERENCES `materiaprima` (`id_materia`),
  CONSTRAINT `ordenesproduccion_insumos_ciclo_ibfk_3` FOREIGN KEY (`id_movimiento_inv_ref`) REFERENCES `movimientosinventariomp` (`id_movimiento_mp`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ordenesproduccion_insumos_ciclo`
--

LOCK TABLES `ordenesproduccion_insumos_ciclo` WRITE;
/*!40000 ALTER TABLE `ordenesproduccion_insumos_ciclo` DISABLE KEYS */;
INSERT INTO `ordenesproduccion_insumos_ciclo` VALUES (1,1,17,84.00,0.00,NULL,0.00,NULL),(2,1,11,3.00,0.00,NULL,60.00,NULL),(3,1,15,0.25,0.00,NULL,100.00,NULL),(4,1,4,2.00,0.00,NULL,35.00,NULL),(5,2,17,82.00,0.00,NULL,0.00,NULL),(6,2,2,10.00,0.00,NULL,24.00,NULL),(7,2,12,8.00,0.00,NULL,1000.00,NULL),(8,3,17,82.00,0.00,NULL,0.00,NULL),(9,3,2,10.00,0.00,NULL,24.00,NULL),(10,3,12,8.00,0.00,NULL,1000.00,NULL),(11,4,17,82.00,0.00,NULL,0.00,NULL),(12,4,2,10.00,0.00,NULL,24.00,NULL),(13,4,12,8.00,0.00,NULL,1000.00,NULL),(14,5,17,87.00,0.00,NULL,0.00,NULL),(15,5,8,13.00,0.00,NULL,12.00,NULL),(16,6,17,82.00,0.00,NULL,0.00,NULL),(17,6,2,10.00,0.00,NULL,24.00,NULL),(18,6,12,8.00,0.00,NULL,1000.00,NULL),(19,7,17,87.00,0.00,NULL,0.00,NULL),(20,7,8,13.00,0.00,NULL,12.00,NULL),(21,8,17,56.00,0.00,NULL,0.00,NULL),(22,8,3,30.00,0.00,NULL,45.00,NULL),(23,8,5,5.00,0.00,NULL,45.00,NULL),(24,8,16,10.00,0.00,NULL,200.00,NULL),(25,9,17,84.00,0.00,NULL,0.00,NULL),(26,9,11,3.00,0.00,NULL,60.00,NULL),(27,9,15,0.25,0.00,NULL,100.00,NULL),(28,9,4,2.00,0.00,NULL,35.00,NULL);
/*!40000 ALTER TABLE `ordenesproduccion_insumos_ciclo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ordenesproduccion_seguimiento_pasos`
--

DROP TABLE IF EXISTS `ordenesproduccion_seguimiento_pasos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ordenesproduccion_seguimiento_pasos` (
  `id_seguimiento` int NOT NULL AUTO_INCREMENT,
  `id_ciclo` int NOT NULL,
  `id_paso_receta_ref` int NOT NULL,
  `orden_ejecucion` int NOT NULL,
  `nombre_paso_momento` varchar(100) NOT NULL,
  `descripcion_paso` text,
  `status_paso` int DEFAULT NULL,
  `fecha_inicio_paso` datetime DEFAULT NULL,
  `fecha_fin_paso` datetime DEFAULT NULL,
  `id_operador_ejecuta` int DEFAULT NULL,
  `observaciones_operador` text,
  `requiere_verificacion` tinyint(1) DEFAULT NULL,
  `id_supervisor_verifica` int DEFAULT NULL,
  PRIMARY KEY (`id_seguimiento`),
  KEY `id_ciclo` (`id_ciclo`),
  KEY `id_operador_ejecuta` (`id_operador_ejecuta`),
  KEY `id_paso_receta_ref` (`id_paso_receta_ref`),
  KEY `id_supervisor_verifica` (`id_supervisor_verifica`),
  CONSTRAINT `ordenesproduccion_seguimiento_pasos_ibfk_1` FOREIGN KEY (`id_ciclo`) REFERENCES `ordenesproduccion_ciclos` (`id_ciclo`) ON DELETE CASCADE,
  CONSTRAINT `ordenesproduccion_seguimiento_pasos_ibfk_2` FOREIGN KEY (`id_operador_ejecuta`) REFERENCES `usuarios` (`id_usuario`),
  CONSTRAINT `ordenesproduccion_seguimiento_pasos_ibfk_3` FOREIGN KEY (`id_paso_receta_ref`) REFERENCES `pasosreceta` (`id_paso`),
  CONSTRAINT `ordenesproduccion_seguimiento_pasos_ibfk_4` FOREIGN KEY (`id_supervisor_verifica`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ordenesproduccion_seguimiento_pasos`
--

LOCK TABLES `ordenesproduccion_seguimiento_pasos` WRITE;
/*!40000 ALTER TABLE `ordenesproduccion_seguimiento_pasos` DISABLE KEYS */;
INSERT INTO `ordenesproduccion_seguimiento_pasos` VALUES (1,1,6,1,'Acondicionamiento de Agua y Quelante','Se debe colocar el total de los 84.65 kg de agua en el contenedor principal de acero inoxidable. Se añade el 0.10 kg de EDTA de forma directa y se inicia una agitación constante hasta lograr que los cristales se disuelvan totalmente y el agua luzca cristalina. Este paso es fundamental para neutralizar los minerales del agua que podrían afectar la transparencia y el desempeño del detergente final.',3,'2026-04-13 17:33:35','2026-04-13 17:33:39',1,'',0,NULL),(2,1,7,2,'Activación de Tensoactivos por Calor','Se incorporan los 6 kg de Alkilbencensulfanato de sodio a la solución acuosa y se procede a calentar la mezcla hasta alcanzar una temperatura de 65°C. Se debe mantener la agitación durante todo el calentamiento hasta observar la disolución total del componente. Es indispensable no sobrepasar esta temperatura y verificar que no queden sedimentos en el fondo del tanque antes de proceder al siguiente paso mientras la mezcla aún permanece en la fuente de calor.',3,'2026-04-13 17:33:41','2026-04-13 17:33:44',1,'',0,NULL),(3,1,8,3,'Integración de Alcohol Láurico','Todavía bajo el fuego y manteniendo la temperatura, se agregan los 3 kg de Alcohol láurico etoxilado a la mezcla. Se agita vigorosamente hasta notar que el líquido es completamente homogéneo y transparente. Una vez lograda la integración total de este tercer componente, se debe retirar la mezcla de la fuente de calor para comenzar el proceso de enfriamiento controlado antes de añadir los elementos volátiles.',3,'2026-04-13 17:33:49','2026-04-13 17:33:52',1,'',0,NULL),(4,1,9,4,'Adición de Solventes y Conservadores','Con la mezcla fuera del fuego pero aún tibia, se deben incorporar bajo agitación vigorosa los 3 kg de Nonil fenol, los 2 kg de Alcohol isopropílico y los 0.25 kg de Formol. Se debe mantener un mezclado constante durante al menos 5 minutos para asegurar que los solventes y el conservador se distribuyan uniformemente en toda la solución. Se recomienda dejar reposar la mezcla brevemente después de este paso para que la temperatura continúe descendiendo de forma natural.',3,'2026-04-13 17:33:55','2026-04-13 17:33:58',1,'',0,NULL),(5,1,10,5,'Acabado Estético y Aromatización','Una vez que la disolución se encuentre completamente fría al tacto, se procede a incorporar el 1 kg de fragancia y el colorante necesario para el tono deseado. Es crucial no realizar este paso mientras el líquido esté caliente, ya que el calor degradaría la fragancia y alteraría el color final. Se agita por última vez hasta que el aroma y el color sean uniformes en todo el lote, quedando el producto listo para pasar directamente al área de envasado.',3,'2026-04-13 17:34:01','2026-04-13 17:34:05',1,'',0,NULL),(6,2,28,1,'Preparación de la Fase de Suspensión (Atole)','Se debe verter la mitad del agua total (41 kg) en el contenedor principal de mezcla a temperatura ambiente. Se incorporan los 8 kg de harina de forma gradual mientras se realiza una agitación mecánica vigorosa para evitar la formación de grumos o asentamientos en el fondo. Se debe continuar el mezclado hasta obtener una consistencia líquida blanquecina totalmente lisa y homogénea, asegurándose de que no existan partículas sólidas secas antes de proceder a la fase química.',1,NULL,NULL,NULL,NULL,0,NULL),(7,2,29,2,'Reacción de Saponificación y Gelificación','Bajo agitación constante y con el equipo de protección personal completo se deben medir e incorporar los 10 kg de Hidróxido de sodio al 50 % directamente sobre la mezcla de harina y agua. Durante este paso la mezcla comenzará a espesar rápidamente y a liberar calor debido a la reacción química entre la sosa y los componentes de la harina. Se debe mantener la agitación vigorosa para asegurar que la sosa se distribuya uniformemente y el gel se forme de manera consistente en todo el volumen del recipiente.',1,NULL,NULL,NULL,NULL,0,NULL),(8,2,30,3,'Ajuste de Viscosidad y Acabado','Una vez formado el gel base se debe añadir el resto del agua (41 kg) de forma lenta y pausada manteniendo la agitación enérgica para integrar el líquido a la estructura espesa ya formada. Se debe continuar el proceso de mezclado hasta que el gel sea visualmente uniforme, brillante y no presente separaciones de fase o partes líquidas aisladas. Es fundamental verificar que la textura final tenga el cuerpo suficiente para adherirse a superficies verticales, cumpliendo así con su función de quitacochambre antes de trasladar al área de llenado.',1,NULL,NULL,NULL,NULL,0,NULL),(9,2,31,4,'Estabilización y Envasado','Al finalizar la integración total se debe permitir que el gel repose para que la temperatura generada por la reacción química descienda y las burbujas de aire atrapadas se eliminen. No se debe tapar herméticamente el contenedor mientras el producto permanezca caliente para evitar la acumulación de vapores. Una vez estabilizado el producto se procede al envasado en recipientes de polietileno de alta densidad debidamente etiquetados con las advertencias de seguridad correspondientes por su alta peligrosidad.',1,NULL,NULL,NULL,NULL,0,NULL),(10,3,28,1,'Preparación de la Fase de Suspensión (Atole)','Se debe verter la mitad del agua total (41 kg) en el contenedor principal de mezcla a temperatura ambiente. Se incorporan los 8 kg de harina de forma gradual mientras se realiza una agitación mecánica vigorosa para evitar la formación de grumos o asentamientos en el fondo. Se debe continuar el mezclado hasta obtener una consistencia líquida blanquecina totalmente lisa y homogénea, asegurándose de que no existan partículas sólidas secas antes de proceder a la fase química.',1,NULL,NULL,NULL,NULL,0,NULL),(11,3,29,2,'Reacción de Saponificación y Gelificación','Bajo agitación constante y con el equipo de protección personal completo se deben medir e incorporar los 10 kg de Hidróxido de sodio al 50 % directamente sobre la mezcla de harina y agua. Durante este paso la mezcla comenzará a espesar rápidamente y a liberar calor debido a la reacción química entre la sosa y los componentes de la harina. Se debe mantener la agitación vigorosa para asegurar que la sosa se distribuya uniformemente y el gel se forme de manera consistente en todo el volumen del recipiente.',1,NULL,NULL,NULL,NULL,0,NULL),(12,3,30,3,'Ajuste de Viscosidad y Acabado','Una vez formado el gel base se debe añadir el resto del agua (41 kg) de forma lenta y pausada manteniendo la agitación enérgica para integrar el líquido a la estructura espesa ya formada. Se debe continuar el proceso de mezclado hasta que el gel sea visualmente uniforme, brillante y no presente separaciones de fase o partes líquidas aisladas. Es fundamental verificar que la textura final tenga el cuerpo suficiente para adherirse a superficies verticales, cumpliendo así con su función de quitacochambre antes de trasladar al área de llenado.',1,NULL,NULL,NULL,NULL,0,NULL),(13,3,31,4,'Estabilización y Envasado','Al finalizar la integración total se debe permitir que el gel repose para que la temperatura generada por la reacción química descienda y las burbujas de aire atrapadas se eliminen. No se debe tapar herméticamente el contenedor mientras el producto permanezca caliente para evitar la acumulación de vapores. Una vez estabilizado el producto se procede al envasado en recipientes de polietileno de alta densidad debidamente etiquetados con las advertencias de seguridad correspondientes por su alta peligrosidad.',1,NULL,NULL,NULL,NULL,0,NULL),(14,4,28,1,'Preparación de la Fase de Suspensión (Atole)','Se debe verter la mitad del agua total (41 kg) en el contenedor principal de mezcla a temperatura ambiente. Se incorporan los 8 kg de harina de forma gradual mientras se realiza una agitación mecánica vigorosa para evitar la formación de grumos o asentamientos en el fondo. Se debe continuar el mezclado hasta obtener una consistencia líquida blanquecina totalmente lisa y homogénea, asegurándose de que no existan partículas sólidas secas antes de proceder a la fase química.',3,'2026-04-13 17:19:30','2026-04-13 17:19:37',1,'',0,NULL),(15,4,29,2,'Reacción de Saponificación y Gelificación','Bajo agitación constante y con el equipo de protección personal completo se deben medir e incorporar los 10 kg de Hidróxido de sodio al 50 % directamente sobre la mezcla de harina y agua. Durante este paso la mezcla comenzará a espesar rápidamente y a liberar calor debido a la reacción química entre la sosa y los componentes de la harina. Se debe mantener la agitación vigorosa para asegurar que la sosa se distribuya uniformemente y el gel se forme de manera consistente en todo el volumen del recipiente.',3,'2026-04-13 17:19:39','2026-04-13 17:19:48',1,'',0,NULL),(16,4,30,3,'Ajuste de Viscosidad y Acabado','Una vez formado el gel base se debe añadir el resto del agua (41 kg) de forma lenta y pausada manteniendo la agitación enérgica para integrar el líquido a la estructura espesa ya formada. Se debe continuar el proceso de mezclado hasta que el gel sea visualmente uniforme, brillante y no presente separaciones de fase o partes líquidas aisladas. Es fundamental verificar que la textura final tenga el cuerpo suficiente para adherirse a superficies verticales, cumpliendo así con su función de quitacochambre antes de trasladar al área de llenado.',3,'2026-04-13 17:19:50','2026-04-13 17:19:55',1,'',0,NULL),(17,4,31,4,'Estabilización y Envasado','Al finalizar la integración total se debe permitir que el gel repose para que la temperatura generada por la reacción química descienda y las burbujas de aire atrapadas se eliminen. No se debe tapar herméticamente el contenedor mientras el producto permanezca caliente para evitar la acumulación de vapores. Una vez estabilizado el producto se procede al envasado en recipientes de polietileno de alta densidad debidamente etiquetados con las advertencias de seguridad correspondientes por su alta peligrosidad.',3,'2026-04-13 17:19:57','2026-04-13 17:20:01',1,'',0,NULL),(18,5,32,1,'Preparación del Vehículo Acuoso','DESCRIPCIÓN:\r\nSe deben verter los 87 kilos de agua en el contenedor principal de plástico asegurándose de que el recipiente esté libre de cualquier residuo orgánico o metálico. Se recomienda el uso de agua suavizada o destilada para evitar que los minerales presentes en el agua corriente reaccionen con el cloro y formen sedimentos en el fondo del envase. Se inicia una agitación lenta para preparar el medio de recepción del concentrado químico sin generar salpicaduras innecesarias.',3,'2026-04-13 17:56:07','2026-04-13 17:56:13',1,'',0,NULL),(19,5,33,2,'Dilución del Activo Desinfectante','Se añaden los 13 kilos de Hipoclorito de sodio al 13% de forma muy pausada directamente sobre el agua mientras se mantiene la agitación constante. Este paso debe realizarse con extremo cuidado para evitar vapores fuertes y asegurar que el concentrado se distribuya de manera uniforme en todo el lote. La mezcla resultante tendrá una concentración aproximada del 1.5% al 2% de cloro activo, que es el estándar comercial para limpieza doméstica y desinfección de superficies.',3,'2026-04-13 17:56:16','2026-04-13 17:56:19',1,'',0,NULL),(20,5,34,3,'Estabilización y Reposo','Al terminar la mezcla se debe detener el agitador y permitir que el producto repose para que la solución se estabilice químicamente antes de pasar al envasado. El contenedor debe permanecer tapado para evitar que el cloro pierda su fuerza al contacto prolongado con el aire y la luz ambiental. Una vez transcurrido el tiempo de reposo se procede a llenar los envases finales, los cuales deben ser opacos para garantizar que la vida útil del producto sea prolongada y mantenga su poder desinfectante.',3,'2026-04-13 17:56:21','2026-04-13 17:56:26',1,'',0,NULL),(21,6,28,1,'Preparación de la Fase de Suspensión (Atole)','Se debe verter la mitad del agua total (41 kg) en el contenedor principal de mezcla a temperatura ambiente. Se incorporan los 8 kg de harina de forma gradual mientras se realiza una agitación mecánica vigorosa para evitar la formación de grumos o asentamientos en el fondo. Se debe continuar el mezclado hasta obtener una consistencia líquida blanquecina totalmente lisa y homogénea, asegurándose de que no existan partículas sólidas secas antes de proceder a la fase química.',1,NULL,NULL,NULL,NULL,0,NULL),(22,6,29,2,'Reacción de Saponificación y Gelificación','Bajo agitación constante y con el equipo de protección personal completo se deben medir e incorporar los 10 kg de Hidróxido de sodio al 50 % directamente sobre la mezcla de harina y agua. Durante este paso la mezcla comenzará a espesar rápidamente y a liberar calor debido a la reacción química entre la sosa y los componentes de la harina. Se debe mantener la agitación vigorosa para asegurar que la sosa se distribuya uniformemente y el gel se forme de manera consistente en todo el volumen del recipiente.',1,NULL,NULL,NULL,NULL,0,NULL),(23,6,30,3,'Ajuste de Viscosidad y Acabado','Una vez formado el gel base se debe añadir el resto del agua (41 kg) de forma lenta y pausada manteniendo la agitación enérgica para integrar el líquido a la estructura espesa ya formada. Se debe continuar el proceso de mezclado hasta que el gel sea visualmente uniforme, brillante y no presente separaciones de fase o partes líquidas aisladas. Es fundamental verificar que la textura final tenga el cuerpo suficiente para adherirse a superficies verticales, cumpliendo así con su función de quitacochambre antes de trasladar al área de llenado.',1,NULL,NULL,NULL,NULL,0,NULL),(24,6,31,4,'Estabilización y Envasado','Al finalizar la integración total se debe permitir que el gel repose para que la temperatura generada por la reacción química descienda y las burbujas de aire atrapadas se eliminen. No se debe tapar herméticamente el contenedor mientras el producto permanezca caliente para evitar la acumulación de vapores. Una vez estabilizado el producto se procede al envasado en recipientes de polietileno de alta densidad debidamente etiquetados con las advertencias de seguridad correspondientes por su alta peligrosidad.',1,NULL,NULL,NULL,NULL,0,NULL),(25,7,32,1,'Preparación del Vehículo Acuoso','DESCRIPCIÓN:\r\nSe deben verter los 87 kilos de agua en el contenedor principal de plástico asegurándose de que el recipiente esté libre de cualquier residuo orgánico o metálico. Se recomienda el uso de agua suavizada o destilada para evitar que los minerales presentes en el agua corriente reaccionen con el cloro y formen sedimentos en el fondo del envase. Se inicia una agitación lenta para preparar el medio de recepción del concentrado químico sin generar salpicaduras innecesarias.',3,'2026-04-13 18:41:21','2026-04-13 18:41:26',1,'',0,NULL),(26,7,33,2,'Dilución del Activo Desinfectante','Se añaden los 13 kilos de Hipoclorito de sodio al 13% de forma muy pausada directamente sobre el agua mientras se mantiene la agitación constante. Este paso debe realizarse con extremo cuidado para evitar vapores fuertes y asegurar que el concentrado se distribuya de manera uniforme en todo el lote. La mezcla resultante tendrá una concentración aproximada del 1.5% al 2% de cloro activo, que es el estándar comercial para limpieza doméstica y desinfección de superficies.',3,'2026-04-13 18:41:28','2026-04-13 18:41:33',1,'',0,NULL),(27,7,34,3,'Estabilización y Reposo','Al terminar la mezcla se debe detener el agitador y permitir que el producto repose para que la solución se estabilice químicamente antes de pasar al envasado. El contenedor debe permanecer tapado para evitar que el cloro pierda su fuerza al contacto prolongado con el aire y la luz ambiental. Una vez transcurrido el tiempo de reposo se procede a llenar los envases finales, los cuales deben ser opacos para garantizar que la vida útil del producto sea prolongada y mantenga su poder desinfectante.',1,NULL,NULL,NULL,NULL,0,NULL),(28,8,11,1,'Hidratación del Tensoactivo Base','Se debe cargar el total de los 56.70 kg de agua en el contenedor principal y comenzar una agitación lenta pero constante. Se incorpora paulatinamente el Lauril Éter Sulfato de Sodio asegurando que se disuelva por completo antes de continuar, ya que este componente es la base de la limpieza y la espuma del producto. Es importante verificar que no queden grumos de gel en las paredes del recipiente para garantizar que la concentración sea uniforme en todo el lote.',3,'2026-04-13 18:26:59','2026-04-13 18:27:06',1,'qwertyu',0,NULL),(29,8,12,2,'Integración de Humectantes y Conservadores','Una vez integrada la base de jabón se deben añadir uno a uno la Dietanolamida, la Glicerina y el Nipagin bajo agitación moderada. La Dietanolamida ayudará a estabilizar la espuma mientras que la glicerina proporcionará la suavidad necesaria para el cuidado de la piel. Se debe mezclar hasta que el líquido sea totalmente homogéneo y transparente, asegurándose de que el conservador (nipagin) se haya distribuido por todo el volumen para evitar la contaminación microbiana futura.',3,'2026-04-13 18:27:14','2026-04-13 18:27:19',1,'',0,NULL),(30,8,13,3,'Ajuste de pH y Coloración','En este paso se debe medir el pH de la mezcla y ajustarlo a un valor de 7 utilizando Ácido Cítrico para bajarlo o Dietanolamida para subirlo según sea necesario. Una vez neutralizado se incorpora la fragancia y el colorante previamente disuelto en un poco de agua hasta obtener la tonalidad deseada por el cliente. No se debe proceder al espesado sin antes haber estabilizado el pH, ya que un cambio drástico en la acidez después de añadir sal puede alterar la transparencia del jabón.',3,'2026-04-13 18:27:21','2026-04-13 18:27:27',1,'',0,NULL),(31,8,14,4,'Espesado Final (Efecto Gel)','Para lograr la consistencia de gel se debe agregar lentamente una solución saturada de cloruro de sodio (sal con agua) mientras se mantiene la agitación. Se debe observar el incremento de viscosidad con mucho cuidado y detener la adición en cuanto se logre el espesor requerido, ya que un exceso de sal puede causar el efecto contrario y licuar el producto nuevamente. Al terminar se apaga el agitador y se deja reposar el lote el tiempo necesario para que cualquier burbuja de aire desaparezca antes de iniciar el envasado.',3,'2026-04-13 18:27:29','2026-04-13 18:27:33',1,'',0,NULL),(32,9,6,1,'Acondicionamiento de Agua y Quelante','Se debe colocar el total de los 84.65 kg de agua en el contenedor principal de acero inoxidable. Se añade el 0.10 kg de EDTA de forma directa y se inicia una agitación constante hasta lograr que los cristales se disuelvan totalmente y el agua luzca cristalina. Este paso es fundamental para neutralizar los minerales del agua que podrían afectar la transparencia y el desempeño del detergente final.',3,'2026-04-13 20:07:24','2026-04-13 20:07:39',1,'Todo correcto',0,NULL),(33,9,7,2,'Activación de Tensoactivos por Calor','Se incorporan los 6 kg de Alkilbencensulfanato de sodio a la solución acuosa y se procede a calentar la mezcla hasta alcanzar una temperatura de 65°C. Se debe mantener la agitación durante todo el calentamiento hasta observar la disolución total del componente. Es indispensable no sobrepasar esta temperatura y verificar que no queden sedimentos en el fondo del tanque antes de proceder al siguiente paso mientras la mezcla aún permanece en la fuente de calor.',3,'2026-04-13 20:07:47','2026-04-13 20:07:50',1,'',0,NULL),(34,9,8,3,'Integración de Alcohol Láurico','Todavía bajo el fuego y manteniendo la temperatura, se agregan los 3 kg de Alcohol láurico etoxilado a la mezcla. Se agita vigorosamente hasta notar que el líquido es completamente homogéneo y transparente. Una vez lograda la integración total de este tercer componente, se debe retirar la mezcla de la fuente de calor para comenzar el proceso de enfriamiento controlado antes de añadir los elementos volátiles.',3,'2026-04-13 20:07:52','2026-04-13 20:07:55',1,'',0,NULL),(35,9,9,4,'Adición de Solventes y Conservadores','Con la mezcla fuera del fuego pero aún tibia, se deben incorporar bajo agitación vigorosa los 3 kg de Nonil fenol, los 2 kg de Alcohol isopropílico y los 0.25 kg de Formol. Se debe mantener un mezclado constante durante al menos 5 minutos para asegurar que los solventes y el conservador se distribuyan uniformemente en toda la solución. Se recomienda dejar reposar la mezcla brevemente después de este paso para que la temperatura continúe descendiendo de forma natural.',3,'2026-04-13 20:07:58','2026-04-13 20:08:02',1,'',0,NULL),(36,9,10,5,'Acabado Estético y Aromatización','Una vez que la disolución se encuentre completamente fría al tacto, se procede a incorporar el 1 kg de fragancia y el colorante necesario para el tono deseado. Es crucial no realizar este paso mientras el líquido esté caliente, ya que el calor degradaría la fragancia y alteraría el color final. Se agita por última vez hasta que el aroma y el color sean uniformes en todo el lote, quedando el producto listo para pasar directamente al área de envasado.',3,'2026-04-13 20:08:04','2026-04-13 20:08:13',1,'',0,NULL);
/*!40000 ALTER TABLE `ordenesproduccion_seguimiento_pasos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `packaging_materials`
--

DROP TABLE IF EXISTS `packaging_materials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `packaging_materials` (
  `id_packaging` int NOT NULL AUTO_INCREMENT,
  `id_presentacion` int NOT NULL,
  `id_material` int NOT NULL,
  `cantidad_por_unidad` decimal(10,4) NOT NULL,
  PRIMARY KEY (`id_packaging`),
  KEY `id_material` (`id_material`),
  KEY `id_presentacion` (`id_presentacion`),
  CONSTRAINT `packaging_materials_ibfk_1` FOREIGN KEY (`id_material`) REFERENCES `materiaprima` (`id_materia`),
  CONSTRAINT `packaging_materials_ibfk_2` FOREIGN KEY (`id_presentacion`) REFERENCES `producto_presentación_precio` (`id_presentacion_precio`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `packaging_materials`
--

LOCK TABLES `packaging_materials` WRITE;
/*!40000 ALTER TABLE `packaging_materials` DISABLE KEYS */;
INSERT INTO `packaging_materials` VALUES (1,6,19,1.0000),(2,6,18,1.0000),(3,3,19,1.0000),(4,3,18,1.0000),(5,2,19,1.0000),(6,2,18,1.0000),(7,19,33,1.0000),(8,19,18,1.0000);
/*!40000 ALTER TABLE `packaging_materials` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `packaging_mp_consumed`
--

DROP TABLE IF EXISTS `packaging_mp_consumed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `packaging_mp_consumed` (
  `id_mp_consumed` int NOT NULL AUTO_INCREMENT,
  `packaging_record_id` int NOT NULL,
  `material_id` int NOT NULL,
  `nombre_material` varchar(100) DEFAULT NULL,
  `cantidad_consumida` decimal(10,4) NOT NULL,
  `stock_antes` decimal(10,2) DEFAULT NULL,
  `stock_despues` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id_mp_consumed`),
  KEY `material_id` (`material_id`),
  KEY `packaging_record_id` (`packaging_record_id`),
  CONSTRAINT `packaging_mp_consumed_ibfk_1` FOREIGN KEY (`material_id`) REFERENCES `materiaprima` (`id_materia`),
  CONSTRAINT `packaging_mp_consumed_ibfk_2` FOREIGN KEY (`packaging_record_id`) REFERENCES `packaging_records` (`id_packaging_record`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `packaging_mp_consumed`
--

LOCK TABLES `packaging_mp_consumed` WRITE;
/*!40000 ALTER TABLE `packaging_mp_consumed` DISABLE KEYS */;
INSERT INTO `packaging_mp_consumed` VALUES (1,1,19,'Botellas 1 Litro',20.0000,42.00,22.00),(2,1,18,'Etiquetas',20.0000,39.00,19.00),(3,2,19,'Botellas 1 Litro',30.0000,102.00,72.00),(4,2,18,'Etiquetas',30.0000,99.00,69.00),(5,3,19,'Botellas 1 Litro',20.0000,72.00,52.00),(6,3,18,'Etiquetas',20.0000,69.00,49.00),(7,4,33,'Botella 500ml',49.0000,100.00,51.00),(8,4,18,'Etiquetas',49.0000,49.00,0.00);
/*!40000 ALTER TABLE `packaging_mp_consumed` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `packaging_records`
--

DROP TABLE IF EXISTS `packaging_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `packaging_records` (
  `id_packaging_record` int NOT NULL AUTO_INCREMENT,
  `lot_id` int NOT NULL,
  `id_presentacion` int NOT NULL,
  `unidades_embasadas` int NOT NULL,
  `contenido_utilizado` decimal(10,2) NOT NULL,
  `operator_id` int NOT NULL,
  `timestamp` datetime DEFAULT NULL,
  `status` int DEFAULT NULL,
  PRIMARY KEY (`id_packaging_record`),
  KEY `id_presentacion` (`id_presentacion`),
  KEY `lot_id` (`lot_id`),
  KEY `operator_id` (`operator_id`),
  CONSTRAINT `packaging_records_ibfk_1` FOREIGN KEY (`id_presentacion`) REFERENCES `producto_presentación_precio` (`id_presentacion_precio`),
  CONSTRAINT `packaging_records_ibfk_2` FOREIGN KEY (`lot_id`) REFERENCES `lotesproduccion` (`id_lote`),
  CONSTRAINT `packaging_records_ibfk_3` FOREIGN KEY (`operator_id`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `packaging_records`
--

LOCK TABLES `packaging_records` WRITE;
/*!40000 ALTER TABLE `packaging_records` DISABLE KEYS */;
INSERT INTO `packaging_records` VALUES (1,3,6,20,20.00,1,'2026-04-14 00:05:58',1),(2,4,3,30,30.00,1,'2026-04-14 00:30:38',1),(3,5,2,20,20.00,1,'2026-04-14 02:11:16',1),(4,5,19,49,24.50,1,'2026-04-14 02:15:17',1);
/*!40000 ALTER TABLE `packaging_records` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pasosreceta`
--

DROP TABLE IF EXISTS `pasosreceta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pasosreceta` (
  `id_paso` int NOT NULL AUTO_INCREMENT,
  `id_receta` int NOT NULL,
  `orden_paso` int NOT NULL,
  `nombre_etapa` varchar(100) NOT NULL,
  `descripcion_especifica` text,
  `tiempo_estimado_paso` int NOT NULL,
  `tipo_proceso` int NOT NULL,
  PRIMARY KEY (`id_paso`),
  KEY `id_receta` (`id_receta`),
  CONSTRAINT `pasosreceta_ibfk_1` FOREIGN KEY (`id_receta`) REFERENCES `recetas` (`id_receta`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pasosreceta`
--

LOCK TABLES `pasosreceta` WRITE;
/*!40000 ALTER TABLE `pasosreceta` DISABLE KEYS */;
INSERT INTO `pasosreceta` VALUES (1,1,1,'Preparación de Base Oleosa','Para iniciar se debe utilizar un recipiente de acero inoxidable o plástico de 20 litros que esté completamente seco y libre de residuos de agua. Se vierten 0.50 kg de Nonil fenol junto con los 5 kg de Aceite de pino y se comienza una agitación constante hasta que el líquido sea totalmente transparente y no se perciban líneas de aceite. Es fundamental no utilizar utensilios de madera en este paso para evitar la contaminación del lote y asegurar que la base esté lista para recibir los siguientes componentes.',10,1),(2,1,2,'Incorporación de Detercon','En este punto se deben añadir los 10 kg de Detercon potásico a la mezcla previa de aceite y nonil fenol directamente en el contenedor principal de 120 litros. Se debe mantener una agitación firme mientras se vierte el componente para evitar la formación de grumos y asegurar que la mezcla adquiera una consistencia similar a un jarabe espeso y uniforme. No se debe detener el mezclado en ningún momento de la adición ya que la integración inmediata es clave para la estabilidad de la fórmula.',15,1),(3,1,3,'Hidratación y Emulsificación','Se procede a incorporar los 84.5 kg de agua utilizando el contenedor de 120 litros con agitación mecánica o manual constante. El agua se debe verter de forma muy lenta y gradual, especialmente durante los primeros 10 litros, para permitir que el aceite se disperse correctamente en el agua sin separarse. Bajo ninguna circunstancia se debe verter el agua de golpe, ya que esto provocaría que la emulsión se corte y el aceite flote en la superficie, invalidando todo el proceso de fabricación.',30,4),(4,1,4,'Homogeneización de Color','Una vez que la emulsión base está terminada se añaden los 0.01 kg de colorante utilizando un dosificador de precisión para no exceder la cantidad marcada. Se debe agitar el producto hasta que el tono verdoso sea completamente idéntico en todos los niveles del contenedor, verificando que no existan asentamientos de color en el fondo. Es importante no sobrepasar la dosis de colorante establecida para evitar que el producto final manche las superficies o textiles donde sea aplicado por el usuario.',10,1),(5,1,5,'Reposo para Envasado','Al finalizar el mezclado se debe detener la agitación por completo y tapar el contenedor para proteger el producto de contaminantes externos. Se deja reposar la mezcla durante una hora para que todas las burbujas de aire atrapadas durante el proceso suban a la superficie y desaparezcan. No se debe realizar el envasado de manera inmediata debido a que el aire atrapado causaría una falsa medición del volumen en las botellas, provocando que luzcan incompletas una vez que el producto se estabilice.',60,5),(6,2,1,'Acondicionamiento de Agua y Quelante','Se debe colocar el total de los 84.65 kg de agua en el contenedor principal de acero inoxidable. Se añade el 0.10 kg de EDTA de forma directa y se inicia una agitación constante hasta lograr que los cristales se disuelvan totalmente y el agua luzca cristalina. Este paso es fundamental para neutralizar los minerales del agua que podrían afectar la transparencia y el desempeño del detergente final.',15,2),(7,2,2,'Activación de Tensoactivos por Calor','Se incorporan los 6 kg de Alkilbencensulfanato de sodio a la solución acuosa y se procede a calentar la mezcla hasta alcanzar una temperatura de 65°C. Se debe mantener la agitación durante todo el calentamiento hasta observar la disolución total del componente. Es indispensable no sobrepasar esta temperatura y verificar que no queden sedimentos en el fondo del tanque antes de proceder al siguiente paso mientras la mezcla aún permanece en la fuente de calor.',40,3),(8,2,3,'Integración de Alcohol Láurico','Todavía bajo el fuego y manteniendo la temperatura, se agregan los 3 kg de Alcohol láurico etoxilado a la mezcla. Se agita vigorosamente hasta notar que el líquido es completamente homogéneo y transparente. Una vez lograda la integración total de este tercer componente, se debe retirar la mezcla de la fuente de calor para comenzar el proceso de enfriamiento controlado antes de añadir los elementos volátiles.',15,1),(9,2,4,'Adición de Solventes y Conservadores','Con la mezcla fuera del fuego pero aún tibia, se deben incorporar bajo agitación vigorosa los 3 kg de Nonil fenol, los 2 kg de Alcohol isopropílico y los 0.25 kg de Formol. Se debe mantener un mezclado constante durante al menos 5 minutos para asegurar que los solventes y el conservador se distribuyan uniformemente en toda la solución. Se recomienda dejar reposar la mezcla brevemente después de este paso para que la temperatura continúe descendiendo de forma natural.',10,1),(10,2,5,'Acabado Estético y Aromatización','Una vez que la disolución se encuentre completamente fría al tacto, se procede a incorporar el 1 kg de fragancia y el colorante necesario para el tono deseado. Es crucial no realizar este paso mientras el líquido esté caliente, ya que el calor degradaría la fragancia y alteraría el color final. Se agita por última vez hasta que el aroma y el color sean uniformes en todo el lote, quedando el producto listo para pasar directamente al área de envasado.',15,1),(11,3,1,'Hidratación del Tensoactivo Base','Se debe cargar el total de los 56.70 kg de agua en el contenedor principal y comenzar una agitación lenta pero constante. Se incorpora paulatinamente el Lauril Éter Sulfato de Sodio asegurando que se disuelva por completo antes de continuar, ya que este componente es la base de la limpieza y la espuma del producto. Es importante verificar que no queden grumos de gel en las paredes del recipiente para garantizar que la concentración sea uniforme en todo el lote.',25,1),(12,3,2,'Integración de Humectantes y Conservadores','Una vez integrada la base de jabón se deben añadir uno a uno la Dietanolamida, la Glicerina y el Nipagin bajo agitación moderada. La Dietanolamida ayudará a estabilizar la espuma mientras que la glicerina proporcionará la suavidad necesaria para el cuidado de la piel. Se debe mezclar hasta que el líquido sea totalmente homogéneo y transparente, asegurándose de que el conservador (nipagin) se haya distribuido por todo el volumen para evitar la contaminación microbiana futura.',15,1),(13,3,3,'Ajuste de pH y Coloración','En este paso se debe medir el pH de la mezcla y ajustarlo a un valor de 7 utilizando Ácido Cítrico para bajarlo o Dietanolamida para subirlo según sea necesario. Una vez neutralizado se incorpora la fragancia y el colorante previamente disuelto en un poco de agua hasta obtener la tonalidad deseada por el cliente. No se debe proceder al espesado sin antes haber estabilizado el pH, ya que un cambio drástico en la acidez después de añadir sal puede alterar la transparencia del jabón.',15,8),(14,3,4,'Espesado Final (Efecto Gel)','Para lograr la consistencia de gel se debe agregar lentamente una solución saturada de cloruro de sodio (sal con agua) mientras se mantiene la agitación. Se debe observar el incremento de viscosidad con mucho cuidado y detener la adición en cuanto se logre el espesor requerido, ya que un exceso de sal puede causar el efecto contrario y licuar el producto nuevamente. Al terminar se apaga el agitador y se deja reposar el lote el tiempo necesario para que cualquier burbuja de aire desaparezca antes de iniciar el envasado.',20,1),(15,4,1,'Preparación de Base Oleosa','Para iniciar se debe utilizar un recipiente de acero inoxidable o plástico de 20 litros que esté completamente seco y libre de residuos de agua. Se vierten 0.50 kg de Nonil fenol junto con los 5 kg de Aceite de pino y se comienza una agitación constante hasta que el líquido sea totalmente transparente y no se perciban líneas de aceite. Es fundamental no utilizar utensilios de madera en este paso para evitar la contaminación del lote y asegurar que la base esté lista para recibir los siguientes componentes.',10,1),(16,4,2,'Incorporación de Detercon','En este punto se deben añadir los 10 kg de Detercon potásico a la mezcla previa de aceite y nonil fenol directamente en el contenedor principal de 120 litros. Se debe mantener una agitación firme mientras se vierte el componente para evitar la formación de grumos y asegurar que la mezcla adquiera una consistencia similar a un jarabe espeso y uniforme. No se debe detener el mezclado en ningún momento de la adición ya que la integración inmediata es clave para la estabilidad de la fórmula.',15,1),(17,4,3,'Hidratación y Emulsificación','Se procede a incorporar los 84.5 kg de agua utilizando el contenedor de 120 litros con agitación mecánica o manual constante. El agua se debe verter de forma muy lenta y gradual, especialmente durante los primeros 10 litros, para permitir que el aceite se disperse correctamente en el agua sin separarse. Bajo ninguna circunstancia se debe verter el agua de golpe, ya que esto provocaría que la emulsión se corte y el aceite flote en la superficie, invalidando todo el proceso de fabricación.',30,4),(18,4,4,'Homogeneización de Color','Una vez que la emulsión base está terminada se añaden los 0.01 kg de colorante utilizando un dosificador de precisión para no exceder la cantidad marcada. Se debe agitar el producto hasta que el tono verdoso sea completamente idéntico en todos los niveles del contenedor, verificando que no existan asentamientos de color en el fondo. Es importante no sobrepasar la dosis de colorante establecida para evitar que el producto final manche las superficies o textiles donde sea aplicado por el usuario.',10,1),(19,4,5,'Reposo para Envasado','Al finalizar el mezclado se debe detener la agitación por completo y tapar el contenedor para proteger el producto de contaminantes externos. Se deja reposar la mezcla durante una hora para que todas las burbujas de aire atrapadas durante el proceso suban a la superficie y desaparezcan. No se debe realizar el envasado de manera inmediata debido a que el aire atrapado causaría una falsa medición del volumen en las botellas, provocando que luzcan incompletas una vez que el producto se estabilice.',60,5),(20,5,1,'Fundición de la Base de Jabón','Se debe colocar el jabón de tocador neutro previamente rallado o cortado en trozos pequeños dentro del contenedor con los 3 kilos de agua suavizada. Se aplica calor moderado y se agita lentamente hasta lograr la disolución total de los sólidos, cuidando que la temperatura no llegue al punto de ebullición para evitar la formación de burbujas excesivas que arruinen la estética de la barra. Se debe obtener una pasta líquida uniforme y sin grumos antes de proceder a la siguiente etapa.',45,2),(21,5,2,'Humectación y Conservación','Una vez que la base está líquida se incorporan los 3 kilos de glicerina y los 10 gramos de nipagín manteniendo una agitación suave pero constante durante 5 minutos. La glicerina debe integrarse perfectamente con la pasta de jabón para asegurar las propiedades humectantes de la pieza final. En caso de requerir un jabón de color blanco sólido, este es el momento de añadir el dióxido de titanio y mezclar hasta que el tono sea completamente opaco y uniforme.',10,1),(22,5,3,'Aromatización y Vertido en Moldes','Se retira la mezcla de la fuente de calor y se permite que baje ligeramente la temperatura sin dejar que la pasta comience a solidificar. Se añade la esencia elegida y se mezcla rápidamente para distribuir el aroma en todo el lote de manera homogénea. Inmediatamente después se debe realizar el vertido en los moldes individuales de forma precisa para evitar derrames y asegurar que cada pieza tenga el peso y la forma correcta antes de que la pasta pierda movilidad.',20,1),(23,5,4,'Solidificación y Acabado','Las piezas deben permanecer en reposo absoluto en un área fresca y seca hasta que la pasta se transforme en una barra sólida y firme. No se debe intentar mover los moldes ni enfriar de manera forzada en refrigeración, ya que esto podría causar grietas o sudoración en el jabón. Una vez que la pieza esté totalmente fría se procede al desmoldado manual y al empaque inmediato para proteger el aroma y evitar que la humedad del ambiente afecte la superficie de la barra.',120,5),(24,6,1,'Fundición de la Base de Jabón','Se debe colocar el jabón de tocador neutro previamente rallado o cortado en trozos pequeños dentro del contenedor con los 3 kilos de agua suavizada. Se aplica calor moderado y se agita lentamente hasta lograr la disolución total de los sólidos, cuidando que la temperatura no llegue al punto de ebullición para evitar la formación de burbujas excesivas que arruinen la estética de la barra. Se debe obtener una pasta líquida uniforme y sin grumos antes de proceder a la siguiente etapa.',45,2),(25,6,2,'Humectación y Conservación','Una vez que la base está líquida se incorporan los 3 kilos de glicerina y los 10 gramos de nipagín manteniendo una agitación suave pero constante durante 5 minutos. La glicerina debe integrarse perfectamente con la pasta de jabón para asegurar las propiedades humectantes de la pieza final. En caso de requerir un jabón de color blanco sólido, este es el momento de añadir el dióxido de titanio y mezclar hasta que el tono sea completamente opaco y uniforme.',10,1),(26,6,3,'Aromatización y Vertido en Moldes','Se retira la mezcla de la fuente de calor y se permite que baje ligeramente la temperatura sin dejar que la pasta comience a solidificar. Se añade la esencia elegida y se mezcla rápidamente para distribuir el aroma en todo el lote de manera homogénea. Inmediatamente después se debe realizar el vertido en los moldes individuales de forma precisa para evitar derrames y asegurar que cada pieza tenga el peso y la forma correcta antes de que la pasta pierda movilidad.',20,1),(27,6,4,'Solidificación y Acabado','Las piezas deben permanecer en reposo absoluto en un área fresca y seca hasta que la pasta se transforme en una barra sólida y firme. No se debe intentar mover los moldes ni enfriar de manera forzada en refrigeración, ya que esto podría causar grietas o sudoración en el jabón. Una vez que la pieza esté totalmente fría se procede al desmoldado manual y al empaque inmediato para proteger el aroma y evitar que la humedad del ambiente afecte la superficie de la barra.',120,5),(28,7,1,'Preparación de la Fase de Suspensión (Atole)','Se debe verter la mitad del agua total (41 kg) en el contenedor principal de mezcla a temperatura ambiente. Se incorporan los 8 kg de harina de forma gradual mientras se realiza una agitación mecánica vigorosa para evitar la formación de grumos o asentamientos en el fondo. Se debe continuar el mezclado hasta obtener una consistencia líquida blanquecina totalmente lisa y homogénea, asegurándose de que no existan partículas sólidas secas antes de proceder a la fase química.',20,1),(29,7,2,'Reacción de Saponificación y Gelificación','Bajo agitación constante y con el equipo de protección personal completo se deben medir e incorporar los 10 kg de Hidróxido de sodio al 50 % directamente sobre la mezcla de harina y agua. Durante este paso la mezcla comenzará a espesar rápidamente y a liberar calor debido a la reacción química entre la sosa y los componentes de la harina. Se debe mantener la agitación vigorosa para asegurar que la sosa se distribuya uniformemente y el gel se forme de manera consistente en todo el volumen del recipiente.',15,3),(30,7,3,'Ajuste de Viscosidad y Acabado','Una vez formado el gel base se debe añadir el resto del agua (41 kg) de forma lenta y pausada manteniendo la agitación enérgica para integrar el líquido a la estructura espesa ya formada. Se debe continuar el proceso de mezclado hasta que el gel sea visualmente uniforme, brillante y no presente separaciones de fase o partes líquidas aisladas. Es fundamental verificar que la textura final tenga el cuerpo suficiente para adherirse a superficies verticales, cumpliendo así con su función de quitacochambre antes de trasladar al área de llenado.',20,1),(31,7,4,'Estabilización y Envasado','Al finalizar la integración total se debe permitir que el gel repose para que la temperatura generada por la reacción química descienda y las burbujas de aire atrapadas se eliminen. No se debe tapar herméticamente el contenedor mientras el producto permanezca caliente para evitar la acumulación de vapores. Una vez estabilizado el producto se procede al envasado en recipientes de polietileno de alta densidad debidamente etiquetados con las advertencias de seguridad correspondientes por su alta peligrosidad.',30,5),(32,8,1,'Preparación del Vehículo Acuoso','DESCRIPCIÓN:\r\nSe deben verter los 87 kilos de agua en el contenedor principal de plástico asegurándose de que el recipiente esté libre de cualquier residuo orgánico o metálico. Se recomienda el uso de agua suavizada o destilada para evitar que los minerales presentes en el agua corriente reaccionen con el cloro y formen sedimentos en el fondo del envase. Se inicia una agitación lenta para preparar el medio de recepción del concentrado químico sin generar salpicaduras innecesarias.',10,1),(33,8,2,'Dilución del Activo Desinfectante','Se añaden los 13 kilos de Hipoclorito de sodio al 13% de forma muy pausada directamente sobre el agua mientras se mantiene la agitación constante. Este paso debe realizarse con extremo cuidado para evitar vapores fuertes y asegurar que el concentrado se distribuya de manera uniforme en todo el lote. La mezcla resultante tendrá una concentración aproximada del 1.5% al 2% de cloro activo, que es el estándar comercial para limpieza doméstica y desinfección de superficies.',20,2),(34,8,3,'Estabilización y Reposo','Al terminar la mezcla se debe detener el agitador y permitir que el producto repose para que la solución se estabilice químicamente antes de pasar al envasado. El contenedor debe permanecer tapado para evitar que el cloro pierda su fuerza al contacto prolongado con el aire y la luz ambiental. Una vez transcurrido el tiempo de reposo se procede a llenar los envases finales, los cuales deben ser opacos para garantizar que la vida útil del producto sea prolongada y mantenga su poder desinfectante.',30,5),(35,9,1,'Disolución de la Base Tensoactiva','Se deben colocar los 65 kilos de agua en el contenedor principal de plástico e iniciar una agitación lenta. Se añade paulatinamente el Lauril Éter Sulfato de Sodio asegurando que se disuelva completamente y se integre con el agua hasta que la mezcla luzca uniforme y sin hilos de gel flotando. Este paso es el corazón de la limpieza del detergente, por lo que se debe verificar que no queden residuos de materia prima pegados en las paredes del tanque antes de continuar.',20,1),(36,9,2,'Estabilización de Espuma y Desengrasante','Una vez integrada la base se incorporan la Amida de coco y el Nonil fenol manteniendo la agitación constante pero controlada para evitar el exceso de burbujas. La amida ayudará a estabilizar la espuma y a dar viscosidad al producto, mientras que el nonil actuará como el agente que remueve las grasas de las fibras textiles. Se debe mezclar hasta que la solución sea totalmente transparente y no presente ninguna turbidez visual.',15,1),(37,9,3,'Conservación y Acabado Estético','Con la mezcla base lista se procede a añadir el Formol como conservador, seguido de la fragancia y el colorante previamente diluido en una pequeña cantidad de agua. Se debe mantener la agitación hasta que el color sea homogéneo en todo el lote y el aroma se perciba balanceado. Es importante no omitir el conservador, ya que el agua y los tensoactivos pueden desarrollar bacterias u hongos si el producto se almacena por periodos prolongados.',15,1),(38,9,4,'Estabilización de Viscosidad y Reposo','Al finalizar la integración de todos los componentes se apaga el agitador y se deja reposar el producto para permitir que la espuma baje por completo. En este punto el detergente adquirirá su viscosidad final y se volverá totalmente cristalino a la vista. No se recomienda envasar antes de que pase este tiempo, ya que el nivel de llenado en las botellas se vería afectado por el aire atrapado durante el proceso de mezclado.',60,5),(39,10,1,'Solubilización de la Fragancia','En un recipiente pequeño de unos 10 litros se deben colocar los 3 kilos de Nonil fenol junto con los 2 kilos de fragancia concentrada. Se debe agitar vigorosamente hasta que ambos líquidos se fusionen en una sola mezcla aceitosa y transparente. Este paso es el más crítico del proceso, ya que el Nonil actúa como un puente que permitirá que el aceite de la fragancia se disuelva en el agua sin enturbiarla ni dejar capas separadas.',15,1),(40,10,2,'Dilución y Fijación','Se vierte la pre-mezcla de fragancia y nonil en el contenedor principal que ya contiene los 94 kilos de agua bajo una agitación constante. Seguidamente se incorporan los 0.8 kilos de Alcohol isopropílico, el cual ayudará a que el aroma se evapore de manera más eficiente al ser aplicado en el ambiente y servirá como un ligero fijador. Se debe continuar el mezclado hasta notar que el líquido es completamente cristalino y el aroma se ha distribuido de forma balanceada en toda la solución.',20,1),(41,10,3,'Conservación y Personalización','Se añade el 0.2 kilo de Formol para garantizar la vida de anaquel del aromatizante y se incorpora el colorante necesario según el aroma elegido (por ejemplo, morado para lavanda o amarillo para vainilla). Se debe utilizar una cantidad mínima de colorante para evitar que el producto manche cortinas, paredes o textiles al ser atomizado. El mezclado termina cuando el color sea uniforme en todo el volumen y no se observen partículas de colorante sin disolver en el fondo del tanque.',10,1),(42,10,4,'Clarificación y Envasado','Se detiene la agitación y se deja reposar el lote por media hora para que la mezcla se estabilice y cualquier microburbuja de aire desaparezca. Este tiempo de reposo asegura que el aromatizante tenga una apariencia profesional y totalmente transparente antes de ser transferido a las botellas con atomizador. Se debe verificar una última vez la claridad del producto antes de proceder al envasado final en recipientes de PET o polietileno.',30,5),(43,11,1,'Preparación del Vehículo Térmico','Se deben verter los 90 kilos de agua en el contenedor principal y calentar hasta alcanzar una temperatura constante de 50°C. Este calor es estrictamente necesario para que el activo suavizante, que suele ser una pasta cerosa o muy densa, pueda fundirse y dispersarse de manera uniforme sin dejar residuos sólidos en el fondo del tanque. Se debe verificar la temperatura con un termómetro industrial antes de proceder a la carga de los químicos para asegurar la estabilidad de la emulsión.',20,3),(44,11,2,'Dispersión del Activo Suavizante','Con el agua a la temperatura correcta y bajo agitación constante, se añaden los 8 kilos de activo suavizante de forma lenta y pausada. En este punto el líquido comenzará a tomar una apariencia lechosa y a incrementar su viscosidad a medida que el sistema se enfría ligeramente. Se debe mantener el mezclado durante todo el tiempo indicado para garantizar que las partículas de suavizante queden perfectamente suspendidas en el agua y no se produzca una separación de fases al enfriarse por completo.',30,4),(45,11,3,'Fijación de Aroma y Conservación','Una vez que la mezcla ha bajado de los 35°C, se incorporan los 1.5 kilos de fragancia concentrada y los 0.2 kilos de formol. Es fundamental realizar este paso a baja temperatura para que el calor no degrade las notas aromáticas del suavizante, permitiendo que el olor perdure más tiempo en la ropa después del lavado. Se continúa agitando hasta que la esencia se haya distribuido por todo el lote de manera imperceptible a la vista pero con un aroma potente y uniforme.',15,1),(46,11,4,'Coloración y Estabilización Final','Se añade el colorante previamente disuelto en un litro de agua para asegurar que no queden vetas de color intenso en el producto final. Se agita por última vez hasta que el tono (ya sea azul pastel, rosa o celeste) sea completamente parejo en todo el volumen del contenedor. Al terminar, se deja reposar el lote tapado hasta que alcance la temperatura ambiente antes de proceder al envasado en botellas opacas, lo que ayudará a proteger los componentes de la luz directa.',15,1),(47,12,1,'Preparación del Vehículo Térmico','Se deben verter los 90 kilos de agua en el contenedor principal y calentar hasta alcanzar una temperatura constante de 50°C. Este calor es estrictamente necesario para que el activo suavizante, que suele ser una pasta cerosa o muy densa, pueda fundirse y dispersarse de manera uniforme sin dejar residuos sólidos en el fondo del tanque. Se debe verificar la temperatura con un termómetro industrial antes de proceder a la carga de los químicos para asegurar la estabilidad de la emulsión.',20,3),(48,12,2,'Dispersión del Activo Suavizante','Con el agua a la temperatura correcta y bajo agitación constante, se añaden los 8 kilos de activo suavizante de forma lenta y pausada. En este punto el líquido comenzará a tomar una apariencia lechosa y a incrementar su viscosidad a medida que el sistema se enfría ligeramente. Se debe mantener el mezclado durante todo el tiempo indicado para garantizar que las partículas de suavizante queden perfectamente suspendidas en el agua y no se produzca una separación de fases al enfriarse por completo.',30,4),(49,12,3,'Fijación de Aroma y Conservación','Una vez que la mezcla ha bajado de los 35°C, se incorporan los 1.5 kilos de fragancia concentrada y los 0.2 kilos de formol. Es fundamental realizar este paso a baja temperatura para que el calor no degrade las notas aromáticas del suavizante, permitiendo que el olor perdure más tiempo en la ropa después del lavado. Se continúa agitando hasta que la esencia se haya distribuido por todo el lote de manera imperceptible a la vista pero con un aroma potente y uniforme.',15,1),(50,12,4,'Coloración y Estabilización Final','Se añade el colorante previamente disuelto en un litro de agua para asegurar que no queden vetas de color intenso en el producto final. Se agita por última vez hasta que el tono (ya sea azul pastel, rosa o celeste) sea completamente parejo en todo el volumen del contenedor. Al terminar, se deja reposar el lote tapado hasta que alcance la temperatura ambiente antes de proceder al envasado en botellas opacas, lo que ayudará a proteger los componentes de la luz directa.',15,1);
/*!40000 ALTER TABLE `pasosreceta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `perfil_modulo`
--

DROP TABLE IF EXISTS `perfil_modulo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `perfil_modulo` (
  `id_perfil` int NOT NULL,
  `id_modulo` int NOT NULL,
  `permiso_escritura` int DEFAULT NULL,
  PRIMARY KEY (`id_perfil`,`id_modulo`),
  KEY `id_modulo` (`id_modulo`),
  CONSTRAINT `perfil_modulo_ibfk_1` FOREIGN KEY (`id_modulo`) REFERENCES `modulos` (`id_modulo`),
  CONSTRAINT `perfil_modulo_ibfk_2` FOREIGN KEY (`id_perfil`) REFERENCES `perfiles` (`id_perfil`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `perfil_modulo`
--

LOCK TABLES `perfil_modulo` WRITE;
/*!40000 ALTER TABLE `perfil_modulo` DISABLE KEYS */;
INSERT INTO `perfil_modulo` VALUES (1,2,4),(1,3,4),(1,4,4),(2,2,1),(2,3,4),(2,4,2),(2,8,4),(3,7,3),(3,8,1),(4,3,2),(4,5,4),(4,8,1),(4,9,4),(5,6,4),(5,7,4),(5,8,1),(7,1,4),(7,2,4),(7,3,4),(7,4,4),(7,5,4),(7,6,4),(7,7,4),(7,8,4),(7,9,4);
/*!40000 ALTER TABLE `perfil_modulo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `perfiles`
--

DROP TABLE IF EXISTS `perfiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `perfiles` (
  `id_perfil` int NOT NULL AUTO_INCREMENT,
  `nombre_perfil` varchar(50) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_perfil`),
  UNIQUE KEY `nombre_perfil` (`nombre_perfil`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `perfiles`
--

LOCK TABLES `perfiles` WRITE;
/*!40000 ALTER TABLE `perfiles` DISABLE KEYS */;
INSERT INTO `perfiles` VALUES (1,'Compras',NULL),(2,'Almacenista',NULL),(3,'Vendedor',NULL),(4,'Produccion',NULL),(5,'Gerente',NULL),(6,'Cliente',NULL),(7,'Administrador','Acceso total al sistema');
/*!40000 ALTER TABLE `perfiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producto_presentación_precio`
--

DROP TABLE IF EXISTS `producto_presentación_precio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto_presentación_precio` (
  `id_presentacion_precio` int NOT NULL AUTO_INCREMENT,
  `id_producto` int NOT NULL,
  `precio_menudeo` decimal(10,2) NOT NULL,
  `precio_mayoreo` decimal(10,2) NOT NULL,
  `presentacion` varchar(50) NOT NULL,
  `cantidad_mayoreo` int NOT NULL,
  `stock_disponible` int DEFAULT NULL,
  `tamano_unidad` decimal(10,0) DEFAULT NULL,
  `tipo_unidad_base` int DEFAULT NULL,
  `foto` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_presentacion_precio`),
  KEY `id_producto` (`id_producto`),
  CONSTRAINT `producto_presentación_precio_ibfk_1` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto_presentación_precio`
--

LOCK TABLES `producto_presentación_precio` WRITE;
/*!40000 ALTER TABLE `producto_presentación_precio` DISABLE KEYS */;
INSERT INTO `producto_presentación_precio` VALUES (1,1,20.00,15.00,'Botella de 1L',10,1000,1,0,'10'),(2,3,25.00,20.00,'Botella 1L',10,112,1000,1,'Limpia_Pisos_1L.png'),(3,4,20.00,18.50,'Botella 1L',10,30,1000,1,'Jabon_Liquido_Manos_500ml.png'),(4,5,12.00,10.00,'Barra de 350gr',7,69,350,2,'Jabon_Manos_350gr.png'),(5,6,30.00,25.99,'Botella 500ml',10,114,500,1,'Gel_Quita_Coch_500ml.png'),(6,7,25.00,20.00,'Botella 1L',10,20,1000,1,'Cloro_1L.png'),(7,8,25.00,22.00,'Botella 1L',12,85,1000,1,'Detergente_Liquido_1L.png'),(8,9,30.00,25.00,'Botella 1L',12,54,1000,1,'LImpia_Vidrios_Anti_500ml.png'),(9,10,30.00,25.00,'Botella 1L',12,62,1000,1,'10'),(10,11,30.00,24.50,'Botella de 1L',10,1000,1,0,'10'),(11,12,30.00,24.99,'Botella 1L',10,0,1000,1,'10'),(12,13,28.00,23.00,'Botella de 1L',10,1000,1,0,'10'),(13,14,20.00,18.50,'Botella de 500ml',10,500,1,0,'10'),(14,15,30.00,5.00,'Bojiewjf',10,500,1,NULL,'10'),(15,16,26.00,20.00,'Botella 1L',10,1000,1,NULL,'10'),(16,16,18.00,15.00,'Botella de 500ml',10,500,1,NULL,'10'),(19,3,15.00,13.90,'Botella de 500ml',10,109,500,1,'13'),(20,2,30.00,20.00,'Botella 1L',10,42,1000,1,'Limpiador_pinol_1L.png'),(21,2,20.00,16.50,'Botella de 500ml',10,60,500,1,'Limpiador_pinol_1L.png'),(24,4,15.00,12.00,'Botella de 500ml',10,40,500,1,'Jabon_Liquido_Manos_500ml.png'),(28,7,17.00,15.50,'Botella 500ml',10,45,500,1,'botella_1l_cloro.jpg');
/*!40000 ALTER TABLE `producto_presentación_precio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos`
--

DROP TABLE IF EXISTS `productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productos` (
  `id_producto` int NOT NULL AUTO_INCREMENT,
  `codigo_barras` varchar(20) DEFAULT NULL,
  `nombre` varchar(100) NOT NULL,
  `categoria` varchar(50) NOT NULL,
  `estatus` enum('Activo','Inactivo') DEFAULT NULL,
  PRIMARY KEY (`id_producto`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos`
--

LOCK TABLES `productos` WRITE;
/*!40000 ALTER TABLE `productos` DISABLE KEYS */;
INSERT INTO `productos` VALUES (2,'C750002','Pinol','Cuidado del Hogar','Activo'),(3,'C750003','Limpia Pisos','Cuidado del Hogar','Activo'),(4,'C750004','Jabón Liquido Para Manos','Cuidado Personal','Activo'),(5,'C750005','Jabón Para Manos','Cuidado Personal','Activo'),(6,'C750006','Gel Quita Cochambre','Cocina','Activo'),(7,'C750007','Cloro','Cuidado del Hogar','Activo'),(8,'C750008','Detergente Líquido para Ropa','Lavanderia','Activo'),(9,'C750009','Aromatizante Líquido (Base Agua)','Cuidado Personal','Activo'),(10,'C750010','Suavizante de Ropa Concentrado','Lavanderia','Activo'),(12,'C750012','Limpiador Multiusos','Cuidado del Hogar','Inactivo');
/*!40000 ALTER TABLE `productos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proveedores`
--

DROP TABLE IF EXISTS `proveedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proveedores` (
  `id_proveedor` int NOT NULL AUTO_INCREMENT,
  `num_unico_prov` varchar(20) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `domicilio` text,
  `telefono` varchar(20) DEFAULT NULL,
  `correo` varchar(100) DEFAULT NULL,
  `estatus` enum('Activo','Inactivo') DEFAULT NULL,
  PRIMARY KEY (`id_proveedor`),
  UNIQUE KEY `num_unico_prov` (`num_unico_prov`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proveedores`
--

LOCK TABLES `proveedores` WRITE;
/*!40000 ALTER TABLE `proveedores` DISABLE KEYS */;
INSERT INTO `proveedores` VALUES (1,'PROV-0001','Limba Limpieza del Bajío','C. Zeta 103, Industrial Delta, León, Guanajuato, México','477 410 9698','contacto@Limba.com.mx','Activo'),(2,'PROV-0002','Pochteca Materias Primas','León, Guanajuato (sucursal industrial)','477 101 5800','contacto@pochteca.com.mx','Activo'),(3,'PROV-0003','CLF Químicos','C. 16 de Septiembre 213, Col. Obregón, León, Guanajuato','477 717 5354','contacto@clf.com.mx','Activo'),(4,'PROV-0004','Productos Químicos Dypasa','C. Mónaco 210, Oriental Anaya, León, Guanajuato','477 514 9848','contacto@dypasa.com.mx','Activo'),(5,'PROV-0005','Materias Primas La Higiénica','Av. B. Domínguez Pte 518, Col. Obrera, León, Guanajuato','477 716 5094','contacto@higienica.com.mx','Activo'),(6,'PROV-0006','AFIMEX','Blvd. La Luz 1711, León, Guanajuato','477 764 1617','contacto@afimex.net','Activo'),(7,'PROV-0007','Envases y Tapas del Bajío','Blvd. Timoteo Lozano, León, Guanajuato, México','477 772 8899','contacto@envasesbajio.com','Activo'),(8,'PROV-0008','Etiquetas Impresas de León','Col. Centro, León, Guanajuato, México','477 715 3344','etiquetasleon@gmail.com','Activo'),(9,'PROV-0009','Agua Transportes','Blvd. la Luz 1568, El Refugio, 37270 León de los Aldama, Gto.','477-761-8097','contacto@agua.com','Activo');
/*!40000 ALTER TABLE `proveedores` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tg_generar_num_unico_prov` BEFORE INSERT ON `proveedores` FOR EACH ROW BEGIN
    DECLARE siguiente_id INT;

    SELECT IFNULL(MAX(id_proveedor), 0) + 1 INTO siguiente_id FROM proveedores;

    SET NEW.num_unico_prov = CONCAT('PROV-', LPAD(siguiente_id, 4, '0'));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `receta_detalle`
--

DROP TABLE IF EXISTS `receta_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `receta_detalle` (
  `id_receta_detalle` int NOT NULL AUTO_INCREMENT,
  `id_receta` int NOT NULL,
  `id_materia` int NOT NULL,
  `cantidad_necesaria` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_receta_detalle`),
  KEY `id_materia` (`id_materia`),
  KEY `id_receta` (`id_receta`),
  CONSTRAINT `receta_detalle_ibfk_1` FOREIGN KEY (`id_materia`) REFERENCES `materiaprima` (`id_materia`),
  CONSTRAINT `receta_detalle_ibfk_2` FOREIGN KEY (`id_receta`) REFERENCES `recetas` (`id_receta`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `receta_detalle`
--

LOCK TABLES `receta_detalle` WRITE;
/*!40000 ALTER TABLE `receta_detalle` DISABLE KEYS */;
INSERT INTO `receta_detalle` VALUES (1,1,17,84.00),(2,1,11,0.50),(3,2,17,84.00),(4,2,11,3.00),(5,2,15,0.25),(6,2,4,2.00),(7,3,17,56.00),(8,3,3,30.00),(9,3,5,5.00),(10,3,16,10.00),(11,4,17,84.00),(12,4,11,0.50),(13,4,21,10.00),(14,4,20,5.00),(15,5,5,5.00),(16,5,23,3.00),(17,5,25,3.00),(18,5,24,0.10),(19,6,5,5.00),(20,6,23,3.00),(21,6,25,3.00),(22,6,24,0.10),(23,6,26,4.00),(24,7,17,82.00),(25,7,2,10.00),(26,7,12,8.00),(27,8,17,87.00),(28,8,8,13.00),(29,9,28,65.00),(30,9,3,25.00),(31,9,29,5.00),(32,9,11,4.00),(33,9,30,0.50),(34,9,15,0.20),(35,9,16,0.30),(36,10,28,94.00),(37,10,11,3.00),(38,10,13,0.80),(39,10,15,0.20),(40,11,17,90.00),(41,11,31,0.80),(42,11,32,1.50),(43,11,15,0.20),(44,11,16,0.30),(45,12,17,90.00),(46,12,31,0.80),(47,12,32,1.50),(48,12,15,0.20),(49,12,16,0.30);
/*!40000 ALTER TABLE `receta_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recetas`
--

DROP TABLE IF EXISTS `recetas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recetas` (
  `id_receta` int NOT NULL AUTO_INCREMENT,
  `num_unico_receta` varchar(20) NOT NULL,
  `nombre_final` varchar(100) NOT NULL,
  `instrucciones_generales` text,
  `tiempo_total_estimado_min` int DEFAULT NULL,
  `costo_estimado_produccion` decimal(10,2) DEFAULT NULL,
  `merma_estimada_porcent` decimal(5,2) DEFAULT NULL,
  `cantidad_producida` int DEFAULT NULL,
  `unidad_medida` tinyint DEFAULT NULL,
  `id_producto` int DEFAULT NULL,
  `estatus` int DEFAULT NULL,
  `receta_version_anterior` int DEFAULT NULL,
  PRIMARY KEY (`id_receta`),
  UNIQUE KEY `num_unico_receta` (`num_unico_receta`),
  KEY `id_producto` (`id_producto`),
  CONSTRAINT `recetas_ibfk_1` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recetas`
--

LOCK TABLES `recetas` WRITE;
/*!40000 ALTER TABLE `recetas` DISABLE KEYS */;
INSERT INTO `recetas` VALUES (1,'REC-0001','Limpiador Desinfectante tipo \"Pinol\"','',125,30.00,5.76,100,2,2,2,NULL),(2,'REC-0002','Limpia Pisos tipo Fabuloso','Este proceso requiere control de temperatura ya que algunos componentes necesitan calor para disolverse correctamente. Se debe utilizar un contenedor con capacidad de 120 litros que resista temperaturas de hasta 65°C. Es vital mantener una ventilación adecuada debido al uso de alcohol isopropílico y formol. No se debe añadir la fragancia mientras la mezcla esté caliente para evitar la evaporación de los aromas.',95,275.00,7.20,100,2,3,1,NULL),(3,'REC-0003','Jabón Líquido Lavamanos','Utilizar un contenedor de plástico de 120 litros con agitador de aspas para evitar la incorporación excesiva de aire. La clave de esta receta es el ajuste final de viscosidad y pH para garantizar la suavidad en la piel.',75,3575.00,5.85,150,1,4,1,NULL),(4,'REC-0001-V2','Limpiador Desinfectante tipo \"Pinol\"','',125,30.00,6.12,100,2,2,1,1),(5,'REC-0004','Jabón de Tocador en Barra (Lavanda)','El proceso requiere fundición por calor controlado. Se deben utilizar moldes de silicona o plástico rígido con la forma deseada para cada pieza. Es vital no dejar que la mezcla hierva para no opacar la glicerina.',195,225.00,4.59,100,4,5,2,NULL),(6,'REC-0004-V2','Jabón de Tocador en Barra (Lavanda)','El proceso requiere fundición por calor controlado. Se deben utilizar moldes de silicona o plástico rígido con la forma deseada para cada pieza. Es vital no dejar que la mezcla hierva para no opacar la glicerina.',195,225.00,4.77,100,4,5,1,5),(7,'REC-0005','Gel Quitacochambre','Este producto es sumamente alcalino y corrosivo. Es obligatorio el uso de guantes de nitrilo, lentes de seguridad y cubrebocas durante todo el proceso. Se debe trabajar en un área con ventilación natural abundante y utilizar contenedores de plástico resistentes a químicos fuertes (evitar aluminio a toda costa).',85,8240.00,5.22,120,1,6,1,NULL),(8,'REC-0006','Cloro Blanqueador y Desinfectante','Este proceso debe realizarse obligatoriamente en recipientes de plástico opacos (HDPE), ya que el cloro reacciona con los metales y se degrada con la luz solar. Es necesario usar equipo de protección personal para evitar salpicaduras en piel y ojos.',60,9828.00,3.33,100,1,7,1,NULL),(9,'REC-0007','Detergente Líquido para Ropa (Cuidado de Color)','Se debe utilizar un contenedor de plástico de 120 litros con un sistema de agitación constante. El orden de los ingredientes es vital para asegurar que el detergente mantenga su transparencia y no se separe en capas después de unos días.\r\nNo añadir los colorantes o fragancias al inicio; siempre van al final. No agitar a velocidades excesivas, ya que la espuma generada dificultará el envasado y la medición exacta del volumen.',110,1445.00,5.76,100,2,8,1,NULL),(10,'REC-0008','Aromatizante Ambiental Premium','El éxito de este producto es la transparencia total. Se debe utilizar un contenedor de plástico de 120 litros perfectamente limpio. Es fundamental mezclar la fragancia con el emulsificante antes de añadir el agua para evitar que el producto quede turbio o \"lechoso\".\r\n\r\nNo verter la fragancia directamente al agua sola, ya que el aceite flotará y no se mezclará. No utilizar agua con altos contenidos de sales, ya que puede opacar el brillo del producto final.',75,600.00,5.22,100,2,9,1,NULL),(11,'REC-0009','Suavizante de Telas Libre Enjuague','El éxito de este producto depende de la temperatura del agua al momento de añadir el activo suavizante. Se debe usar un contenedor de plástico de 120 litros. Es vital que el agitador esté en marcha antes de añadir la materia prima para evitar que se formen \"pelotas\" de grasa que no se disuelvan.\r\n\r\nNo utilizar agua fría para disolver el activo suavizante, ya que se cortará la mezcla. No agitar demasiado rápido una vez que el producto espese para evitar atrapar aire que opaque el brillo del suavizante.',80,80.00,6.39,120,1,10,2,NULL),(12,'REC-0009-V2','Suavizante de Telas Libre Enjuague','El éxito de este producto depende de la temperatura del agua al momento de añadir el activo suavizante. Se debe usar un contenedor de plástico de 120 litros. Es vital que el agitador esté en marcha antes de añadir la materia prima para evitar que se formen \"pelotas\" de grasa que no se disuelvan.\r\n\r\nNo utilizar agua fría para disolver el activo suavizante, ya que se cortará la mezcla. No agitar demasiado rápido una vez que el producto espese para evitar atrapar aire que opaque el brillo del suavizante.  ',80,135.60,6.39,120,1,10,1,11);
/*!40000 ALTER TABLE `recetas` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tg_generar_num_unico_receta` BEFORE INSERT ON `recetas` FOR EACH ROW BEGIN
    DECLARE max_id INT;
    DECLARE siguiente_id INT;

    -- Solo entramos si es una receta nueva
    IF NEW.num_unico_receta = 'TEMP' OR NEW.num_unico_receta IS NULL OR NEW.num_unico_receta = '' THEN
        
        -- Buscamos el número más alto en los códigos que NO son versiones (-V)
        -- SUBSTRING extrae desde la posición 5 (después de 'REC-')
        SELECT MAX(CAST(SUBSTRING(num_unico_receta, 5) AS UNSIGNED)) INTO max_id 
        FROM recetas 
        WHERE num_unico_receta NOT LIKE '%-V%';

        -- Si la tabla está vacía, empezamos en 1, si no, máximo + 1
        SET siguiente_id = IFNULL(max_id, 0) + 1;

        SET NEW.num_unico_receta = CONCAT('REC-', LPAD(siguiente_id, 4, '0'));
        
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id_usuario` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `fs_uniquifier` varchar(64) NOT NULL,
  `estatus` enum('Activo','Inactivo') DEFAULT NULL,
  `id_perfil` int DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `fs_uniquifier` (`fs_uniquifier`),
  UNIQUE KEY `username` (`username`),
  KEY `id_perfil` (`id_perfil`),
  CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`id_perfil`) REFERENCES `perfiles` (`id_perfil`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'admin_crystal','Admin','$2b$12$CrbV9Y8AiGWCBpKk8VBDJu/XkKdUL8SBkpqoPZ1CzcvrRw5P9H8va','b46ba64e-2721-4f30-924b-734459568cbe','Activo',7),(3,'crystal@crystal.com','Cliente General','$2b$12$WvLjLh3Ic0Aj313yw20I/uHZ9b/hk9x4.PAGRTIviH0yx7yZxRFRy','44f0eafa-dc17-4dd0-8ed3-862cc19d1100','Activo',6),(4,'Vendedor','Vendedor','$2b$12$P8QtPd1K1p41H6sexgcXSug9JDaX828LFeNKQyJs.Hb5XWp0zBMyO','d349128ee12b7b2e358e56fc8d7e553f22fed4ae788ebc2602fa6cea88af455c','Activo',3),(5,'Noe@gmail.com','Noe','$2b$12$caDparnlJZcUKvTJvvMr1eZ7Ga2.BwGLLQqnW5thqOGaS01Tz53.a','126901b4-94e4-45c0-8d91-d9723ad3b626','Activo',6),(6,'flor@gmail.com','Flor','$2b$12$RamyishVA.U3gOlo775cfuCfXkVKKaRRYXXPptsfe2rbNp/V.uc/m','7cbca424-12a8-4d1c-93e3-388144094770','Activo',6),(8,'Almacen','Almacen','$2b$12$mq08ElcA5gcXCMM0Wcw33.SeRH4m9YJZhnumnaxlOikjRE9pO5THG','10aa23db50edf53f6b84ceea5fe8b8d2a82a5ceb8307c2af8ae6e25f3f92ac2f','Activo',2),(9,'Produccion','Produccion','$2b$12$XtkZmMMny6a/hsit0k4WJuQgoK0C7MZhx03SDfRg3Gn52GtbBkU8.','31823aa23a1285b6c3f0c4f88c306f2a1969e087f3bee7b9b9f9c09a0e2148e7','Activo',4);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ventas`
--

DROP TABLE IF EXISTS `ventas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ventas` (
  `id_venta` int NOT NULL AUTO_INCREMENT,
  `folio` varchar(20) DEFAULT NULL,
  `id_usuario` int DEFAULT NULL,
  `fecha_venta` datetime DEFAULT (now()),
  `fecha_entrega_estimada` varchar(5) DEFAULT NULL,
  `total_bruto` decimal(10,2) DEFAULT NULL,
  `total_utilidad` decimal(10,2) DEFAULT NULL,
  `id_direccion` int DEFAULT NULL,
  `direccion_envio_texto` text,
  `id_cliente_vendido` int DEFAULT NULL,
  `id_corte` int DEFAULT NULL,
  `rastreo` varchar(50) DEFAULT NULL,
  `status` int DEFAULT NULL,
  PRIMARY KEY (`id_venta`),
  UNIQUE KEY `folio` (`folio`),
  KEY `id_cliente_vendido` (`id_cliente_vendido`),
  KEY `id_corte` (`id_corte`),
  KEY `id_direccion` (`id_direccion`),
  KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `ventas_ibfk_1` FOREIGN KEY (`id_cliente_vendido`) REFERENCES `clientes` (`id_cliente`),
  CONSTRAINT `ventas_ibfk_2` FOREIGN KEY (`id_corte`) REFERENCES `cortes_cajas` (`id_corte`),
  CONSTRAINT `ventas_ibfk_3` FOREIGN KEY (`id_direccion`) REFERENCES `direcciones` (`id_direccion`),
  CONSTRAINT `ventas_ibfk_4` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ventas`
--

LOCK TABLES `ventas` WRITE;
/*!40000 ALTER TABLE `ventas` DISABLE KEYS */;
INSERT INTO `ventas` VALUES (2,'C8CF4444',6,'2026-04-13 18:00:30',NULL,104.40,NULL,1,'Joyas #50 col. Leon 2, Salamanca, 34600',3,NULL,NULL,4),(6,'606EC1E3',4,'2026-04-13 19:05:45',NULL,42.92,NULL,NULL,NULL,1,1,NULL,5),(9,'C61C42C1',6,'2026-04-13 20:20:10',NULL,464.00,NULL,1,'Joyas #50 col. Leon 2, Salamanca, 34600',3,NULL,NULL,4);
/*!40000 ALTER TABLE `ventas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ventas_pagos`
--

DROP TABLE IF EXISTS `ventas_pagos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ventas_pagos` (
  `id_pago` int NOT NULL AUTO_INCREMENT,
  `id_venta` int NOT NULL,
  `metodo_pago` int NOT NULL,
  `monto_pagado` decimal(10,2) NOT NULL,
  `referencia_pago` varchar(100) DEFAULT NULL,
  `fecha_pago` datetime DEFAULT (now()),
  PRIMARY KEY (`id_pago`),
  KEY `id_venta` (`id_venta`),
  CONSTRAINT `ventas_pagos_ibfk_1` FOREIGN KEY (`id_venta`) REFERENCES `ventas` (`id_venta`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ventas_pagos`
--

LOCK TABLES `ventas_pagos` WRITE;
/*!40000 ALTER TABLE `ventas_pagos` DISABLE KEYS */;
INSERT INTO `ventas_pagos` VALUES (1,2,3,104.40,'**** 1123','2026-04-13 18:00:31'),(2,6,1,42.92,NULL,'2026-04-13 19:05:46'),(3,9,3,464.00,'**** 2121','2026-04-13 20:20:10');
/*!40000 ALTER TABLE `ventas_pagos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'crystalcontrol'
--

--
-- Dumping routines for database 'crystalcontrol'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-15  0:03:01
