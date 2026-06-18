# modules/scl.py
# -*- coding: utf-8 -*-
import os
import requests
import re
import time
import tempfile
import threading
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import subprocess
from zlapi.models import Message
from modules.canvas import *

des = {
    'version': "3.2.0",
    'credits': "Hoàng Khánh Premium",
    'description': "Tải nhạc SoundCloud nhanh chóng.",
    'power': "Thành viên"
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

_search_results = {}

# Danh sách client_id dự phòng
CLIENT_IDS = [
    "VhS9YhXpPfLpE0Rc3K7m",
    "a3e1a9f8b5c6d7e8f9a0b1c2",
    "Gg3sE4dF5gH6jK7lL8zX9cC",
    "M7nB8vC9xZ0a1s2d3f4g5h6",
]

def get_client_id():
    for cid in CLIENT_IDS:
        try:
            test_url = f"https://api-v2.soundcloud.com/search/tracks?q=test&client_id={cid}&limit=1"
            resp = requests.get(test_url, timeout=5)
            if resp.status_code == 200:
                return cid
        except:
            continue
    
    try:
        resp = requests.get("https://soundcloud.com", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        match = re.search(r'client_id:"(.*?)"', resp.text)
        if match:
            return match.group(1)
    except:
        pass
    
    return "VhS9YhXpPfLpE0Rc3K7m"

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://soundcloud.com/"
    }

def ms_to_mmss(ms):
    seconds = ms // 1000
    minutes = seconds // 60
    seconds %= 60
    return f"{minutes}:{seconds:02d}"

def search_soundcloud(query, limit=8):
    try:
        client_id = get_client_id()
        if not client_id:
            return []
        
        url = f'https://api-v2.soundcloud.com/search/tracks?q={requests.utils.quote(query)}&client_id={client_id}&limit={limit}'
        resp = requests.get(url, headers=get_headers(), timeout=15)
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        songs = []
        for item in data.get('collection', []):
            songs.append({
                'title': item.get('title', 'Unknown'),
                'artist': item.get('user', {}).get('username', 'Unknown'),
                'duration': item.get('duration', 0),
                'cover': item.get('artwork_url', '').replace('-large', '-t500x500'),
                'url': item.get('permalink_url', '')
            })
        return songs
    except Exception as e:
        print(f"Search error: {e}")
        return []

def get_stream_url(track_url):
    try:
        client_id = get_client_id()
        if not client_id:
            return None
        
        resolve_url = f'https://api-v2.soundcloud.com/resolve?url={track_url}&client_id={client_id}'
        resp = requests.get(resolve_url, headers=get_headers(), timeout=10)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        for transcode in data.get('media', {}).get('transcodings', []):
            if transcode.get('format', {}).get('protocol') == 'progressive':
                stream_url = f"{transcode['url']}?client_id={client_id}"
                resp2 = requests.get(stream_url, headers=get_headers(), timeout=10)
                if resp2.status_code == 200:
                    return resp2.json().get('url')
        return None
    except Exception as e:
        print(f"Stream error: {e}")
        return None

def download_audio(url, output_path):
    try:
        resp = requests.get(url, stream=True, timeout=60)
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(16384):
                f.write(chunk)
        return output_path
    except Exception as e:
        print(f"Download error: {e}")
        return None

def convert_to_aac(input_path, output_path):
    try:
        cmd = ['ffmpeg', '-y', '-i', input_path, '-vn', '-c:a', 'aac', '-b:a', '96k', '-loglevel', 'error', output_path]
        subprocess.run(cmd, check=True, timeout=120)
        return output_path
    except:
        return None

def upload_to_tmpfiles(file_path):
    try:
        with open(file_path, 'rb') as f:
            response = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': (os.path.basename(file_path), f)}, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') and data.get('data', {}).get('url'):
                return data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    except:
        pass
    return None

