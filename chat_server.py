import time
import socket
import select
import sys
import string
import indexer
import pickle as pkl
from chat_utils import *
import chat_group as grp
from FiveInARow import *

PLAYER_BLACK = False
PLAYER_WHITE = True
F_END = -1

class Server:
    def __init__(self):
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_name2sock = {}  # dictionary mapping username to socket
        self.logged_sock2name = {}  # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        # start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        # initialize past chat indices
        self.indices = {}
        # sonnet
        self.sonnet_f = open('AllSonnets.txt.idx', 'rb')
        self.sonnet = pkl.load(self.sonnet_f)
        self.sonnet_f.close()
        # game
        self.game = Five(10, 10)
        self.game_started = False                           #whether game is on
        self.who = PLAYER_BLACK                             #whose turn
        self.players = []                                   #unused for now, to be developed

    def new_client(self, sock):
        # add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        # read the msg that should have login code plus username
        msg = myrecv(sock)
        if len(msg) > 0:
            code = msg[0]

            if code == M_LOGIN:
                name = msg[1:]
                if self.group.is_member(name) != True:
                    # move socket from new clients list to logged clients
                    self.new_clients.remove(sock)
                    # add into the name to sock mapping
                    self.logged_name2sock[name] = sock
                    self.logged_sock2name[sock] = name
                    # load chat history of that user
                    if name not in self.indices.keys():
                        try:
                            self.indices[name] = pkl.load(open(name + '.idx', 'rb'))
                        except IOError:  # chat index does not exist, then create one
                            self.indices[name] = indexer.Index(name)
                    print(name + ' logged in')
                    self.group.join(name)
                    mysend(sock, M_LOGIN + 'ok')
                else:  # a client under this name has already logged in
                    mysend(sock, M_LOGIN + 'duplicate')
                    print(name + ' duplicate login attempt')
            else:
                print('wrong code received')
        else:  # client died unexpectedly
            self.logout(sock)

    def logout(self, sock):
        # remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx', 'wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

    # ==============================================================================
    # main command switchboard
    # ==============================================================================
    def handle_msg(self, from_sock):
        # read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
            code = msg[0]
            # ==============================================================================
            # handle connect request
            # ==============================================================================
            if code == M_CONNECT:
                to_name = msg[1:]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = M_CONNECT + 'hey you'
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = M_CONNECT + 'ok'
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, M_CONNECT + from_name)
                else:
                    msg = M_CONNECT + 'no_user'
                mysend(from_sock, msg)
            # ==============================================================================
            # handle message exchange
            # ==============================================================================
            elif code == M_EXCHANGE:
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                said = msg[1:]
                said2 = text_proc(said, from_name)
                self.indices[from_name].add_msg_and_index(said2)
                for g in the_guys[1:]:
                    to_sock = self.logged_name2sock[g]
                    self.indices[g].add_msg_and_index(said2)
                    mysend(to_sock, msg)
            # ==============================================================================
            # handle game module
            # ==============================================================================
            elif code == M_GAME:
                move = msg[3:].strip()
                from_name = self.logged_sock2name[from_sock]
                #to_name = self.group.list_me(from_name)[1]
                #to_sock = self.logged_name2sock[to_name]
                if not self.game_started:               #if not started, "-g (whatever)" can start
                    peer = move                         #"move" actually is peer name
                    #print ("peer = ", peer, ", listme = ", self.group.list_me(from_name))
                    if peer in self.group.list_me(from_name):
                        to_name = peer
                        self.players = [from_name, to_name]
                    elif peer == '' and len(self.group.list_me(from_name)) == 2:
                        to_name = self.group.list_me(from_name)[1]
                        self.players = [from_name, to_name]
                    else:
                        mysend(from_sock, M_EXCHANGE + "No such person.")
                        return
                    
                    to_sock = self.logged_name2sock[to_name]        
                    self.game_started = True
                    self.who = PLAYER_BLACK             #always black first, 
                    self.game = Five(10, 10)            #though who is black is random
                    self.game.board_init(self.who, from_sock, to_sock)
                    
                    """peers = self.group.list_me(from_name)[1:]
                    for peer in peers:
                        if peer not in self.players:
                            to_sock = self.logged_name2sock[peer]
                            self.game.send_to_peer(to_sock)"""
                else:
                    if self.players[0] == from_name:
                        to_name = self.players[1]
                    else: to_name = self.players[0]
                    to_sock = self.logged_name2sock[to_name]
                    response = self.game.make_move(self.who, move, from_sock, to_sock)
                    if not response:                    #response = true: run normally
                        print("Wrong game command.")    #response = false: illegal command
                    elif response == F_END:             #response = F_END = -1, game ends
                        self.game_started = False
                    else:
                        self.who = not self.who
            # ==============================================================================
            # listing available peers
            # ==============================================================================
            elif code == M_LIST:
                from_name = self.logged_sock2name[from_sock]
                msg = self.group.list_all()
                mysend(from_sock, msg)
            # ==============================================================================
            # retrieve a sonnet
            # ==============================================================================
            elif code == M_POEM:
                poem_indx = int(msg[1:])
                from_name = self.logged_sock2name[from_sock]
                print(from_name + ' asks for ', poem_indx)
                poem = self.sonnet.get_sect(poem_indx)
                print('here:\n', poem)
                mysend(from_sock, M_POEM + poem)
            # ==============================================================================
            # time
            # ==============================================================================
            elif code == M_TIME:
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, ctime)
            # ==============================================================================
            # search
            # ==============================================================================
            elif code == M_SEARCH:
                term = msg[1:]
                from_name = self.logged_sock2name[from_sock]
                print('search for ' + from_name + ' for ' + term)
                search_rslt = (self.indices[from_name].search(term)).strip()
                print('server side search: ' + search_rslt)
                mysend(from_sock, M_SEARCH + search_rslt)
            # ==============================================================================
            # the "from" guy has had enough (talking to "to")!
            # ==============================================================================
            elif code == M_DISCONNECT:
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, M_DISCONNECT)
                # ==============================================================================
                # the "from" guy really, really has had enough
                # ==============================================================================
            elif code == M_LOGOUT:
                self.logout(from_sock)
        else:
            # client died unexpectedly
            self.logout(from_sock)

        # ==============================================================================
        # main loop, loops *forever*
        # ==============================================================================

    def run(self):
        print('starting server...')
        while (1):
            read, write, error = select.select(self.all_sockets, [], [])
            print('checking logged clients..')
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            print('checking new clients..')
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            print('checking for new connections..')
            if self.server in read:
                # new client request
                sock, address = self.server.accept()
                self.new_client(sock)


def main():
    server = Server()
    server.run()


main()
