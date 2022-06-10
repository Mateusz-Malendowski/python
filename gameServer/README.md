Console server and client applications for playing poker using socket and asyncio libraries.
To run this code there are required three additional files:
- server certificate
- private key of that certificate
- certificate of Certification Authority which issued that certificate

Basic usage:
- python server.py    -   starts server with default parameters
- python client.py    -   runs client with default parameters

Server parameters:
- -h    [ADDR]   -   changes server address, default localhost
- -p    [PORT]   -   changes server port, default 1769
- -crt  [CERT]   -   changes server certificate, default server.crt
- -key  [KEY]    -   changes key of used certificate, default server.pem

Client parameters:
- -v6            -   connects using IPv6, default uses IPv4
- -h    [ADDR]   -   changes server address, default localhost
- -p    [PORT]   -   changes server port, default 1769
- -ca   [CERT]   -   changes CA certificate, default ca.crt
- -crt  [CERT]   -   changes server certificate, default server.crt

Server uses (or creates if necessary) three additional files:
- credentials.txt which contains logins, hashed, salted passwords and amount of user coins
- salts.txt which contains user logins, and their salts
- ServerLogs.txt  which logs activity of every connected user
