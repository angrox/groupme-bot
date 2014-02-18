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
    
    def __init__(self, bot_token, bot_user_id, portnumber, ip='', commandprefix='.', apiurl='api.groupme.com', callback=None, id_path=None, debug=False):
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
        self.__bot_user_id = unicode(bot_user_id)
        self.__bot_token = unicode(bot_token)
        self.__portnumber = portnumber
        self.__ip = ip
        self.__commandprefix = unicode(commandprefix)
        self.__apiurl = unicode(apiurl)
        self.__debug = debug
        self.commands = {}
        self.remotebots = {}
        self.idpath = id_path
        self.callback = callback
        for name, value in inspect.getmembers(self):
            if inspect.ismethod(value) and getattr(value, '_groupmebot_command', False):
                name = getattr(value, '_groupmebot_command_name')
                self.commands[name] = value
    


    def debug(self,txt):
        if self.__debug == True:
            print "[debug] "+txt

    def getBotID(self):
        return self.__bot_user_id

    def getBotToken(self):
        return self.__bot_token

    def getBotApiURL(self):
        return self.__apiurl

    def start(self):
        try:
            server = BotHTTPServer((self.__ip, self.__portnumber), GroupMeBotHTTPServer, botobj=self)
            print 'Started groupme bot on port ' , self.__portnumber
            
            server.serve_forever()
        except KeyboardInterrupt:
            print '^C received, shutting down ...'
            server.socket.close()

    # Adds a remote bot. The URL is the id_path of the remote bot, the botfunc
    # must be defined within this class and will be called.
    def addRemoteBot(self, path, url, botfunc):
        if path not in self.remotebots:
            self.remotebots[path]={'func': botfunc, 'url': url}
        print self.remotebots

    def getRemoteBots(self):
        return self.remotebots

    def getRemoteBot(self, url):
        if url in self.remotebots:
            return self.remotebots[url]
        return None

    def getIdPath(self):
        return self.idpath

    def getCallback(self):
        return self.callback

    def sendtoRemoteBot(self, data, url):
        data.update({ 'botpath': self.idpath, 'callback': self.callback })
        params = urllib.urlencode( data )
        headers = {"Content-type": "application/x-www-form-urlencoded",  "Accept": "text/plain"} 
        conn = httplib.HTTPConnection(url)
        conn.request('POST', self.idpath, params, headers)
        response=conn.getresponse()
        return response
        

    def sendMessage(self, msg, user_id ):
        if user_id == self.getBotID():
            return
        params = urllib.urlencode( {'bot_id': self.getBotToken(), 'text': msg} )
        headers = {"Content-type": "application/x-www-form-urlencoded",  "Accept": "text/plain"} 
        conn = httplib.HTTPSConnection(self.getBotApiURL())
        conn.request('POST', '/v3/bots/post', params, headers)
        response=conn.getresponse()
        print response
        return response


    def parseData(self, data):
        splitline=unicode(data['text']).split(' ')
        cmd=splitline[0]
        args=splitline[1:]
        self.debug("parseData: text = %s" % data['text'])
        self.debug("parseData: cmd = %s" % cmd)
        if data['user_id'] != self.__bot_user_id:
            self.catchAll(args, data)
        if self.__commandprefix != '':
            if not cmd.startswith(self.__commandprefix):
                if data['user_id'] != self.__bot_user_id:
                    return self.catchNoCmd(args, data)
                else:
                    return None
            else:
                cmd = cmd.lstrip(self.__commandprefix)
        self.debug("parseData: Found correct parsed command, checking it: %s" % cmd)
        if self.commands.has_key(cmd):
            try:
                reply = self.commands[cmd](args)
                self.debug("parseData: Reply = %s" % reply)
                self.sendMessage(reply, data['user_id'])
            except Exception, e:
                reply = "Error"


    # Will be called on every event: 
    def catchAll(self, args, data):
        return None

    # Will be called on every event except commands
    def catchNoCmd(self, args, data):
        return None


    # Default help command:
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
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write("Error")
        return


    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        varLen = int(self.headers['Content-Length'])
        postVars = json.JSONDecoder().decode(self.rfile.read(varLen))
        path=vars(self)['path']
        remotebotcmd=self.server.botobj.getRemoteBot(path)
        if remotebotcmd is not None:
            rbc=getattr(self.server.botobj, remotebotcmd['func'])
            rbc(path, postVars)
        else:
            self.server.botobj.parseData(postVars)

        






