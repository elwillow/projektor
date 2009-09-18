# Eiffel Forum License, version 2
#
# 1. Permission is hereby granted to use, copy, modify and/or
#    distribute this package, provided that:
#       * copyright notices are retained unchanged,
#       * any distribution of this package, whether modified or not,
#         includes this license text.
# 2. Permission is hereby also granted to distribute binary programs
#    which depend on this package. If the binary program depends on a
#    modified version of this package, you are encouraged to publicly
#    release the modified version of this package.
#
# THIS PACKAGE IS PROVIDED "AS IS" AND WITHOUT WARRANTY. ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE TO ANY PARTY FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS PACKAGE.

__author__ = "Martin Samson"
__license__ = "Eiffel Version 2"
__version__ = "0.1"
__revision__ = ""

import sys,os
class SocketLocationException(): pass
class CommandEmptyException(): pass
class CommandMalformedException(): pass

class PlayerInterface():
    """Abstraction class to Mplayer"""

    def __init__(self, socketLocation):
        '''@param string socketLocation The location of the communication socket'''
        
        if not socketLocation:
            raise SocketLocationException()
            
        if not os.path.exists(socketLocation):
            raise SocketLocationException()
            
        self.socketLocation = socketLocation
        self.socket = None
        
        #Will lock until mplayer is listening.
        try:
           self.socket = os.open(socketLocation, os.O_WRONLY)
        except Exception,e:
            raise e
        
        self._commands = {}
        self._commands['open_file'] = "loadfile %s\n"
        self._commands['open_playlist'] = "loadlist %s\n"
        self._commands['fullscreen'] = "vo_fullscreen %d\n"
        self._commands['seek'] = "seek %c%d\n"
        
    def __del__(self):
        try:
            os.close(self.socket)
        except Exception,e:
            print e
            return False
        return True

    def _communicate(self,command):
        '''Communicate with mplayer thru the socket. Does some basic command verifications
        @param string command A command to mplayer.
        @return boolean True/False
        '''
        if not command:
            raise CommandEmptyException()

        if not command.endswith("\n"):
            raise CommandMalformedException()
        try:
            os.write(self.socket, command)
        except Exception,e:
            raise e
        
        return True
    
    def _execute(self,command):
        '''Execute a given command with exception catching
        @param string command The command to execute
        @return boolean True/False'''
        try:
            result = self._communicate(command)
        except Exception,e:
            print e
            return False
        return result
    
    def fullscreen(self, enabled):
        '''Turn on/off fullscreeen
        @param boolean enabled True/False
        @return boolean True/False
        '''
        command = None
        if enabled:
            command = self._commands['fullscreen'] % True
        else:
            command = self._commands['fullscreen'] % False
        
        return self._execute(command)
            
        
    def openFile(self, fileLocation):
        '''Open a file
        @param string fileLocation The location of the file
        @return boolean
        '''
        command = None
        if fileLocation.endswith('.pls'):
            #We got a playlist
            command = self._commands['open_playlist'] % fileLocation
        else:
            command = self._commands['open_file'] % fileLocation
        if self._execute(command):
            print self.fullscreen(True)
            return True
        else:
            return False

    def seek(self, forward, seekTime):
        """
        @param boolean forward Going forward(True) or backward(False)
        @param integer seekTime Seek by how many minutes
        @return boolean True/False
        """
        if forward:
            direction = "+"
        else:
            direction = "-"
            
        command = self._commands['seek'] % (direction, seekTime * 60)
        
        return self._execute(command)

if __name__ == "__main__":
    from playlist import PlayList
    pl = PlayList()
    pl.load('/home/masom/dev/videos')
    file = pl.getNext()
    print file['file']
    
    p = PlayerInterface("/tmp/mplayer")
    print p.openFile(file['file'])
    