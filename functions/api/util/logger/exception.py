class ZaloAPIException(Exception):
    """
 - methods Exception Debug
    """

class LoginMethodNotSupport(ZaloAPIException):
	def __init__(this, message=None):
		this.message = message
		super().__init__(message)
		
class ZaloLoginError(ZaloAPIException):
	def __init__(this, message=None):
		this.message = message
		super().__init__(message)
		
class ZaloUserError(ZaloAPIException):
	def __init__(this, message=None):
		this.message = message
		super().__init__(message)

class EncodePayloadError(ZaloAPIException):
	def __init__(this, message=None):
		this.message = message
		super().__init__(message)
		
class DecodePayloadError(ZaloAPIException):
	def __init__(this, message=None):
		this.message = message
		super().__init__(message)