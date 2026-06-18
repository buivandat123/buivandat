from .....index import *

class UploadImageApi:
    def _BuildUploadImage(this, filePath, threadId, type):
        if not os.path.exists(filePath):
            raise ZaloUserError(f"{filePath} not found")

        f = open(filePath, "rb")
        files = [("chunkContent", f)]
        try:
            fileSize = int(os.stat(filePath).st_size)
        except:
            fileSize = 0

        fileName = os.path.basename(str(filePath)) or "image"

        params = {
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype,
            "params": this._encode({
                "totalChunk": 1,
                "fileName": fileName,
                "clientId": utils.now(),
                "totalSize": fileSize,
                "imei": this._imei,
                "isE2EE": 0,
                "jxl": 0,
                "chunkId": 1
            })
        }

        if type == ThreadType.USER:
            url = "https://tt-files-wpa.chat.zalo.me/api/message/photo_original/upload"
            params["type"] = 2
            decoded = this._decode(params["params"])
            decoded["toid"] = str(threadId)
            params["params"] = this._encode(decoded)
        elif type == ThreadType.GROUP:
            url = "https://tt-files-wpa.chat.zalo.me/api/group/photo_original/upload"
            params["type"] = 11
            decoded = this._decode(params["params"])
            decoded["grid"] = str(threadId)
            params["params"] = this._encode(decoded)
        else:
            f.close()
            raise ZaloUserError("Thread type is invalid")

        return url, params, files, f

    def uploadImage(this, filePath, threadId, type):
        url, params, files, f = this._BuildUploadImage(filePath, threadId, type)
        try:
            data = this.PostSession(url, params=params, files=files).json()
        finally:
            try:
                f.close()
            except:
                pass

        if data.get("error_code") == 0 and data.get("data"):
            results = this._decode(data["data"])
            results = results.get("data") if isinstance(results, dict) and results.get("data") else results
            if results is None:
                raise ZaloAPIException("Error #1337 when sending requests: Data is None")
            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except:
                    raise ZaloAPIException(f"Error #1337 when sending requests: {results}")
            return results

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}"
        )

    async def uploadImageAsync(this, filePath, threadId, type):
        url, params, files, f = this._BuildUploadImage(filePath, threadId, type)
        try:
            data = await this.PostSessionAsync(url, params=params, files=files)
        finally:
            try:
                f.close()
            except:
                pass

        if data.get("error_code") == 0 and data.get("data"):
            results = this._decode(data["data"])
            results = results.get("data") if isinstance(results, dict) and results.get("data") else results
            if results is None:
                raise ZaloAPIException("Error #1337 when sending requests: Data is None")
            if isinstance(results, str):
                try:
                    results = json.loads(results)
                except:
                    raise ZaloAPIException(f"Error #1337 when sending requests: {results}")
            return results

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: {data.get('error_message') or data.get('data')}"
        )