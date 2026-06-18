from functions.services.hook.core_hook.extra_multibot_core import loopInitExpire
from src.command.groupBot.block import blacklistEvent
from src.command.chatBot.student.learn import learnListen
from src.command.groupBot.coreGroup import autoJoinGroups
from functions.services.hook.bot_hook.im_core import DontcareMessage, initCheckFriendRequests
from functions.services.init.sendTime import initSchedulerHandle
from functions.services.hook.bot_hook.approve_core import InitAutoApprove
from src.queue.scheduler.verifyShield import *
from src.queue.manager.antiBot import *
from src.queue.manager.antiForward import *
from src.queue.manager.antiUrl import *
from src.queue.manager.antiClassical import *
from src.queue.manager.filterMessage import *
from src.queue.scheduler.autoApprove import *
from src.queue.manager.antiSpam import *
from src.command.botTool.download import *
from src.command.groupBot.silent import *
from dto.index import *
from src.events.init.prAuto import *
from src.command.api.music.timeout import *
initAuto = False
antiStarted = False
def handleInit(this):
    initSchedulerHandle(this)
    blacklistEvent(this)
    InitAutoApprove(this)
    initCheckFriendRequests(this)
    startPR(this)
    initAdmin(this)

    loopInitExpire(this)
    InitTimeoutMenu(this)
    InitTimeoutAudiomack(this)
    InitTimeoutMixCloud(this)
    InitTimeoutSoundCloud(this)
    InitTimeoutYouTubeMusic(this)
    InitTimeoutNhacCuaTui(this)
    InitTimeoutZing(this)
    InitTimeoutTikTok(this)
    InitTimeoutSpotify(this)

def handleListenAnti(this, message, data, userId, threadId, type):
    if IsNeedVerify(this, threadId, userId):
        VerifyShieldCaptcha(this, message, data, userId, threadId, type)
        return
    learnListen(this, message, data, userId, threadId, type)
    antiBot(this, message, data, userId, threadId, type)
    filterBadwordOnMessage(this, message, data, userId, threadId, type)
    filterNsfwOnMessage(this, message, data, userId, threadId, type)
    antiForward(this, message, data, userId, threadId, type)
    silentListener(this, message, data, userId, threadId, type)
    antiUrlMessage(this, message, data, userId, threadId, type)
    antiMsgType(this, message, data, userId, threadId, type)
    antiSpamMessage(this, message, data, userId, threadId, type)
    AutoLink(this, message, data, userId, threadId, type)
    autoJoinGroups(this, message, data, userId, threadId, type)
    DontcareMessage(this, message, data, userId, threadId, type)
