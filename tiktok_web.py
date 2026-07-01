# tiktok_web.py
# -*- coding: utf-8 -*-
import os
import re
import json
import hashlib
import subprocess
import threading
import time
import shutil
import requests
from flask import Flask, render_template_string, request, jsonify, send_file, abort
from urllib.parse import quote

app = Flask(__name__)

# ==================== CẤU HÌNH ====================
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

video_cache = {}  # Lưu thông tin video
video_files = {}  # Lưu đường dẫn file đã tải
file_timestamps = {}  # Lưu thời gian tạo file

# ==================== CLOUDFLARE TUNNEL ====================
_tunnel_url = None
_tunnel_process = None

def start_cloudflare_tunnel():
    global _tunnel_url, _tunnel_process
    try:
        check = subprocess.run(["cloudflared", "--version"], capture_output=True, timeout=2)
        if check.returncode != 0:
            print("⚠️ Cloudflared chưa được cài đặt!")
            return None
        
        print("🚀 Đang khởi động Cloudflare Tunnel...")
        
        _tunnel_process = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://localhost:5000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(_tunnel_process.stdout.readline, ''):
            print(line.strip())
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                _tunnel_url = match.group(0)
                print(f"✅ Public URL: {_tunnel_url}")
                return _tunnel_url
        
        return None
        
    except Exception as e:
        print(f"❌ Lỗi Cloudflare Tunnel: {e}")
        return None

def get_public_url():
    global _tunnel_url
    if not _tunnel_url:
        _tunnel_url = start_cloudflare_tunnel()
    return _tunnel_url

