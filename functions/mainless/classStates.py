from dto.index import *
from .mainLibs import *
class StatesLoader(GhostFunctions):
    def InitStates(this):
        this.audiomackStates = {}
        this.soundcloudStates = {}
        this.groupModifyStates = {}
        this.nhaccuatuiStates = {}
        this.zingStates = {}
        this.mixcloudStates = {}
        this.menuStates = {}
        this.tiktokState = {}
        this.youtubemusicStates = {}
        this.khophimStates = {}
        this.ghostMessage = {}
        this.spotifyStates = {}

        handleInit(this)