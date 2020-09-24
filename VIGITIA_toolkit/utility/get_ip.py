from urllib import request, error

# https://stackoverflow.com/questions/2311510/getting-a-machines-external-ip-address-with-python
def get_ip_address():
    try:
        # Try to get the public IP address of the computer
        ip = request.urlopen('https://ident.me').read().decode('utf8')
    except error.URLError as e:
        # If no Internet connection is available, use the local IP address instead
        import socket
        ip = socket.gethostbyname(socket.gethostname())

    return ip