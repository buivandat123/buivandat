import requests
import os
import urllib.parse
import mimetypes
import re
import json
from io import BytesIO
from zlapi.models import Message
import time
import random
import warnings
warnings.filterwarnings('ignore')

des = {
    'version': "1.0.2",
    'credits': "Nguyễn Văn Bảo",
    'description': "Tải file/video từ link và gửi trực tiếp lên chat",
    'power': "Thành viên"
}

def get_session():
    """Tạo session để tải file"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

def extract_links_from_text(text):
    """Trích xuất link từ text"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    links = re.findall(url_pattern, text)
    return links

def get_filename_from_url(url, content_type=''):
    """Lấy tên file từ URL hoặc content-type"""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    filename = os.path.basename(path)
    
    if not filename or '.' not in filename:
        ext = mimetypes.guess_extension(content_type.split(';')[0]) if content_type else '.bin'
        if not ext:
            ext = '.bin'
        timestamp = int(time.time())
        filename = f"download_{timestamp}{ext}"
    
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename

def get_file_size(url, session):
    """Lấy kích thước file"""
    try:
        response = session.head(url, allow_redirects=True, timeout=10)
        size = int(response.headers.get('content-length', 0))
        return size
    except:
        return 0

def format_file_size(size):
    """Định dạng kích thước file"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def is_video_file(filename, content_type):
    """Kiểm tra có phải file video không"""
    video_extensions = ['.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv', '.m4v', '.3gp', '.ts']
    video_mimes = ['video/', 'application/vnd.apple.mpegurl', 'application/x-mpegURL']
    
    # Kiểm tra extension
    ext = os.path.splitext(filename)[1].lower()
    if ext in video_extensions:
        return True
    
    # Kiểm tra content-type
    if content_type:
        if any(video_mime in content_type.lower() for video_mime in video_mimes):
            return True
    
    return False

def download_file(url, temp_path):
    """Tải file về máy"""
    session = get_session()
    
    try:
        response = session.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True, os.path.getsize(temp_path)
        
    except Exception as e:
        return False, str(e)

def send_file_directly(client, file_path, filename, thread_id, thread_type):
    """Gửi file trực tiếp (không qua upload)"""
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Gửi file
        client.sendCustomFile(
            url=None,  # Không dùng URL, gửi trực tiếp
            fileName=filename,
            fileSize=len(file_data),
            thread_id=thread_id,
            thread_type=thread_type,
            message=None,
            fileData=file_data  # Gửi trực tiếp dữ liệu file
        )
        return True
    except Exception as e:
        print(f"Lỗi gửi file trực tiếp: {e}")
        return False

def send_video_directly(client, file_path, filename, thread_id, thread_type):
    """Gửi video trực tiếp"""
    try:
        with open(file_path, 'rb') as f:
            video_data = f.read()
        
        # Gửi video
        client.sendCustomVideo(
            url=None,
            videoFileName=filename,
            videoSize=len(video_data),
            videoData=video_data,
            thread_id=thread_id,
            thread_type=thread_type,
            thumbnail=None,
            duration=0,
            width=0,
            height=0
        )
        return True
    except Exception as e:
        print(f"Lỗi gửi video trực tiếp: {e}")
        # Nếu không gửi được video, thử gửi như file thường
        return send_file_directly(client, file_path, filename, thread_id, thread_type)

def send_image_directly(client, file_path, filename, thread_id, thread_type):
    """Gửi ảnh trực tiếp"""
    try:
        with open(file_path, 'rb') as f:
            img_data = f.read()
        
        client.sendCustomImage(
            url=None,
            imgFileName=filename,
            imgSize=len(img_data),
            imgData=img_data,
            thread_id=thread_id,
            thread_type=thread_type
        )
        return True
    except Exception as e:
        print(f"Lỗi gửi ảnh trực tiếp: {e}")
        return False

def handle_dl_command(message, message_object, thread_id, thread_type, author_id, client):
    """
    Lệnh dl - Tải file/video từ link và gửi trực tiếp lên chat
    """
    
    # Lấy link từ message hoặc reply
    links = []
    
    if message:
        links = extract_links_from_text(message)
    
    if not links and message_object.quote:
        quote_msg = message_object.quote
        if quote_msg.content:
            links = extract_links_from_text(quote_msg.content)
        if quote_msg.attach:
            try:
                attach_data = json.loads(quote_msg.attach)
                attach_url = attach_data.get('hdUrl') or attach_data.get('href') or attach_data.get('url')
                if attach_url:
                    links.append(attach_url)
            except:
                pass
    
    if not links:
        client.replyMessage(
            Message(text="❌ Vui lòng cung cấp link tải!\n📝 Cách dùng: dl <link> hoặc reply vào tin nhắn có link"),
            message_object, thread_id, thread_type, ttl=10000
        )
        return
    
    # Xử lý từng link
    for link in links:
        link = urllib.parse.unquote(link)
        
        # Gửi thông báo đang tải
        client.replyMessage(
            Message(text=f"⏳ Đang tải...\n🔗 {link[:80]}..."),
            message_object, thread_id, thread_type, ttl=30000
        )
        
        # Tạo thư mục tạm
        script_dir = os.path.dirname(__file__)
        temp_dir = os.path.join(script_dir, 'cache', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        unique_id = f"{thread_id}_{int(time.time())}_{random.randint(1000, 9999)}"
        temp_file = os.path.join(temp_dir, f"download_{unique_id}.tmp")
        
        try:
            # Lấy thông tin file
            session = get_session()
            content_type = session.head(link).headers.get('content-type', '')
            filename = get_filename_from_url(link, content_type)
            file_size = get_file_size(link, session)
            
            # Tải file
            success, result = download_file(link, temp_file)
            
            if not success:
                raise Exception(result)
            
            if os.path.getsize(temp_file) == 0:
                raise Exception("File rỗng hoặc không tải được")
            
            # Kiểm tra loại file
            is_video = is_video_file(filename, content_type)
            is_image = content_type.startswith('image/') or filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
            
            # Gửi file theo loại
            if is_video:
                success = send_video_directly(client, temp_file, filename, thread_id, thread_type)
                file_type = "video"
            elif is_image:
                success = send_image_directly(client, temp_file, filename, thread_id, thread_type)
                file_type = "ảnh"
            else:
                success = send_file_directly(client, temp_file, filename, thread_id, thread_type)
                file_type = "file"
            
            if success:
                # Xóa thông báo đang tải
                # (không thể xóa vì không có hàm deleteMessage, nhưng cũng không sao)
                pass
            else:
                raise Exception(f"Không thể gửi {file_type}")
            
        except Exception as e:
            error_msg = str(e)
            client.replyMessage(
                Message(text=f"❌ Lỗi: {error_msg[:150]}"),
                message_object, thread_id, thread_type, ttl=10000
            )
        
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

def LIGHT():
    return {
        'dl': handle_dl_command
    }