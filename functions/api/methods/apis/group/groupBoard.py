from ....index import *

class GroupBoardApi:
    """
    Get group board data: pin, note, poll.
    """

    def _request(this, boardType, groupId, page, count, lastId, lastType):
        params = {
            "params": this._encode({
                "group_id": str(groupId),
                "board_type": boardType,
                "page": page,
                "count": count,
                "last_id": lastId,
                "last_type": lastType,
                "imei": this._imei
            }),
            "zpw_ver": 645,
            "zpw_type": this.apiLogintype
        }

        data = this.GetSession(
            "https://groupboard-wpa.chat.zalo.me/api/board/list",
            params=params
        ).json()

        if data.get("error_code") == 0:
            r = this._decode(data.get("data"))
            return Group.fromDict(r.get("data"), None)

        raise ZaloAPIException(
            f"Error #{data.get('error_code')} when sending requests: "
            f"{data.get('error_message') or data.get('data')}"
        )

    def getGroupBoardList(this, groupId, page=1, count=20, last_id=0, last_type=0):
        return this._request(0, groupId, page, count, last_id, last_type)

    def getGroupPinMsg(this, groupId, page=1, count=20, last_id=0, last_type=0):
        return this._request(2, groupId, page, count, last_id, last_type)

    def getGroupNote(this, groupId, page=1, count=20, last_id=0, last_type=0):
        return this._request(1, groupId, page, count, last_id, last_type)

    def getGroupPoll(this, groupId, page=1, count=20, last_id=0, last_type=0):
        return this._request(3, groupId, page, count, last_id, last_type)