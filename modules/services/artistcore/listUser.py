# modules/services/artistcore/listUser.py
import os
from PIL import Image, ImageDraw, ImageFont

def DrawList(Owner, Admins, OutPath, Title=None, SubTitle=None, Source=None, ItemsPerPage=10):
    width = 800
    height = 200 + len(Admins) * 60
    img = Image.new('RGB', (width, height), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/system/fonts/Roboto-Regular.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    y = 20
    draw.text((20, y), f"Owner: {Owner.get('name', 'Unknown')}", fill='white', font=font)
    y += 40
    
    for admin in Admins:
        draw.text((20, y), f"- {admin.get('name', 'Unknown')} ({admin.get('role', '')})", fill='#a0aec0', font=font)
        y += 35
    
    img.save(OutPath)
    return OutPath, width, height
