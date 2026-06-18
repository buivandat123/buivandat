from ....index import *
from ...core.AuthServices import *

class LoginAPi(LoginAuth):
    """
    Auth API: Login account.

    Usage:
        api.Login(phone, password, imei)
        await api.LoginAsync(phone, password, imei)
    """

    def Login(this, phone, password, imei, userAgent=None):
        if not (phone and password):
            raise ZaloUserError("Phone and password not set")
        this.onLoggingIn()
        this._state.Login(phone, password, imei, userAgent=userAgent)
        this._imei = getattr(this._state, "clientUUID", None) or imei
        try:
            this.uid = this.fetchAccountInfo().profile.get("userId", this._state.userClientId)
        except:
            this.uid = this._state.userClientId
        this.onLoggedIn(this._state._config.get("phone_number"))
        return this.uid

    async def LoginAsync(this, phone, password, imei, userAgent=None):
        if not (phone and password):
            raise ZaloUserError("Phone and password not set")
        this.onLoggingIn()
        await this._state.LoginAsync(phone, password, imei, userAgent=userAgent)
        this._imei = getattr(this._state, "clientUUID", None) or imei
        try:
            acc = await this.fetchAccountInfoAsync()
            this.uid = acc.profile.get("userId", this._state.userClientId)
        except:
            this.uid = this._state.userClientId
        this.onLoggedIn(this._state._config.get("phone_number"))
        return this.uid