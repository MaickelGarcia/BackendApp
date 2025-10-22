from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import time

app = Flask(__name__)
CORS(app)

TEMP_DIR = tempfile.gettempdir()

@app.route('/api/info', methods=['POST'])
def get_video_info():
    """Obtiene información del video sin descargarlo"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL requerida'}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            audio_formats = []
            
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'quality': f.get('height', 0),
                        'filesize': f.get('filesize', 0)
                    })
                elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    audio_formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'abr': f.get('abr', 0)
                    })
            
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'video_formats': formats[:5],
                'audio_formats': audio_formats[:3]
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def get_download_url():
    """Obtiene la URL directa de descarga"""
    try:
        data = request.get_json()
        url = data.get('url')
        format_type = data.get('format', 'mp4')
        
        if not url:
            return jsonify({'error': 'URL requerida'}), 400
        
        if format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
        else:
            ydl_opts = {
                'format': 'best[height<=720]',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'url' in info:
                download_url = info['url']
            elif 'requested_formats' in info:
                download_url = info['requested_formats'][0]['url']
            elif 'formats' in info:
                download_url = info['formats'][0]['url']
            else:
                return jsonify({'error': 'No se pudo obtener URL'}), 500
            
            return jsonify({
                'download_url': download_url,
                'title': info.get('title'),
                'ext': info.get('ext', format_type)
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Verificar que el servidor está funcionando"""
    return jsonify({'status': 'ok', 'message': 'Server is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

4. Click **Commit changes** → **Commit directly to the main branch** → **Commit changes**

#### **Archivo 2: requirements.txt**

1. Click **Add file** → **Create new file**
2. Nombre: `requirements.txt`
3. Contenido:
```
Flask==3.0.0
flask-cors==4.0.0
yt-dlp==2024.10.7
gunicorn==21.2.0
```

4. Click **Commit changes**

#### **Archivo 3: Procfile** (IMPORTANTE - te falta este)

1. Click **Add file** → **Create new file**
2. Nombre: `Procfile` (sin extensión, exactamente así)
3. Contenido:
```
web: gunicorn app:app
```

4. Click **Commit changes**

---

### **Paso 3: Desplegar en Render**

1. Ve a https://render.com
2. Click **Sign Up** (si no tienes cuenta) o **Log In**
3. Puedes registrarte con tu cuenta de GitHub (recomendado)

#### **Crear el Web Service:**

1. En el dashboard de Render, click **New +** (arriba derecha)
2. Selecciona **Web Service**
3. Click **Connect account** junto a GitHub (si no lo has hecho)
4. Autoriza a Render para acceder a tus repositorios
5. Busca tu repositorio `youtube-backend` y click **Connect**

#### **Configuración del servicio:**

En la página de configuración:

| Campo | Valor |
|-------|-------|
| **Name** | `youtube-backend` (o cualquier nombre) |
| **Region** | `Oregon (US West)` o el más cercano |
| **Branch** | `main` |
| **Root Directory** | (dejar vacío) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Instance Type** | `Free` |

#### **Variables de entorno (opcional):**

Puedes agregar estas variables en "Environment":
- `PYTHON_VERSION`: `3.11.0`

#### **Finalizar:**

1. Click **Create Web Service**
2. **Espera 2-5 minutos** mientras Render despliega tu app
3. Verás logs en tiempo real del proceso de despliegue

---

### **Paso 4: Obtener tu URL**

Una vez que termine el despliegue:

1. Verás un mensaje: **"Your service is live"** 🎉
2. En la parte superior verás tu URL, algo como:
```
   https://youtube-backend-xxxx.onrender.com
