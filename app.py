# app.py
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import os
import json
from uuid import uuid4

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = 'super_secret_key'

CATALOGO_PATH = 'data/catalogo.json'
USUARIO = 'sergioo.vu2'
CLAVE = '123'

@app.route('/uploads/<path:filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def cargar_catalogo():
    if not os.path.exists(CATALOGO_PATH):
        return []
    try:
        with open(CATALOGO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def guardar_catalogo(data):
    with open(CATALOGO_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def vista_cliente():
    catalogo = cargar_catalogo()
    visibles = [p for p in catalogo if p['visible']]

    marca = request.args.get('marca', '')
    categoria = request.args.get('categoria', '')
    talla = request.args.get('talla', '')

    if marca:
        visibles = [p for p in visibles if p['marca'] == marca]
    if categoria:
        visibles = [p for p in visibles if p['categoria'] == categoria]
    if talla:
        visibles = [p for p in visibles if p['talla'] == talla]

    return render_template('cliente.html', productos=visibles)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        if usuario == USUARIO and clave == CLAVE:
            session['vendedor'] = True
            return redirect(url_for('vista_vendedor'))
        else:
            return render_template('login.html', error='Credenciales inválidas')
    mensaje = 'Debes iniciar sesión primero' if request.args.get('next') else None
    return render_template('login.html', error=mensaje)

@app.route('/logout')
def logout():
    session.pop('vendedor', None)
    return redirect(url_for('vista_cliente'))

@app.route('/vendedor', methods=['GET', 'POST'])
def vista_vendedor():
    if 'vendedor' not in session or session['vendedor'] != True:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        marca = request.form['marca']
        talla = request.form['talla']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        imagenes = request.files.getlist('imagenes')

        imagenes_guardadas = []
        for imagen in imagenes:
            if imagen and imagen.filename != '':
                filename = f"{uuid4().hex}_{imagen.filename}"
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                imagen.save(path)
                imagenes_guardadas.append(filename)

        if imagenes_guardadas:
            catalogo = cargar_catalogo()
            nuevo = {
                'id': uuid4().hex,
                'nombre': nombre,
                'descripcion': descripcion,
                'categoria': categoria,
                'precio': precio,
                'stock': stock,
                'marca': marca,
                'talla': talla,
                'imagenes': imagenes_guardadas,
                'visible': True
            }
            catalogo.append(nuevo)
            guardar_catalogo(catalogo)

        return redirect(url_for('vista_vendedor'))

    # Aquí renderizas la vista con los productos
    catalogo = cargar_catalogo()
    return render_template('vendedor.html', productos=catalogo)

@app.route('/ocultar/<producto_id>')
def ocultar_producto(producto_id):
    if 'vendedor' not in session or session['vendedor'] != True:
        return redirect(url_for('login'))

    catalogo = cargar_catalogo()
    for producto in catalogo:
        if producto['id'] == producto_id:
            producto['visible'] = False
            break
    guardar_catalogo(catalogo)
    return redirect(url_for('vista_vendedor'))

@app.route('/mostrar/<producto_id>')
def mostrar_producto(producto_id):
    if 'vendedor' not in session or session['vendedor'] != True:
        return redirect(url_for('login'))

    catalogo = cargar_catalogo()
    for producto in catalogo:
        if producto['id'] == producto_id:
            producto['visible'] = True
            break
    guardar_catalogo(catalogo)
    return redirect(url_for('vista_vendedor'))

@app.route('/editar/<producto_id>', methods=['POST'])
def editar_producto(producto_id):
    if 'vendedor' not in session or session['vendedor'] != True:
        return redirect(url_for('login'))

    catalogo = cargar_catalogo()
    for producto in catalogo:
        if producto['id'] == producto_id:
            producto['precio'] = float(request.form['precio'])
            producto['stock'] = int(request.form['stock'])
            break
    guardar_catalogo(catalogo)
    return redirect(url_for('vista_vendedor'))

@app.route('/toggle_visibilidad/<producto_id>', methods=['POST'])
def toggle_visibilidad(producto_id):
    if 'vendedor' not in session or session['vendedor'] != True:
        return redirect(url_for('login'))

    catalogo = cargar_catalogo()
    for producto in catalogo:
        if producto['id'] == producto_id:
            producto['visible'] = not producto['visible']
            break
    guardar_catalogo(catalogo)
    return redirect(url_for('vista_vendedor'))


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('data', exist_ok=True)
    app.run(debug=True)
