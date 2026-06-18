from ....index import *
from html import unescape
from urllib.parse import urljoin, urlparse
import json
import re


class SendLinkApi:
    def _PickMeta(this, html, keys):
        for k in keys:
            m = re.search(
                r'<meta[^>]+(?:property|name)\s*=\s*["\']'
                + re.escape(k)
                + r'["\'][^>]+content\s*=\s*["\']([^"\']+)["\']',
                html,
                re.I,
            )
            if m:
                return unescape(m.group(1)).strip()

            m = re.search(
                r'<meta[^>]+content\s*=\s*["\']([^"\']+)["\'][^>]+(?:property|name)\s*=\s*["\']'
                + re.escape(k)
                + r'["\']',
                html,
                re.I,
            )
            if m:
                return unescape(m.group(1)).strip()

        return ""

    def _PickTitleTag(this, html):
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        return unescape(m.group(1)).strip() if m else ""

    def _PickFavicon(this, html, baseUrl):
        m = re.search(
            r'<link[^>]+rel=["\'](?:shortcut icon|icon)["\'][^>]+href=["\']([^"\']+)["\']',
            html,
            re.I,
        )
        if not m:
            m = re.search(
                r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\'](?:shortcut icon|icon)["\']',
                html,
                re.I,
            )

        if m:
            href = m.group(1).strip()
            return href if href.startswith("http") else urljoin(baseUrl, href)

        parsed = urlparse(baseUrl)
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico" if parsed.scheme and parsed.netloc else ""

    def _UploadThumbToZalo(this, thumbUrl):
        if not thumbUrl:
            return ""

        try:
            r = this.GetSession(thumbUrl, allow_redirects=True, timeout=15)
            ctype = (r.headers.get("content-type") or "image/jpeg").split(";")[0].strip().lower()
            ext_map = {
                "image/jpeg": "thumb.jpg",
                "image/jpg": "thumb.jpg",
                "image/png": "thumb.png",
                "image/gif": "thumb.gif",
                "image/webp": "thumb.webp",
            }
            filename = ext_map.get(ctype, "thumb.jpg")
            uploadUrl = "https://tt-files-wpa.chat.zalo.me/api/message/photo_original/upload"
            params = {"zpw_ver": 645, "zpw_type": this.apiLogintype}
            files = {"fileContent": (filename, r.content, ctype)}
            res = this.PostSession(uploadUrl, params=params, files=files).json()

            if res.get("error_code") == 0:
                decoded = this._decode(res.get("data", ""))
                if isinstance(decoded, dict):
                    cdn = (
                        decoded.get("normalUrl")
                        or decoded.get("hdUrl")
                        or decoded.get("thumb")
                        or decoded.get("url")
                        or ""
                    )
                    if cdn:
                        return cdn
        except Exception:
            pass

        return thumbUrl

    def _FetchLinkData(this, link):
        u = str(link or "").strip()
        if not u:
            return None
        if not re.match(r"^https?://", u, re.I):
            u = "https://" + u

        try:
            r = this.GetSession(u, allow_redirects=True, timeout=20)
            finalUrl = r.url or u
            host = urlparse(finalUrl).hostname or ""
            ctype = (r.headers.get("content-type") or "").lower()

            if "text/html" not in ctype and "application/xhtml" not in ctype:
                return {
                    "href": finalUrl,
                    "src": host,
                    "title": "",
                    "desc": "",
                    "thumb": "",
                    "icon": "",
                }

            html = r.text or ""
            title = this._PickMeta(html, ["og:title", "twitter:title"]) or this._PickTitleTag(html)
            desc = this._PickMeta(html, ["og:description", "twitter:description", "description"]) or ""
            thumb = this._PickMeta(html, ["og:image", "twitter:image", "twitter:image:src"]) or ""
            href = this._PickMeta(html, ["og:url"]) or finalUrl
            icon = this._PickFavicon(html, finalUrl)

            if thumb and not thumb.startswith("http"):
                thumb = urljoin(finalUrl, thumb)

            return {
                "href": href,
                "src": host,
                "title": title or "",
                "desc": desc or "",
                "thumb": thumb or "",
                "icon": icon or "",
            }
        except Exception:
            host = urlparse(u).hostname or ""
            return {
                "href": u,
                "src": host,
                "title": "",
                "desc": "",
                "thumb": "",
                "icon": "",
            }

    def _buildSendLink(
        this,
        linkUrl,
        threadId,
        type,
        message=None,
        ttl=0,
        title="",
        thumbnailUrl="",
        domainUrl="",
        desc="",
    ):
        params = {"zpw_ver": 645, "zpw_type": this.apiLogintype}
        linkData = this._FetchLinkData(linkUrl)

        if not linkData:
            raise ZaloUserError("Invalid link")

        custom_title = title or linkData["title"] or ""
        custom_thumb = thumbnailUrl or linkData["thumb"] or ""
        custom_desc = desc or linkData["desc"] or ""
        custom_src = domainUrl or linkData["src"] or urlparse(str(linkUrl or "")).hostname or ""
        custom_href = linkData["href"] or str(linkUrl or "")
        custom_icon = linkData.get("icon") or ""

        cdn_thumb = this._UploadThumbToZalo(custom_thumb) if custom_thumb else ""

        inner_params = {
            "redirect_url": "",
            "src": custom_src,
            "mediaTitle": custom_title,
            "title": custom_title,
            "desc": custom_desc,
            "streamUrl": "",
            "type": 12,
            "linkType": 12,
            "artist": "",
            "count": "",
            "stream_icon": custom_icon,
            "mediaId": "",
            "video_duration": 0,
            "arid": 0,
            "href": custom_href,
            "tType": 1,
            "tWidth": 486,
            "tHeight": 256,
            "width": 250,
            "height": 250,
            "thumb_renew": cdn_thumb,
            "local_path_thumb_link": cdn_thumb,
            "thumb_src_type": 1,
            "link_sub_type": 1,
            "video_brain": {
                "thumb": cdn_thumb,
                "title": custom_title,
                "desc": custom_desc,
                "src": custom_src,
                "href": custom_href,
                "icon": custom_icon,
            },
        }

        payloadParams = {
            "msg": (message.text if message else "") or "",
            "title": custom_title,
            "description": custom_desc,
            "href": custom_href,
            "thumb": cdn_thumb,
            "thumb_renew": cdn_thumb,
            "thumbWidth": 486,
            "thumbHeight": 256,
            "icon": custom_icon,
            "src": custom_src,
            "type": 12,
            "action": "recommened.link",
            "params": json.dumps(inner_params, ensure_ascii=False),
            "ttl": int(ttl or 0),
            "clientId": utils.now(),
        }

        if message and getattr(message, "mention", None):
            payloadParams["mentionInfo"] = message.mention
        elif type == ThreadType.GROUP:
            payloadParams["mentionInfo"] = "[]"

        if type == ThreadType.USER:
            url = "https://tt-chat4-wpa.chat.zalo.me/api/message/link"
            payloadParams["toId"] = str(threadId)
        elif type == ThreadType.GROUP:
            url = "https://tt-group-wpa.chat.zalo.me/api/group/sendlink"
            payloadParams["imei"] = this._imei
            payloadParams["grid"] = str(threadId)
            payloadParams["visibility"] = 0
        else:
            raise ZaloUserError("Thread type is invalid")

        payload = {"params": this._encode(payloadParams)}
        return url, params, payload, type

    def _parseSendLink(this, data, type):
        results = data.get("data") if data.get("error_code") == 0 else None
        if results:
            results = this._decode(results)
            results = results.get("data") if isinstance(results, dict) and results.get("data") else results

            if results is None:
                results = {"error_code": 1337, "error_message": "Data is None"}

            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except Exception:
                    results = {"error_code": 1337, "error_message": results}

            return Group.fromDict(results, None) if type == ThreadType.GROUP else User.fromDict(results, None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}"
        )

    def sendLink(
        this,
        linkUrl,
        threadId,
        type,
        message=None,
        ttl=0,
        title="",
        thumbnailUrl="",
        domainUrl="",
        desc="",
    ):
        url, params, payload, tType = this._buildSendLink(
            linkUrl,
            threadId,
            type,
            message=message,
            ttl=ttl,
            title=title,
            thumbnailUrl=thumbnailUrl,
            domainUrl=domainUrl,
            desc=desc,
        )
        data = this.PostSession(url, params=params, data=payload).json()
        return this._parseSendLink(data, tType)

    async def sendLinkAsync(
        this,
        linkUrl,
        threadId,
        type,
        message=None,
        ttl=0,
        title="",
        thumbnailUrl="",
        domainUrl="",
        desc="",
    ):
        url, params, payload, tType = this._buildSendLink(
            linkUrl,
            threadId,
            type,
            message=message,
            ttl=ttl,
            title=title,
            thumbnailUrl=thumbnailUrl,
            domainUrl=domainUrl,
            desc=desc,
        )
        data = await this.PostSessionAsync(url, params=params, data=payload)
        return this._parseSendLink(data, tType)
