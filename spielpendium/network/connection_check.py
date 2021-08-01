import socket


def is_connected_to_internet():
    """Checks if there's an internet connection
    
    :returns: True if an internet connection exists, False otherwise.
    """
    try:
        # try to connect to 1.1.1.1, which should always be up
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        # if it can't connect, it'll come here
        pass
    return False


if __name__ == '__main__':
	print(is_connected())
	