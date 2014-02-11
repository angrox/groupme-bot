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
        super(JarvisBot, self).__init__(*args, **kwargs)

    # Here we are decorating the command function of the bot to give him 
    # commands to react upon. Must be called with the commandprefix, 
    # for example ".": .syn
    @botcmd
    def syn(self, args): 
        print "ack"
        return "ack"


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
        bot_user_id = config.getint('groupmebot', 'bot_user_id')
        bot_token = config.get('groupmebot', 'bot_token')
    except ConfigParser.NoSectionError as err:
        print "Error: %s " % err
        sys.exit(1)

    mybot = MyBot(bot_user_id=bot_user_id, bot_token=bot_token, portnumber=port, ip=ip, apiurl=apiurl, debug=False)
    mybot.start()
