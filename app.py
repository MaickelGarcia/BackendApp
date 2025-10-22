from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import time

app = Flask(__name__)
CORS(app)

TEMP_DIR = tempfile.gettempdir()

# Configuración mejorada de yt-dlp para evitar bloqueos de YouTube
YT_DLP_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'referer': 'https://www.youtube.com/',
    'headers': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Sec-Fetch-Mode': 'navigate',
    }
}

@app.route('/', methods=['GET'])
def home():
    """Página de inicio"""
    return jsonify({
        'message': 'YouTube Downloader API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'info': '/api/info (POST)',
            'download': '/api/download (POST)'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Verificar que el servidor está funcionando"""
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/api/info', methods=['POST'])
def get_video_info():
    """Obtiene información del video sin descargarlo"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL requerida'}), 400
        
        ydl_opts = YT_DLP_OPTS.copy()
        
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
        
        # Validar que la URL tenga un video ID válido
        if 'v=null' in url or url.endswith('v='):
            return jsonify({'error': 'URL de YouTube inválida o incompleta'}), 400
        
        ydl_opts = YT_DLP_OPTS.copy()
        
        if format_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
            })
        else:
            ydl_opts.update({
                'format': 'best[height<=720][ext=mp4]/best[height<=720]/best',
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Obtener la URL directa
            download_url = None
            if 'url' in info:
                download_url = info['url']
            elif 'requested_formats' in info and len(info['requested_formats']) > 0:
                download_url = info['requested_formats'][0]['url']
            elif 'formats' in info and len(info['formats']) > 0:
                # Buscar el mejor formato disponible
                for fmt in info['formats']:
                    if fmt.get('url'):
                        download_url = fmt['url']
                        break
            
            if not download_url:
                return jsonify({'error': 'No se pudo obtener URL de descarga'}), 500
            
            return jsonify({
                'download_url': download_url,
                'title': info.get('title'),
                'ext': info.get('ext', format_type)
            })
    
    except Exception as e:
        error_msg = str(e)
        
        # Mensajes de error más amigables
        if 'Sign in to confirm' in error_msg or 'bot' in error_msg:
            error_msg = 'YouTube está bloqueando la descarga. Intenta con otro video o más tarde.'
        elif 'Video unavailable' in error_msg:
            error_msg = 'Video no disponible o privado'
        elif 'This video is not available' in error_msg:
            error_msg = 'Este video no está disponible en tu región'
        
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
