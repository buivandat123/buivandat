from ..core.Enum import Enum

class GroupEventType(Enum):
	JOIN = "join"
	LEAVE = "leave"
	UPDATE = "update"
	UNKNOWN = "unknown"
	REACTION = "reaction"
	NEW_LINK = "new_link"
	ADD_ADMIN = "add_admin"
	REMOVE_ADMIN = "remove_admin"
	JOIN_REQUEST = "join_request"
	BLOCK_MEMBER = "block_member"
	REMOVE_MEMBER = "remove_member"
	UPDATE_SETTING = "update_setting"


class EventType(Enum):
	REACTION = "reaction"