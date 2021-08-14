'''
Server
'''
import socket
import threading
import queue
import random
import hashlib
import datetime
import asyncio
import ssl
import secrets
import re
import sys
from concurrent.futures import ThreadPoolExecutor

PROTOCOL_NAME="PokerProtocol"
PROTOCOL_VERSION="1.0"

SERVER_HOST=""
SERVER_PORT=1769
SERVER_CERT="server.crt"
SERVER_KEY="server.pem"

def msgUnwrapper(msg):
    lines=msg.split("\n",2)
    if lines[0] != f"{PROTOCOL_NAME} {PROTOCOL_VERSION}": return "Unsupported protocol"
    if "OPTIONS" in lines[1]:
        return "", "OPTIONS"

    elif "COMMAND" in lines[1]:
        return lines[2][:-3], "CMD"

    elif "VERIFY" in lines[1]:
        cookies=re.search("VERIFY (.*);(.*)",lines[1])
        return (cookies.group(1),cookies.group(2)), "VERIFY"
    
    elif "GAME" in lines[1]:
        return lines[2][:-2], "GAME"

def messageWrapper(code,msg):
    retmsg = f"{PROTOCOL_NAME} {PROTOCOL_VERSION}\n"
    if code == 100: retmsg += f"{code} INFO\n{msg}\r\n"
    elif code == 200: retmsg += f"{code} OK\nDATA\n{msg}\r\n"
    elif code == 201: retmsg += f"{code} INPUT REQUIRED\nDATA\n{msg}\r\n"
    elif code == 202: retmsg += f"{code} PASSWORD REQUIRED\nDATA\n{msg}\r\n"
    elif code == 203: retmsg += f"{code} EXIT\r\n"
    elif code == 300: retmsg += f"{code} REDIRECT P1\nADDRESS={msg[0]}, PORT={msg[1]}\nCOOKIE={msg[2]}\r\n"
    elif code == 301: retmsg += f"{code} REDIRECT P2\nVERIFICATION={msg}\r\n"
    elif code == 302: retmsg += f"{code} REDIRECT\nADDRESS={msg[0]}, PORT={msg[1]}\r\n"
    elif code == 400: retmsg += f"{code} CRITICAL ERROR\nTERMINATING CONNECTION\r\n"
    elif code == 401: retmsg += f"{code} ERROR\n{msg}\r\n"
    elif code == 402: retmsg += f"{code} PASSWORD ERROR\n{msg}\r\n"
    elif code == 403: retmsg += f"{code} NBERROR\n{msg}\r\n"
    return retmsg.encode("utf-8")
    

def seekWinner(board, allHands):
    scores = []
    for i, hand in enumerate(allHands):
        scores.append((poker((board + ' ' + hand).split()), i))

    best = max(scores)[0]

    handNames = {
        (1,): "High card",
        (2, 1, 1, 1): "Pair",
        (2, 2, 1): "Two pair",
        (3, 1, 1): "Three of a kind",
        (3, 1, 2): "Straight",
        (3, 1, 3): "Flush",
        (3, 2): "Fullhouse",
        (4, 1): "Four of a kind",
        (5,): "Straight flush"
    }

    winningHand = handNames[best[0]]

    if winningHand == "Straight flush":
        if best[1] == (12, 11, 10, 9, 8):
            winningHand = "Royal flush"

    winners = []
    for win in filter(lambda win: win[0] == best, scores):
        winners.append(win[1])

    return winners, winningHand


def poker(hand):

    ranks = {"2": 0, "3": 1, "4": 2, "5": 3, "6": 4, "7": 5,
             "8": 6, "9": 7, "T": 8, "J": 9, "Q": 10, "K": 11, "A": 12}

    if len(hand) > 5:  # texas
        return max([poker(hand[:i] + hand[i+1:]) for i in range(len(hand))])

    hand = sorted(hand, key=lambda val: ranks[val[0]])[::-1]  # sortowanie reki

    cardDict = {}
    for card in hand:  # ile roznych wartosci kart w rece
        if ranks[card[0]] in cardDict:
            cardDict[ranks[card[0]]] += 1
        else:
            cardDict[ranks[card[0]]] = 1

    # liczenie wystapien roznych
    ranks = tuple([x for _, x in sorted(
        zip(cardDict.values(), cardDict))][::-1])
    score = tuple(sorted(cardDict.values())[::-1])  # wartosci kart

    if len(score) == 5:  # sprawdza czy straight albo kolor
        if ranks[0:2] == (12, 3):  # jezeli straight od A-5
            ranks = (3, 2, 1, 0, -1)

        colorDict = {}
        for card in hand:
            if card[1] in colorDict:
                colorDict[card[1]] += 1
            else:
                colorDict[card[1]] = 1

        if len(colorDict) == 1:
            score = ([(3, 1, 3), (5,)])[ranks[0] - ranks[4] == 4]
        else:
            score = ([(1,), (3, 1, 2)])[ranks[0] - ranks[4] == 4]

    return score, ranks


