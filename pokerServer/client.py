'''
Client
'''
import socket
import os
import re
import ssl
import sys
from getpass import getpass

PROTOCOL_NAME = "PokerProtocol"
PROTOCOL_VERSION = "1.0"

SERVER_HOST="localhost"
SERVER_PORT=1769
IP_VERSION=socket.AF_INET
CERT_AUTH="ca.crt"
SERVER_CERT="server.crt"

def msgUnwrapper(msg):
    response=""
    lines=msg.split("\n", 3)
    if lines[0] != f"{PROTOCOL_NAME} {PROTOCOL_VERSION}": return "Unsupported protocol"
    if lines[1][:3] == "100":
        response="YES"
        return lines[2], response

    elif lines[1][:3] == "200":
        return lines[3], response

    elif lines[1][:3] == "201":
        response="YES"
        return lines[3], response

    elif lines[1][:3] == "202":
        response="PASS"
        return lines[3], response

    elif lines[1][:3] == "203":
        response="EXIT"
        return None, response

    elif lines[1][:3] == "300":
        response="REDIRECT"
        srch=re.search("ADDRESS=(.*), PORT=(.*)",lines[2])
        addr=srch.group(1)
        port=int(srch.group(2))
        cookie=re.search("COOKIE=(.*)",lines[3]).group(1)
        return (addr,port,cookie), response

    elif lines[1][:3] == "301":
        response="VERIFICATION"
        cookie=re.search("VERIFICATION=(.*)",lines[2]).group(1)
        return cookie, response

    elif lines[1][:3] == "302":
        response="SHORT REDIRECT"
        srch=re.search("ADDRESS=(.*), PORT=(.*)",lines[2])
        addr=srch.group(1)
        port=int(srch.group(2))
        return (addr,port), response
    
    elif lines[1][:3] == "400":
        response="CRITICAL ERROR"
        return None, response

    elif lines[1][:3] == "401":
        response="ERROR"
        lines=msg.split("\n", 2)
        return lines[2], response

    elif lines[1][:3] == "402":
        response="PASSWORD ERROR"
        return lines[2], response

    elif lines[1][:3] == "403":
        response="NBERROR"
        return lines[2], response

def messageWrapper(msgtype,msg):
    retmsg = f"{PROTOCOL_NAME} {PROTOCOL_VERSION}\n"
    if msgtype == "OPTIONS":
        retmsg += f"{msgtype}\r\n"
    elif msgtype == "COMMAND":
        retmsg += f"{msgtype}\n{msg}\n\r\n"
    elif msgtype == "VERIFY":
        retmsg += f"{msgtype} {msg[0]};{msg[1]}\n\r\n"
    elif msgtype == "GAME":
        retmsg += f"{msgtype}\n{msg}\r\n"
    return retmsg.encode("utf-8")

def receive(socket):
    rec_data=""
    while not "\r\n" in rec_data:
        data=socket.recv(1024)
        rec_data+=data.decode("utf-8")
    return rec_data[:-2]

def msgColorifier(msg):
    COLOR = {
        "RED": "\u001b[38;5;160m",
        "LRED": "\u001b[38;5;167m",
        "YELLOW": "\u001b[33;1m",
        "GRAY": "\u001b[38;5;240m",
        "LGRAY": "\u001b[38;5;244m",
        "CLEAR": "\033[0m"    
        }

    if type(msg) != type(""):
        return msg
    if "♥" in msg or "♦" in msg:
        msg=re.sub(r"♥", rf'{COLOR["RED"]}♥{COLOR["CLEAR"]}',msg)
        msg=re.sub(r"♦", rf'{COLOR["LRED"]}♦{COLOR["CLEAR"]}',msg)
    if "♠" in msg or "♣" in msg:
        msg=re.sub(r"♠", rf'{COLOR["GRAY"]}♠{COLOR["CLEAR"]}',msg)
        msg=re.sub(r"♣", rf'{COLOR["LGRAY"]}♣{COLOR["CLEAR"]}',msg)
    if "coins" in msg.lower():
        msg=re.sub(r"[cC]oins: \d*", rf'{COLOR["YELLOW"]}\g<0>{COLOR["CLEAR"]}', msg)
        msg=re.sub(r"[0-9]+ coins", rf'{COLOR["YELLOW"]}\g<0>{COLOR["CLEAR"]}', msg)
    return msg

