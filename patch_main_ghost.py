# patch_main_ghost.py
import os
import re
import shutil
from datetime import datetime

def patch_main():
    main_path = "main.py"
    
    if not os.path.exists(main_path):
        print("❌ Không tìm thấy main.py")
        return False
    
    # Backup
    backup_path = f"main_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    shutil.copy(main_path, backup_path)
    print(f"✅ Backup: {backup_path}")
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ============================================================
    # PATCH 1: Thêm import ghost và mute
    # ============================================================
    if "from modules.ghost import push_ghost_message, is_ghost_available" not in content:
        content = content.replace(
            "import logging",
            "import logging\nfrom modules.ghost import push_ghost_message, is_ghost_available, is_ghost_enabled\nfrom modules.mute import is_muted"
        )
        print("✅ Patch 1: Thêm import ghost và mute")
    
    # ============================================================
    # PATCH 2: Thêm kiểm tra mute vào onMessage
    # ============================================================
    if "is_muted" in content and "Kiểm tra mute" not in content:
        pattern = r'(def onMessage\(self, message, message_object, thread_id, thread_type, author_id\):)\s*\n'
        mute_check = '''        # ===== KIỂM TRA MUTE =====
        if thread_type == ThreadType.GROUP and is_muted(self, thread_id, author_id):
            return
        # =========================
        
'''
        content = re.sub(pattern, r'\1\n' + mute_check, content)
        print("✅ Patch 2: Thêm kiểm tra mute")
    
    # ============================================================
    # PATCH 3: Thêm push ghost vào cuối xử lý lệnh
    # ============================================================
    if "push_ghost_message" in content and "push ghost" not in content:
        # Tìm chỗ xử lý lệnh và thêm push ghost
        pattern = r'(if handler:\s+try:\s+handler\(message, message_object, thread_id, thread_type, author_id, self\)\s+except Exception as e:.*?\n\s+)(?=\s+def |\s+if |\s+return|\Z)'
        
        def add_ghost_push(match):
            code = match.group(0)
            # Thêm push ghost sau khi xử lý xong
            ghost_push = '''                # ===== PUSH GHOST =====
                if is_ghost_enabled(self):
                    push_ghost_message(self, message_object, thread_id)
                # ======================
'''
            return code + ghost_push
        
        content = re.sub(pattern, add_ghost_push, content, flags=re.DOTALL)
        print("✅ Patch 3: Thêm push ghost")
    
    # ============================================================
    # GHI FILE
    # ============================================================
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "="*50)
    print("✅ PATCH THÀNH CÔNG!")
    print("="*50)
    print("\n📌 Các tính năng đã thêm:")
    print("  ✅ Mute - Cấm người dùng nói trong nhóm")
    print("  ✅ Ghost - Tự động xóa tin nhắn sau khi gửi")
    print("\n📌 Cách dùng:")
    print("  .mute @user 1h      - Cấm 1 giờ")
    print("  .mute list           - Xem danh sách bị cấm")
    print("  .mute un @user       - Bỏ cấm")
    print("  .ghost on            - Bật chế độ ma")
    print("  .ghost off           - Tắt chế độ ma")
    print("  .ghost delay 30      - Xóa sau 30s")
    print("\n🔄 RESTART BOT để áp dụng!")
    
    return True

def restore_backup():
    """Khôi phục main.py từ backup"""
    backups = [f for f in os.listdir('.') if f.startswith('main_backup_') and f.endswith('.py')]
    if not backups:
        print("❌ Không tìm thấy file backup!")
        return
    backups.sort(reverse=True)
    shutil.copy(backups[0], 'main.py')
    print(f"✅ Đã khôi phục từ {backups[0]}")

def show_status():
    """Kiểm tra trạng thái patch"""
    if not os.path.exists("main.py"):
        print("❌ Không tìm thấy main.py!")
        return
    with open("main.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📊 TRẠNG THÁI PATCH:")
    print("="*40)
    checks = [
        ("Import ghost", "from modules.ghost import push_ghost_message"),
        ("Import mute", "from modules.mute import is_muted"),
        ("Kiểm tra mute", "Kiểm tra MUTE"),
        ("Push ghost", "push_ghost_message")
    ]
    for name, pattern in checks:
        status = "✅" if pattern in content else "❌"
        print(f"  {name}: {status}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "restore":
            restore_backup()
        elif cmd == "status":
            show_status()
        else:
            print("📌 Cách dùng:")
            print("  python patch_main_ghost.py          - Patch main.py")
            print("  python patch_main_ghost.py restore  - Khôi phục backup")
            print("  python patch_main_ghost.py status   - Kiểm tra trạng thái")
    else:
        patch_main()