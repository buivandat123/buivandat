import enum

class Enum(enum.Enum):
	def __repr__(this):
		return "{}.{}".format(type(this).__name__, this.name)