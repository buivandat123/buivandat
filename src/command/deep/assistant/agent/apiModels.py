from io import BytesIO
import json
from dataclasses import dataclass
from typing import List, Optional, Callable, Any
from google import genai
from google.genai import types
import base64
import sys
from openai import OpenAI

class ApiModels:
    @property
    def keyPath(this):
        return "assets/config/ai-database.json"

    @dataclass
    class Keys:
        Gemini: List[str]
        Gpt: List[str]

    def __init__(this):
        this.keyIndexGemini = 0
        this.keyIndexGpt = 0
        this.keys = this.loadKeys()

    def loadKeys(this):
        with open(this.keyPath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return this.Keys(
            Gemini=data.get("GEMINI", []) or [],
            Gpt=data.get("GPT", []) or []
        )

    def rotateGemini(this) -> Optional[str]:
        keys = this.keys.Gemini
        if not keys:
            return None
        key = keys[this.keyIndexGemini]
        this.keyIndexGemini = (this.keyIndexGemini + 1) % len(keys)
        return key

    def rotateGpt(this) -> Optional[str]:
        keys = this.keys.Gpt
        if not keys:
            return None
        key = keys[this.keyIndexGpt]
        this.keyIndexGpt = (this.keyIndexGpt + 1) % len(keys)
        return key

    def tryMany(this, count: int, clientFactory: Callable[[], Any], call: Callable[[Any], Any]):
        lastErr = None
        loops = count if count and count > 0 else 1
        for i in range(loops):
            try:
                c = clientFactory()
                if not c:
                    break
                return call(c)
            except Exception as e:
                lastErr = e
        if lastErr:
            raise lastErr
        raise RuntimeError("No API keys configured")

    def geminiCall(this, call: Callable[[Any], Any]):
        return this.tryMany(
            len(this.keys.Gemini),
            lambda: genai.Client(api_key=this.rotateGemini()) if this.keys.Gemini else None,
            call
        )

    def gptCall(this, call: Callable[[Any], Any]):
        return this.tryMany(
            len(this.keys.Gpt),
            lambda: OpenAI(api_key=this.rotateGpt()) if this.keys.Gpt else None,
            call
        )

    def geminiThenGpt(this, geminiCall: Callable[[Any], Any], gptCall: Callable[[Any], Any]):
        try:
            return this.geminiCall(geminiCall)
        except Exception:
            return this.gptCall(gptCall)

class GeminiContent:
    def __init__(this, api: ApiModels):
        this.api = api
        this.prompt = ""

    def getText(this):
        return this.api.geminiThenGpt(
            lambda c: c.models.generate_content(model="gemini-2.5-flash", contents=this.prompt).text,
            lambda c: c.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": this.prompt}]
            ).choices[0].message.content
        )

class GeminiGenerateImages:
    def __init__(this, api: ApiModels):
        this.api = api
        this.prompt = ""

    def getImagesBytes(this):
        def CollectParts(r):
            if getattr(r, "parts", None):
                return r.parts
            cands = getattr(r, "candidates", None) or []
            if cands:
                c0 = cands[0]
                content = getattr(c0, "content", None)
                if content and getattr(content, "parts", None):
                    return content.parts
            return []

        def DoGemini(client):
            r = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[this.prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    number_of_images=1,
                    aspect_ratio="1:1",
                    image_size="1K",
                ),
            )
            parts = CollectParts(r)
            out = []
            for part in parts:
                if getattr(part, "inline_data", None) is not None:
                    img = part.as_image()
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    out.append(buf.getvalue())

            if not out:
                raise RuntimeError("Gemini image empty")
            return out

        return this.api.geminiThenGpt(DoGemini, lambda c: [])