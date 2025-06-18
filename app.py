from flask import Flask, render_template, request, redirect, url_for, session
import os
from datetime import datetime
import pickle

app = Flask(__name__)
app.secret_key = 'clave-super-secreta-insegura'
app.config['SESSION_COOKIE_HTTPONLY'] = False

DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.txt')
POSTS_FILE = os.path.join(DATA_DIR, 'posts.txt')
COMMENTS_FILE = os.path.join(DATA_DIR, 'comments.txt')

# Helpers

def cargar_usuarios():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        lines = f.readlines()
        usuarios = {}
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) == 3:
                username, password, avatar = parts
                usuarios[username] = {'password': password, 'avatar': avatar}
            else:
                username, password = parts
                usuarios[username] = {'password': password, 'avatar': '/static/default.png'}
        return usuarios



def guardar_usuario(username, password, profile_url):
    with open(USERS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{username}|{password}|{profile_url}\n")

def usuario_existe(username):
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if parts and parts[0] == username:
                    return True
    except FileNotFoundError:
        pass
    return False


def cargar_posts():
    if not os.path.exists(POSTS_FILE):
        return []
    with open(POSTS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        posts = []
        for idx, line in enumerate(lines):
            parts = line.strip().split('|')
            if len(parts) != 5:
                continue  # skip malformed lines
            titulo, contenido, autor, timestamp, carrera = parts
            posts.append({
                'id': idx,
                'titulo': titulo,
                'contenido': contenido,
                'autor': autor,
                'timestamp': timestamp,
                'carrera': carrera
            })
        return posts


def guardar_post(titulo, contenido, autor, carrera):
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Guardando post: {titulo}, {autor}, {fecha}, {carrera}")
    with open('data/posts.txt', 'a', encoding='utf-8') as f:
        f.write(f"{titulo}|{contenido}|{autor}|{fecha}|{carrera}\n")


def cargar_comentarios(post_id):
    if not os.path.exists(COMMENTS_FILE):
        return []
    with open(COMMENTS_FILE, 'r') as f:
        lines = f.readlines()
        comentarios = []
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) != 4:
                continue
            pid, autor, comentario, timestamp = parts
            if int(pid) == post_id:
                comentarios.append({'autor': autor, 'comentario': comentario, 'timestamp': timestamp})
        return comentarios


def guardar_comentario(post_id, autor, comentario):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(COMMENTS_FILE, 'a') as f:
        f.write(f"{post_id}|{autor}|{comentario}|{timestamp}\n")

# Borrar post
def eliminar_post(post_id):
    posts = cargar_posts()
    posts = [p for p in posts if p['id'] != post_id]
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        for p in posts:
            f.write(f"{p['titulo']}|{p['contenido']}|{p['autor']}|{p['timestamp']}|{p['carrera']}\n")

# Borrar comentario
def eliminar_comentario(post_id, autor, timestamp):
    comentarios = cargar_comentarios(-1)  # Cargamos todos
    comentarios = [c for c in comentarios if not (c['pid'] == post_id and c['autor'] == autor and c['timestamp'] == timestamp)]
    with open(COMMENTS_FILE, 'w') as f:
        for c in comentarios:
            f.write(f"{c['pid']}|{c['autor']}|{c['comentario']}|{c['timestamp']}\n")

# Cargar todos los comentarios (sin filtrar por post)
def cargar_comentarios(post_id=None):
    if not os.path.exists(COMMENTS_FILE):
        return []
    with open(COMMENTS_FILE, 'r') as f:
        lines = f.readlines()
        comentarios = []
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) != 4:
                continue
            pid, autor, comentario, timestamp = parts
            if post_id is None or int(pid) == post_id:
                comentarios.append({'pid': int(pid), 'autor': autor, 'comentario': comentario, 'timestamp': timestamp})
        return comentarios

