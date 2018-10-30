# -*- coding: utf-8 -*-
import xbmc

from client import KinoPubClient
from data import get_adv_setting


class Player(xbmc.Player):

    def __init__(self, *args, **kwargs):
        self.list_item = kwargs.pop("list_item")
        self.is_playing = True
        self.marktime = 0
        super(Player, self).__init__()

    def set_marktime(self):
        if self.isPlaying():
            self.marktime = int(self.getTime())

    @property
    def should_make_resume_point(self):
        # https://kodi.wiki/view/HOW-TO:Modify_automatic_watch_and_resume_points#Settings_explained
        return (self.marktime > get_adv_setting("video", "ignoresecondsatstart") and
                not self.should_mark_as_watched)

    @property
    def should_mark_as_watched(self):
        return (100 * self.marktime / float(self.list_item.getduration()) >
                get_adv_setting("video", "playcountminimumpercent"))

    @property
    def should_reset_resume_point(self):
        return (self.marktime < get_adv_setting("video", "ignoresecondsatstart") and
                self.list_item.getProperty("resumetime") != "0")

    def _base_data(self):
        id = self.list_item.getProperty("id")
        video_number = self.list_item.getVideoInfoTag().getEpisode()
        season_number = self.list_item.getVideoInfoTag().getSeason()
        if video_number != -1 and season_number != -1:
            data = {"id": id, "season": season_number, "video": video_number}
        elif season_number != -1:
            data = {"id": id, "season": season_number}
        else:
            data = {"id": id}
        return data

    def onPlayBackStopped(self):
        self.is_playing = False
        data = self._base_data()
        if self.should_make_resume_point:
            data["time"] = self.marktime
            KinoPubClient("watching/marktime").get(data=data)
        elif self.should_mark_as_watched and self.list_item.getVideoInfoTag().getPlayCount() < 1:
            data["status"] = 1
            KinoPubClient("watching/toggle").get(data=data)
        elif self.should_reset_resume_point:
            data["time"] = 0
            KinoPubClient("watching/marktime").get(data=data)
        else:
            return
        xbmc.executebuiltin("Container.Refresh")

    def onPlayBackEnded(self):
        self.is_playing = False
        if self.list_item.getVideoInfoTag().getPlayCount() < 1:
            data = self._base_data()
            data["status"] = 1
            KinoPubClient("watching/toggle").get(data=data)
            xbmc.executebuiltin("Container.Refresh")

    def onPlaybackError(self):
        self.is_playing = False
