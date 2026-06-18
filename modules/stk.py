import requests
import subprocess
import json
import urllib.parse
import os
import threading
import time
import random
import re
from PIL import Image
from io import BytesIO
from zlapi.models import Message

des = {
    'version': "2.0.5",
    'credits': "Hoàng Khánh Premium",
    'description': "Tạo sticker từ ảnh/video, hỗ trợ JXL, không watermark",
    'power': "Thành viên"
}

def check_ffmpeg():
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=2)
        return result.returncode == 0
    except:
        return False

def detect_file_type_by_content(content):
    """Nhận diện loại file dựa vào magic bytes"""
    if len(content) < 12:
        return "unknown"
    
    # PNG
    if content[:8] == b'\x89PNG\r\n\x1a\n':
        return "image"
    # JPEG
    if content[:2] == b'\xff\xd8':
        return "image"
    # GIF
    if content[:6] in (b'GIF87a', b'GIF89a'):
        return "image"
    # WEBP
    if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return "image"
    # BMP
    if content[:2] == b'BM':
        return "image"
    # MP4 / Video
    if content[:4] == b'ftyp' or content[4:8] == b'ftyp':
        return "video"
    # AVI
    if content[:4] == b'RIFF' and content[8:12] == b'AVI ':
        return "video"
    # MKV / WebM
    if content[:4] == b'\x1aE\xdf\xa3':
        return "video"
    
    return "unknown"

def download_file_partial(url, max_bytes=8192):
    """Tải một phần đầu file để kiểm tra magic bytes"""
    headers = {'User-Agent': 'Mozilla/5.0', 'Range': f'bytes=0-{max_bytes-1}'}
    try:
        resp = requests.get(url, headers=headers, timeout=10, stream=True)
        if resp.status_code in (200, 206):
            return resp.content[:max_bytes]
    except:
        pass
    return None

def fix_jxl_url(url):
    """Chuyển đuôi .jxl hoặc .jx thành .jpg, và /jxl/ thành /jpg/"""
    url_lower = url.lower()
    if '.jxl' in url_lower:
        url = url.replace('.jxl', '.jpg')
    elif '.jx' in url_lower:
        url = url.replace('.jx', '.jpg')
    if '/jxl/' in url_lower:
        url = url.replace('/jxl/', '/jpg/')
    return url

def get_file_type_from_url(url):
    """Lấy loại file từ URL bằng magic bytes + fallback"""
    # Sửa URL .jxl
    url = fix_jxl_url(url)
    
    # Thử tải một phần file để kiểm tra
    partial = download_file_partial(url)
    if partial:
        file_type = detect_file_type_by_content(partial)
        if file_type != "unknown":
            return file_type
    
    # Fallback: kiểm tra đuôi mở rộng
    url_lower = url.lower()
    image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
    video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.m4v', '.3gp']
    
    for ext in image_exts:
        if ext in url_lower:
            return "image"
    for ext in video_exts:
        if ext in url_lower:
            return "video"
    
    return "unknown"

def process_image_from_content(content, size, temp_webp):
    """Xử lý ảnh từ dữ liệu đã tải"""
    try:
        img = Image.open(BytesIO(content))
    except Exception as e:
        # Nếu lỗi, thử tải lại với URL đã sửa
        raise e
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    
    new_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    new_img.paste(img, (x, y))
    
    new_img.save(temp_webp, format='WEBP', quality=80, method=3)
    return True