def clearAndPrev():
    print('\033[1A\033[K')
    print('\033[1A',end="\r")


def main():
    global IP_VERSION, SERVER_HOST, SERVER_PORT, CERT_AUTH, SERVER_CERT
    if "-v6" in sys.argv:
        IP_VERSION=socket.AF_INET6
    if "-h" in sys.argv:
        SERVER_HOST=sys.argv[sys.argv.index("-h") + 1]
    if "-p" in sys.argv:
        SERVER_PORT=int(sys.argv[sys.argv.index("-p") + 1])
    if "-ca" in sys.argv:
        CERT_AUTH=sys.argv[sys.argv.index("-ca") + 1]
    if "-crt" in sys.argv:
        SERVER_CERT=sys.argv[sys.argv.index("-crt") + 1]

    s = socket.socket(IP_VERSION, socket.SOCK_STREAM)
    ssl_s = ssl.wrap_socket(s, cert_reqs=ssl.CERT_REQUIRED, ssl_version=ssl.PROTOCOL_TLSv1_2, ca_certs=CERT_AUTH)

    os.system("color")

    try:
        ssl_s.connect((SERVER_HOST, SERVER_PORT))
        ssl_s.sendall(messageWrapper("OPTIONS",""))
        cookie=""
        remainder=""
        swap=False
        while True:
            message=remainder+receive(ssl_s)
            try: remainder=message.split("\r\n")[1]
            except IndexError: pass
            message=message.split("\r\n")[0]
            rec_data, resp = msgUnwrapper(message)
            rec_data=msgColorifier(rec_data)    

            if resp=="":
                print(rec_data)
            elif resp=="YES" or resp=="ERROR":
                print(rec_data)
                inp = input()
                if not swap: ssl_s.sendall(messageWrapper("COMMAND",f"{inp}"))
                else: ssl_s.sendall(messageWrapper("GAME",f"{inp}"))

            elif resp=="PASS":
                inp = getpass(prompt=rec_data)
                ssl_s.sendall(messageWrapper("COMMAND",f"{inp}"))

            elif resp=="REDIRECT":
                ssl_s.close()
                s.close()
                
                swap = not swap

                s = socket.socket(IP_VERSION, socket.SOCK_STREAM)
                
                ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,)
                ssl_context.check_hostname = False
                ssl_context.load_verify_locations(SERVER_CERT)
                
                ssl_s = ssl_context.wrap_socket(s,server_side=False)
                
                cookie=rec_data[2]
                ssl_s.connect((rec_data[0],rec_data[1]))            
                
            
            elif resp=="VERIFICATION":
                ssl_s.sendall(messageWrapper("VERIFY",(cookie,rec_data)))

            elif resp=="SHORT REDIRECT":
                ssl_s.close()
                s.close()
                
                swap = not swap

                s = socket.socket(IP_VERSION, socket.SOCK_STREAM)
                ssl_s = ssl.wrap_socket(s, cert_reqs=ssl.CERT_REQUIRED, ssl_version=ssl.PROTOCOL_TLSv1_2, ca_certs=CERT_AUTH)
                
                ssl_s.connect((rec_data[0],rec_data[1]))
                ssl_s.sendall(messageWrapper("VERIFY",(cookie,None)))                
                
            elif resp=="CRITICAL ERROR":
                print("Critical error")
                ssl_s.close()
                s.close()
                exit(1)
            elif resp=="PASSWORD ERROR":
                print(rec_data)
            elif resp=="NBERROR":
                print(rec_data)
            elif resp=="EXIT":
                break
            else:
                print("ERROR: Unsupported message type, aborting...")
                exit(1)

        ssl_s.close()
        s.close()
    except (socket.error, KeyboardInterrupt) as E:
        print(f"ERROR: {E}")
        ssl_s.close()
        s.close()

if __name__ == "__main__":
    main()
