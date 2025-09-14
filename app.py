from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
# Cambiar sqlite3 por mysql.connector
import mysql.connector
from mysql.connector import Error
import os
import json
import csv
from datetime import datetime
from io import StringIO, BytesIO

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_muy_segura_2024'

# NUEVA CONFIGURACIÓN PARA MYSQL (reemplaza la configuración SQLite)
# Configuración de MySQL 
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'inventario_libreria',  # o 'desarrollo_web' como prefieras
    'user': 'root',
    'password': '2004'  
}

# Configuración de archivos (mantener igual)
DATA_DIR = 'datos'
TXT_FILE = os.path.join(DATA_DIR, 'datos.txt')
JSON_FILE = os.path.join(DATA_DIR, 'datos.json')
CSV_FILE = os.path.join(DATA_DIR, 'datos.csv')

def ensure_data_directory():
    """Crear directorio de datos si no existe"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

# NUEVAS FUNCIONES PARA MYSQL
def get_mysql_connection():
    """Obtiene una conexión a MySQL"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

def init_db():
    """Inicializa la base de datos MySQL con las tablas necesarias"""
    connection = get_mysql_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Crear tabla usuarios (REQUERIDA por la tarea)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    mail VARCHAR(100) UNIQUE NOT NULL,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Crear tabla categorías
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categorias (
                    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
                    nombre_categoria VARCHAR(50) NOT NULL,
                    descripcion TEXT
                )
            ''')
            
            # Crear tabla productos (adaptada para MySQL)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS productos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(200) NOT NULL UNIQUE,
                    descripcion TEXT,
                    cantidad INT NOT NULL DEFAULT 0,
                    precio DECIMAL(10,2) NOT NULL DEFAULT 0,
                    categoria VARCHAR(100) NOT NULL DEFAULT 'General',
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            connection.commit()
            print("Tablas creadas exitosamente")
            
        except Error as e:
            print(f"Error al crear tablas: {e}")
        finally:
            cursor.close()
            connection.close()

# RUTA REQUERIDA PARA LA TAREA
@app.route('/test_db')
def test_database():
    """Ruta para probar la conexión a la base de datos MySQL"""
    try:
        connection = get_mysql_connection()
        if connection and connection.is_connected():
            db_info = connection.get_server_info()
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            database_name = cursor.fetchone()
            cursor.close()
            connection.close()
            
            return jsonify({
                'status': 'success',
                'message': f'Conectado exitosamente a MySQL Server versión {db_info}',
                'database': database_name[0] if database_name else 'No seleccionada'
            })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al conectar: {e}'
        })

def get_all_products():
    """Obtiene todos los productos de la base de datos MySQL"""
    connection = get_mysql_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM productos ORDER BY id DESC')
            products = cursor.fetchall()
            return products
        except Error as e:
            print(f"Error al obtener productos: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    return []

def get_product_by_id(product_id):
    """Obtiene un producto por su ID"""
    connection = get_mysql_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM productos WHERE id = %s', (product_id,))
            product = cursor.fetchone()
            return product
        except Error as e:
            print(f"Error al obtener producto: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    return None

def product_exists_by_name(name, exclude_id=None):
    """Verifica si existe un producto con el mismo nombre"""
    connection = get_mysql_connection()
    if connection:
        try:
            cursor = connection.cursor()
            if exclude_id:
                cursor.execute('SELECT id FROM productos WHERE LOWER(nombre) = LOWER(%s) AND id != %s', (name, exclude_id))
            else:
                cursor.execute('SELECT id FROM productos WHERE LOWER(nombre) = LOWER(%s)', (name,))
            result = cursor.fetchone()
            return result is not None
        except Error as e:
            print(f"Error al verificar producto: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    return False

def search_products(term, search_type='nombre'):
    """Busca productos por nombre o categoría"""
    connection = get_mysql_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            if search_type == 'nombre':
                cursor.execute('''
                    SELECT * FROM productos 
                    WHERE LOWER(nombre) LIKE LOWER(%s) OR LOWER(descripcion) LIKE LOWER(%s)
                    ORDER BY nombre
                ''', (f'%{term}%', f'%{term}%'))
            elif search_type == 'categoria':
                cursor.execute('''
                    SELECT * FROM productos 
                    WHERE LOWER(categoria) LIKE LOWER(%s)
                    ORDER BY nombre
                ''', (f'%{term}%',))
            else:
                return []
            
            products = cursor.fetchall()
            return products
        except Error as e:
            print(f"Error en búsqueda: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    return []

def get_categories():
    """Obtiene todas las categorías únicas"""
    connection = get_mysql_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT DISTINCT categoria FROM productos 
                WHERE categoria IS NOT NULL AND categoria != ''
                ORDER BY categoria
            ''')
            categories = cursor.fetchall()
            return [cat[0] for cat in categories]
        except Error as e:
            print(f"Error al obtener categorías: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    return []

def get_stats():
    """Obtiene estadísticas del inventario"""
    connection = get_mysql_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM productos')
            total_products = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(cantidad * precio) FROM productos')
            total_value = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM productos WHERE cantidad < 10')
            low_stock = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT categoria) FROM productos')
            categories_count = cursor.fetchone()[0]
            
            return {
                'total_products': total_products or 0,
                'total_value': float(total_value) if total_value else 0,
                'low_stock': low_stock or 0,
                'categories': categories_count or 0
            }
        except Error as e:
            print(f"Error al obtener estadísticas: {e}")
            return {'total_products': 0, 'total_value': 0, 'low_stock': 0, 'categories': 0}
        finally:
            cursor.close()
            connection.close()
    return {'total_products': 0, 'total_value': 0, 'low_stock': 0, 'categories': 0}

