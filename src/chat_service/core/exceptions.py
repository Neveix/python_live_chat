


class MessageAlreadyListening(Exception):
    ...



class RepoError(Exception):
    ...

class ListenTimeoutError(RepoError):
    ...

    
class RepoElementAlreadyExists(RepoError):
    ...


class ListenCancelled(Exception):
    ...

    
class RoomNotFoundError(Exception):
    ...

