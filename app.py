from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = 'clave-super-secreta-insegura'

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
            print(f"DEBUG LINE: {line}")
            username, password = line.strip().split('|')
            usuarios[username] = password
        print(f"DEBUG USUARIOS: {usuarios}")
        return usuarios


def guardar_usuario(username, password):
    with open(USERS_FILE, 'a') as f:
        f.write(f"{username}|{password}\n")

def cargar_posts():
    if not os.path.exists(POSTS_FILE):
        return []
    with open(POSTS_FILE, 'r') as f:
        lines = f.readlines()
        posts = []
        for idx, line in enumerate(lines):
            titulo, contenido, autor = line.strip().split('|')
            posts.append({'id': idx, 'titulo': titulo, 'contenido': contenido, 'autor': autor})
        return posts

def guardar_post(titulo, contenido, autor):
    with open(POSTS_FILE, 'a') as f:
        f.write(f"{titulo}|{contenido}|{autor}\n")

def cargar_comentarios(post_id):
    if not os.path.exists(COMMENTS_FILE):
        return []
    with open(COMMENTS_FILE, 'r') as f:
        lines = f.readlines()
        comentarios = []
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) != 3:
                continue  # saltar líneas mal formadas
            pid, autor, comentario = parts
            if int(pid) == post_id:
                comentarios.append({'autor': autor, 'comentario': comentario})
        return comentarios

def guardar_comentario(post_id, autor, comentario):
    with open(COMMENTS_FILE, 'a') as f:
        f.write(f"{post_id}|{autor}|{comentario}\n")

# Rutas

@app.route('/')
def index():
    posts = cargar_posts()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        guardar_usuario(username, password)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        usuarios = cargar_usuarios()
        if username in usuarios and usuarios[username] == password:
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
        autor = session['user']
        guardar_post(titulo, contenido, autor)
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
    return render_template('post.html', post=post, comentarios=comentarios)


if __name__ == '__main__':
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    app.run(debug=True)
