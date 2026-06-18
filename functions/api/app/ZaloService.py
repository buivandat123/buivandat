from .ZaloWorker import *

class ZaloAPI(*ApisMethod, framework):
    def __init__(this, phone, password, imei, sessionCookies=None, userAgent=None, autoLogin=True, login=loginapi):
        this.initFrameWork(phone, password, imei, sessionCookies, userAgent, autoLogin, login)