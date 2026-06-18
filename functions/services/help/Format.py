def Fmt(t):
    try:
        t = int(t or 0)
    except:
        t = 0
    if t > 24 * 3600:
        t //= 1000
    h, t = divmod(t, 3600)
    m, s = divmod(t, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"