from ..apis.properties.changeAccountSetting import ChangeAccountSettingApi
from ..apis.properties.changeAccountAvatar import ChangeAccountAvatarApi
from ..apis.properties.setTyping import SetTypingApi
from ..apis.properties.markAsDelivered import MarkAsDeliveredApi
from ..apis.properties.markAsRead import MarkAsReadApi

class AccountFactory(
    ChangeAccountSettingApi,
    ChangeAccountAvatarApi,
    SetTypingApi,
    MarkAsDeliveredApi,
    MarkAsReadApi
):
    def uid(this):
        return this.uid
    
    def zfcloudId(this):
        return this._state.userClientId