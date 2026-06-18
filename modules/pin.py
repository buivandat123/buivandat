import time
import re
import os
import requests
import urllib.parse
import random
from zlapi.models import Message, ThreadType

des = {
    'version': "1.1.0",
    'credits': "Khanh Sang & Yuta Bot",
    'description': "Tim anh tu Pinterest",
    'power': "Thanh vien"
}

CACHE_DIR = "modules/cache/pin"
os.makedirs(CACHE_DIR, exist_ok=True)

def handle_pin_command(message, message_object, thread_id, thread_type, author_id, client):
    prefix = client.settings.get("prefix", ".")
    
    # Xoa prefix va ten lenh
    cmd = message.strip()
    if cmd.startswith(prefix):
        cmd = cmd[len(prefix):].strip()
    
    if cmd.startswith("pin"):
        content = cmd[3:].strip()
    else:
        return
    
    if not content:
        help_text = f"""
TIM ANH TREN PINTEREST

Cach dung: {prefix}pin <tu khoa> <so luong>
Vi du: {prefix}pin dog 5
{prefix}pin hoa 3

So luong: 1-10 anh
        """
        client.replyMessage(Message(text=help_text.strip()), message_object, thread_id, thread_type, ttl=30000)
        return

    parts = content.split()
    
    # Lay so luong (mac dinh la 1)
    try:
        if parts[-1].isdigit():
            num_images = min(int(parts[-1]), 10)
            search_terms = " ".join(parts[:-1])
        else:
            num_images = 1
            search_terms = content
    except:
        num_images = 1
        search_terms = content
    
    if not search_terms.strip():
        client.replyMessage(Message(text="Vui long nhap tu khoa can tim!"), message_object, thread_id, thread_type, ttl=30000)
        return
    
    if num_images < 1:
        num_images = 1
    if num_images > 10:
        num_images = 10
    
    # Gui thong bao
    client.replyMessage(
        Message(text=f"🔍 Dang tim kiem '{search_terms}'..."),
        message_object, thread_id, thread_type, ttl=5000
    )
    
    try:
        encoded_text = urllib.parse.quote(search_terms)
        
        # Thu nhieu API khac nhau
        apis = [
            f"https://pinterest-api-one.vercel.app/?search={encoded_text}",
            f"https://pinterest-api.vercel.app/?search={encoded_text}",
            f"https://pinterest-downloader.p.rapidapi.com/search?query={encoded_text}&count={num_images}"
        ]
        
        image_urls = []
        
        for api_url in apis:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(api_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Xu ly theo tung format API
                    if isinstance(data, list):
                        for item in data[:num_images]:
                            if isinstance(item, str) and item.startswith('http'):
                                image_urls.append(item)
                            elif isinstance(item, dict) and 'url' in item:
                                image_urls.append(item['url'])
                            elif isinstance(item, dict) and 'image' in item:
                                image_urls.append(item['image'])
                    elif isinstance(data, dict):
                        if 'data' in data and isinstance(data['data'], list):
                            for item in data['data'][:num_images]:
                                if isinstance(item, str):
                                    image_urls.append(item)
                                elif isinstance(item, dict) and 'url' in item:
                                    image_urls.append(item['url'])
                        elif 'images' in data and isinstance(data['images'], list):
                            image_urls = data['images'][:num_images]
                        elif 'results' in data and isinstance(data['results'], list):
                            for item in data['results'][:num_images]:
                                if 'url' in item:
                                    image_urls.append(item['url'])
                                elif 'image' in item:
                                    image_urls.append(item['image'])
                    
                    if image_urls:
                        break
            except:
                continue
        
        # Neu khong co ket qua tu API, thu cach khac
        if not image_urls:
            # Fallback: dung unsplash API
            try:
                unsplash_url = f"https://source.unsplash.com/featured/?{encoded_text}&{num_images}"
                image_urls = [unsplash_url]
            except:
                pass
        
        if not image_urls:
            client.replyMessage(
                Message(text=f"❌ Khong tim thay anh cho '{search_terms}'\nVui long thu tu khoa khac!"),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        
        # Tai va gui anh
        image_paths = []
        success_count = 0
        
        for idx, img_url in enumerate(image_urls[:num_images]):
            try:
                img_response = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                if img_response.status_code == 200:
                    img_path = os.path.join(CACHE_DIR, f"pin_{int(time.time())}_{idx}.jpg")
                    with open(img_path, 'wb') as f:
                        f.write(img_response.content)
                    image_paths.append(img_path)
                    success_count += 1
            except:
                continue
        
        if success_count == 0:
            client.replyMessage(
                Message(text="❌ Khong the tai anh! Vui long thu lai."),
                message_object, thread_id, thread_type, ttl=30000
            )
            return
        
        # Gui anh
        if success_count == 1:
            client.sendLocalImage(
                image_paths[0],
                thread_id=thread_id,
                thread_type=thread_type,
                message=Message(text=f"🖼️ Ket qua tim '{search_terms}':"),
                ttl=120000
            )
        else:
            client.sendMultiLocalImage(
                imagePathList=image_paths,
                message=Message(text=f"🖼️ Da tim thay {success_count} anh cho '{search_terms}'"),
                thread_id=thread_id,
                thread_type=thread_type,
                width=800,
                height=800,
                ttl=120000
            )
        
        client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
        
        # Xoa file tam
        for path in image_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
                
    except requests.exceptions.Timeout:
        client.replyMessage(
            Message(text="❌ Yeu cau het thoi gian! Vui long thu lai."),
            message_object, thread_id, thread_type, ttl=30000
        )
    except Exception as e:
        client.replyMessage(
            Message(text=f"❌ Loi: {str(e)[:100]}"),
            message_object, thread_id, thread_type, ttl=30000
        )

def LIGHT():
    return {
        'pin': handle_pin_command
    }