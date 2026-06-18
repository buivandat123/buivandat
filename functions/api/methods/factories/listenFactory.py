from ..apis.socket.listening import *
from ..apis.socket.login import *
from ..apis.socket.stopListening import *
from ..apis.socket.pingsocket import *
from ..apis.socket.onSocket import *
class SocketFactory(pingSocket, 
                    LoginAPi, 
                    ListeningApi, 
                    stopListeningAPi, 
                    onSocketAPi):
    pass