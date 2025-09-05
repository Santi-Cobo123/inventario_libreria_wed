#!/usr/bin/env python3
"""
Script para poblar la base de datos con productos de ejemplo
Ejecutar: python populate_database.py
"""

import sqlite3
import os
from datetime import datetime

# Configuración de la base de datos
DATABASE = 'inventario.db'

def init_db():
    """Inicializa la base de datos si no existe"""
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

def clear_products():
    """Limpia todos los productos existentes"""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('DELETE FROM productos')
        conn.commit()
        print("🗑️  Base de datos limpiada")

def add_sample_products():
    """Agrega productos de ejemplo"""
    productos_ejemplo = [
        # Electrónicos
        ("Laptop Dell Inspiron 15", "Laptop para uso profesional con procesador Intel Core i5", 15, 750.00, "Electrónicos"),
        ("iPhone 14 Pro", "Smartphone Apple con cámara de 48MP y pantalla Super Retina XDR", 8, 1200.00, "Electrónicos"),
        ("Samsung Galaxy S24", "Teléfono Android con pantalla AMOLED de 6.1 pulgadas", 12, 899.99, "Electrónicos"),
        ("iPad Air 10.9", "Tablet Apple con chip M1 y pantalla Liquid Retina", 6, 650.00, "Electrónicos"),
        ("MacBook Pro 14", "Laptop Apple con chip M3 Pro para profesionales", 4, 2399.00, "Electrónicos"),
        ("AirPods Pro 2", "Auriculares inalámbricos con cancelación de ruido", 25, 249.99, "Electrónicos"),
        ("Apple Watch Series 9", "Reloj inteligente con GPS y monitor de salud", 10, 429.00, "Electrónicos"),
        ("Nintendo Switch OLED", "Consola de videojuegos portátil con pantalla OLED", 7, 349.99, "Electrónicos"),
        
        # Hogar y Decoración
        ("Sofá 3 Plazas Moderno", "Sofá cómodo de tela gris con patas de madera", 3, 899.00, "Hogar"),
        ("Mesa de Comedor Redonda", "Mesa de madera maciza para 6 personas", 2, 550.00, "Hogar"),
        ("Lámpara de Pie LED", "Lámpara moderna con regulador de intensidad", 8, 125.00, "Hogar"),
        ("Espejo Decorativo Grande", "Espejo de pared con marco dorado de 120cm", 5, 89.99, "Hogar"),
        ("Cojines Decorativos Set", "Set de 4 cojines de diferentes texturas y colores", 20, 45.00, "Hogar"),
        ("Cortinas Blackout", "Cortinas que bloquean la luz, ideales para dormitorios", 15, 75.00, "Hogar"),
        
        # Ropa y Accesorios
        ("Jeans Levis 501 Original", "Jeans clásicos de mezclilla azul, talla variada", 30, 89.99, "Ropa"),
        ("Camiseta Nike Dri-FIT", "Camiseta deportiva de alta tecnología", 45, 29.99, "Ropa"),
        ("Zapatillas Adidas Ultraboost", "Zapatillas para running con tecnología Boost", 18, 180.00, "Ropa"),
        ("Chaqueta North Face", "Chaqueta impermeable para actividades al aire libre", 12, 199.99, "Ropa"),
        ("Bolso Michael Kors", "Bolso de mano de cuero genuino color negro", 6, 285.00, "Ropa"),
        ("Reloj Casio G-Shock", "Reloj deportivo resistente al agua y golpes", 14, 120.00, "Ropa"),
        
        # Libros y Educación
        ("Python Programming 4th Ed", "Libro completo para aprender programación en Python", 25, 49.99, "Libros"),
        ("Cien Años de Soledad", "Novela clásica de Gabriel García Márquez", 18, 15.99, "Libros"),
        ("Curso de JavaScript Completo", "Manual paso a paso para desarrollo web", 20, 39.99, "Libros"),
        ("Atlas Mundial 2024", "Atlas geográfico actualizado con mapas detallados", 10, 65.00, "Libros"),
        ("Diccionario Inglés-Español", "Diccionario completo con más de 50,000 entradas", 15, 28.99, "Libros"),
        
        # Deportes y Fitness
        ("Bicicleta Mountain Bike", "Bicicleta todo terreno con 21 velocidades", 5, 450.00, "Deportes"),
        ("Set de Pesas Ajustables", "Pesas de 2kg a 20kg con barra y discos", 8, 189.99, "Deportes"),
        ("Pelota de Fútbol FIFA", "Pelota oficial para competencias profesionales", 22, 35.00, "Deportes"),
        ("Esterilla de Yoga Premium", "Esterilla antideslizante de 6mm de grosor", 30, 45.00, "Deportes"),
        ("Raqueta de Tenis Wilson", "Raqueta profesional con grip cómodo", 9, 125.00, "Deportes"),
        
        # Cocina y Electrodomésticos  
        ("Licuadora Vitamix A3500", "Licuadora de alta potencia con 5 programas", 4, 595.00, "Cocina"),
        ("Cafetera Nespresso", "Máquina de café expreso con sistema de cápsulas", 12, 199.00, "Cocina"),
        ("Sartén Antiadherente 28cm", "Sartén premium con recubrimiento cerámico", 16, 75.00, "Cocina"),
        ("Batidora KitchenAid", "Batidora de pie profesional con múltiples accesorios", 3, 449.99, "Cocina"),
        ("Juego de Cuchillos", "Set de 8 cuchillos profesionales con block de madera", 7, 159.99, "Cocina"),
        
        # Oficina y Papelería
        ("Silla Ergonómica Oficina", "Silla con soporte lumbar y reposabrazos ajustables", 11, 289.00, "Oficina"),
        ("Escritorio de Madera", "Escritorio ejecutivo con 3 cajones y acabado premium", 4, 399.99, "Oficina"),
        ("Monitor 4K 27 pulgadas", "Monitor profesional para diseño gráfico", 6, 349.99, "Oficina"),
        ("Impresora HP LaserJet", "Impresora láser monocromática para oficina", 8, 199.00, "Oficina"),
        ("Pack Cuadernos Moleskine", "Set de 3 cuadernos de tapa dura rayados", 25, 45.00, "Oficina"),
        
        # Salud y Belleza
        ("Crema Facial Anti-edad", "Crema con retinol y ácido hialurónico", 40, 85.00, "Belleza"),
        ("Perfume Chanel No. 5", "Fragancia clásica femenina de 100ml", 8, 165.00, "Belleza"),
        ("Kit de Maquillaje Profesional", "Set completo con pinceles y paleta de colores", 15, 129.99, "Belleza"),
        ("Champú Orgánico Libre de Sulfatos", "Champú natural para todo tipo de cabello", 35, 22.99, "Belleza"),
        ("Vitaminas Multivitamínico", "Suplemento diario con vitaminas y minerales", 50, 29.99, "Belleza"),
        
        # Juguetes y Entretenimiento
        ("LEGO Creator Expert", "Set de construcción avanzado de 2000 piezas", 12, 179.99, "Juguetes"),
        ("Drone DJI Mini 3", "Drone compacto con cámara 4K y gimbal", 5, 759.00, "Juguetes"),
        ("Puzzle 1000 Piezas", "Rompecabezas de paisaje europeo", 20, 19.99, "Juguetes"),
        ("Guitarra Acústica Yamaha", "Guitarra para principiantes con cuerdas de acero", 6, 199.00, "Juguetes"),
        ("Juego de Mesa Catan", "Juego estratégico para toda la familia", 18, 55.00, "Juguetes")
    ]
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        for nombre, descripcion, cantidad, precio, categoria in productos_ejemplo:
            try:
                cursor.execute('''
                    INSERT INTO productos (nombre, descripcion, cantidad, precio, categoria)
                    VALUES (?, ?, ?, ?, ?)
                ''', (nombre, descripcion, cantidad, precio, categoria))
                print(f"✅ Agregado: {nombre} - ${precio} ({cantidad} unidades)")
                
            except sqlite3.IntegrityError:
                print(f"⚠️  Ya existe: {nombre}")
                
        conn.commit()

