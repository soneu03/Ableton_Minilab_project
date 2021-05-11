# Embedded file name: /Users/versonator/Jenkins/live/output/Live/mac_64_static/Release/python-bundle/MIDI Remote Scripts/MiniLab_mkII/SessionComponent.py
from __future__ import absolute_import, print_function, unicode_literals

from itertools import product

from ableton.v2.base import liveobj_valid

from _Framework.ClipSlotComponent import ClipSlotComponent as ClipSlotComponentBase
from _Framework.Control import EncoderControl
from _Framework.SceneComponent import SceneComponent as SceneComponentBase
from _Framework.SessionComponent import SessionComponent as SessionComponentBase

EMPTY_VALUE = 0  # - apagado
SELECTED_VALUE = 127  # - blanco
BLUE = 16
TRACK_ARMED_VALUE = 17  # - magenta
TRACK_ARMED_MUTED_VALUE = 16  # - azul
TRACK_MUTED_VALUE = 20  # - cyan
TRIGGERED_TO_RECORD_VALUE = 17  # - magenta
RECORDING_VALUE = 1  # - red
TRACK_MUTED_RECORDING_VALUE = 16  # - azul
TRIGGERED_TO_PLAY_VALUE = 4  # - green
STARTED_VALUE = 4  # - green
TRACK_MUTED_STARTED_VALUE = 16  # - azul
STOPPED_VALUE = 5  # - yellow
TRACK_MUTED_STOPPED_VALUE = 16  # - azul


class ClipSlotComponent(ClipSlotComponentBase):
    
    def __init__(self, *a, **k):
        super(ClipSlotComponent, self).__init__(*a, **k)
        self._led = None
        self.transport = None
        self._mute_button_value = None
    
    def set_led(self, led):
        self._led = led
    
    def update(self):
        super(ClipSlotComponent, self).update()
        self._update_led()
    
    def _update_led(self):
        if self.is_enabled() and self._led != None:
            value_to_send = EMPTY_VALUE
            if liveobj_valid(self._clip_slot):
                track = self._clip_slot.canonical_parent
                slot_or_clip = self._clip_slot.clip if self.has_clip() else self._clip_slot
                value_to_send = self._led_feedback_value(track, slot_or_clip)
            self._led.send_value((value_to_send,))
    
    def _led_feedback_value(self, track, slot_or_clip):
        if self.has_clip():
            if slot_or_clip.is_triggered:
                if slot_or_clip.will_record_on_start:
                    if track.mute is True:
                        return TRACK_ARMED_MUTED_VALUE
                    return TRIGGERED_TO_RECORD_VALUE
                return TRIGGERED_TO_PLAY_VALUE
            elif slot_or_clip.is_playing:
                if slot_or_clip.is_recording:
                    if track.mute is True:
                        return TRACK_MUTED_RECORDING_VALUE
                    return RECORDING_VALUE
                if track.mute is True:
                    return TRACK_MUTED_STARTED_VALUE
                return STARTED_VALUE
            else:
                return STOPPED_VALUE
        else:
            if self._track_is_armed(track):
                if track.mute is True:
                    return TRACK_ARMED_MUTED_VALUE
                return TRACK_ARMED_VALUE
            if track.mute is True:
                return TRACK_MUTED_VALUE
            return SELECTED_VALUE


class SceneComponent(SceneComponentBase):
    clip_slot_component_type = ClipSlotComponent


class SessionComponent(SessionComponentBase):
    scene_select_encoder = EncoderControl()
    scene_component_type = SceneComponent
    _session_component_ends_initialisation = False
    
    def __init__(self, *a, **k):
        super(SessionComponent, self).__init__(*a, **k)
        self.set_offsets(0, 0)
        self.on_selected_scene_changed()
        self.on_selected_track_changed()
    
    def set_scene_select_control(self, control):
        self.scene_select_encoder.set_control_element(control)
    
    @scene_select_encoder.value
    def scene_select_encoder(self, value, encoder):
        selected_scene = self.song().view.selected_scene
        all_scenes = self.song().scenes
        current_index = list(all_scenes).index(selected_scene)
        if value > 0 and selected_scene != all_scenes[-1]:
            self.song().view.selected_scene = all_scenes[current_index + 1]
        elif value < 0 and selected_scene != all_scenes[0]:
            self.song().view.selected_scene = all_scenes[current_index - 1]
    
    def on_selected_scene_changed(self):
        super(SessionComponent, self).on_selected_scene_changed()
        all_scenes = list(self.song().scenes)
        selected_scene = self.song().view.selected_scene
        new_scene_offset = all_scenes.index(selected_scene)
        self.set_offsets(self.track_offset(), new_scene_offset)
    
    def on_selected_track_changed(self):
        super(SessionComponent, self).on_selected_track_changed()
        tracks = list(self.song().tracks)
        selected_track = self.song().view.selected_track
        if selected_track in tracks:
            track_index = tracks.index(selected_track)
            new_track_offset = track_index - track_index % self.width()
            self.set_offsets(new_track_offset, self.scene_offset())
    
    def set_clip_slot_leds(self, leds):
        # assert not leds or leds.width() == self._num_tracks and leds.height() == 1
        assert not leds or leds.width() == self._num_tracks
        if leds:
            for led, (x, y) in leds.iterbuttons():
                scene = self.scene(y)
                slot = scene.clip_slot(x)
                slot.set_led(led)
        else:
            for x, y in product(xrange(self._num_tracks), xrange(self._num_scenes)):
                scene = self.scene(y)
                slot = scene.clip_slot(x)
                slot.set_led(None)