def obtener_datos_usuario(username):
    if not os.path.exists('data/users.txt'):
        return None
    with open('data/users.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) == 3 and parts[0] == username:
                return {
                    'username': parts[0],
                    'password': parts[1],  # opcional
                    'foto': parts[2]
                }
    return None


# Rutas

@app.route('/')
def index():
    posts = cargar_posts()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        profile_url = request.form.get('profile_url', '').strip()

        if not username or not password:
            return render_template('register.html', error="Todos los campos son obligatorios.")

        if usuario_existe(username):
            return render_template('register.html', error="El nombre de usuario ya está en uso.")

        guardar_usuario(username, password, profile_url)

        # Autologin
        session['user'] = username
        return redirect(url_for('index')) 

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        usuarios = cargar_usuarios()
        if username in usuarios and usuarios[username]['password'] == password:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        titulo = request.form['titulo']
        contenido = request.form['contenido']
        carrera = request.form['carrera']
        autor = session['user']
        guardar_post(titulo, contenido, autor, carrera)
        return redirect(url_for('index'))
    return render_template('new_post.html')

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def ver_post(post_id):
    posts = cargar_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post no encontrado", 404

    if request.method == 'POST':
        if 'user' not in session:
            return redirect(url_for('login'))
        comentario = request.form['comentario']
        guardar_comentario(post_id, session['user'], comentario)
        return redirect(url_for('ver_post', post_id=post_id))

    comentarios = cargar_comentarios(post_id)

    # Obtener foto del autor del post
    autor_info = obtener_datos_usuario(post['autor'])
    foto_autor = autor_info['foto'] if autor_info else None

    # Obtener foto para cada comentarista
    for c in comentarios:
        info = obtener_datos_usuario(c['autor'])
        c['foto'] = info['foto'] if info else url_for('static', filename='user.webp')

    return render_template('post.html', post=post, comentarios=comentarios, foto_autor=foto_autor)


@app.route('/perfil/<username>')
def perfil(username):
    usuarios = cargar_usuarios()
    user = usuarios.get(username)
    if not user:
        return "Usuario no encontrado", 404
    
    posts = cargar_posts()
    user_posts = [p for p in posts if p['autor'] == username]
    
    # Calcular comentarios (asumiendo que tienes una función para cargarlos)
    comentarios = cargar_comentarios()
    user_comentarios = sum(1 for c in comentarios if c['autor'] == username)
    
    # Añadir datos al perfil
    user['comentarios'] = user_comentarios
    
    return render_template('perfil.html', 
                         username=username, 
                         user=user, 
                         posts=user_posts)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'user' not in session or session['user'] != 'admin':
        return "Acceso denegado", 403

    usuarios = cargar_usuarios()
    posts = cargar_posts()
    comentarios = cargar_comentarios()

    return render_template('admin.html', usuarios=usuarios, posts=posts, comentarios=comentarios)

@app.route('/borrar_post/<int:post_id>', methods=['POST', 'GET'])  # Oh no, GET allowed too!
def borrar_post(post_id):
    if request.method == 'GET':
        eliminar_post(post_id)
        return redirect(url_for('admin_panel'))
    
    # "Authentication" that can be bypassed by just knowing the URL
    if 'user' in session and session['user'] == 'admin':
        eliminar_post(post_id)
    else:
        # Weak error message that reveals too much
        return f"""<html>
            <head><title>Error</title></head>
            <body bgcolor="#FFFFFF">
                <font face="Verdana" size="2">
                <center>
                    <h2>❌ Error 403</h2>
                    <p>Debes ser admin para borrar posts</p>
                    <p>Post ID: {post_id}</p>
                    <a href="/login"><img src="/static/login_button.gif" border="0"></a>
                </center>
                </font>
            </body>
        </html>""", 403
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/user/<username>')
def ver_usuario_admin(username):
    usuarios = cargar_usuarios()
    if username not in usuarios:
        return "Usuario no encontrado", 404

    # 🔐 Control de acceso basado en sesión
    if session.get('user') != 'admin':
        return "Acceso no autorizado", 403

    user = usuarios[username]
    return render_template('admin_user.html', username=username, user=user)


@app.route("/carreras")
def carreras():
    carreras_disponibles = [
        "Primer Año", "Segundo Año", "Electrónica", "Sistemas", 
        "Mecánica", "Parciales", "Finales", "Apuntes"
    ]
    return render_template("carrera.html", carreras=carreras_disponibles)

@app.route("/recursos")
def recursos():
    recursos = [
        {"titulo": "Apuntes Álgebra UTN", "url": "https://example.com/algebra"},
        {"titulo": "Guía de Finales Física I", "url": "https://example.com/fisica"},
        {"titulo": "TP Modelos y Simulación", "url": "https://example.com/modelos"},
    ]
    return render_template("recursos.html", recursos=recursos)

@app.route("/calendario")
def calendario():
    return render_template("calendario.html")

@app.route("/ayuda")
def ayuda():
    return render_template("ayuda.html")

@app.route("/buscar")
def buscar():
    query = request.args.get("q", "").lower()
    posts = cargar_posts()
    
    resultados = []
    if query:
        for post in posts:
            # Search in title, content, and author
            if (query in post['titulo'].lower() or 
                query in post['contenido'].lower() or 
                query in post['autor'].lower() or
                query in post['carrera'].lower()):
                resultados.append(post)
    
    return render_template("busqueda.html", query=query, resultados=resultados)

@app.route('/carrera/<carrera>')
def ver_carrera(carrera):
    posts = [p for p in cargar_posts() if p['carrera'].lower() == carrera.lower()]
    return render_template('carrera.html', carrera=carrera, posts=posts)

if __name__ == '__main__':
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    app.run(debug=True)