def show_statistics():
    """Muestra estadísticas de los productos agregados"""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        # Total de productos
        total_productos = cursor.execute('SELECT COUNT(*) FROM productos').fetchone()[0]
        
        # Valor total del inventario
        valor_total = cursor.execute('SELECT SUM(cantidad * precio) FROM productos').fetchone()[0]
        
        # Productos por categoría
        categorias = cursor.execute('''
            SELECT categoria, COUNT(*) as cantidad, SUM(cantidad * precio) as valor
            FROM productos 
            GROUP BY categoria 
            ORDER BY cantidad DESC
        ''').fetchall()
        
        print(f"\n📊 ESTADÍSTICAS DEL INVENTARIO")
        print(f"{'='*50}")
        print(f"🏪 Total de productos: {total_productos}")
        print(f"💰 Valor total del inventario: ${valor_total:,.2f}")
        print(f"📈 Stock total de unidades: {cursor.execute('SELECT SUM(cantidad) FROM productos').fetchone()[0]}")
        
        print(f"\n📦 PRODUCTOS POR CATEGORÍA:")
        print(f"{'Categoría':<20} {'Productos':<10} {'Valor':<15}")
        print(f"{'-'*45}")
        for categoria, cantidad, valor in categorias:
            print(f"{categoria:<20} {cantidad:<10} ${valor:>12,.2f}")

def main():
    """Función principal"""
    print("🚀 Inicializando base de datos de inventario...")
    
    # Inicializar base de datos
    init_db()
    
    # Preguntar si limpiar datos existentes
    if os.path.exists(DATABASE):
        respuesta = input("\n¿Deseas limpiar los productos existentes? (s/n): ").lower()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            clear_products()
    
    # Agregar productos de ejemplo
    print("\n📦 Agregando productos de ejemplo...")
    add_sample_products()
    
    # Mostrar estadísticas
    show_statistics()
    
    print(f"\n✨ ¡Listo! La base de datos ha sido poblada con productos.")
    print(f"🌐 Puedes ver los productos en: http://127.0.0.1:5000")
    print(f"📄 Base de datos guardada en: {os.path.abspath(DATABASE)}")

if __name__ == "__main__":
    main()