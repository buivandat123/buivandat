# modules/client.py
# -*- coding: utf-8 -*-

class GetClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._clients = {}
            cls._instance._main = None
        return cls._instance
    
    def setMain(self, client, data=None, botKey="main"):
        self._main = {"client": client, "data": data or {}, "botKey": str(botKey)}
    
    def setClient(self, botIntId, client, data=None):
        self._clients[str(botIntId)] = {"client": client, "data": data or {}, "botKey": str(botIntId)}
    
    def getMain(self):
        return self._main
    
    def get(self, botIntId):
        key = str(botIntId)
        if self._main and self._main.get("botKey") == key:
            return self._main
        return self._clients.get(key)
    
    def __contains__(self, botIntId):
        return self.get(botIntId) is not None
    
    def items(self):
        if self._main:
            yield self._main["botKey"], self._main
        for key, value in self._clients.items():
            yield key, value

getClient = GetClient()