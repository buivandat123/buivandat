from ..apis.get.fetchAccountInfo import *
from ..apis.get.fetchPhoneNumber import *
from ..apis.get.fetchUserInfo import *
from ..apis.get.fetchGroupInfo import *
from ..apis.get.fetchAllFriends import *
from ..apis.get.fetchAllGroups import *
from ..apis.get.getAvatar import *
from ..apis.get.getCategory import *
from ..apis.get.findSticker import *
class FetchFactory(
    FetchAccountInfoApi,
    FetchPhoneNumberApi,
    FetchUserInfoApi,
    FetchGroupInfoApi,
    FetchAllFriendsApi,
    FetchAllGroupsApi,
    GetAvatarApi,
    getCategoryApi,
    SuggestStickerApi
):
    pass