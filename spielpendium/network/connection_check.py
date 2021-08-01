import socket
import urllib.request
import urllib.error


_BGG_URL = "https://www.boardgamegeek.com"


def is_connected_to_internet() -> bool:
    """Checks if there's an internet connection
    
    :returns: True if an internet connection exists, False otherwise.
    """
    try:
        # try to connect to 1.1.1.1, which is a DNS server and should always be up
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        # if it can't connect, it'll come here
        pass
    return False


def bgg_is_up() -> bool:
    """Checks if boardgamegeek.com is up

    :returns: True if boardgamegeek.com is up, False otherwise.
	"""

    try:
        # try to connect to.BGG and check the return status. 200 means "ok success status"
        return urllib.request.urlopen(_BGG_URL).getcode() == 200
    except urllib.error.URLError:
        # if there's any error with connecting, return False
        pass
    
    return False
    
    
    def bgg_api_is_up() -> bool:
    	
    	return True

if __name__ == '__main__':
    print(is_connected_to_internet())
    print(bgg_is_up())
	