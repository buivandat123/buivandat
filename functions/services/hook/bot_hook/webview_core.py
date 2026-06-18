import asyncio
import argparse
from urllib.parse import urlparse
from playwright.async_api import async_playwright

def NormalizeUrl(Url: str) -> str:
    U = (Url or "").strip()
    if not U:
        raise ValueError("Missing Url")
    if not U.startswith(("http://", "https://")):
        U = "https://" + U
    P = urlparse(U)
    if not P.netloc:
        raise ValueError("Invalid Url")
    return U

async def Shot(Url: str, OutPath: str, FullPage: bool, Width: int, Height: int, Scale: float, WaitMs: int, TimeoutMs: int, Fmt: str, Quality: int, Debug: bool):
    Url = NormalizeUrl(Url)
    Fmt = (Fmt or "png").lower().strip()
    if Fmt == "jpg":
        Fmt = "jpeg"
    if Fmt not in ("png", "jpeg", "webp"):
        raise ValueError("Fmt must be png|jpeg|webp")

    async with async_playwright() as P:
        Browser = await P.chromium.launch(
            headless=not Debug,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
            ],
        )
        Ctx = await Browser.new_context(
            viewport={"width": int(Width), "height": int(Height)},
            device_scale_factor=float(Scale),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        Page = await Ctx.new_page()
        Page.set_default_timeout(int(TimeoutMs))
        Page.set_default_navigation_timeout(int(TimeoutMs))

        await Page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        )

        try:
            Resp = None
            for WaitUntil in ("domcontentloaded", "load"):
                try:
                    Resp = await Page.goto(Url, wait_until=WaitUntil, timeout=int(TimeoutMs))
                    break
                except:
                    Resp = None

            if Resp is not None:
                Status = Resp.status
            else:
                Status = -1

            try:
                await Page.wait_for_load_state("networkidle", timeout=min(int(TimeoutMs), 30000))
            except:
                pass

            await Page.wait_for_timeout(max(0, int(WaitMs)))

            try:
                await Page.wait_for_function(
                    "document.body && document.body.innerText && document.body.innerText.trim().length > 0",
                    timeout=min(int(TimeoutMs), 12000),
                )
            except:
                pass

            try:
                await Page.evaluate("() => document.fonts && document.fonts.ready ? document.fonts.ready : null")
            except:
                pass

            Kw = {"full_page": bool(FullPage), "type": Fmt}
            if Fmt in ("jpeg", "webp"):
                Kw["quality"] = int(Quality)

            await Page.screenshot(path=OutPath, **Kw)

            if Status >= 400 or Status == -1:
                HtmlPath = OutPath.rsplit(".", 1)[0] + ".html"
                try:
                    Html = await Page.content()
                    with open(HtmlPath, "w", encoding="utf-8") as f:
                        f.write(Html)
                except:
                    pass
        finally:
            try:
                await Ctx.close()
            except:
                pass
            try:
                await Browser.close()
            except:
                pass

def ParseArgs():
    P = argparse.ArgumentParser()
    P.add_argument("Url")
    P.add_argument("-o", "--out", default="shot.png")
    P.add_argument("--full", action="store_true")
    P.add_argument("--width", type=int, default=1366)
    P.add_argument("--height", type=int, default=768)
    P.add_argument("--scale", type=float, default=1.0)
    P.add_argument("--wait", type=int, default=1200)
    P.add_argument("--timeout", type=int, default=30000)
    P.add_argument("--fmt", default="png")
    P.add_argument("--quality", type=int, default=85)
    P.add_argument("--debug", action="store_true")
    return P.parse_args()

if __name__ == "__main__":
    A = ParseArgs()
    asyncio.run(Shot(A.Url, A.out, A.full, A.width, A.height, A.scale, A.wait, A.timeout, A.fmt, A.quality, A.debug))