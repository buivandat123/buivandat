from .Format import *

class TextHelp:
    __slots__ = ("_d",)

    def __init__(this, c, **k):
        this._d = {
            "groupModify": f"""{c} list: Get list group or community joined
{c} find: Find member in group
{c} settings: Change group settings
""",
            "commandHelp": f"""{c} on, off: Enable, disbale command
{c} permission: Edit command permission
{c} cooldown: Edit command cooldown
{c} find: Find commands
{c} load: Reload commands
""",
            "iAmHelp": f"""{c} ghost: Ghost status for bot
{c} ignore: Ignore invited stranger box, can approve in my document notify
{c} learn: Learn message and response
{c} vietnamese: Yee, I'm a Vietnamese or a Vietnamese but like speak English
{c} friend: Set friendly status to approve all friend requests
{c} dontcare: Set silent status for a user, only iAm cant see that user message
{c} lazy: Set lazy status to undo message by reaction, only /-heart reaction and only if the message is sent by bot
"""
        }
        if k:
            this._d.update({kk: str(v) for kk, v in k.items()})

    def __getattr__(this, k):
        v = this._d.get(k)
        if v is None:
            raise AttributeError(k)
        return v

def textHelp(c, **k):
    return TextHelp(c, **k)