def DrawSclCard(songs, out_path):
    img = CreateBackground(W, H)

    card = (PAD, PAD, W - PAD, H - PAD)
    Glass(img, card, radius=36)

    d = ImageDraw.Draw(img)

    cover_size = 400
    cover_pad = 44
    
    if songs:
        first = songs[0]
        cover = LoadImage(first.get("cover", ""), size=(500, 500))
        cover = CropSquare(cover).resize((cover_size, cover_size), Image.LANCZOS)
        mask = RoundMask(cover_size, cover_size, 28)
        img.paste(cover, (PAD + cover_pad, PAD + cover_pad), mask)

        tx = PAD + cover_pad + cover_size + 52
        ty = PAD + 70
        max_text_w = (W - PAD) - tx - 44

        title_font = Font(52, bold=True)
        artist_font = Font(32)
        time_font = Font(28)

        title = FitText(d, first.get("title", "Unknown"), title_font, max_text_w)
        artist = FitText(d, first.get("artist", "Unknown"), artist_font, max_text_w)
        duration = ms_to_mmss(first.get("duration", 0))

        d.text((tx, ty), title, font=title_font, fill=TextTitle)
        d.text((tx, ty + 75), artist, font=artist_font, fill=TextSub)
        d.text((tx, ty + 120), duration, font=time_font, fill=TextDim)

    items = songs[1:7] if len(songs) > 1 else []
    
    x1 = PAD + cover_pad
    y1 = PAD + cover_pad + cover_size + 50
    row_h = 65
    
    for i, song in enumerate(items[:5]):
        name = song.get("title", "Unknown")[:32]
        artist = song.get("artist", "Unknown")[:22]
        duration = ms_to_mmss(song.get("duration", 0))
        
        y = y1 + i * row_h
        d.text((x1 + 20, y), f"{i+1}. {name}", font=Font(28, bold=True), fill=TextTitle)
        d.text((x1 + 55, y + 35), f"{artist} | {duration}", font=Font(22), fill=TextSub)

    badge_font = Font(28, bold=True)
    badge_text = "SoundCloud"
    badge_w = 170
    badge_h = 46
    badge_x = W - PAD - badge_w - 20
    badge_y = H - PAD - badge_h - 20
    
    Glass(img, (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h), radius=23, alpha=(255, 255, 255, 22), blur=18)
    d.text((badge_x + badge_w // 2, badge_y + badge_h // 2), badge_text, font=badge_font, fill=(255, 200, 255), anchor="mm")

    img.save(out_path, "PNG", optimize=True)
    return out_path

def download_song(song, client, thread_id, thread_type, message_object):
    try:
        stream_url = get_stream_url(song['url'])
        if not stream_url:
            return
        
        temp_mp3 = os.path.join(CACHE_DIR, f"temp_{int(time.time())}.mp3")
        temp_aac = os.path.join(CACHE_DIR, f"temp_{int(time.time())}.aac")
        
        download_audio(stream_url, temp_mp3)
        convert_to_aac(temp_mp3, temp_aac)
        
        audio_url = upload_to_tmpfiles(temp_aac)
        
        if audio_url:
            file_size = os.path.getsize(temp_aac)
            client.sendRemoteVoice(audio_url, thread_id=thread_id, thread_type=thread_type, 
                                  fileSize=file_size, ttl=360000)
        
        for f in [temp_mp3, temp_aac]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass
    except Exception as e:
        print(f"Download song error: {e}")

def handle_scl(message, message_object, thread_id, thread_type, author_id, client):
    parts = message.strip().split()
    
    if len(parts) < 2:
        client.replyMessage(Message(text="🎵 Nhap ten bai hat!\nVD: scl <ten bai hat>"), 
                          message_object, thread_id, thread_type, ttl=60000)
        return
    
    query = " ".join(parts[1:])
    
    try:
        songs = search_soundcloud(query, limit=8)
        
        if not songs:
            client.replyMessage(Message(text="❌ Khong tim thay bai hat!"), 
                              message_object, thread_id, thread_type, ttl=60000)
            return
        
        _search_results[author_id] = {
            'songs': songs,
            'time': time.time()
        }
        
        out_path = os.path.join(CACHE_DIR, f"scl_{int(time.time())}.png")
        DrawSclCard(songs, out_path)
        
        with Image.open(out_path) as im:
            w, h = im.size
        
        client.sendLocalImage(out_path, thread_id=thread_id, thread_type=thread_type, 
                              message=Message(text=""), width=w, height=h)
        
        try:
            os.remove(out_path)
        except:
            pass
            
    except Exception as e:
        client.replyMessage(Message(text="❌ Loi!"), 
                          message_object, thread_id, thread_type, ttl=60000)

def handle_select(message, message_object, thread_id, thread_type, author_id, client):
    if not message.strip().isdigit():
        return
    
    if author_id not in _search_results:
        return
    
    num = int(message.strip())
    data = _search_results[author_id]
    
    if time.time() - data["time"] > 120:
        del _search_results[author_id]
        return
    
    songs = data["songs"]
    if num < 1 or num > len(songs):
        return
    
    song = songs[num - 1]
    del _search_results[author_id]
    
    threading.Thread(target=download_song, args=(song, client, thread_id, thread_type, message_object), daemon=True).start()

def LIGHT():
    return {
        "scl": handle_scl,
        "sc": handle_select
    }
