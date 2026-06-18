from .mainLibs import *

class maintainVariables:
    def InitMainVariables(this, apiKey, secretkey, imei=None, sessionCookies=None, prefix='', mainBot=None, apiLogintype=None):
        this.eventLogger = EventLogger()
        this.mainBot = mainBot
        this.commands = Loader(this, "src")
        this.prefix = prefix
        this.imei = imei
        this.sessionCookies = sessionCookies
        this.secretkey = secretkey
        this.apiLogintype = apiLogintype
        this.bot = this.fetchAccountInfo().profile.get('displayName')
        this.apiKey = apiKey
        this.senderInfo = {}
        doneRestart(this)
        InitMongoWorker(this)
        clearPyc(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        threading.Thread(target=StartClearCacheLoop, args=("assets/cache", 300), daemon=True).start()