class Player:
    def __init__(self, s, login, credit):
        self.socket = s
        self.login = login
        self.active = False
        self.ready = False
        self.credit = credit
        self.hand = None
        self.pState = 0
        self.fold = False
        self.totalBet = 0
        self.allIn = False

    def getSocket(self): return self.socket
    def getActive(self): return self.active
    def getLogin(self): return self.login
    def getReady(self): return self.ready
    def getCredit(self): return self.credit
    def getHand(self): return self.hand
    def getState(self): return self.pState
    def getFold(self): return self.fold
    def getTotalBet(self): return self.totalBet
    def getAllIn(self): return self.allIn

    def setActive(self): self.active = True
    def setReady(self): self.ready = True
    def setHand(self, hand): self.hand = hand
    def setState(self, val): self.pState = val
    def setTotalBet(self, val): self.totalBet = val

    def clrActive(self): self.active = False
    def clrReady(self): self.ready = False
    def clrState(self): self.pState = 0
    def clrAllIn(self): self.allIn = False
    
    def modCredit(self, mod): self.credit += mod
    def Fold(self): self.fold = True
    def unFold(self): self.fold = False
    def allIn(self): self.allIn = True

class Room:

    def __init__(self, serverAddr, serverPort):
        self.players = {}
        self.state = 0
        self.readyCount = 0
        self.activePlrs = []
        self.activeAndDraw = 0
        self.sAddr = serverAddr
        self.port = serverPort
        self.deck = cardsArr
        self.discard = []
        self.allHands = []
        self.turnIndex = 0
        self.bet = 0
        self.pool = 0
        self.folded = 0
        self.checks = 0
        self.round = 0

    def __str__(self):
        if len(self.players) == 0:
            return "--Empty--"
        if len(self.players) == 8:
            return "--FULL--"
        playerStr = ""
        for plr in self.players.values():
            playerStr = f"{playerStr}, {plr.getLogin()}"
        return playerStr[2:]

    def Add(self, cookie, plr):
        self.players[cookie] = plr
        if len(self.players) > 1 and self.state < 1:
            self.state = 1

    def Remove(self, cookie):
        try:
            if self.players[cookie].getReady():
                self.readyCount -= 1
            del self.players[cookie]
        except KeyError: pass

    def removeActive(self, plr): del self.activePlrs[self.activePlrs.index(plr)]

    def Size(self): return len(self.players)
    def getPlayers(self): return self.players
    def getActivePlrs(self): return self.activePlrs
    def getState(self): return self.state
    def getAddr(self): return self.sAddr
    def getPort(self): return self.port
    def getAADraw(self): return self.activeAndDraw
    def getBet(self): return self.bet
    def getPool(self): return self.pool
    def getFoldCount(self): return self.folded
    def getChecks(self): return self.checks
    def getAllHands(self): return self.allHands
    def getReadyCount(self): return self.readyCount
    def getTurnIndex(self):
        if self.turnIndex >= len(self.activePlrs):
            self.turnIndex=0
        return self.turnIndex

    def clrAADraw(self): self.activeAndDraw = 0
    def clrFold(self): self.folded = 0
    def clrCheck(self): self.checks = 0

    def incAADraw(self): self.activeAndDraw += 1
    def incFold(self): self.folded += 1
    def incCheck(self): self.checks += 1
    def incTurnIndex(self):
        self.turnIndex += 1
        if self.turnIndex >= len(self.activePlrs):
            self.turnIndex = 0

    def modBet(self, mod): self.bet = mod
    def addPool(self, mod): self.pool += mod


    def Ready(self, plr):
        if not plr.getReady():
            plr.setReady()
            self.readyCount += 1
            if self.readyCount > 1 and self.state < 2:
                self.state = 2

    def unReady(self, plr):
        if plr.getReady(): self.readyCount -= 1
        plr.clrReady()

    def Activate(self, plr):
        plr.setActive()
        self.activePlrs.append(plr)

    def deActivate(self, plr):
        plr.clrActive()
        try: del self.activePlrs[self.activePlrs.index(plr)]
        except ValueError: pass

    def startState(self):
        self.state = 3

    def draw(self, plr):
        tmp = ""
        for i in range(5):
            drawnCard = self.deck[random.randint(0, len(self.deck)-1)]
            self.deck.remove(drawnCard)
            tmp += drawnCard+" "
        tmp = tmp[:-1]
        q.put(f"{plr.getLogin()} 200: HAND {tmp}")
        plr.getSocket().write(messageWrapper(201, f"Your hand: {tmp} do you want to do mulligan? (Y\\N)"))
        plr.setHand(tmp)
        self.allHands.append(tmp)

    def redraw(self, plr, hand, redraw):
        if len(redraw) == 0:
            plr.getSocket().write(messageWrapper(200,f"Your hand: {hand}."))
            return
        else:
            self.allHands.remove(hand)

            if len(self.deck) < len(redraw):
                self.deck.extend(self.discard)
                self.discard.clear()

            sHand = hand.split(" ")
            for i in range(len(redraw)):
                self.discard.append(sHand[int(redraw[i])-1])
                drawnCard = self.deck[random.randint(0, len(self.deck)-1)]
                self.deck.remove(drawnCard)
                sHand[int(redraw[i])-1] = drawnCard
            hand = " ".join(sHand)
            q.put(f"{plr.getLogin()} 200: REDRAW {hand}")
            plr.setHand(hand)
            self.allHands.append(hand)

        plr.getSocket().write(messageWrapper(200,f"Your hand: {hand}."))
        
        for other in self.players.values():
            if other != plr:
                other.getSocket().write(messageWrapper(200, f"{plr.getLogin()} drew {len(redraw)} cards"))

    def foldPlayer(self, player):
        self.incFold()
        player.Fold()
        self.allHands.remove(player.getHand())
        # self.activePlrs.remove(player)

    def over(self):
        self.state = 2
        for plr in self.players.values():
            plr.clrState()
            plr.clrActive()
            plr.setHand(None)
            plr.setTotalBet(0)
            plr.unFold()
            plr.clrAllIn()

        self.round += 1
        self.activePlrs.clear()
        self.activeAndDraw = 0
        self.deck = cardsArr
        self.discard.clear()
        self.allHands.clear()
        self.turnIndex = 0+self.round
        self.bet = 0
        self.pool = 0
        self.folded = 0
        self.checks = 0
        self.deck = cardsArr
        self.discard = []
        if len(self.players) < 2: self.state=0
        elif self.readyCount < 2: self.state=1


