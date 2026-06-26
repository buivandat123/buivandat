# app/core/server/live/apiHome.py
from ..libs import app, PublicDir
from flask import send_from_directory, session, render_template
import os

@app.get("/")
def Home():
    dist = os.path.join(PublicDir, "dist")
    if session.get("account"):
        return send_from_directory(dist, "dashboard.html")
    return send_from_directory(dist, "login.html")

@app.get("/dashboard")
def Dashboard():
    dist = os.path.join(PublicDir, "dist")
    if session.get("account"):
        return send_from_directory(dist, "dashboard.html")
    return send_from_directory(dist, "login.html")

@app.get("/admin/login")
def AdminLoginPage():
    return send_from_directory(os.path.join(PublicDir, "admin"), "login.html")

@app.get("/admin/dashboard")
def AdminDashboardPage():
    if not session.get("isAdmin"):
        return send_from_directory(os.path.join(PublicDir, "admin"), "login.html")
    return send_from_directory(os.path.join(PublicDir, "admin"), "dashboard.html")

@app.get("/bot/<bot_id>/login")
def BotLoginPage(bot_id):
    return send_from_directory(os.path.join(PublicDir, "bot"), "login.html")

@app.get("/bot/<bot_id>")
def BotDashboardPage(bot_id):
    if session.get("botIntId") != bot_id:
        return send_from_directory(os.path.join(PublicDir, "bot"), "login.html")
    return send_from_directory(os.path.join(PublicDir, "bot"), "dashboard.html")

@app.get("/<path:p>")
def StaticFiles(p):
    dist = os.path.join(PublicDir, "dist")
    fp_dist = os.path.join(dist, p)
    if os.path.isfile(fp_dist):
        return send_from_directory(dist, p)
    fp = os.path.join(PublicDir, p)
    if os.path.isfile(fp):
        return send_from_directory(PublicDir, p)
    return send_from_directory(dist, "login.html")
