from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL, SECRET_KEY
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = SECRET_KEY

def get_conn():
    """Devuelve una conexión a la base de datos"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print("Error al conectar a la base de datos:", e)
        return None

# ------------------ AUTENTICACIÓN ------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('No tiene permisos para acceder a esta página', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('u')
        password = request.form.get('p')
        
        if not username or not password:
            flash('Por favor, complete todos los campos', 'error')
            return render_template('login.html')
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_conn()
        if not conn:
            flash('Error de conexión a la base de datos', 'error')
            return render_template('login.html')
        
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                'SELECT id, username, rol FROM usuarios WHERE username = %s AND password_hash = %s',
                (username, password_hash)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['rol'] == 'admin'
                flash(f'Bienvenido, {user["username"]}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Usuario o contraseña incorrectos', 'error')
        except Exception as e:
            conn.close()
            flash(f'Error al iniciar sesión: {e}', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_conn()
        if not conn:
            flash('Error de conexión a la base de datos', 'error')
            return render_template('register.html')
        
        try:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO usuarios (username, password_hash, rol) VALUES (%s, %s, %s)',
                (username, password_hash, 'usuario')
            )
            conn.commit()
            cur.close()
            conn.close()
            flash('Usuario registrado exitosamente. Puede iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            conn.close()
            flash('El usuario o email ya existe', 'error')
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Error al registrar usuario: {e}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('index'))

# ------------------ INDEX ------------------
@app.route('/')
def index():
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor()
        # Obtener estadísticas generales
        cur.execute('SELECT COUNT(*) FROM productos')
        num_products = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM clientes')
        num_clients = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM pedidos')
        num_orders = cur.fetchone()[0]
        
        # Obtener productos con stock bajo (menos de 10)
        cur.execute('SELECT COUNT(*) FROM productos WHERE stock < 10')
        low_stock_products = cur.fetchone()[0]
        
        # Obtener total de ventas
        cur.execute('SELECT COALESCE(SUM(total), 0) FROM pedidos')
        total_sales = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return render_template('index.html', 
                             num_products=num_products,
                             num_clients=num_clients,
                             num_orders=num_orders,
                             low_stock_products=low_stock_products,
                             total_sales=total_sales)
    except Exception as e:
        conn.close()
        return f"Error en la consulta: {e}"

# ------------------ PRODUCTOS ------------------
@app.route('/productos')
@login_required
def listar_productos():
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre, precio, stock FROM productos ORDER BY id')
        productos = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('productos.html', productos=productos)
    except Exception as e:
        conn.close()
        return f"Error en la consulta de productos: {e}"

@app.route('/productos/agregar', methods=['POST'])
def agregar_producto():
    nombre = request.form.get('nombre')
    precio = request.form.get('precio')
    stock = request.form.get('stock')
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor()
        # Verificar si el producto ya existe
        cur.execute('SELECT id, stock FROM productos WHERE nombre = %s', (nombre,))
        producto_existente = cur.fetchone()
        
        if producto_existente:
            # Si existe, sumar al stock existente
            nuevo_stock = producto_existente[1] + int(stock)
            cur.execute('UPDATE productos SET stock = %s, precio = %s WHERE id = %s', 
                       (nuevo_stock, precio, producto_existente[0]))
            flash(f'Stock actualizado para {nombre}. Nuevo stock: {nuevo_stock}', 'success')
        else:
            # Si no existe, crear nuevo producto
            cur.execute(
                'INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s)',
                (nombre, precio, stock)
            )
            flash('Producto agregado con éxito', 'success')
        
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('listar_productos'))
    except Exception as e:
        conn.rollback()
        conn.close()
        return f"Error al agregar producto: {e}"

@app.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        stock = request.form.get('stock')
        try:
            cur = conn.cursor()
            cur.execute(
                'UPDATE productos SET nombre = %s, precio = %s, stock = %s WHERE id = %s',
                (nombre, precio, stock, id)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash('Producto actualizado con éxito', 'success')
            return redirect(url_for('listar_productos'))
        except Exception as e:
            conn.rollback()
            conn.close()
            return f"Error al actualizar producto: {e}"
    else:
        try:
            cur = conn.cursor()
            cur.execute('SELECT id, nombre, precio, stock FROM productos WHERE id = %s', (id,))
            producto = cur.fetchone()
            cur.close()
            conn.close()
            if not producto:
                flash('Producto no encontrado', 'error')
                return redirect(url_for('listar_productos'))
            return render_template('editar_producto.html', producto=producto)
        except Exception as e:
            conn.close()
            return f"Error al obtener producto: {e}"

@app.route('/productos/eliminar/<int:id>')
@login_required
def eliminar_producto(id):
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM productos WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('Producto eliminado con éxito', 'success')
        return redirect(url_for('listar_productos'))
    except Exception as e:
        conn.rollback()
        conn.close()
        return f"Error al eliminar producto: {e}"

@app.route('/productos/buscar')
@login_required
def buscar_producto():
    nombre = request.args.get('nombre')
    if not nombre:
        return redirect(url_for('listar_productos'))
    
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre, precio, stock FROM productos WHERE nombre ILIKE %s ORDER BY id', (f'%{nombre}%',))
        productos = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('productos.html', productos=productos)
    except Exception as e:
        conn.close()
        return f"Error en la búsqueda de productos: {e}"

# ------------------ CLIENTES ------------------
@app.route('/clientes')
@login_required
def listar_clientes():
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Intentar agregar la columna cedula si no existe
        try:
            cur.execute('ALTER TABLE clientes ADD COLUMN IF NOT EXISTS cedula VARCHAR(20)')
            conn.commit()
        except Exception as alter_error:
            conn.rollback()  # Hacer rollback si hay error en ALTER
            print(f"Info: {alter_error}")  # La columna probablemente ya existe
        
        cur.execute('SELECT id, nombre, correo, cedula FROM clientes ORDER BY id')
        clientes_list = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('clientes.html', clientes=clientes_list)
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return f"Error en la consulta de clientes: {e}"

@app.route('/clientes/agregar', methods=['GET', 'POST'])
def agregar_cliente():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        cedula = request.form.get('cedula')
        conn = get_conn()
        if not conn:
            return "Error: No se pudo conectar a la base de datos."
        try:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO clientes (nombre, correo, cedula) VALUES (%s, %s, %s)',
                (nombre, correo, cedula)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash('Cliente registrado con éxito', 'success')
            return redirect(url_for('listar_clientes'))
        except Exception as e:
            conn.rollback()
            conn.close()
            return f"Error al agregar cliente: {e}"
    return render_template('agregar_cliente.html')

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        cedula = request.form.get('cedula')
        try:
            cur = conn.cursor()
            cur.execute(
                'UPDATE clientes SET nombre = %s, correo = %s, cedula = %s WHERE id = %s',
                (nombre, correo, cedula, id)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash('Cliente actualizado con éxito', 'success')
            return redirect(url_for('listar_clientes'))
        except Exception as e:
            conn.rollback()
            conn.close()
            return f"Error al actualizar cliente: {e}"
    
    # GET request - mostrar formulario con datos actuales
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM clientes WHERE id = %s', (id,))
        cliente = cur.fetchone()
        cur.close()
        conn.close()
        if not cliente:
            flash('Cliente no encontrado', 'error')
            return redirect(url_for('listar_clientes'))
        return render_template('editar_cliente.html', cliente=cliente)
    except Exception as e:
        conn.close()
        return f"Error al obtener cliente: {e}"

@app.route('/clientes/eliminar/<int:id>')
def eliminar_cliente(id):
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM clientes WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('Cliente eliminado con éxito', 'success')
        return redirect(url_for('listar_clientes'))
    except Exception as e:
        conn.rollback()
        conn.close()
        return f"Error al eliminar cliente: {e}"

@app.route('/clientes/buscar')
def buscar_cliente():
    nombre = request.args.get('nombre')
    cedula = request.args.get('cedula')
    
    if not nombre and not cedula:
        return redirect(url_for('listar_clientes'))
    
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if nombre and cedula:
            cur.execute('SELECT id, nombre, correo, cedula FROM clientes WHERE nombre ILIKE %s OR cedula ILIKE %s', (f'%{nombre}%', f'%{cedula}%'))
        elif nombre:
            cur.execute('SELECT id, nombre, correo, cedula FROM clientes WHERE nombre ILIKE %s', (f'%{nombre}%',))
        elif cedula:
            cur.execute('SELECT id, nombre, correo, cedula FROM clientes WHERE cedula ILIKE %s', (f'%{cedula}%',))
            
        clientes_list = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('clientes.html', clientes=clientes_list)
    except Exception as e:
        conn.close()
        return f"Error en la búsqueda de clientes: {e}"

# ------------------ PEDIDOS ------------------
@app.route('/pedidos', methods=['GET','POST'])
@login_required
def gestionar_pedidos():
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if request.method == 'POST':
            cliente_id = int(request.form.get('cliente_id'))
            producto_id = int(request.form.get('producto_id'))
            cantidad = int(request.form.get('cantidad'))
            try:
                cur.execute('CALL registrar_pedido(%s, %s, %s);', (cliente_id, producto_id, cantidad))
                conn.commit()
                flash('Pedido registrado correctamente', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error al registrar pedido: {e}', 'danger')

        cur.execute("""
            SELECT p.id, c.nombre as cliente, prod.nombre as producto, p.cantidad, p.total, p.fecha
            FROM pedidos p
            LEFT JOIN clientes c ON p.cliente_id=c.id
            LEFT JOIN productos prod ON p.producto_id=prod.id
            ORDER BY p.fecha DESC
        """)
        pedidos_list = cur.fetchall()

        cur.execute('SELECT id, nombre FROM clientes')
        clientes_list = cur.fetchall()

        cur.execute('SELECT id, nombre, stock FROM productos')
        productos_list = cur.fetchall()

        cur.close()
        conn.close()
        return render_template('pedidos.html', pedidos=pedidos_list, clientes=clientes_list, productos=productos_list)
    except Exception as e:
        conn.close()
        return f"Error en la gestión de pedidos: {e}"

@app.route('/pedidos/buscar')
@login_required
def buscar_pedido():
    cliente = request.args.get('cliente')
    if not cliente:
        return redirect(url_for('gestionar_pedidos'))
    
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar pedidos por nombre de cliente
        cur.execute("""
            SELECT p.id, c.nombre as cliente, prod.nombre as producto, p.cantidad, p.total, p.fecha
            FROM pedidos p
            LEFT JOIN clientes c ON p.cliente_id=c.id
            LEFT JOIN productos prod ON p.producto_id=prod.id
            WHERE c.nombre ILIKE %s
            ORDER BY p.fecha DESC
        """, (f'%{cliente}%',))
        pedidos_list = cur.fetchall()

        # Obtener listas para el formulario
        cur.execute('SELECT id, nombre FROM clientes')
        clientes_list = cur.fetchall()

        cur.execute('SELECT id, nombre, stock FROM productos')
        productos_list = cur.fetchall()

        cur.close()
        conn.close()
        return render_template('pedidos.html', pedidos=pedidos_list, clientes=clientes_list, productos=productos_list)
    except Exception as e:
        conn.close()
        return f"Error en la búsqueda de pedidos: {e}"

# ------------------ VENTAS TOTALES ------------------
@app.route('/ventas')
@login_required
def ventas_totales():
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Obtener todas las ventas (pedidos) con detalles
        cur.execute("""
            SELECT p.id, c.nombre as cliente, prod.nombre as producto, 
                   p.cantidad, p.precio_unitario, p.total, p.fecha
            FROM pedidos p
            LEFT JOIN clientes c ON p.cliente_id=c.id
            LEFT JOIN productos prod ON p.producto_id=prod.id
            ORDER BY p.fecha DESC
        """)
        ventas_list = cur.fetchall()
        
        # Obtener el total de ventas
        cur.execute('SELECT COALESCE(SUM(total), 0) FROM pedidos')
        total_ventas = cur.fetchone()[0]
        
        # Obtener estadísticas adicionales
        cur.execute('SELECT COUNT(*) FROM pedidos')
        num_ventas = cur.fetchone()[0]
        
        cur.execute("""
            SELECT AVG(total) FROM pedidos
        """)
        promedio_venta = cur.fetchone()[0] or 0
        
        cur.close()
        conn.close()
        
        return render_template('ventas_totales.html', 
                             ventas=ventas_list,
                             total_ventas=total_ventas,
                             num_ventas=num_ventas,
                             promedio_venta=promedio_venta)
    except Exception as e:
        conn.close()
        return f"Error al obtener ventas: {e}"

@app.route('/nueva_venta', methods=['GET', 'POST'])
@login_required
def nueva_venta():
    conn = get_conn()
    if not conn:
        return "Error: No se pudo conectar a la base de datos."
    
    if request.method == 'POST':
        try:
            cliente_id = int(request.form.get('cliente_id'))
            producto_id = int(request.form.get('producto_id'))
            cantidad = int(request.form.get('cantidad'))
            
            cur = conn.cursor()
            # Usar el procedimiento almacenado para registrar la venta
            cur.execute('CALL registrar_pedido(%s, %s, %s);', (cliente_id, producto_id, cantidad))
            conn.commit()
            cur.close()
            conn.close()
            
            flash('Venta registrada exitosamente', 'success')
            return redirect(url_for('ventas_totales'))
            
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Error al registrar venta: {e}', 'error')
            return redirect(url_for('nueva_venta'))
    
    # GET request - mostrar formulario
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Obtener clientes
        cur.execute('SELECT id, nombre FROM clientes ORDER BY nombre')
        clientes_list = cur.fetchall()
        
        # Obtener productos con stock disponible
        cur.execute('SELECT id, nombre, precio, stock FROM productos WHERE stock > 0 ORDER BY nombre')
        productos_list = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('nueva_venta.html', 
                             clientes=clientes_list,
                             productos=productos_list)
    except Exception as e:
        conn.close()
        return f"Error al cargar formulario de venta: {e}"

if __name__ == '__main__':
    app.run(debug=True)