class PokerServerClientProtocol(asyncio.Protocol):
    def __init__(self, room):
        self.room = room
        self.temp = {}
        self.nextRC = b'PokerProtocol 1.0\nGAME\nr\r\n'

    def connection_made(self, transport):
        self.transport = transport
        self.addr = transport.get_extra_info('peername')
        q.put(f"{self.addr}: --- 200: CONNECTED")
        tempSalt = secrets.token_hex(16)
        tempCookie = hashlib.sha256(tempSalt.encode()).hexdigest()
        self.temp[tempCookie] = self.transport
        self.transport.write(messageWrapper(301,f"{tempCookie}"))
        self.transport.write(messageWrapper(201,"Welcome to the table!\nIf you're ready type \"R\", to exit at any time - \"E\""))

    def data_received(self, data):
        global loggedPlayers

        while True:
            data = data.decode("utf-8")
            data, purpose = msgUnwrapper(data)
            if purpose == "VERIFY":
                loginCredit = loggedPlayers[data[0]]
                transp = self.temp[data[1]]
                p = Player(transp, loginCredit[0], loginCredit[1])
                self.cookie = data[0]
                for plr in self.room.getPlayers().values():
                    plr.getSocket().write(messageWrapper(200,f"{loginCredit[0]} joined."))
                self.room.Add(data[0], p)
                self.plr = self.room.getPlayers()[data[0]]
                q.put(f"{self.addr}: {loginCredit[0]} 200: VERIFIED")
                del self.temp[data[1]]
                return

            else:

                if data[0].upper() == "E":
                    q.put(f"{self.addr}: {self.plr.getLogin()} 301: EXIT")
                    if len(self.room.getPlayers()) > 1:
                        for plr in self.room.getPlayers().values():
                            plr.getSocket().write(messageWrapper(200,f"{self.plr.getLogin()} left."))
                    
                    loggedPlayers[self.cookie]=(self.plr.getLogin(), self.plr.getCredit())
                    if SERVER_HOST=="": self.plr.getSocket().write(messageWrapper(302,("localhost",SERVER_PORT)))
                    else: self.plr.getSocket().write(messageWrapper(302,(SERVER_HOST,SERVER_PORT)))
                    self.room.deActivate(self.plr)
                    self.room.Remove(self.cookie)

                    if len(self.room.getActivePlrs()) == 1:
                        self.room.over()
                        self.data_received(self.nextRC)

                if self.plr.getState() == 0:
                    if data[0].upper() == "R":
                        self.room.Ready(self.plr)
                        if self.room.getState() == 0:
                            q.put(f"{self.addr}: {self.plr.getLogin()} 200: READY - WAITING FOR MORE PLAYERS")
                            self.plr.getSocket().write(messageWrapper(200,"Waiting for more players..."))
                        elif self.room.getState() == 2:
                            for i in range(len(self.room.getPlayers())):
                                currPlr = list(self.room.getPlayers().values())[i]
                                if currPlr.getReady():
                                    q.put(f"{self.addr}: {self.plr.getLogin()} 200: READY - STARTING GAME")
                                    currPlr.getSocket().write(messageWrapper(200,"Players connected, starting game..."))
                                    self.room.Activate(currPlr)
                                    self.room.startState()
                                    self.room.draw(currPlr)
                        elif self.room.getState() > 2 and not self.plr.getActive():
                            q.put(f"{self.addr}: {self.plr.getLogin()} 200: READY - GAME IN PROGRESS")
                            self.plr.getSocket().write(messageWrapper(200,"Game has already started, please wait for next round."))

                    elif data[0].upper() == "Y" and self.plr.getActive():
                        self.plr.setState(1)
                        self.plr.getSocket().write(messageWrapper(201,"Which cards? (numbers separated by space)"))

                    elif data[0].upper() == "N" and self.plr.getActive():
                        self.plr.setState(2)
                        self.room.incAADraw()
                        if self.room.getAADraw() == len(self.room.getActivePlrs()):
                            currplr = self.room.getActivePlrs()[self.room.getTurnIndex()]
                            q.put(f"{self.addr}: {self.plr.getLogin()} 200: {currplr.getLogin()} TURN")
                            for other in self.room.getPlayers().values():
                                if other != currplr:
                                    other.getSocket().write(messageWrapper(200,f"Turn of {currplr.getLogin()}."))
                            currplr.getSocket().write(messageWrapper(201,f"Your turn. Coins: {currplr.getCredit()}.\nYou can bet X coins (B X) or fold (F)."))
                        else:
                            self.plr.getSocket().write(messageWrapper(200,"Please wait for other players."))
                    
                    else:
                        q.put(f"{self.addr}: {self.plr.getLogin()} 401: UNKNOWN COMMAND")
                        self.plr.getSocket().write(messageWrapper(401,"Unknown command\nReady (R), Exit (E)"))

                elif self.plr.getState() == 1:
                    rdraw = data.split(" ")
                    q.put(f"{self.addr}: {self.plr.getLogin()} 200: REDRAW LEN {len(rdraw)}")
                    for nrs in rdraw:
                        try:
                            if int(nrs) > 5 or int(nrs) < 1 or len(rdraw) > 5 or len(rdraw) == 0:
                                q.put(f"{self.addr}: {self.plr.getLogin()} 401: INCORRECT REDRAW")
                                self.plr.getSocket().write(messageWrapper(401,"Choose card(s) between 1 and 5 (ex. \"1 2 5\" will redraw cards 1, 2 and 5)."))
                                return
                        except ValueError:
                            q.put(f"{self.addr}: {self.plr.getLogin()} 401: INCORRECT REDRAW")
                            self.plr.getSocket().write(messageWrapper(401,"Incorrect redraw\nExample: \"1 2 3 4 5\" to redraw whole hand"))
                            return


                    self.room.redraw(self.plr, self.plr.getHand(), rdraw)
                    self.plr.setState(2)
                    self.room.incAADraw()
                    if self.room.getAADraw() == len(self.room.getActivePlrs()):
                        currplr = self.room.getActivePlrs()[self.room.getTurnIndex()]
                        q.put(f"{self.addr}: {self.plr.getLogin()} 200: {currplr.getLogin()} TURN")
                        for other in self.room.getPlayers().values():
                            if other != currplr:
                                other.getSocket().write(messageWrapper(200,f"Turn of {currplr.getLogin()}."))
                        currplr.getSocket().write(messageWrapper(201,f"Your turn. Coins: {currplr.getCredit()}.\nYou can bet X coins (B X) or fold (F)."))
                    else:
                        self.plr.getSocket().write(messageWrapper(200,"Please wait for other players."))

                elif self.plr.getState() == 2:
                    if self.plr == self.room.getActivePlrs()[self.room.getTurnIndex()]:
                        if data[0].upper() == "B" and len(data.split(" ")) > 1:
                            try:
                                bet = int(data.split(" ")[1])
                                if bet < 5 or bet < self.room.getBet()+5:
                                    raise ValueError
                                if self.plr.getCredit() >= bet:
                                    self.plr.setTotalBet(
                                        self.plr.getTotalBet()+bet)
                                    self.plr.modCredit(-bet)
                                    self.room.addPool(bet)
                                    self.room.modBet(bet)
                                    q.put(f"{self.addr}: {self.plr.getLogin()} 200: BET {bet} ")
                                    for other in self.room.getPlayers().values():
                                        if other != self.plr:
                                            other.getSocket().write(messageWrapper(200,f"{self.plr.getLogin()} bet {bet} coins."))

                                self.room.clrCheck()
                                self.room.incCheck()
                                self.room.incTurnIndex()
                                nextplr = self.room.getActivePlrs()[self.room.getTurnIndex()]
                                while nextplr.getFold() or nextplr.getAllIn():
                                    self.room.incTurnIndex()
                                    nextplr = self.room.getActivePlrs()[
                                        self.room.getTurnIndex()]
                                nextplr.getSocket().write(messageWrapper(201,f"Your turn. Coins: {nextplr.getCredit()}.\nYou can check (C), bet X coins (B X) or fold (F)."))
                                q.put(f"{self.addr}: {self.plr.getLogin()} 200: {nextplr.getLogin()} TURN")
                                for other in self.room.getPlayers().values():
                                    if other != nextplr:
                                        other.getSocket().write(messageWrapper(200,f"Turn of {nextplr.getLogin()}."))

                            except ValueError:
                                q.put(f"{self.addr}: {self.plr.getLogin()} 401: INCORRECT AMOUNT/FORMAT {data}")
                                self.plr.getSocket().write(messageWrapper(401,"Incorrect format/amount.\nMinimal bet is 5 coins.\nTo bet type \"B\" (AMOUNT), example: \"B 100\" bets 100 coins"))
                        elif data[0].upper() == "F":
                            self.room.foldPlayer(self.plr)
                            q.put(f"{self.addr}: {self.plr.getLogin()} 200: FOLD")
                            winner = None
                            if self.room.getFoldCount() == len(self.room.getActivePlrs())-1:
                                for plr in self.room.getActivePlrs():
                                    if not plr.getFold():
                                        winner = plr

                            if winner is not None:
                                for other in self.room.getPlayers().values():
                                    if other != winner:
                                        other.getSocket().write(messageWrapper(200,f"{winner.getLogin()} won {self.room.getPool()} coins before showdown.\nPlease wait for other players."))
                                winner.getSocket().write(messageWrapper(200,f"You won {self.room.getPool()} coins before showdown.\nPlease wait for other players."))
                                winner.modCredit(self.room.getPool())
                                q.put(f"{self.addr}: {self.plr.getLogin()} 200: WINNER {winner.getLogin()} {self.room.getPool()} BEFORE SHOWDOWN")
                                self.room.over()
                                data = self.nextRC
                                continue
                            else:
                                self.room.incTurnIndex()
                                nextplr = self.room.getActivePlrs()[
                                    self.room.getTurnIndex()]
                                while nextplr.getFold() or nextplr.getAllIn():
                                    self.room.incTurnIndex()
                                    nextplr = self.room.getActivePlrs()[
                                        self.room.getTurnIndex()]
                                q.put(f"{self.addr}: {self.plr.getLogin()} 200: {nextplr.getLogin()} TURN")

                                for other in self.room.getPlayers().values():
                                    if other != self.plr:
                                        other.getSocket().write(messageWrapper(200,f"{self.plr.getLogin()} folded. Now turn of {nextplr.getLogin()}"))
                                if self.room.bet == 0:
                                    nextplr.getSocket().write(messageWrapper(200,f"Your turn. Coins: {nextplr.getCredit()}.\nYou can bet X coins (B X) or fold (F)."))
                                else:
                                    nextplr.getSocket().write(messageWrapper(201,f"Your turn. Coins: {nextplr.getCredit()}.\nYou can check (C), bet X coins (B X) or fold (F)."))

                        elif data[0].upper() == "C" and self.room.getBet() != 0:
                            if self.plr.getCredit() >= self.room.getBet() - self.plr.getTotalBet():
                                self.plr.modCredit(-(self.room.getBet() -
                                                self.plr.getTotalBet()))
                                self.room.addPool(
                                    self.room.getBet() - self.plr.getTotalBet())
                                self.plr.setTotalBet(self.room.getBet())
                                q.put(f"{self.addr}: {self.plr.getLogin()} 200: CHECK")
                            else:
                                coins = self.plr.getCredit()
                                self.plr.modCredit(-coins)
                                self.room.addPool(coins)
                                self.plr.setTotalBet(self.plr.getTotalBet+coins)
                                self.plr.allIn()
                                q.put(f"{self.addr}: {self.plr.getLogin()} 200: ALLIN")

                            self.room.incCheck()

                            if self.room.getChecks() == len(self.room.getActivePlrs()) - self.room.getFoldCount():
                                plrHandDict = {}
                                for plr in self.room.getPlayers().values():
                                    for actPlr in self.room.getActivePlrs():
                                        if plr == actPlr:
                                            plr.getSocket().write(messageWrapper(200,f"Your hand: {actPlr.getHand()}"))
                                        else:
                                            plr.getSocket().write(messageWrapper(200,f"{actPlr.getLogin()}'s hand: {actPlr.getHand()}"))
                                        plrHandDict[actPlr.getHand()] = actPlr

                                winHands, handName = seekWinner(
                                    '', self.room.getAllHands())
                                winners = []
                                for x in winHands:
                                    winners.append(
                                        plrHandDict[self.room.getAllHands()[x]])
                                
                                q.put(f"{self.addr}: {self.plr.getLogin()} 200: WINNERS {[win.getLogin() for win in winners]} WITH {handName} {self.room.getPool()}")

                                for winner in winners:
                                    for plr in self.room.getPlayers().values():
                                        if plr == winner:
                                            plr.getSocket().write(messageWrapper(200,f"You won {int(self.room.getPool()/len(winners))} coins with {handName}!"))
                                        else:
                                            plr.getSocket().write(messageWrapper(200,f"{winner.getLogin()} won {int(self.room.getPool()/len(winners))} coins with {handName}!"))
                                    winner.modCredit(self.room.getPool())

                                self.room.over()
                                data = self.nextRC
                                continue
                            else:
                                self.room.incTurnIndex()
                                nextplr = self.room.getActivePlrs()[
                                    self.room.getTurnIndex()]
                                while nextplr.getFold() or nextplr.getAllIn():
                                    self.room.incTurnIndex()
                                    nextplr = self.room.getActivePlrs()[
                                        self.room.getTurnIndex()]

                                q.put(f"{self.addr}: {self.plr.getLogin()} 200: {nextplr.getLogin} TURN")

                                for other in self.room.getPlayers().values():
                                    if other != self.plr:
                                        if self.plr.getAllIn():
                                            other.getSocket().write(messageWrapper(200,f"{self.plr.getLogin()} went all-in. Now turn of {nextplr.getLogin()}"))
                                        else:
                                            other.getSocket().write(messageWrapper(200,f"{self.plr.getLogin()} checks. Now turn of {nextplr.getLogin()}"))

                                nextplr.getSocket().write(messageWrapper(201,f"Your turn. Coins: {nextplr.getCredit()}.\nYou can check (C), bet X coins (B X) or fold (F)."))

                        else:
                            if self.room.getBet() == 0:
                                q.put(f"{self.addr}: {self.plr.getLogin()} 401: INCORRECT FORMAT")
                                self.plr.getSocket().write(messageWrapper(401,"Incorrect format, to bet type \"B\" (AMOUNT), example: \"B 100\" bets 100 coins, to fold just type \"F\"."))
                            else:
                                q.put(f"{self.addr}: {self.plr.getLogin()} 401: INCORRECT FORMAT")
                                self.plr.getSocket().write(messageWrapper(401,"Incorrect format, to bet type \"B\" (AMOUNT), example: \"B 100\" bets 100 coins, to check type \"C\", to fold type \"F\"."))

            break

    def connection_lost(self, ex):
        q.put(f"{self.addr}: {self.plr.getLogin()} 200: DISCONNECTED")
        self.room.deActivate(self.plr)
        #self.room.unReady(self.plr)
        try: self.room.deActivate(self.plr)
        except ValueError: pass
        if len(self.room.getPlayers()) > 1:
            for plr in self.room.getPlayers().values():
                plr.getSocket().write(messageWrapper(200,f"{self.plr.getLogin()} left."))

        with lock:
            with open("credentials.txt", "r") as f:
                whole = f.read()
            s_old = re.search(f"{self.plr.getLogin()};.*;\d*", whole).group(0)
            s_new = s_old[:s_old.rfind(";")]+f";{str(self.plr.getCredit())}"
            whole = re.sub(s_old, s_new, whole)
            with open("credentials.txt", "w") as f:
                f.write(whole)

        self.room.Remove(self.cookie)

        if len(self.room.getActivePlrs()) == 1:
            self.room.over()
            self.data_received(self.nextRC)


