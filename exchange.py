#!/usr/bin/env python

serviceFunction = {}
# service function is a mapping from activity number to
# a tuple (marshall,
#
import string
import socket
import asynchat
import select
import os
import sys

serviceConnections = {  }
revServiceConnections = { }
serviceCounter = 10000
serviceDatabase = { 'default' : {} }
vocabularyDatabase = { 'default' : {'NAME' : ('string',None),
                                    'VERSION': ('real','1.0')}
                       }
def first_word(str):
    return string.split(str)[0]

def return_code(str):
    return string.atoi(first_word(str))

def RegisterVocabulary(name,attributes):
    if vocabularyDatabase.has_key(name):
        return '200 Vocabulary exists'
    # check that it's vaguely sane
    attribute_database = {}
    for attr in attributes:
        try:
            [varname,vartype] = string.split(attr,'::',2)
        except:
            return '203 Vocabulary attributes ill-defined'
        if string.find(vartype,'=') > 0:
            print varname,"has a default --",vartype
            [vartype,default_val] =  string.split(vartype,'=',2)
        else:
            default_val = None
        attribute_database[varname] = (vartype,default_val)
    vocabularyDatabase[name] = attribute_database
    serviceDatabase[name] = {}
    return '100 Vocabulary Registered'

def DeregisterVocabulary(name):
    if name == 'default':
        return '206 Cannot delete default vocabulary'
    if not(vocabularyDatabase.has_key(name)):
        return '201 Vocabulary name not found'
    if serviceDatabase[name].keys() != []:
        return '213 Cannot delete vocabulary while services are registered'
    del vocabularyDatabase[name]
    return '101 Vocabulary Deregistered'

def RegisterService(vocabname,attributes,connection):
    if not(vocabularyDatabase.has_key(vocabname)):
        return '202 Vocabulary unknown'
    # check that the attributes are sane
    this_vocab = vocabularyDatabase[vocabname]
    this_service_description = {}
    for attr in attributes:
        try:
            [key,value] = string.split(string.upper(attr),'=',2)
        except:
            return '204 Service attributes ill-defined'
        if not(this_vocab.has_key(key)):
            print this_vocab
            print "Does not have",key
            return '205 Service attributes not in vocabulary'
        this_service_description[key] = value
    for key in vocabularyDatabase[vocabname].keys():
        if not(this_service_description.has_key(key)):
            if this_vocab[key][1] is None:
                return '207 Necessary attribute missing'
            else:
                this_service_description[key] = this_vocab[key][1]
    servid = connection.servid
    if serviceDatabase[vocabname].has_key(servid):
       return '216 Service already registered in this vocabulary'
    serviceDatabase[vocabname][servid] = this_service_description
    return '102 ' + `serviceCounter` + ' Service Registered'

def DeregisterService(servid):
    if not(serviceConnections.has_key(servid)):
       return '215 Unknown service identifier'
    connection = serviceConnections[servid]
    vocabname = revServiceConnections[id(connection)][servid]
    del revServiceConnections[id(connection)][servid]
    del serviceConnections[servid]
    del serviceDatabase[vocabname][servid]
    return '111 Service deregistered'

def findServices(vocabname,attributes,stop_after_the_first=0):
    if not(vocabularyDatabase.has_key(vocabname)):
        return '202 Vocabulary unknown'
    # check that the attributes are sane
    this_vocab = vocabularyDatabase[vocabname]
    this_servicedb = serviceDatabase[vocabname]
    results = []
    for service in this_servicedb.keys():
        this_service = this_servicedb[service]
        checks_out = 1
        for attr in attributes:
            try:
                [key,value] = string.split(string.upper(attr),'=',2)
                # Later I need to support cleverer searches,  e.g. >, <=
                # possibly even 'LIKE',  etc...
            except:
                return '208 Search criteria malformed'
            if not(this_vocab.has_key(key)):
                return '209 Search on non-existant fields'
            if this_service[key] != value:
                checks_out = 0
                break
        if checks_out==1:
            if stop_after_the_first: return ('103 1 Service Found -- list follows (full stop terminates):\r\n' + `service` + '\r\n.')
            results.append(service)
    if results == []:
        return '104 No services found'
    else:
        str = '104 ' + `len(results)` + ' Services Found -- list follows (full stop terminates):\r\n'
        listing = string.join(map(lambda x: `x`,results),'\r\n')
        return str + listing + '\r\n.'



