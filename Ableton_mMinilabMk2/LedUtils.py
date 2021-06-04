from __future__ import absolute_import, print_function, unicode_literals
import time
from itertools import cycle
import logging
logger = logging.getLogger(__name__)

from Ableton_mMinilabMk2.Constants import BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE

COLORS = [BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE]
PADS = [112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127]
DEFAULT_BLINK = 1



def blink_conditioned(self, condition=lambda: False, pad_number=120, colors=[RED, BLACK], timeout=3):
    c = cycle(colors)
    def callback():
        if condition():
            _send_color(self, pad_number, next(c))
            self.schedule_message(timeout, callback)
        else:
            _send_color(self, pad_number, BLACK)
    
    # give the condition some time (1 tick) to fulfil itself
    self.schedule_message(1, callback)


def _send_color(self, pad_number, color):
    if pad_number in PADS and color in COLORS:
        self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, pad_number, color, 247))


def _shift_led(self, mode=False):
    if mode == True:
        self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, 46, 127, 247))
    else:
        self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, 46, 0, 247))


def _color_leds(self, color=WHITE):
    p_id = 112
    for i in range(16):
        logger.info("led :: " + str(i + p_id))
        _send_color(self, i + p_id, color)
        # self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, i + p_id, color, 247))


def _off_leds(self):
    self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, 47, 0, 247))
    self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, 46, 0, 247))
    p_id = 112
    for i in range(16):
        self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, i + p_id, 0, 247))


def _leds_NormalMode(self, song_instance):
    if song_instance.is_playing:
        _send_color(self, 120, GREEN)
        _send_color(self, 121, WHITE)
    else:
        _send_color(self, 120, YELLOW)
        if song_instance.current_song_time > 0:
            _send_color(self, 121, CYAN)
        else:
            _send_color(self, 121, BLUE)
            _send_color(self, 120, WHITE)
    
    if song_instance.overdub:
        _send_color(self, 122, RED)
    else:
        _send_color(self, 122, MAGENTA)
    
    # undo
    _send_color(self, 123, CYAN)
    # * alternate detail view
    _send_color(self, 124, WHITE)
    _send_color(self, 125, BLACK)
    # self._blink(True, 125, timeout=5, colors=[0, 20])
    # new scene
    _send_color(self, 126, RED)
    
    scene_selected = song_instance.view.selected_scene
    if scene_selected.is_empty:
        _send_color(self, 127, BLACK)
    else:
        _send_color(self, 127, YELLOW)
        if scene_selected.is_triggered:
            _send_color(self, 127, GREEN)
        for clip in scene_selected.clip_slots:
            if clip.is_playing:
                _send_color(self, 127, GREEN)


def _leds_ClipMode(self, song_instance):
    # * overdub
    if self.song_instance.overdub:
        _send_color(self, 120, RED)
    else:
        _send_color(self, 120, MAGENTA)
    # * undo
    _send_color(self, 121, CYAN)
    # * nope
    _send_color(self, 122, BLACK)
    _send_color(self, 123, BLACK)
    # * alternate detail view
    _send_color(self, 124, WHITE)
    # * quantize
    _send_color(self, 125, BLUE)
    clip = song_instance.view.detail_clip
    if not clip:
        _send_color(self, 125, BLACK)
        _send_color(self, 126, BLACK)
        _send_color(self, 127, BLACK)
    
    else:
        if not clip.is_playing:
            # * scrub
            _send_color(self, 126, YELLOW)
            # * play clip
            _send_color(self, 127, YELLOW)
        else:
            # * scrub
            _send_color(self, 126, GREEN)
            # * play clip
            _send_color(self, 127, GREEN)
