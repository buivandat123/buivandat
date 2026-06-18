import json
import os
import time

BOT_START_TIME = time.time()

def get_uptime():
    elapsed = int(time.time() - BOT_START_TIME)
    h = elapsed // 3600
    m = (elapsed % 3600) // 60
    s = elapsed % 60
    return f"{h}h {m}m {s}s"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, 'seting.json')

def read_setting_value(key):
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings.get(key)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {SETTINGS_PATH}. Sử dụng giá trị mặc định cho {key}.")
        return None
    except json.JSONDecodeError:
        print(f"Lỗi: File {SETTINGS_PATH} không hợp lệ. Sử dụng giá trị mặc định cho {key}.")
        return None

def read_prefix():
    return read_setting_value('prefix') or "?"

def read_admin():
    return read_setting_value('admin') or "2057392636234756923"

IMEI = "254e63a6-bc3a-4eee-9a9f-001bb8064146-6d797a3d21eb30c3af058ab3a2bf562d"
SESSION_COOKIES ={"_ga_VM4ZJE1265":"GS2.2.s1772599019$o1$g0$t1772599019$j60$l0$h0","ozi":"2000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjMXe9fFM8W-cUwbc4fUYZsTfwUUJH2ECvEbgv904Oy.1","_ga_YT9TMXZYV9":"GS2.1.s1774932503$o2$g1$t1774932514$j49$l0$h0","_ga_YS1V643LGV":"GS2.1.s1776044832$o7$g0$t1776044832$j60$l0$h0","_ga_RYD7END4JE":"GS2.2.s1776044833$o6$g0$t1776044833$j60$l0$h0","_ga":"GA1.2.560451865.1772599019","__zi":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WzaEkdaKDOWdcLwgdKGb-0T9Rjf3Gu.1","__zi-legacy":"3000.SSZzejyD6zOgdh2mtnLQWYQN_RAG01ICFjIXe9fEM8WzaEkdaKDOWdcLwgdKGb-0T9Rjf3Gu.1","app.event.zalo.me":"8738922422920909519","_zlang":"vn","_gid":"GA1.2.2048443389.1781255010","_ga_3EM8ZPYYN3":"GS2.2.s1781255011$o31$g0$t1781255011$j60$l0$h0","zpsid":"Y89u.439638469.37.HEZwhgh6zunldyEMfiRtZD-rXRYP_y6_alB1jQGdMbzwXim2gxqyfy36zum","zpw_sek":"bZL8.439638469.a0.Eq0qvReavt9_VTDecoJdSi46WXcO7iKsrs6Z7l5bXX7YKBOOubImE_bpemFx6TfGnoe6tsdqfqaq9PovaKxdSW"}
API_KEY = 'api_key'
SECRET_KEY = 'secret_key'
PREFIX = read_prefix()
ADMIN = read_admin()
GEMINI_API_KEY = "AIzaSyBiKqIS4xlwQHMlsv7MLzeRoYl_5ppal"