import mysql.connector
from mysql.connector import Error

class DatabaseConnection:
    def __init__(self):
        self.host = 'localhost'
        self.database = 'inventario_libreria'  # o 'desarrollo_web' como prefieras
        self.user = 'root'
        self.password = ''  # Cambia por tu contraseña de MySQL
        
    def get_connection(self):
        """Crear y retornar una conexión a la base de datos"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return None
    
    def test_connection(self):
        """Probar la conexión a la base de datos"""
        try:
            connection = self.get_connection()
            if connection and connection.is_connected():
                db_info = connection.get_server_info()
                cursor = connection.cursor()
                cursor.execute("SELECT DATABASE();")
                database_name = cursor.fetchone()
                cursor.close()
                connection.close()
                return {
                    'status': 'success',
                    'message': f'Conectado exitosamente a MySQL Server versión {db_info}',
                    'database': database_name[0] if database_name else 'No seleccionada'
                }
        except Error as e:
            return {
                'status': 'error',
                'message': f'Error al conectar: {e}'
            }
        
    def create_tables(self):
        """Crear las tablas necesarias si no existen"""
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                
                # Tabla usuarios (requerida por la tarea)
                create_usuarios = """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    mail VARCHAR(100) UNIQUE NOT NULL,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                
                # Tabla categorias para el proyecto
                create_categorias = """
                CREATE TABLE IF NOT EXISTS categorias (
                    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
                    nombre_categoria VARCHAR(50) NOT NULL,
                    descripcion TEXT
                )
                """
                
                # Tabla libros para el inventario
                create_libros = """
                CREATE TABLE IF NOT EXISTS libros (
                    id_libro INT AUTO_INCREMENT PRIMARY KEY,
                    titulo VARCHAR(200) NOT NULL,
                    autor VARCHAR(150) NOT NULL,
                    isbn VARCHAR(13) UNIQUE,
                    id_categoria INT,
                    precio DECIMAL(10,2),
                    stock INT DEFAULT 0,
                    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
                )
                """
                
                cursor.execute(create_usuarios)
                cursor.execute(create_categorias) 
                cursor.execute(create_libros)
                
                connection.commit()
                print("Tablas creadas exitosamente")
                
            except Error as e:
                print(f"Error al crear tablas: {e}")
            finally:
                cursor.close()
                connection.close()