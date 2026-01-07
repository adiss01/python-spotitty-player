import vlc


class Player:
    def __init__(self):
        self.vlc = vlc.Instance()
        self.player = self.vlc.media_player_new()

        self.volume = 80
        self.player.audio_set_volume(self.volume)

        # Callbacks
        self.on_end = None
        self.on_play = None
        self.on_pause = None

        self._bind_events()

    # ---------- VLC EVENTS ----------
    def _bind_events(self):
        em = self.player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._handle_end)
        em.event_attach(vlc.EventType.MediaPlayerPlaying, self._handle_play)
        em.event_attach(vlc.EventType.MediaPlayerPaused, self._handle_pause)

    def _handle_end(self, event):
        if callable(self.on_end):
            self.on_end()

    def _handle_play(self, event):
        if callable(self.on_play):
            self.on_play()

    def _handle_pause(self, event):
        if callable(self.on_pause):
            self.on_pause()

    # ---------- CALLBACK SETTERS ----------
    def set_on_end(self, cb):
        self.on_end = cb

    def set_on_play(self, cb):
        self.on_play = cb

    def set_on_pause(self, cb):
        self.on_pause = cb

    # ---------- PLAYBACK ----------
    def play(self, track):

        if not isinstance(track, dict):
            raise ValueError("player.play() track dict bekliyor")

        url = track.get("audio")
        if not url:
            raise ValueError("Track audio URL bulunamadı")

        # VLC media
        media = self.vlc.media_new(url)
        self.player.set_media(media)
        self.player.play()

        # =====================
        # PLAYER BAR BİLGİLERİ
        # =====================
        self.current_track = track

        if hasattr(self, "on_track_change"):
            self.on_track_change(track)

    
    def pause(self):
        self.player.pause()

    def resume(self):
        self.player.play()

    def toggle(self):
        if self.player.is_playing():
            self.pause()
        else:
            self.resume()

    def stop(self):
        self.player.stop()

    # ---------- VOLUME ----------
    def set_volume(self, value):
        try:
            value = int(float(value))
            value = max(0, min(100, value))
            self.volume = value
            self.player.audio_set_volume(value)
        except:
            pass

    def volume_up(self):
        self.set_volume(self.volume + 5)

    def volume_down(self):
        self.set_volume(self.volume - 5)

    # ---------- POSITION ----------
    def get_position(self):
        try:
            return self.player.get_position()
        except:
            return 0

    def set_position(self, pos):
        try:
            self.player.set_position(float(pos))
        except:
            pass
    def get_progress(self):
        current = self.player.get_time() / 1000
        total = self.player.get_length() / 1000
        return current, total
    
    def seek(self, ratio):
        self.player.set_position(float(ratio))
