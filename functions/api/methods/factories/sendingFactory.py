from ..apis.handle.sendReaction import *
from ..apis.handle.sendFile import *
from ..apis.handle.sendMultiReaction import *
from ..apis.handle.sendVideo import *
from ..apis.handle.sendVoice import *
from ..apis.handle.sendGifphy import *
from ..apis.handle.sendImage import *
from ..apis.handle.sendMultiImage import *
from ..apis.handle.sendLocalImage import *
from ..apis.handle.sendMultiLocalImage import *
from ..apis.handle.sendCustomSticker import *
from ..apis.handle.sendSticker import *
from ..apis.handle.sendCall import *
from ..apis.handle.sendLink import *
from ..apis.handle.sendReport import *
from ..apis.handle.sendBusinessCard import *
from ..apis.handle.sendCardBank import *
from ..apis.handle.sendMessages import *
class SendingFactory(
    SendReactionApi, 
    SendMultiReactionApi, 
    SendFileApi, 
    SendVideoApi, 
    SendVoiceApi, 
    SendGifApi, 
    SendImageApi, 
    SendMultiImageApi,
    SendLocalImageApi,
    SendMultiLocalImageApi,
    SendCustomStickerApi,
    SendStickerApi,
    SendLinkApi,
    SendCallApi,
    SendBusinessCardApi,
    SendCardBankApi,
    SendReportApi,
    SendApi
):
    pass