# ==================== HTML VIDEO PLAYER ====================
VIDEO_PAGE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Video</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            padding: 30px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }
        h1 {
            text-align: center;
            color: #fff;
            font-size: 28px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #fe2c55, #ff6b81);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .video-wrapper {
            position: relative;
            padding-bottom: 100%;
            height: 0;
            overflow: hidden;
            border-radius: 20px;
            background: #000;
            margin: 20px 0;
        }
        .video-wrapper video {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        .info {
            color: rgba(255,255,255,0.8);
            padding: 16px;
        }
        .info .title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .info .author {
            color: rgba(255,255,255,0.6);
            font-size: 14px;
            margin-bottom: 12px;
        }
        .info .author span {
            color: #fe2c55;
        }
        .stats {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 16px;
        }
        .stats .stat {
            color: rgba(255,255,255,0.6);
            font-size: 13px;
        }
        .download-btn {
            display: inline-block;
            padding: 14px 28px;
            background: linear-gradient(135deg, #00b894, #00cec9);
            color: #fff;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            text-align: center;
        }
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 206, 201, 0.4);
        }
        .back-btn {
            display: inline-block;
            margin-top: 12px;
            color: rgba(255,255,255,0.5);
            text-decoration: none;
            font-size: 14px;
            text-align: center;
            width: 100%;
        }
        .back-btn:hover {
            color: #fff;
        }
        .error {
            color: #ff6b81;
            text-align: center;
            padding: 40px 20px;
        }
        .expiry {
            color: rgba(255,255,255,0.3);
            font-size: 12px;
            text-align: center;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 TikTok Video</h1>
        
        <div class="video-wrapper">
            <video id="videoPlayer" controls autoplay></video>
        </div>
        
        <div class="info">
            <div class="title" id="videoTitle">Đang tải...</div>
            <div class="author">👤 Tác giả: <span id="videoAuthor">@username</span></div>
            <div class="stats">
                <span class="stat">👁️ <span id="views">0</span></span>
                <span class="stat">❤️ <span id="likes">0</span></span>
                <span class="stat">💬 <span id="comments">0</span></span>
                <span class="stat">⏱️ <span id="duration">00:00</span></span>
            </div>
            <a id="downloadLink" class="download-btn" download>📥 Tải video xuống</a>
            <div class="expiry">⏰ Video sẽ tự động xóa sau 10 phút</div>
            <a href="/" class="back-btn">⬅ Quay lại tải video khác</a>
        </div>
    </div>

    <script>
        const videoId = window.location.pathname.split('/').pop();
        
        async function loadVideo() {
            try {
                const response = await fetch(`/api/video/${videoId}`);
                const data = await response.json();
                
                if (data.error) {
                    document.querySelector('.video-wrapper').innerHTML = `<div class="error">❌ ${data.error}</div>`;
                    return;
                }
                
                document.getElementById('videoTitle').textContent = data.title || 'Không có tiêu đề';
                document.getElementById('videoAuthor').textContent = '@' + (data.author || 'unknown');
                document.getElementById('views').textContent = formatNumber(data.views);
                document.getElementById('likes').textContent = formatNumber(data.likes);
                document.getElementById('comments').textContent = formatNumber(data.comments);
                document.getElementById('duration').textContent = data.duration || '00:00';
                
                const video = document.getElementById('videoPlayer');
                video.src = `/download/${videoId}`;
                video.load();
                
                document.getElementById('downloadLink').href = `/download/${videoId}`;
                
            } catch (error) {
                document.querySelector('.video-wrapper').innerHTML = `<div class="error">❌ Lỗi tải video</div>`;
            }
        }
        
        function formatNumber(num) {
            if (num >= 1000000) return (num/1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num/1000).toFixed(1) + 'K';
            return num.toString();
        }
        
        loadVideo();
    </script>
</body>
</html>
'''

# ==================== HTML INDEX ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Downloader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            max-width: 700px;
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }
        h1 {
            text-align: center;
            color: #fff;
            font-size: 32px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #fe2c55, #ff6b81);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            text-align: center;
            color: rgba(255,255,255,0.6);
            font-size: 14px;
            margin-bottom: 30px;
        }
        .input-group {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        .input-group input {
            flex: 1;
            padding: 16px 20px;
            border: 2px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            background: rgba(255,255,255,0.05);
            color: #fff;
            font-size: 16px;
            outline: none;
            transition: all 0.3s;
        }
        .input-group input:focus {
            border-color: #fe2c55;
            background: rgba(255,255,255,0.08);
        }
        .input-group input::placeholder {
            color: rgba(255,255,255,0.3);
        }
        .btn {
            padding: 16px 32px;
            border: none;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            background: linear-gradient(135deg, #fe2c55, #ff6b81);
            color: #fff;
            min-width: 120px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(254, 44, 85, 0.4);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .loading {
            text-align: center;
            color: rgba(255,255,255,0.8);
            padding: 40px 0;
            display: none;
        }
        .loading .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255,255,255,0.1);
            border-top-color: #fe2c55;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .result {
            display: none;
            margin-top: 30px;
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .video-card {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .video-card video {
            width: 100%;
            max-height: 400px;
            background: #000;
            display: block;
        }
        .video-info {
            padding: 20px;
        }
        .video-info h2 {
            color: #fff;
            font-size: 18px;
            margin-bottom: 6px;
            line-height: 1.4;
        }
        .video-info .author {
            color: rgba(255,255,255,0.6);
            font-size: 13px;
            margin-bottom: 12px;
        }
        .video-info .author span {
            color: #fe2c55;
        }
        .stats {
            display: flex;
            gap: 16px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        .stats .stat {
            color: rgba(255,255,255,0.6);
            font-size: 13px;
        }
        .short-url {
            margin-top: 12px;
            padding: 12px 16px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.08);
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .short-url .label {
            color: rgba(255,255,255,0.4);
            font-size: 12px;
        }
        .short-url .url {
            color: #00cec9;
            font-size: 13px;
            word-break: break-all;
            flex: 1;
        }
        .copy-btn {
            padding: 6px 14px;
            background: rgba(255,255,255,0.1);
            border: none;
            border-radius: 8px;
            color: #fff;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s;
        }
        .copy-btn:hover {
            background: rgba(255,255,255,0.2);
        }
        .error {
            color: #ff6b81;
            text-align: center;
            padding: 20px;
            background: rgba(255, 107, 129, 0.1);
            border-radius: 12px;
            border: 1px solid rgba(255, 107, 129, 0.2);
            display: none;
        }
        .public-url {
            background: rgba(0, 206, 201, 0.08);
            border: 1px solid rgba(0, 206, 201, 0.15);
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 20px;
            text-align: center;
        }
        .public-url .label {
            color: rgba(255,255,255,0.4);
            font-size: 12px;
            display: block;
            margin-bottom: 4px;
        }
        .public-url .url {
            color: #00cec9;
            font-size: 14px;
            word-break: break-all;
        }
        .expiry-note {
            color: rgba(255,255,255,0.3);
            font-size: 12px;
            text-align: center;
            margin-top: 12px;
        }
        @media (max-width: 600px) {
            .container { padding: 20px; }
            .input-group { flex-direction: column; }
            .btn { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 TikTok Downloader</h1>
        <p class="subtitle">Tải video TikTok không logo chất lượng cao</p>
        
        <div class="public-url" id="publicUrl">
            <span class="label">🔗 Public URL (chia sẻ cho người khác)</span>
            <span class="url" id="publicUrlText">Đang khởi tạo...</span>
        </div>
        
        <div class="input-group">
            <input type="text" id="urlInput" placeholder="Paste TikTok link here...">
            <button class="btn" id="downloadBtn" onclick="fetchVideo()">⬇️ Tải xuống</button>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Đang tải video...</p>
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="result" id="result">
            <div class="video-card">
                <video id="videoPlayer" controls></video>
                <div class="video-info">
                    <h2 id="videoTitle">Tiêu đề video</h2>
                    <p class="author">👤 Tác giả: <span id="videoAuthor">@username</span></p>
                    <div class="stats">
                        <span class="stat">👁️ <span id="views">0</span></span>
                        <span class="stat">❤️ <span id="likes">0</span></span>
                        <span class="stat">💬 <span id="comments">0</span></span>
                        <span class="stat">⏱️ <span id="duration">00:00</span></span>
                    </div>
                    <div class="short-url">
                        <span class="label">🔗 Link xem video:</span>
                        <span class="url" id="shortUrl">https://...</span>
                        <button class="copy-btn" onclick="copyShortUrl()">📋 Sao chép</button>
                    </div>
                    <a id="downloadLink" class="download-btn" style="display:inline-block;width:100%;text-align:center;padding:12px;border-radius:12px;background:linear-gradient(135deg,#00b894,#00cec9);color:#fff;text-decoration:none;font-weight:600;margin-top:12px;" download>📥 Tải video xuống</a>
                    <div class="expiry-note">⏰ Video sẽ tự động xóa sau 10 phút</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function getPublicUrl() {
            try {
                const response = await fetch('/api/public_url');
                const data = await response.json();
                document.getElementById('publicUrlText').textContent = data.url || 'Không có URL';
            } catch (error) {
                document.getElementById('publicUrlText').textContent = 'Lỗi lấy URL';
            }
        }
        getPublicUrl();
        
        async function fetchVideo() {
            const url = document.getElementById('urlInput').value.trim();
            if (!url) {
                showError('Vui lòng nhập link TikTok!');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('downloadBtn').disabled = true;
            
            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                showResult(data);
                
            } catch (error) {
                showError('Có lỗi xảy ra, vui lòng thử lại!');
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('downloadBtn').disabled = false;
            }
        }
        
        function showResult(data) {
            document.getElementById('result').style.display = 'block';
            document.getElementById('videoTitle').textContent = data.title || 'Không có tiêu đề';
            document.getElementById('videoAuthor').textContent = '@' + (data.author || 'unknown');
            document.getElementById('views').textContent = formatNumber(data.views);
            document.getElementById('likes').textContent = formatNumber(data.likes);
            document.getElementById('comments').textContent = formatNumber(data.comments);
            document.getElementById('duration').textContent = data.duration || '00:00';
            
            const videoPlayer = document.getElementById('videoPlayer');
            videoPlayer.src = `/download/${data.short_id}`;
            videoPlayer.load();
            
            document.getElementById('downloadLink').href = `/download/${data.short_id}`;
            document.getElementById('shortUrl').textContent = data.short_url || data.download_url;
        }
        
        function showError(message) {
            const errorEl = document.getElementById('error');
            errorEl.textContent = '❌ ' + message;
            errorEl.style.display = 'block';
        }
        
        function formatNumber(num) {
            if (num >= 1000000) return (num/1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num/1000).toFixed(1) + 'K';
            return num.toString();
        }
        
        function copyShortUrl() {
            const url = document.getElementById('shortUrl').textContent;
            navigator.clipboard.writeText(url).then(() => {
                const btn = document.querySelector('.copy-btn');
                btn.textContent = '✅ Đã copy!';
                setTimeout(() => { btn.textContent = '📋 Sao chép'; }, 2000);
            });
        }
        
        document.getElementById('urlInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') fetchVideo();
        });
    </script>
</body>
</html>
'''

# ==================== TẢI VIDEO TIKTOK ====================

def get_tiktok_video_info(url):
    """Lấy thông tin video từ TikTok"""
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return None, f"Lỗi API: {response.status_code}"
        
        data = response.json()
        
        if data.get('code') != 0:
            return None, data.get('msg', 'Không xác định')
        
        result = data.get('data', {})
        
        video_url = result.get('play', '')
        if not video_url:
            video_url = result.get('wmplay', '')
        
        video_info = {
            'title': result.get('title', 'Không có tiêu đề'),
            'author': result.get('author', {}).get('unique_id', 'Unknown'),
            'author_name': result.get('author', {}).get('nickname', 'Unknown'),
            'download_url': video_url,
            'duration': result.get('duration', 0),
            'likes': result.get('digg_count', 0),
            'comments': result.get('comment_count', 0),
            'views': result.get('play_count', 0),
            'cover': result.get('cover', '')
        }
        
        return video_info, None
        
    except Exception as e:
        return None, str(e)

def download_video_to_server(url, filename):
    """Tải video về server"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.tiktok.com/"
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        
        if response.status_code != 200:
            return None, f"Lỗi tải: {response.status_code}"
        
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        if os.path.getsize(filepath) == 0:
            os.remove(filepath)
            return None, "File rỗng"
        
        # Lưu thời gian tạo
        file_timestamps[filename] = time.time()
        
        return filepath, None
        
    except Exception as e:
        return None, str(e)

def format_duration(seconds):
    if not seconds:
        return "00:00"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# ==================== DỌN DẸP FILE ====================

def clean_old_files():
    """Xóa file cũ sau 10 phút"""
    while True:
        time.sleep(60)  # Kiểm tra mỗi phút
        try:
            current_time = time.time()
            files_deleted = 0
            
            # Duyệt qua tất cả file trong downloads
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    # Lấy thời gian tạo file
                    created_time = file_timestamps.get(filename, os.path.getmtime(filepath))
                    
                    # Xóa nếu file cũ hơn 10 phút (600 giây)
                    if current_time - created_time > 600:
                        os.remove(filepath)
                        files_deleted += 1
                        
                        # Xóa khỏi cache
                        for short_id, path in list(video_files.items()):
                            if path == filepath:
                                del video_files[short_id]
                                break
                        
                        # Xóa khỏi timestamps
                        if filename in file_timestamps:
                            del file_timestamps[filename]
            
            if files_deleted > 0:
                print(f"🗑️ Đã xóa {files_deleted} file cũ (hơn 10 phút)")
                
        except Exception as e:
            print(f"Lỗi dọn dẹp: {e}")

def delete_video_file(short_id):
    """Xóa video theo short_id ngay lập tức"""
    try:
        if short_id in video_files:
            filepath = video_files[short_id]
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️ Đã xóa file: {os.path.basename(filepath)}")
            
            # Xóa khỏi cache
            del video_files[short_id]
            
            # Xóa khỏi video_cache
            if short_id in video_cache:
                del video_cache[short_id]
            
            return True
    except Exception as e:
        print(f"Lỗi xóa video: {e}")
    return False

# Chạy thread dọn dẹp
clean_thread = threading.Thread(target=clean_old_files, daemon=True)
clean_thread.start()

# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/public_url')
def public_url():
    url = get_public_url() or "http://localhost:5000"
    return jsonify({'url': url})

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Không có dữ liệu'})
        
        url = data.get('url', '')
        
        if not url:
            return jsonify({'error': 'Vui lòng nhập link TikTok!'})
        
        if not re.search(r'tiktok\.com', url):
            return jsonify({'error': 'Link không phải TikTok!'})
        
        # Lấy thông tin video
        video_info, error = get_tiktok_video_info(url)
        
        if error:
            return jsonify({'error': error})
        
        if not video_info or not video_info.get('download_url'):
            return jsonify({'error': 'Không tìm thấy video!'})
        
        # Tạo short_id
        short_id = hashlib.md5(video_info['download_url'].encode()).hexdigest()[:8]
        
        # Tạo tên file
        filename = f"tiktok_{short_id}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        # Kiểm tra file đã tồn tại chưa
        if not os.path.exists(filepath):
            # Tải video về server
            filepath, error = download_video_to_server(video_info['download_url'], filename)
            
            if error:
                return jsonify({'error': f'Lỗi tải video: {error}'})
        
        # Lưu vào cache
        video_cache[short_id] = video_info
        video_files[short_id] = filepath
        
        # Tạo short URL
        public_url = get_public_url() or "http://localhost:5000"
        short_url = f"{public_url}/v/{short_id}"
        
        video_info['short_id'] = short_id
        video_info['short_url'] = short_url
        
        return jsonify(video_info)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/v/<short_id>')
def video_page(short_id):
    """Trang xem video"""
    video_info = video_cache.get(short_id)
    if not video_info:
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Video không tồn tại</title></head>
        <body style="background:#0f0c29;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;flex-direction:column;">
            <h1 style="color:#ff6b81;">❌ Video không tồn tại</h1>
            <p style="color:rgba(255,255,255,0.6);">Link đã hết hạn hoặc không hợp lệ</p>
            <a href="/" style="color:#00cec9;text-decoration:none;margin-top:20px;">⬅ Quay lại</a>
        </body>
        </html>
        ''')
    
    return render_template_string(VIDEO_PAGE)

@app.route('/api/video/<short_id>')
def get_video_info(short_id):
    """API lấy thông tin video"""
    video_info = video_cache.get(short_id)
    if not video_info:
        return jsonify({'error': 'Video không tồn tại'})
    return jsonify(video_info)

@app.route('/download/<short_id>')
def download_video(short_id):
    """Tải video về máy người dùng"""
    filepath = video_files.get(short_id)
    if not filepath or not os.path.exists(filepath):
        abort(404)
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"tiktok_video_{short_id}.mp4",
        mimetype='video/mp4'
    )

# ==================== MAIN ====================

if __name__ == '__main__':
    print("🚀 Đang khởi động TikTok Web Server...")
    
    public_url = get_public_url()
    
    if public_url:
        print(f"\n✅ Public URL (chia sẻ cho người khác):")
        print(f"🔗 {public_url}\n")
    else:
        print("\n⚠️ Không thể tạo Cloudflare Tunnel!")
        print("📌 Sử dụng local: http://localhost:5000\n")
    
    print("⏰ Video sẽ tự động xóa sau 10 phút")
    print("📁 Thư mục lưu video: downloads/\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)