#!/usr/bin/python

# A simple example bot

import sys
import os
import xmlrpclib
import ConfigParser
import argparse
import json
import urllib2
import re
import codecs
from groupmebot import GroupMeBot, botcmd

class MyBot(GroupMeBot): 

    def __init__(self, *args, **kwargs):
        ''' Initialize variables. '''
        super(MyBot, self).__init__(*args, **kwargs)

    # Here we are decorating the command function of the bot to give him 
    # commands to react upon. Must be called with the commandprefix, 
    # for example ".": .syn
    @botcmd
    def syn(self, args): 
        print "ack"
        return "ack"

    # This is a function which can be called by a remotebot (in this case
    # called examplebot2. It will be called, if the callbackurl from this bot 
    # is called with the url of examplebot2. 
    # So examplebot2 called: http://www.example.com:9834/examplebot2/
    # Examplebot1 (this one) has defined that the function "examplebot2func" will be 
    # called if a POST request comes to "/examplebot2/"
    # The arguments of the POST request are stored in the dict "parseArgs" of this
    # function
    def examplebot2func(self, path, parseArgs):
        print "this function was called by examplebot2"
        print parseArgs
        print "Path called: %s" % path
        print "This are the informations if we need to send something back:"
        print self.getRemoteBot(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--conffile' , help='specify the config file')
    args = parser.parse_args()
    conffile=vars(args)['conffile']

    if not conffile:
        parser.print_help()
        sys.exit(1)
    if not os.path.isfile(conffile):
        print "File %s does not exist or is not readable" % conffile
        sys.exit(1)

    global config
    config = ConfigParser.RawConfigParser()
    config.readfp(codecs.open(conffile, "r", "utf8"))
    try: 
        port = config.getint('connection', 'port')
        ip = config.get('connection', 'ip')
        apiurl = config.get('connection', 'apiurl')
        callback = config.get('connection', 'callback')
        bot_user_id = config.getint('groupmebot', 'bot_user_id')
        bot_token = config.get('groupmebot', 'bot_token')
        id_path = config.get('groupmebot', 'id_path')
    except ConfigParser.NoSectionError as err:
        print "Error: %s " % err
        sys.exit(1)

    mybot = MyBot(bot_user_id=bot_user_id, bot_token=bot_token, portnumber=port, ip=ip, apiurl=apiurl, callback=callback, id_path=id_path, debug=False)

    # Add a remotebot: If the POST request received has the path /examplebot2/ the function
    # examplebot2func will be called. 
    mybot.addRemoteBot("/examplebot2/", "http://www.example2.com:6666", "examplebot2func")

    mybot.start()