# NUEVAS FUNCIONES PARA GESTIÓN DE USUARIOS (requerido por la tarea)
@app.route('/usuarios')
def usuarios():
    """Mostrar lista de usuarios"""
    connection = get_mysql_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM usuarios ORDER BY fecha_registro DESC')
            usuarios = cursor.fetchall()
            return render_template('usuarios.html', usuarios=usuarios)
        except Error as e:
            flash(f'Error al obtener usuarios: {e}', 'error')
            return render_template('usuarios.html', usuarios=[])
        finally:
            cursor.close()
            connection.close()
    return render_template('usuarios.html', usuarios=[])

@app.route('/usuarios/agregar', methods=['POST'])
def agregar_usuario():
    """Agregar nuevo usuario"""
    nombre = request.form['nombre']
    mail = request.form['mail']  # Usar 'mail' como requiere la tarea
    
    connection = get_mysql_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('INSERT INTO usuarios (nombre, mail) VALUES (%s, %s)', (nombre, mail))
            connection.commit()
            flash('Usuario agregado exitosamente', 'success')
        except Error as e:
            flash(f'Error al agregar usuario: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('usuarios'))

# Funciones para manejo de archivos (mantener igual pero adaptar para MySQL)
def export_to_txt():
    """Exporta todos los productos a archivo TXT"""
    products = get_all_products()
    ensure_data_directory()
    
    with open(TXT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Sistema de Inventario - Datos de Ejemplo\n")
        f.write("# Formato: ID|Nombre|Descripcion|Cantidad|Precio|Categoria|Fecha_Creacion\n\n")
        
        for product in products:
            descripcion = product['descripcion'] or ''
            line = str(product['id']) + '|' + product['nombre'] + '|' + descripcion + '|' + str(product['cantidad']) + '|' + str(product['precio']) + '|' + product['categoria'] + '|' + str(product['fecha_creacion']) + '\n'
            f.write(line)

def export_to_json():
    """Exporta todos los productos a archivo JSON"""
    products = get_all_products()
    categories = get_categories()
    ensure_data_directory()
    
    # Convertir datetime objects a string para JSON
    for product in products:
        if 'fecha_creacion' in product and product['fecha_creacion']:
            product['fecha_creacion'] = str(product['fecha_creacion'])
        if 'fecha_actualizacion' in product and product['fecha_actualizacion']:
            product['fecha_actualizacion'] = str(product['fecha_actualizacion'])
    
    data = {
        "productos": products,
        "metadata": {
            "version": "1.0",
            "fecha_exportacion": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_productos": len(products),
            "categorias": categories
        }
    }
    
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def export_to_csv():
    """Exporta todos los productos a archivo CSV"""
    products = get_all_products()
    ensure_data_directory()
    
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        if products:
            fieldnames = ['id', 'nombre', 'descripcion', 'cantidad', 'precio', 'categoria', 'fecha_creacion', 'fecha_actualizacion']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in products:
                # Convertir datetime a string para CSV
                product_dict = dict(product)
                if 'fecha_creacion' in product_dict and product_dict['fecha_creacion']:
                    product_dict['fecha_creacion'] = str(product_dict['fecha_creacion'])
                if 'fecha_actualizacion' in product_dict and product_dict['fecha_actualizacion']:
                    product_dict['fecha_actualizacion'] = str(product_dict['fecha_actualizacion'])
                writer.writerow(product_dict)

def import_from_csv(file_path):
    """Importa productos desde archivo CSV"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            imported_count = 0
            
            connection = get_mysql_connection()
            if connection:
                cursor = connection.cursor()
                for row in reader:
                    # Verificar si el producto ya existe
                    if not product_exists_by_name(row['nombre']):
                        cursor.execute('''
                            INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
                            VALUES (%s, %s, %s, %s, %s)
                        ''', (
                            row['nombre'],
                            row['descripcion'],
                            int(row['cantidad']),
                            float(row['precio']),
                            row['categoria']
                        ))
                        imported_count += 1
                
                connection.commit()
                cursor.close()
                connection.close()
            
            return imported_count
    except Exception as e:
        raise Exception("Error al importar CSV: " + str(e))

def import_from_json(file_path):
    """Importa productos desde archivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            imported_count = 0
            
            connection = get_mysql_connection()
            if connection:
                cursor = connection.cursor()
                for product in data.get('productos', []):
                    # Verificar si el producto ya existe
                    if not product_exists_by_name(product['nombre']):
                        cursor.execute('''
                            INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
                            VALUES (%s, %s, %s, %s, %s)
                        ''', (
                            product['nombre'],
                            product.get('descripcion', ''),
                            int(product['cantidad']),
                            float(product['precio']),
                            product['categoria']
                        ))
                        imported_count += 1
                
                connection.commit()
                cursor.close()
                connection.close()
            
            return imported_count
    except Exception as e:
        raise Exception("Error al importar JSON: " + str(e))

# Todas las demás rutas mantienen su lógica pero adaptadas para MySQL
@app.route('/')
def index():
    """Página principal con estadísticas"""
    stats = get_stats()
    recent_products = get_all_products()[:5]  # Últimos 5 productos
    return render_template('index.html', stats=stats, recent_products=recent_products)

@app.route('/inventario')
def inventario():
    """Página del inventario completo"""
    products = get_all_products()
    categories = get_categories()
    return render_template('inventario.html', products=products, categories=categories)

@app.route('/producto/nuevo', methods=['GET', 'POST'])
def nuevo_producto():
    """Crear un nuevo producto"""
    if request.method == 'POST':
        try:
            nombre = request.form['nombre'].strip()
            descripcion = request.form.get('descripcion', '').strip()
            cantidad = int(request.form['cantidad'])
            precio = float(request.form['precio'])
            categoria = request.form['categoria'].strip() or 'General'
            
            # Validaciones
            if not nombre:
                flash('El nombre del producto es obligatorio', 'error')
                return render_template('producto_form.html', categories=get_categories())
            
            if product_exists_by_name(nombre):
                flash('Ya existe un producto con ese nombre', 'error')
                return render_template('producto_form.html', categories=get_categories())
            
            if cantidad < 0:
                flash('La cantidad no puede ser negativa', 'error')
                return render_template('producto_form.html', categories=get_categories())
            
            if precio < 0:
                flash('El precio no puede ser negativo', 'error')
                return render_template('producto_form.html', categories=get_categories())
            
            # Guardar en base de datos MySQL
            connection = get_mysql_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute('''
                    INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (nombre, descripcion, cantidad, precio, categoria))
                connection.commit()
                cursor.close()
                connection.close()
            
            # Actualizar archivos de datos
            export_to_txt()
            export_to_json()
            export_to_csv()
            
            flash('Producto creado exitosamente', 'success')
            return redirect(url_for('inventario'))
            
        except ValueError:
            flash('Por favor ingrese valores numéricos válidos', 'error')
        except Exception as e:
            flash('Error al crear el producto: ' + str(e), 'error')
    
    categories = get_categories()
    return render_template('producto_form.html', categories=categories)

@app.route('/producto/<int:product_id>/editar', methods=['GET', 'POST'])
def editar_producto(product_id):
    """Editar un producto existente"""
    product = get_product_by_id(product_id)
    
    if not product:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('inventario'))
    
    if request.method == 'POST':
        try:
            nombre = request.form['nombre'].strip()
            descripcion = request.form.get('descripcion', '').strip()
            cantidad = int(request.form['cantidad'])
            precio = float(request.form['precio'])
            categoria = request.form['categoria'].strip() or 'General'
            
            # Validaciones
            if not nombre:
                flash('El nombre del producto es obligatorio', 'error')
                return render_template('producto_form.html', product=product, categories=get_categories())
            
            if product_exists_by_name(nombre, product_id):
                flash('Ya existe otro producto con ese nombre', 'error')
                return render_template('producto_form.html', product=product, categories=get_categories())
            
            if cantidad < 0:
                flash('La cantidad no puede ser negativa', 'error')
                return render_template('producto_form.html', product=product, categories=get_categories())
            
            if precio < 0:
                flash('El precio no puede ser negativo', 'error')
                return render_template('producto_form.html', product=product, categories=get_categories())
            
            # Actualizar en base de datos MySQL
            connection = get_mysql_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute('''
                    UPDATE productos 
                    SET nombre=%s, descripcion=%s, cantidad=%s, precio=%s, categoria=%s
                    WHERE id=%s
                ''', (nombre, descripcion, cantidad, precio, categoria, product_id))
                connection.commit()
                cursor.close()
                connection.close()
            
            # Actualizar archivos de datos
            export_to_txt()
            export_to_json()
            export_to_csv()
            
            flash('Producto actualizado exitosamente', 'success')
            return redirect(url_for('inventario'))
            
        except ValueError:
            flash('Por favor ingrese valores numéricos válidos', 'error')
        except Exception as e:
            flash('Error al actualizar el producto: ' + str(e), 'error')
    
    categories = get_categories()
    return render_template('producto_form.html', product=product, categories=categories)

@app.route('/producto/<int:product_id>/eliminar', methods=['POST'])
def eliminar_producto(product_id):
    """Eliminar un producto"""
    try:
        product = get_product_by_id(product_id)
        
        if not product:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('inventario'))
        
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute('DELETE FROM productos WHERE id = %s', (product_id,))
            connection.commit()
            cursor.close()
            connection.close()
        
        # Actualizar archivos de datos
        export_to_txt()
        export_to_json()
        export_to_csv()
        
        flash('Producto eliminado exitosamente', 'success')
        
    except Exception as e:
        flash('Error al eliminar el producto: ' + str(e), 'error')
    
    return redirect(url_for('inventario'))

@app.route('/buscar')
def buscar():
    """Página de búsqueda"""
    term = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'nombre')
    results = []
    
    if term:
        results = search_products(term, search_type)
    
    categories = get_categories()
    return render_template('buscar.html', 
                         results=results, 
                         term=term, 
                         search_type=search_type,
                         categories=categories)

@app.route('/producto/<int:product_id>')
def ver_producto(product_id):
    """Ver detalles de un producto"""
    product = get_product_by_id(product_id)
    
    if not product:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('inventario'))
    
    return render_template('producto_detalle.html', product=product)

# NUEVAS RUTAS PARA MANEJO DE ARCHIVOS (mantener las mismas rutas)
@app.route('/datos')
def datos_panel():
    """Panel de gestión de datos"""
    stats = get_stats()
    
    # Verificar existencia de archivos
    files_info = {
        'txt': os.path.exists(TXT_FILE),
        'json': os.path.exists(JSON_FILE),
        'csv': os.path.exists(CSV_FILE)
    }
    
    return render_template('datos_panel.html', stats=stats, files_info=files_info)

@app.route('/exportar/<formato>')
def exportar_datos(formato):
    """Exportar datos en diferentes formatos"""
    try:
        if formato == 'txt':
            export_to_txt()
            return send_file(TXT_FILE, as_attachment=True, download_name='inventario.txt')
        
        elif formato == 'json':
            export_to_json()
            return send_file(JSON_FILE, as_attachment=True, download_name='inventario.json')
        
        elif formato == 'csv':
            export_to_csv()
            return send_file(CSV_FILE, as_attachment=True, download_name='inventario.csv')
        
        else:
            flash('Formato no válido', 'error')
            return redirect(url_for('datos_panel'))
    
    except Exception as e:
        flash('Error al exportar datos: ' + str(e), 'error')
        return redirect(url_for('datos_panel'))

@app.route('/importar', methods=['GET', 'POST'])
def importar_datos():
    """Importar datos desde archivos"""
    if request.method == 'POST':
        if 'archivo' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('datos_panel'))
        
        file = request.files['archivo']
        
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('datos_panel'))
        
        if file:
            try:
                filename = file.filename.lower()
                
                # Crear directorio temporal
                temp_path = os.path.join(DATA_DIR, 'temp_import_' + filename)
                file.save(temp_path)
                
                imported_count = 0
                
                if filename.endswith('.csv'):
                    imported_count = import_from_csv(temp_path)
                elif filename.endswith('.json'):
                    imported_count = import_from_json(temp_path)
                else:
                    flash('Formato de archivo no soportado. Use CSV o JSON.', 'error')
                    os.remove(temp_path)
                    return redirect(url_for('datos_panel'))
                
                # Limpiar archivo temporal
                os.remove(temp_path)
                
                if imported_count > 0:
                    # Actualizar todos los archivos de datos
                    export_to_txt()
                    export_to_json()
                    export_to_csv()
                    
                    flash('Se importaron ' + str(imported_count) + ' productos exitosamente', 'success')
                else:
                    flash('No se importaron productos (posiblemente ya existen)', 'warning')
                
            except Exception as e:
                flash('Error al importar datos: ' + str(e), 'error')
                # Limpiar archivo temporal si existe
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
    
    return redirect(url_for('datos_panel'))

@app.route('/sincronizar')
def sincronizar_datos():
    """Sincronizar todos los archivos de datos con la base de datos"""
    try:
        export_to_txt()
        export_to_json()
        export_to_csv()
        flash('Archivos de datos sincronizados exitosamente', 'success')
    except Exception as e:
        flash('Error al sincronizar datos: ' + str(e), 'error')
    
    return redirect(url_for('datos_panel'))

@app.route('/api/stats')
def api_stats():
    """API para obtener estadísticas en formato JSON"""
    return jsonify(get_stats())

@app.route('/api/productos')
def api_productos():
    """API para obtener todos los productos en formato JSON"""
    products = get_all_products()
    return jsonify(products)

@app.route('/api/exportar/<formato>')
def api_exportar(formato):
    """API para exportar datos programáticamente"""
    try:
        if formato == 'json':
            export_to_json()
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        
        elif formato == 'csv':
            export_to_csv()
            output = StringIO()
            products = get_all_products()
            
            if products:
                fieldnames = ['id', 'nombre', 'descripcion', 'cantidad', 'precio', 'categoria', 'fecha_creacion', 'fecha_actualizacion']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for product in products:
                    # Convertir datetime a string
                    product_dict = dict(product)
                    if 'fecha_creacion' in product_dict and product_dict['fecha_creacion']:
                        product_dict['fecha_creacion'] = str(product_dict['fecha_creacion'])
                    if 'fecha_actualizacion' in product_dict and product_dict['fecha_actualizacion']:
                        product_dict['fecha_actualizacion'] = str(product_dict['fecha_actualizacion'])
                    writer.writerow(product_dict)
            
            response = make_response(output.getvalue())
            response.headers["Content-Disposition"] = "attachment; filename=inventario.csv"
            response.headers["Content-type"] = "text/csv"
            return response
        
        else:
            return jsonify({"error": "Formato no válido"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Filtros personalizados para Jinja2
@app.template_filter('currency')
def currency_filter(amount):
    """Filtro para formatear moneda"""
    return "${:,.2f}".format(amount)

@app.template_filter('datetime')
def datetime_filter(date_string):
    """Filtro para formatear fecha"""
    if date_string:
        try:
            if isinstance(date_string, str):
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                dt = date_string
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return str(date_string)
    return ''

# Manejo de errores
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Crear directorios necesarios
    ensure_data_directory()
    
    # Inicializar base de datos MySQL
    init_db()
    
    # Crear archivos de datos iniciales si no existen
    if get_all_products():
        export_to_txt()
        export_to_json()
        export_to_csv()
    
    # Ejecutar aplicación
    app.run(debug=True, host='0.0.0.0', port=5000)