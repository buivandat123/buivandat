from .dtobuilder import *

class Start(svtBuilder):
    def __init__(build):
        super().__init__()
        build.dec = None
        build.sys = SystemExit(build.goto("..main.py",sys.argv[1:]))

    def run(build):
        build.core()
        raise build.sys

Start().run()