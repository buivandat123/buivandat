from ..apis.group.checkGroup import *
from ..apis.group.getQRLink import *
from ..apis.group.getBlockedMembers import *
from ..apis.group.getLastMsgs import *
from ..apis.group.getRecentGroup import *
from ..apis.group.groupBoard import *
from ..apis.group.getGroupLink import *
from ..apis.get.getGroupMember import *

from ..apis.get.updatePersonalSticker import *
from ..apis.get.searchSticker import *
from ..apis.get.getSticker import *
class GettingFactory(
    CheckGroupApi,
    GetQRLinkApi,
    GetBlockedMembersApi,
    GetLastMsgsApi,
    GetRecentGroupApi,
    GroupBoardApi,
    GetGroupLinkApi,
    GetGroupMemberApi,
    UpdateStickersPersonalApi,
    SearchStickerApi,
    GetStickerDetailApi
):
    pass