def serverReceive(socket):
    rec_data = ""
    while not "\r\n" in rec_data:
        data = socket.recv(1024)
        rec_data += data.decode("utf-8")
    return rec_data


def clientResp(client, addr, redirected=False):
    try:
        login = ""
        credit = None
        cookie = None
        rec_data, purpose = msgUnwrapper(serverReceive(client))
        if purpose == "OPTIONS":
            q.put(f"{addr}: {purpose}")
            client.sendall(messageWrapper(100,"Do you want to log-in (L), or register (R)?"))

        if purpose == "VERIFY":
            loginCredit = loggedPlayers[rec_data[0]]
            login=loginCredit[0]
            credit=loginCredit[1]
            cookie = rec_data[0]
            q.put(f"{addr}: {loginCredit[0]} 200: VERIFIED")

        else:
            isOk = False
            while not isOk:
                rec_data, _ = msgUnwrapper(serverReceive(client))
                q.put(f"{addr}: {rec_data}")
                try:
                    if rec_data[0].upper() == "L":
                        client.sendall(messageWrapper(201,"Login:"))
                        login, _ = msgUnwrapper(serverReceive(client))
                        q.put(f"{addr}: {login}")
                        client.sendall(messageWrapper(202,"Password:")) 
                        password, _ = msgUnwrapper(serverReceive(client))

                        try:
                            if login in list(loggedPlayers.values())[0]:
                                q.put(f"{addr}: {login} 401: ALREADY LOGGED IN")
                                client.sendall(messageWrapper(401,"This user is already logged in.\nLog-in (L), register (R)"))
                                continue

                        except IndexError:
                            pass

                        with lock:
                            cred = open("credentials.txt", "r")
                            salts = open("salts.txt", "r")
                            fullCred = cred.read()
                            fullSalt = salts.read()
                            cred.close()
                            salts.close()
                        lineStart = fullCred.find(login+";")
                        if lineStart == -1:
                            q.put(f"{addr}: {login} 401: USERNAME INCORRECT")
                            client.sendall(messageWrapper(401,"Username incorrect, try again.\nLog-in (L), register (R)"))
                            continue
                        else:
                            lineEnd = fullCred[lineStart:].find("\n")
                            lineCr = fullCred[lineStart:lineStart+lineEnd]
                            splitCr = lineCr.split(";")

                            lineStart = fullSalt.find(login)
                            lineEnd = fullSalt[lineStart:].find("\n")
                            lineS = fullSalt[lineStart:lineStart+lineEnd]

                            if splitCr[1] == hashlib.sha256((password+lineS.split(";")[1]).encode()).hexdigest():
                                isOk = True
                                credit = int(splitCr[2])

                                cookieSalt = secrets.token_hex(16)
                                cookie = hashlib.sha256((login+cookieSalt).encode()).hexdigest()
                                loggedPlayers[cookie] = (login, credit)

                            else:
                                q.put(f"{addr}: {login} 401: PASSWORD INCORRECT")
                                client.sendall(messageWrapper(401,"Password incorrect, try again.\nLog-in (L), register (R)"))
                                continue
                    elif rec_data[0].upper() == "R":
                        client.sendall(messageWrapper(201,"Choose login:"))
                        login, _ = msgUnwrapper(serverReceive(client))

                        if not re.fullmatch(r"\w{3,15}", login):
                            q.put(f"{addr}: {login} 401: USERNAME INCORRECT")
                            client.sendall(messageWrapper(401,"Username incorrect, only alphanumeric characters and underscore allowed, min length 3, max 15.\nLog-in (L), register (R)"))
                            continue

                        with lock:
                            cred = open("credentials.txt", "r")
                            fullCred = cred.read()
                            cred.close()

                        if bool(re.search(f"\n?{login};", fullCred)):
                            q.put(f"{addr}: {login} 401: USERNAME TAKEN")
                            client.sendall(messageWrapper(401,"Username already taken.\nLog-in (L), register (R)"))
                            continue

                        match = False
                        while not match:
                            client.sendall(messageWrapper(202,"Choose password:")) 
                            password, _ = msgUnwrapper(serverReceive(client))

                            if not re.fullmatch(r"\S{8,25}", password):
                                q.put(f"{addr}: {login} 402: PASSWORD INCORRECT")
                                client.sendall(messageWrapper(402,"Password incorrect, minimal length - 8, maximal - 25, no whitespaces"))
                                continue

                            client.sendall(messageWrapper(202,"Verify password:")) 
                            verPassword, _ = msgUnwrapper(serverReceive(client))
                            if password == verPassword:
                                salt = secrets.token_hex(8)
                                pHash = hashlib.sha256((password+salt).encode()).hexdigest()
                                with lock:
                                    with open("credentials.txt", "a") as f:
                                        f.write(f"{login};{pHash};500\n")
                                    with open("salts.txt", "a") as f:
                                        f.write(f"{login};{salt}\n")
                                q.put(f"{addr}: {login} 200: ACCOUNT CREATED")
                                client.sendall(messageWrapper(200,"Account created."))
                                match = True
                                isOk = True
                                credit = 500

                                cookieSalt = secrets.token_hex(16)
                                cookie = hashlib.sha256((login+cookieSalt).encode()).hexdigest()
                                loggedPlayers[cookie] = (login, credit)

                            else:
                                q.put(f"{addr}: {login} 402: PASSWORD MISMATCH")
                                client.sendall(messageWrapper(402,"Passwords don't match. Try again."))
                    else:
                        q.put(f"{addr}: {login} 401: UNKNOWN COMMAND")
                        client.sendall(messageWrapper(401,"Unknown command\nDo you want to log-in (L), or register (R)?"))
                except IndexError:
                    q.put(f"{addr}: {login} 401: UNKNOWN COMMAND - INDEX ERROR")
                    client.sendall(messageWrapper(401,"Unknown command\nDo you want to log-in (L), or register (R)?"))

        q.put(f"{addr}: {login} 200: USER LOGGED IN")
        client.sendall(messageWrapper(200,f"Logged in as: {login}. Coins: {credit}"))

        while True:
            roomSeq = "\n"
            for i in range(len(roomArr)):
                roomSeq += f"{str(i+1)}. {roomArr[i]}\n"
            
            client.sendall(messageWrapper(201,f"Rooms available: {len(roomArr)}{roomSeq}If you wish to create new room, type New(N). To log-out(L)"))

            rec_data, _ = msgUnwrapper(serverReceive(client))
            try:
                if rec_data[0].upper() == "N":
                    if len(roomArr)*8 > len(loggedPlayers)+8:
                        q.put(f"{addr}: {login} 403: TOO MANY ROOMS")
                        client.sendall(messageWrapper(403,f"There are still empty seats in existing rooms, please join one of them"))
                        continue
                    rPort = random.randint(30000, 50000)
                    if SERVER_HOST=="": r = Room("localhost", rPort)
                    else: r = Room(SERVER_HOST, rPort)
                    roomArr.append(r)

                    eloop = asyncio.new_event_loop()
                    asyncio.set_event_loop(eloop)
                    loop = asyncio.get_event_loop()

                    ssl_context = ssl.create_default_context( ssl.Purpose.CLIENT_AUTH)
                    ssl_context.check_hostname = False
                    ssl_context.load_cert_chain(SERVER_CERT, SERVER_KEY)

                    if SERVER_HOST=="": coroutine = loop.create_server(lambda: PokerServerClientProtocol(r,), host="localhost", port=rPort, ssl=ssl_context)
                    else: coroutine = loop.create_server(lambda: PokerServerClientProtocol(r,), host=SERVER_HOST, port=rPort, ssl=ssl_context)
                    q.put(f"{addr}: {login} 200: NEW SERVER STARTED")

                    if SERVER_HOST=="": client.sendall(messageWrapper(300,("localhost",rPort,cookie)))
                    else: client.sendall(messageWrapper(300,(SERVER_HOST,rPort,cookie)))
                    server = eloop.run_until_complete(coroutine)
                    eloop.run_forever()
                    return
                elif rec_data[0].upper() == "L":
                    del loggedPlayers[cookie]
                    client.sendall(messageWrapper(203,None))
                    return
                else:
                    try:
                        joiningRoom = int(rec_data)
                        if joiningRoom <= len(roomArr):
                            joiningRoom -= 1
                            client.sendall(messageWrapper(300,(roomArr[joiningRoom].getAddr(), roomArr[joiningRoom].getPort(), cookie)))
                            q.put(f"{addr}: {login} 300: REDIRECT TO GAME SERVER")
                            return
                        else:
                            client.sendall(messageWrapper(403,f"No such room, try again."))
                            q.put(f"{addr}: {login} 403: INCORRECT ROOM")
                            

                    except ValueError:
                        client.sendall(messageWrapper(403,f"Incorrect command, try again."))
                        q.put(f"{addr}: {login} 403: INCORRECT COMMAND")

            except IndexError:
                client.sendall(messageWrapper(403,f"Incorrect command, try again."))
                q.put(f"{addr}: {login} 403: INCORRECT COMMAND")

    except ConnectionResetError:
        q.put(f"{addr}: {login} 400: CONNECTION RESET ERROR")
        if cookie in loggedPlayers:
            del loggedPlayers[cookie]


