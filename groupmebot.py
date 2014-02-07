#!/usr/bin/python
# -*- coding: utf-8 -*-

# GroupMeBot: A python framework for a GroupMe Bot
# See http://www.groupme.com for more details

# Copyright (c)  Martin Zehetmayer <angrox at idle dot at>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

# Parts of the code where taken from the jabberbot framework from 
# Thomas Perl <thp.io/about>

import os
import re
import sys
import httplib
import urllib

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import cgi
import json
import inspect

# Stolen from groupmebot:
def botcmd(*args, **kwargs):
    """Decorator for bot command functions"""

    def decorate(func, hidden=False, name=None):
        setattr(func, '_groupmebot_command', True)
        setattr(func, '_groupmebot_hidden', hidden)
        setattr(func, '_groupmebot_command_name', name or func.__name__)
        return func

    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)



class GroupMeBot(object):
    
    def __init__(self, bot_token, bot_id, portnumber, ip='', commandprefix='.'):
        """Initializes the groupme bot and sets up commands.

        If privatedomain is provided, it should be either
        True to only allow subscriptions from the same domain
        as the bot or a string that describes the domain for
        which subscriptions are accepted (e.g. 'groupme.org').

        If acceptownmsgs it set to True, this bot will accept
        messages from the same JID that the bot itself has. This
        is useful when using JabberBot with a single Jabber account
        and multiple instances that want to talk to each other.
        """
        self.__bot_id = bot_id
        self.__bot_token = bot_token
        self.__portnumber = portnumber
        self.__ip = ip
        self.__commandprefix = commandprefix
        self.commands = {}
        for name, value in inspect.getmembers(self):
            if inspect.ismethod(value) and getattr(value, '_groupmebot_command', False):
                name = getattr(value, '_groupmebot_command_name')
                self.commands[name] = value
    


    def getBotID(self):
        return self.__bot_id

    def getBotToken(self):
        return self.__bot_token

    def start(self):
        try:
            server = BotHTTPServer((self.__ip, self.__portnumber), GroupMeBotHTTPServer, botobj=self)
            print 'Started groupme bot on port ' , self.__portnumber
            
            server.serve_forever()
        except KeyboardInterrupt:
            print '^C received, shutting down ...'
            server.socket.close()


    def sendmessage(self, msg, user_id ):
        if user_id == self.getBotID():
            return
        params = urllib.urlencode( {'bot_id': self.getBotToken(), 'text': msg} )
        headers = {"Content-type": "application/x-www-form-urlencoded",  "Accept": "text/plain"} 
        conn = httplib.HTTPSConnection("api.groupme.com")
        conn.request('POST', '/v3/bots/post', params, headers)


    def parseData(self, data):
        #self.sendmessage("ack", data['user_id'])
        
        splitline=unicode(data['text']).split(' ')
        cmd=splitline[0]
        args=splitline[1:]
        if self.__commandprefix != '':
            if not cmd.startswith(self.__commandprefix):
                return None
            else:
                cmd = cmd.lstrip(self.__commandprefix)
        if self.commands.has_key(cmd):
            try:
                reply = self.commands[cmd](args)
                self.sendmessage(reply, data['user_id'])
            except Exception, e:
                reply = "Error"


    @botcmd
    def help(self, args):
        usage=[]
        for (name, command) in self.commands.iteritems():
           usage.append("%s%s" % (self.__commandprefix,name))
        return "Possible commands:\n"+",".join(usage)


# Needed to pass arguments to the Requesthandler
# https://mail.python.org/pipermail/python-list/2012-March/621720.html
class BotHTTPServer(HTTPServer):

    def __init__(self, *args, **kw):
        self.botobj= kw.get('botobj')
        HTTPServer.__init__(self, *args)

# RequestHandler. Sends all messages back to the main class
class GroupMeBotHTTPServer(BaseHTTPRequestHandler):
    #Handler for the GET requests
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write("Error")
        return


    def do_POST(self):
        global postVars
        self.send_response(200)
        self.end_headers()
        varLen = int(self.headers['Content-Length'])
        postVars = json.JSONDecoder().decode(self.rfile.read(varLen))
        self.server.botobj.parseData(postVars)

        






