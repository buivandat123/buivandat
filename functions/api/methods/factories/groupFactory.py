from ..apis.group.status.updateTTL import *
from ..apis.group.createGroup import *
from ..apis.group.upgradeCommunity import *
from ..apis.group.changeGroupAvatar import *
from ..apis.group.changeGroupName import *
from ..apis.group.changeGroupSetting import *
from ..apis.group.changeGroupOwner import *
from ..apis.group.addUsersToGroup import *
from ..apis.group.action.kickUsers import *
from ..apis.group.action.blockUsers import *
from ..apis.group.action.unblockUsers import *
from ..apis.group.action.addAdmins import *
from ..apis.group.action.removeAdmins import *
from ..apis.group.message.pinMessage import *
from ..apis.group.message.unpinMessage import *
from ..apis.group.message.deleteMessage import *
from ..apis.group.status.setMute import *
from ..apis.group.status.listInviteBox import *
from ..apis.group.status.boxInviteAccept import *
from ..apis.group.status.generateNewLink import *
from ..apis.group.status.disableLink import *
from ..apis.group.status.viewGroupPending import *
from ..apis.group.status.handleGroupPending import *
from ..apis.group.status.viewPollDetail import *
from ..apis.group.action.votePoll import *
from ..apis.group.action.createPoll import *
from ..apis.group.action.lockPoll import *
from ..apis.group.status.disperseGroup import *
class GroupAPi(
    CreateGroupApi, 
    UpgradeCommunityApi, 
    ChangeGroupAvatarApi,
    ChangeGroupNameApi,
    ChangeGroupSettingApi,
    ChangeGroupOwnerApi,
    AddUsersToGroupApi,
    KickUsersApi,
    BlockUsersApi,
    AddAdminsApi,
    RemoveAdminsApi,
    PinMessageApi,
    UnpinMessageApi,
    DeleteMessageApi,
    SetMuteApi,
    ListInviteBoxApi,
    BoxInviteAcceptApi,
    GenerateNewLinkApi,
    DisableGroupLinkApi,
    ViewGroupPendingApi,
    HandleGroupPendingApi,
    ViewPollDetailApi,
    VotePollApi,
    CreatePollApi,
    LockPollApi,
    DisperseGroupApi,
    UpdateAutoDeleteChatApi
):
    pass