def logger():
    while True:
        with open("ServerLogs.txt","ab") as f:
            data=q.get()
            f.write(f"{datetime.datetime.now()} {data} \n".encode())


def main():
    global SERVER_HOST, SERVER_PORT, SERVER_CERT, SERVER_KEY, roomArr, loggedPlayers, lock, cardsArr, q
    
    with open("credentials.txt", "a") as f: pass
    with open("salts.txt", "a") as f: pass

    if "-h" in sys.argv:
        SERVER_HOST=sys.argv[sys.argv.index("-h") + 1]
    if "-p" in sys.argv:
        SERVER_PORT=int(sys.argv[sys.argv.index("-p") + 1])
    if "-crt" in sys.argv:
        SERVER_CERT=sys.argv[sys.argv.index("-crt") + 1]
    if "-key" in sys.argv:
        SERVER_KEY=sys.argv[sys.argv.index("-key") + 1]

    q = queue.Queue()
    s = socket.create_server((SERVER_HOST, SERVER_PORT), family=socket.AF_INET6, dualstack_ipv6=True)

    log = threading.Thread(target=logger)
    log.start()

    s.listen(16)
    roomArr = []
    loggedPlayers = {}
    lock = threading.Lock()
    cardsArr = ["2♥", "3♥", "4♥", "5♥", "6♥", "7♥", "8♥", "9♥", "T♥", "J♥", "Q♥", "K♥", "A♥",
                "2♦", "3♦", "4♦", "5♦", "6♦", "7♦", "8♦", "9♦", "T♦", "J♦", "Q♦", "K♦", "A♦",
                "2♠", "3♠", "4♠", "5♠", "6♠", "7♠", "8♠", "9♠", "T♠", "J♠", "Q♠", "K♠", "A♠",
                "2♣", "3♣", "4♣", "5♣", "6♣", "7♣", "8♣", "9♣", "T♣", "J♣", "Q♣", "K♣", "A♣"]

    while True:
        client, addr = s.accept()

        ssl_client = ssl.wrap_socket(client, server_side=True, certfile=SERVER_CERT, keyfile=SERVER_KEY, ssl_version=ssl.PROTOCOL_TLSv1_2)

        q.put(f"Connected: {addr}")
        x = threading.Thread(target=clientResp, args=(ssl_client, addr,))
        x.start()

if __name__ == "__main__":
    main()
