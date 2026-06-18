from ..apis.handle.addFriend import *
from ..apis.handle.unfriendUser import *
from ..apis.group.action.joinGroup import *
from ..apis.group.action.leaveGroup import *
from ..apis.properties.undoMessage import *
from ..apis.properties.acceptFriendRequest import *
from ..apis.handle.blockViewFeed import *
from ..apis.handle.blockUser import *
from ..apis.handle.unblockUser import *
from ..apis.get.listFriendRequests import *
from ..apis.handle.setAlias import *

class UserFactory(
    SendFriendRequestApi,
    UnfriendUserApi,
    JoinGroupApi,
    LeaveGroupApi,
    UndoMessageApi,
    AcceptFriendRequestApi,
    BlockViewFeedApi,
    BlockUserApi,
    UnblockUserApi,
    ListFriendRequestsApi,
    SetAliasApi
):
    pass