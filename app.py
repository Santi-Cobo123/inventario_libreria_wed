from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
import sqlite3
import os
import json
import csv
from datetime import datetime
from io import StringIO, BytesIO

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_muy_segura_2024'

# Configuración de la base de datos y archivos
DATABASE = 'inventario.db'
DATA_DIR = 'datos'
TXT_FILE = os.path.join(DATA_DIR, 'datos.txt')
JSON_FILE = os.path.join(DATA_DIR, 'datos.json')
CSV_FILE = os.path.join(DATA_DIR, 'datos.csv')

def ensure_data_directory():
    """Crear directorio de datos si no existe"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                cantidad INTEGER NOT NULL DEFAULT 0,
                precio REAL NOT NULL DEFAULT 0,
                categoria TEXT NOT NULL DEFAULT 'General',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_products():
    """Obtiene todos los productos de la base de datos"""
    with get_db_connection() as conn:
        products = conn.execute('''
            SELECT * FROM productos ORDER BY id DESC
        ''').fetchall()
    return products

def get_product_by_id(product_id):
    """Obtiene un producto por su ID"""
    with get_db_connection() as conn:
        product = conn.execute('''
            SELECT * FROM productos WHERE id = ?
        ''', (product_id,)).fetchone()
    return product

def product_exists_by_name(name, exclude_id=None):
    """Verifica si existe un producto con el mismo nombre"""
    with get_db_connection() as conn:
        if exclude_id:
            result = conn.execute('''
                SELECT id FROM productos WHERE LOWER(nombre) = LOWER(?) AND id != ?
            ''', (name, exclude_id)).fetchone()
        else:
            result = conn.execute('''
                SELECT id FROM productos WHERE LOWER(nombre) = LOWER(?)
            ''', (name,)).fetchone()
    return result is not None

def search_products(term, search_type='nombre'):
    """Busca productos por nombre o categoría"""
    with get_db_connection() as conn:
        if search_type == 'nombre':
            products = conn.execute('''
                SELECT * FROM productos 
                WHERE LOWER(nombre) LIKE LOWER(?) OR LOWER(descripcion) LIKE LOWER(?)
                ORDER BY nombre
            ''', ('%' + term + '%', '%' + term + '%')).fetchall()
        elif search_type == 'categoria':
            products = conn.execute('''
                SELECT * FROM productos 
                WHERE LOWER(categoria) LIKE LOWER(?)
                ORDER BY nombre
            ''', ('%' + term + '%',)).fetchall()
        else:
            products = []
    return products

def get_categories():
    """Obtiene todas las categorías únicas"""
    with get_db_connection() as conn:
        categories = conn.execute('''
            SELECT DISTINCT categoria FROM productos 
            WHERE categoria IS NOT NULL AND categoria != ''
            ORDER BY categoria
        ''').fetchall()
    return [cat['categoria'] for cat in categories]

def get_stats():
    """Obtiene estadísticas del inventario"""
    with get_db_connection() as conn:
        total_products = conn.execute('SELECT COUNT(*) as count FROM productos').fetchone()['count']
        total_value = conn.execute('SELECT SUM(cantidad * precio) as total FROM productos').fetchone()['total']
        low_stock = conn.execute('SELECT COUNT(*) as count FROM productos WHERE cantidad < 10').fetchone()['count']
        categories_count = conn.execute('SELECT COUNT(DISTINCT categoria) as count FROM productos').fetchone()['count']
    
    return {
        'total_products': total_products,
        'total_value': total_value if total_value else 0,
        'low_stock': low_stock,
        'categories': categories_count
    }

# Funciones para manejo de archivos
def export_to_txt():
    """Exporta todos los productos a archivo TXT"""
    products = get_all_products()
    ensure_data_directory()
    
    with open(TXT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Sistema de Inventario - Datos de Ejemplo\n")
        f.write("# Formato: ID|Nombre|Descripcion|Cantidad|Precio|Categoria|Fecha_Creacion\n\n")
        
        for product in products:
            descripcion = product['descripcion'] or ''
            line = str(product['id']) + '|' + product['nombre'] + '|' + descripcion + '|' + str(product['cantidad']) + '|' + str(product['precio']) + '|' + product['categoria'] + '|' + product['fecha_creacion'] + '\n'
            f.write(line)

def export_to_json():
    """Exporta todos los productos a archivo JSON"""
    products = get_all_products()
    categories = get_categories()
    ensure_data_directory()
    
    data = {
        "productos": [dict(product) for product in products],
        "metadata": {
            "version": "1.0",
            "fecha_exportacion": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_productos": len(products),
            "categorias": categories
        }
    }
    
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
                writer.writerow(dict(product))

def import_from_csv(file_path):
    """Importa productos desde archivo CSV"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            imported_count = 0
            
            with get_db_connection() as conn:
                for row in reader:
                    # Verificar si el producto ya existe
                    if not product_exists_by_name(row['nombre']):
                        conn.execute('''
                            INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            row['nombre'],
                            row['descripcion'],
                            int(row['cantidad']),
                            float(row['precio']),
                            row['categoria']
                        ))
                        imported_count += 1
                
                conn.commit()
            
            return imported_count
    except Exception as e:
        raise Exception("Error al importar CSV: " + str(e))

def import_from_json(file_path):
    """Importa productos desde archivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            imported_count = 0
            
            with get_db_connection() as conn:
                for product in data.get('productos', []):
                    # Verificar si el producto ya existe
                    if not product_exists_by_name(product['nombre']):
                        conn.execute('''
                            INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            product['nombre'],
                            product.get('descripcion', ''),
                            int(product['cantidad']),
                            float(product['precio']),
                            product['categoria']
                        ))
                        imported_count += 1
                
                conn.commit()
            
            return imported_count
    except Exception as e:
        raise Exception("Error al importar JSON: " + str(e))

# Rutas de la aplicación
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
            
            # Guardar en base de datos
            with get_db_connection() as conn:
                conn.execute('''
                    INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
                    VALUES (?, ?, ?, ?, ?)
                ''', (nombre, descripcion, cantidad, precio, categoria))
                conn.commit()
            
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
            
            # Actualizar en base de datos
            with get_db_connection() as conn:
                conn.execute('''
                    UPDATE productos 
                    SET nombre=?, descripcion=?, cantidad=?, precio=?, categoria=?, fecha_actualizacion=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (nombre, descripcion, cantidad, precio, categoria, product_id))
                conn.commit()
            
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
        
        with get_db_connection() as conn:
            conn.execute('DELETE FROM productos WHERE id = ?', (product_id,))
            conn.commit()
        
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

# NUEVAS RUTAS PARA MANEJO DE ARCHIVOS

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
    return jsonify([dict(product) for product in products])

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
                    writer.writerow(dict(product))
            
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
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return date_string
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
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE)) if os.path.dirname(DATABASE) else '.', exist_ok=True)
    ensure_data_directory()
    
    # Inicializar base de datos
    init_db()
    
    # Crear archivos de datos iniciales si no existen
    if get_all_products():
        export_to_txt()
        export_to_json()
        export_to_csv()
    
    # Ejecutar aplicación
    app.run(debug=True, host='0.0.0.0', port=5000)