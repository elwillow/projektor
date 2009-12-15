#!/usr/bin/python
#
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
"""
this is the deamon module part of the Touei project.
please see http://elwillow.net/touei for more info.
"""

__author__ = "G-Anime"
__license__ = "Eiffel Version 2"
__version__ = "0.1"
__revision__ = ""
__contributors__= "Mathieu Charron, Martin Samson"

import time, signal, datetime, os
import mkvutils

# Instanciate the logging
import logging
module_logger = logging.getLogger("touei.daemon")

class ToueiDaemon():
    """
    This class provide a way to keep the video database in memory and
    a fast way of checking witch video to play.
    """
    def __init__(self, playlist, player, config, mkv):
        # Instanciate the logger
        self.logger = logging.getLogger("touei.daemon.ToueiDaemon")
        self.logger.info("Creating instance")

        signal.signal (signal.SIGTERM, self._signalTerm)
        signal.signal (signal.SIGHUP, self._signalTerm)
        signal.signal (signal.SIGCONT, self._signalCont)
        self._isRunning = True
        self._Playlist = playlist
        self._Player = player
        self._Config = config
        self._MkvUtils = mkv
        self._CurrentVideo = self._Config.get("video","recovery")

    def stop(self):
        self.logger.debug("stop() called")
        self._isRunning = False

    def playerRunning(self):
        """
        Will check for the player state file deleted by toueid.
        """
        return os.path.exists(self._Config.get("core","tmp-location")+"/player_running")

    def setPlayerRunning(self):
        """
        Create the file for toueid and the player state (if we crash)
        """
        if not self.playerRunning():
            open(self._Config.get("core","tmp-location")+"/player_running", "w").close()

    def getCurTime(self):
        self.logger.debug("getCurTime() called. Time is: " + datetime.datetime.now().strftime("%H%M"))
        return datetime.datetime.now().strftime("%H%M")

    def run(self):
        self.logger.debug("Entering run loop")
        curTime = self.getCurTime()
        # This will containt a sq3.row instance
        CurrentVideo = {}
        # For logging purposes
        loopCounter = 0
        while(self._isRunning):
            self.logger.info("Entering Loop %s" % (loopCounter,))
            video = self._Playlist.get()
            self.logger.debug("Current Video: " + self._CurrentVideo)
            #self.logger.debug("Playlist Video: " + video['file'])
            if not video:
                # Nothing for current time, Play standby video
                self.logger.debug("No video for current block")
                if self._CurrentVideo == self._Config.get("video","standby"):
                    # Standby video is playing
                    self.logger.info("Standby video is playing, sleeping")
                else:
                    # Play the standby video
                    self.logger.info("Playing standby video")
                    self._CurrentVideo = self._Config.get("video","standby")
                    # Open the file is "soft" mode, aka append.
                    self._Player.openFile(self._CurrentVideo, True)

            elif self._CurrentVideo != video['file']:
                # We have a new video to play (apparently)
                self.logger.debug("Restoring: Current video is different")
                currentVideo = video
                self._CurrentVideo = video['file']
                # Create the intro file
                introVideo = self._MkvUtils.generate_intro(os.path.split(video['file'])[1])
                self.logger.debug("Restoring: Intro video is " + introVideo)

                # Check if the video is alive
                if not self.playerRunning():
                    # Not running, we have to restore the video
                    self.logger.warn("Restoring: Player was dead, restoring")
                    # Send the intro to player
                    self._Player.openFile(introVideo)
                    # Send the video to player
                    self._Player.openFile(self._CurrentVideo, True)
                    # Send the outro to player
                    #self._Player.openFile(self._Config.get("video","outro"))
                    # Recreate the file
                    self.setPlayerRunning()
                else:
                    # Player is still alive, do nothing
                    self.logger.warn("Restoring: Player is still alive, sleeping")

            else:
                # Nothing to do, video is playing
                # It could also mean we just went through a _signalCont()
                self.logger.debug("Still playing, sleeping")
            self.logger.debug("Loop ending")
            loopCounter = loopCounter + 1
            time.sleep(10)

    def _signalTerm(self,signal,frame):
        """
        Will exit the loop and let the application close.
        """
        self.logger.warn("SIGNTERM signal received, quitting")
        self._isRunning = False
        if self.playerRunning():
            os.remove(self._Config.get("core","tmp-location")+"/player_running")

    def _signalCont(self, signal, frame):
        """
        Signal from the TOUEID process telling the loop that mplayer have
        been restart. replaying the current video.
        """
        self.logger.debug("Received signal %s" % (signal, ))
        if signal == 18:
            # we restore the current video
            self.logger.warn("SIGCONT signal received, restoring video")
            # @TODO Add the seek feature when mplayer crash in the middle of a video

            # Close the socket et reopen it
            self._Player.closeSocket()
            self._Player.openSocket()

            # Force play it
            self._Player.openFile(self._CurrentVideo)
            # @TODO Add the seek to restore the video where is was

        # REMOVED, simply kill touei_run and toueid will restart it and generate
        # The new stuff
        #elif signal == 25:
            ## We rebuild the playlist database
            #self.logger.warn("Signal 25 received, rebuilding video DB")
            #self._Playlist.load(self._Config.get("video", "location"))


if __name__ == "__main__":
    print "##### DEBUG ######"
    d = ToueiDaemon()
    d.run()