def get_video_duration(file_path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except:
        pass
    return 0

def process_video_from_url(media_url, size, temp_input, temp_webp):
    if not check_ffmpeg():
        return False
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(media_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    with open(temp_input, 'wb') as f:
        f.write(response.content)
    
    duration = get_video_duration(temp_input)
    
    scale_filter = f"scale={size}:{size}:force_original_aspect_ratio=1:flags=lanczos,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2"
    
    if duration > 30:
        scale_filter = f"trim=duration=30,setpts=PTS-STARTPTS,{scale_filter}"
    
    cmd = [
        "ffmpeg", "-y", "-i", temp_input,
        "-vf", scale_filter,
        "-c:v", "libwebp_anim",
        "-loop", "0",
        "-r", "12",
        "-q:v", "75",
        "-an",
        "-t", "30",
        "-loglevel", "error",
        temp_webp
    ]
    
    try:
        subprocess.run(cmd, check=True, timeout=45, capture_output=True)
        return True
    except:
        return False

def upload_to_catbox(file_path):
    try:
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': ('sticker.webp', f, 'image/webp')}
            response = requests.post('https://catbox.moe/user/api.php', files=files, data={'reqtype': 'fileupload'}, timeout=20)
        if response.status_code == 200 and response.text.startswith('https://'):
            return response.text.strip()
    except:
        pass
    return None

def upload_to_0x0st(file_path):
    try:
        with open(file_path, 'rb') as f:
            response = requests.post('https://0x0.st', files={'file': ('sticker.webp', f, 'image/webp')}, timeout=20)
        if response.status_code == 200:
            url = response.text.strip()
            if url.startswith('https://'):
                return url
    except:
        pass
    return None

def upload_to_tmpfiles(file_path):
    try:
        with open(file_path, 'rb') as f:
            response = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': ('sticker.webp', f, 'image/webp')}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') and data.get('data', {}).get('url'):
                return data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    except:
        pass
    return None

def upload_to_imgbb(file_path):
    try:
        import base64
        with open(file_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={'key': '6d207e02198a847aa98d0a2a901485a5', 'image': img_data, 'expiration': 600},
            timeout=20
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('url'):
                return data['data']['url']
    except:
        pass
    return None

def upload_file(file_path):
    services = [upload_to_catbox, upload_to_0x0st, upload_to_tmpfiles, upload_to_imgbb]
    for service in services:
        url = service(file_path)
        if url:
            return url
    return None

def handle_stk_command(message, message_object, thread_id, thread_type, author_id, client):
    """Xử lý lệnh tạo sticker"""
    
    # Kiểm tra reply
    if not message_object.quote or not message_object.quote.attach:
        client.replyMessage(Message(text="➜ Reply vào ảnh hoặc video để tạo sticker."), message_object, thread_id, thread_type, ttl=60000)
        return

    # Lấy kích thước (mặc định 512)
    size = 512
    cmd_text = message.strip().lower()
    size_match = re.search(r'stk\s+(\d+)', cmd_text)
    if size_match:
        size = int(size_match.group(1))
        if size not in [128, 256, 512]:
            size = 512

    # Lấy URL media từ attach
    try:
        attach_data = json.loads(message_object.quote.attach)
        media_url = attach_data.get('hdUrl') or attach_data.get('href')
        if not media_url:
            client.replyMessage(Message(text="➜ Không tìm thấy URL media."), message_object, thread_id, thread_type, ttl=60000)
            return

        media_url = urllib.parse.unquote(media_url.replace("\\/", "/"))
        
        # NHẬN DIỆN LOẠI FILE
        file_type = get_file_type_from_url(media_url)
        
        print(f"[DEBUG] URL: {media_url[:100]}")
        print(f"[DEBUG] Detected type: {file_type}")
        
        if file_type == "unknown":
            client.replyMessage(Message(text="❌ Không thể nhận diện file (không phải ảnh/video hợp lệ)."), message_object, thread_id, thread_type, ttl=60000)
            return

    except Exception as e:
        client.replyMessage(Message(text=f"➜ Lỗi lấy URL: {str(e)[:50]}"), message_object, thread_id, thread_type, ttl=60000)
        return

    # Xử lý trong thread riêng
    def process_and_send():
        temp_dir = os.path.join(os.path.dirname(__file__), 'cache', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        unique_id = f"{thread_id}_{int(time.time())}_{random.randint(1000, 9999)}"
        temp_webp = os.path.join(temp_dir, f"sticker_{unique_id}.webp")
        temp_input = os.path.join(temp_dir, f"video_{unique_id}.mp4")
        
        try:
            # Sửa URL .jxl trước khi tải
            download_url = fix_jxl_url(media_url)
            
            if file_type == "image":
                headers = {'User-Agent': 'Mozilla/5.0'}
                resp = requests.get(download_url, headers=headers, timeout=20)
                resp.raise_for_status()
                success = process_image_from_content(resp.content, size, temp_webp)
            else:
                if not check_ffmpeg():
                    client.replyMessage(Message(text="➜ Lỗi: Chưa cài FFmpeg."), message_object, thread_id, thread_type, ttl=60000)
                    return
                
                client.replyMessage(Message(text="⏳ Đang xử lý video (tối đa 30s)..."), message_object, thread_id, thread_type, ttl=30000)
                success = process_video_from_url(download_url, size, temp_input, temp_webp)
            
            if not success:
                client.replyMessage(Message(text="❌ Xử lý thất bại."), message_object, thread_id, thread_type, ttl=60000)
                return
            
            # Upload sticker
            webp_url = upload_file(temp_webp)
            
            if webp_url:
                client.sendCustomSticker(
                    animationImgUrl=webp_url,
                    staticImgUrl=webp_url,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    width=size,
                    height=size
                )
            else:
                client.replyMessage(Message(text="❌ Upload thất bại."), message_object, thread_id, thread_type, ttl=60000)
                
        except Exception as e:
            print(f"[DEBUG] Error: {e}")
            client.replyMessage(Message(text=f"❌ Lỗi: {str(e)[:50]}"), message_object, thread_id, thread_type, ttl=60000)
        finally:
            for f in [temp_webp, temp_input]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except:
                    pass
    
    threading.Thread(target=process_and_send, daemon=True).start()

# QUAN TRỌNG: Hàm LIGHT để bot nhận diện module
def LIGHT():
    return {'stk': handle_stk_command}