
from ..util import utils

from ..moderator import *
from ..util.pack import *
from . import State
from ..util.logger.logging import Logging
from ..methods.services import UtilServices
from ..methods.factories.hostUploadFactory import AttachmentsFactory
from ..methods.factories.fetchFactory import FetchFactory
from ..methods.factories.gettingFactory import GettingFactory
from ..methods.factories.accountFactory import AccountFactory
from ..methods.factories.groupFactory import GroupAPi
from ..methods.factories.userFactory import UserFactory
from ..methods.factories.sendingFactory import SendingFactory
from ..methods.factories.listenFactory import SocketFactory


loginapi = 24
pool = ThreadPoolExecutor(max_workers=9999)
ApisMethod = (
    AttachmentsFactory, 
    UtilServices,
    FetchFactory, 
    GettingFactory, 
    AccountFactory, 
    GroupAPi,
    UserFactory, 
    SendingFactory, 
    SocketFactory
)

class framework:
    def initFrameWork(this, phone, password, imei, sessionCookies=None, userAgent=None, autoLogin=True, login=loginapi):
        this._state = State.State()
        this.threadCondition = threading.Event()
        this.apiLogintype = login
        this.uploadCallbacks = {}
        this.uploadAsyncCallbacks = {}
        this.bools = ThreadPoolExecutor()
        if autoLogin:
            if (
                not sessionCookies
                or not this.setSession(sessionCookies)
                or not this.isLoggedIn()
            ):
                this.Login(phone, password, imei, userAgent)