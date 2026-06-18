import os
import threading
import time

def clearPyc(dic):
    for root, dirs, files in os.walk(dic):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                pycache_path = os.path.join(root, dir_name)
                try:
                    for file in os.listdir(pycache_path):
                        file_path = os.path.join(pycache_path, file)
                        os.remove(file_path)
                    os.rmdir(pycache_path)
                    
                except Exception as e:
                    pass
clearPyc(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))