class MicrospeakExchange(asynchat.async_chat):
    def __init__(self,conn):
         asynchat.async_chat.__init__(self,conn)
         self.__incoming = ''
         self.conn = conn
         self.set_terminator('\r\n')
         self.message_destination = None  # could also be 1
         global serviceCounter
         serviceCounter = serviceCounter + 1
         self.servid = serviceCounter
         serviceConnections[self.servid] = self
         self.identities = []
         #self.registered_services
    def collect_incoming_data(self,data):
         self.__incoming = self.__incoming + data
         # I should actually check to see whether this
         # is getting too large.  Maybe 1MB???
    def found_terminator(self):
         if self.message_destination is not None:
             self.__incoming = self.__incoming + '\r\n.\r\n'
             self.message_destination.send(`self.servid`,self.__incoming)
             self.__incoming = ''
             self.set_terminator('\r\n')
             self.message_destination = None
             self.conn.send('106 Message sent\r\n')
             return
         # otherwise,  it's an ordinary transaction command
         # Get the first word
         sys.stderr.write('Finding first word in ' + self.__incoming + '\n')
         pos = 0
         while self.__incoming[pos] not in string.whitespace:
             pos = pos + 1
             if pos >= len(self.__incoming):  break
         first_word = string.upper(self.__incoming[:pos])
         if first_word == '.':
            # they are needing to reset.  OK
            pass
         elif first_word == 'REGVOCAB':
            parts = string.split(self.__incoming[pos:])
            self.conn.send(RegisterVocabulary(parts[0],parts[1:]) +'\r\n')
         elif first_word == 'DEREGVOCAB':
            self.conn.send(DeregisterVocabulary(string.strip(self.__incoming[pos:])) +'\r\n')
         elif first_word == 'REGSERVICE':
             attributes = string.split(self.__incoming[pos:])
             vocabname = attributes[0]
             result = RegisterService(attributes[0],attributes[1:],self)+'\r\n'
             self.conn.send(result)

             if return_code(result) == 102:
                 i = id(self.conn)
                 if revServiceConnections.has_key(i):
                     revServiceConnections[i][self.servid]=vocabname
                 else:
                     revServiceConnections[i] = {self.servid:vocabname}
         elif first_word == 'DEREGSERVICE':
            self.conn.send(DeregisterService(string.strip(self.__incoming[pos:]))+'\r\n')	
         elif first_word == 'FINDSERVICE':
            attributes = string.split(self.__incoming[pos:])
            self.conn.send(findServices(attributes[0],attributes[1:],1)+'\r\n')
         elif first_word == 'FINDALLSERV':
            attributes = string.split(self.__incoming[pos:])
            self.conn.send(findServices(attributes[0],attributes[1:])+'\r\n')
         elif first_word == 'QUIT':
             self.conn.close()
             # now I need to clean up.  I haven't finished this code yet
         elif first_word == 'SENDTO':
            other_words = string.split(self.__incoming[pos:])
            try:
               servnum = string.atoi(other_words[0])
            except:
               self.conn.send('210 Service number incomprehensible\r\n')
               self.__incoming = ''
               return
            global serviceConnections
            if not(serviceConnections.has_key(servnum)):
               self.conn.send('211 Service number not registered\r\n')
               self.__incoming = ''
               return
            self.message_destination = serviceConnections[servnum]
            self.set_terminator('\r\n.\r\n')
            self.conn.send('105 Ready to send -- end with . on its own\r\n')
         elif first_word == 'VERSION':
            self.conn.send('107 1.0 version number\r\n')
         elif first_word == 'HELP':
            self.conn.send('108 Help... cmds known are REGVOCAB DEREGVOCAB REGSERVICE DEREGSERVICE FINDSERVICE FINDALLSERV SENDTO VERSION HELP QUIT\r\n')
         else:
            self.conn.send('212 Command not understood\r\n')
         self.__incoming = ''
    def send(self,src,data):
         self.conn.send('900 ' + src + ' incoming message\r\n')
         self.conn.send(data)
    def fileno(self):
         return self.conn.fileno()
    def terminate(self):
         i = id(self)
         if revServiceDatabase.has_key[i]:
             for serv in revServiceDatabase[i].keys():
                    DeregisterService(serv)
         del serviceConnections[self.servid]
         self.conn.close()
         global filehandles
         filehandles.remove(self)

listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.bind('',1377)
listen_socket.listen(1)

filehandles = [listen_socket]

while 1:
    (reads,writes,errors) = select.select(filehandles,[],filehandles)
    for f in reads:
       if f == listen_socket:
          conn,addr = listen_socket.accept()
          filehandles.append(MicrospeakExchange(conn))
          conn.send('111 Hello\r\n')
       else:
          f.handle_read()
    for f in errors:
       if f == listen_socket:
          sys.exit('Error on listening socket!')
       else:
          f.terminate()
          #filehandles.remove(f)
