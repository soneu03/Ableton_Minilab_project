# Embedded file name: /Users/versonator/Jenkins/live/output/Live/mac_64_static/Release/python-bundle/MIDI Remote Scripts/MiniLab_mkII/MiniLabMk2.py
from __future__ import absolute_import, print_function, unicode_literals

from functools import partial
from itertools import izip
import logging
logger = logging.getLogger(__name__)
import Live

from _Arturia.ArturiaControlSurface import ArturiaControlSurface
from _Arturia.ArturiaControlSurface import COLOR_PROPERTY, LIVE_MODE_MSG_HEAD, LOAD_MEMORY_COMMAND, \
    MEMORY_SLOT_PROPERTY, OFF_VALUE, SETUP_MSG_PREFIX, SETUP_MSG_SUFFIX, STORE_IN_MEMORY_COMMAND, \
    WORKING_MEMORY_ID, WRITE_COMMAND, split_list
from _Framework import Task
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.DeviceComponent import DeviceComponent
from _Framework.EncoderElement import EncoderElement
from _Framework.InputControlElement import MIDI_CC_TYPE, MIDI_NOTE_TYPE
from _Framework.Layer import Layer
from _Framework.SubjectSlot import subject_slot
from _Framework.SysexValueControl import SysexValueControl
from _Framework.TransportComponent import TransportComponent
from .HardwareSettingsComponent import HardwareSettingsComponent
from .MixerComponent import MixerComponent
from .SessionComponent import SessionComponent
from .Util import _send_color, BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _off_leds, _shift_led, _leds_NormalMode, _leds_ClipMode

'''En modo live, los 8 primeros pads actuan en modo sesion
y los siguientes actuan como Play, Stop, Overdub,.. y los
finales como Undo, Nueva escena a partir de lo reproducido, Play escena.
El knob 1 si se pulsa, cambia de vista entre Session y Arranger
si se pulsa junto con SHIFT, cambia la vista de los Device de ese Track
devices con los que nos moveremos con el knob 8 (si pulsamos SHIFT)
El knob 9 pulsado arma el Track seleccionado, (con SHIFT no implementado)

Recomendable poner el modo de lanzamiento de clips por defecto en Toggle,
en Preferencias > Lanzamiento > Modo Lanzar por defecto, asi se consigue que
los clips en modo sesion se puedan parar'''

# ?   + general view                                                plugin preset
# ?   h.scroll        |----------  device controls ---------|      loop position  loop_start    loop_end
#     ((+))        (( ))        (( ))        (( ))        (( ))        (( ))        (( ))        (( ))
#     [ 1 ]        [ 2 ]        [ 3 ]        [ 4 ]        [ 5 ]        [ 6 ]        [ 7 ]        [ 8 ]
#       0            1            2            3            4            5            6            7
# !   h.scroll       |----------  device controls ---------|         vol send a     send a         pan
# *  + detail view
#                                                                                     |---track----|
# *  + arm track
# !   v.scroll      |----------  device controls ----------|         vol send b     send b       volumen
#     ((+))        (( ))        (( ))        (( ))        (( ))        (( ))        (( ))        (( ))
#     [ 9 ]       [ 10 ]       [ 11 ]       [ 12 ]       [ 13 ]       [ 14 ]       [ 15 ]       [ 16 ]
#       8           9            10           11           12           13           14           15
# ?   v.scroll      |----------  device controls ---------|         view grid    start_marker   end_marker
# ? + general quantization
# ? + [Clip Mode]

# ? Clip Mode
# ?      |--------------------------------------scene clip controls---------------------------------------|
# !      |--------------------------------------scene clip controls---------------------------------------|
#    [  1  ]       [  2  ]       [  3  ]       [  4  ]       [  5  ]       [  6  ]       [  7  ]       [  8  ]
#       0             1             2             3             4             5             6             7

# !  global play   g. stop      g. overdub       undo                                   new scene     play scene
#    [  9  ]       [  10 ]       [  11 ]       [  12 ]       [  13 ]       [  14 ]       [  15 ]       [  16 ]
#       8             9             10            11            12            13            14            15
# ?    loop        quantize   arm & overdub      undo   consolidate loop                  scrub     play / stop scrub

# ?  arm & overdub    undo                      g. quant     scrub      play/stop scrub   cons loop    set loop

ANALOG_LAB_MEMORY_SLOT_ID = 1
LIVE_MEMORY_SLOT_ID = 8
HARDWARE_ENCODER_IDS = (48, 1, 2, 9, 11, 12, 13, 14, 51, 3, 4, 10, 5, 6, 7, 8)
HARDWARE_BUTTON_IDS = xrange(112, 128) #
PAD_IDENTIFIER_OFFSET = 36
IS_MOMENTARY = True
ENCODER_PUSH1 = 113
ENCODER_PUSH1_ALT = 112
ENCODER_PUSH2 = 115
ENCODER_PUSH2_ALT = 116
SHIFT_BUTTON = 46
SWITCHPAD_BUTTON = 47
# SHIFT_BUTTON_MSG = (240, 0, 32, 107, 127, 66, 2, 0, 0, 46)
SHIFT_BUTTON_MSG = SETUP_MSG_PREFIX + (
    WRITE_COMMAND, WORKING_MEMORY_ID, WORKING_MEMORY_ID, SHIFT_BUTTON)  # 2, 0, 0, 46
SWITCHPAD_BUTTON_MSG = SETUP_MSG_PREFIX + (
    WRITE_COMMAND, WORKING_MEMORY_ID, WORKING_MEMORY_ID, SWITCHPAD_BUTTON)  # 2, 0, 0, 47
LIVE_MODE = False
# * Al cambiar de Device, se deben collapsar los no seleccionados?
IN_DEVICE_VIEW_COLLAPSED = True



class mMiniLabMk2(ArturiaControlSurface):
    session_component_type = SessionComponent
    
    encoder_msg_channel = 0
    # button_encoder_msg_channel = 9 en el preset pero se cambia, en este caso a 2
    button_encoder_msg_channel = 2
    alt_button_encoder_msg_channel = 2
    encoder_msg_ids = (7, 74, 71, 76, 77, 93, 73, 75, 114, 18, 19, 16, 17, 91, 79, 72)  # Analog Lab defaults
    pad_channel = 10
    
    
    def __init__(self, *a, **k):
        
        super(mMiniLabMk2, self).__init__(*a, **k)
        
        with self.component_guard():
            self.live_mode = False
            self.shift_active = False
            self.altpad_pushed = False
            self.modo_clip_activo = False
            self.show_message("mMiniLabMk2 cargado")
            logger.info("soneu remote script loaded")
            self._create_controls()
            self._create_hardware_settings()
            self._create_device()
            self._create_session()
            self._create_mixer()
            self._create_transport()
            _off_leds(self)
            
    def _create_controls(self):
        self._horizontal_scroll_encoder = EncoderElement(MIDI_CC_TYPE, self.encoder_msg_channel,
                                                         self.encoder_msg_ids[0],
                                                         Live.MidiMap.MapMode.relative_smooth_two_compliment,
                                                         name=u'Horizontal_Scroll_Encoder')
        self._vertical_scroll_encoder = EncoderElement(MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[8],
                                                       Live.MidiMap.MapMode.relative_smooth_two_compliment,
                                                       name=u'Vertical_Scroll_Encoder')
        
        self._device_controls = ButtonMatrixElement(rows=[[EncoderElement(MIDI_CC_TYPE, self.encoder_msg_channel,
                                                                          identifier,
                                                                          Live.MidiMap.MapMode.relative_smooth_two_compliment,
                                                                          name=u'Encoder_%d_%d' % (
                                                                              column_index, row_index)) for
                                                           column_index, identifier in enumerate(row)] for
                                                          row_index, row in enumerate(
                (self.encoder_msg_ids[1:5], self.encoder_msg_ids[9:13]))])
        
        # volumenes de los send tracks
        self._return_a_encoder = EncoderElement(MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[5],
                                                Live.MidiMap.MapMode.relative_smooth_two_compliment,
                                                name=u'Return_A_Encoder')
        self._return_b_encoder = EncoderElement(MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[13],
                                                Live.MidiMap.MapMode.relative_smooth_two_compliment,
                                                name=u'Return_B_Encoder')
        self._return_encoders = ButtonMatrixElement(rows=[[self._return_a_encoder, self._return_b_encoder]])
        
        # envios de los send
        self._send_a_encoder = EncoderElement(MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[6],
                                              Live.MidiMap.MapMode.relative_smooth_two_compliment,
                                              name=u'Send_A_Encoder')
        self._send_b_encoder = EncoderElement(MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[14],
                                              Live.MidiMap.MapMode.relative_smooth_two_compliment,
                                              name=u'Send_B_Encoder')
        self._send_encoders = ButtonMatrixElement(rows=[[self._send_a_encoder, self._send_b_encoder]])
        
        self._pan_encoder = EncoderElement(MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[7],
                                           Live.MidiMap.MapMode.relative_smooth_two_compliment, name=u'Pan_Encoder')
        
        self._volume_encoder = EncoderElement(MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[15],
                                              Live.MidiMap.MapMode.relative_smooth_two_compliment,
                                              name=u'Volume_Encoder')
        
        self._pads = ButtonMatrixElement(rows=[
            [ButtonElement(True, MIDI_NOTE_TYPE, self.pad_channel, col + 36 + 8 * row, name=u'Pad_%d_%d' % (col, row))
             for col in xrange(8)] for row in xrange(1)])
        self._pads2 = ButtonMatrixElement(rows=[
            [ButtonElement(True, MIDI_NOTE_TYPE, self.pad_channel, col + 36 + 8 * row, name=u'Pad_%d_%d' % (col, row))
             for col in xrange(8)] for row in xrange(2)])
        
        self._pad_leds = ButtonMatrixElement(rows=[[SysexValueControl(message_prefix=SETUP_MSG_PREFIX + (
            WRITE_COMMAND, WORKING_MEMORY_ID, COLOR_PROPERTY, column + 112 + row * 8), default_value=(0,),
                                                                      name=u'Pad_LED_%d' % (column,)) for column in
                                                    xrange(8)] for row in xrange(1)], name=u'Pad_LED_Matrix')
        
        self._arm_button = ButtonElement(True, MIDI_CC_TYPE, self.button_encoder_msg_channel, 115, name='Arm_Button')
        self._change_focus_button = ButtonElement(True, MIDI_CC_TYPE, self.button_encoder_msg_channel, 113,
                                                  name='Change_Focus_Button')

# Inconsistente en el canal, Bug en MCC?
#         self._alt_encoder0 = EncoderElement(MIDI_CC_TYPE, self.alt_button_encoder_msg_channel, 112, Live.MidiMap.MapMode.relative_smooth_two_compliment, name=u'Alternative_Encoder0')
#         self._alt_encoder8 = EncoderElement(MIDI_CC_TYPE, self.alt_button_encoder_msg_channel, 116, Live.MidiMap.MapMode.relative_smooth_two_compliment, name=u'Alternative_Encoder9')
        
        '''
         In:  B0  07  00  |  Ch 1 CC 7 - Channel Volume
         In:  B2  07  02  |  Ch 3 CC 7 - Channel Volume
         In:  B0  72  00  |  Ch 1 CC 114 - Undefined
         In:  B2  74  0C  |  Ch 3 CC 116 - Undefined
        '''
        
        self._switchpad_button = SysexValueControl(SWITCHPAD_BUTTON_MSG, name='Pad_Selection_button')
        self._shift_button = SysexValueControl(SHIFT_BUTTON_MSG, name=u'Shift_button_pressed')
        
        self._memory_slot_selection = SysexValueControl(message_prefix=SETUP_MSG_PREFIX + (MEMORY_SLOT_PROPERTY,),
                                                        name=u'Memory_Slot_Selection')
        self._hardware_live_mode_switch = SysexValueControl(message_prefix=LIVE_MODE_MSG_HEAD,
                                                            default_value=(OFF_VALUE,),
                                                            name=u'Hardware_Live_Mode_Switch')
        
    def _setup_control_listeners(self):
        if not self._pads2[8].value_has_listener(self._pads2_n8):
            self._pads2[8].add_value_listener(self._pads2_n8, identify_sender=False)
        if not self._pads2[9].value_has_listener(self._pads2_n9):
            self._pads2[9].add_value_listener(self._pads2_n9, identify_sender=False)
        if not self._pads2[10].value_has_listener(self._pads2_n10):
            self._pads2[10].add_value_listener(self._pads2_n10, identify_sender=False)
        if not self._pads2[11].value_has_listener(self._pads2_n11):
            self._pads2[11].add_value_listener(self._pads2_n11, identify_sender=False)
        if not self._pads2[12].value_has_listener(self._pads2_n12):
            self._pads2[12].add_value_listener(self._pads2_n12, identify_sender=False)
        if not self._pads2[13].value_has_listener(self._pads2_n13):
            self._pads2[13].add_value_listener(self._pads2_n13, identify_sender=False)
        if not self._pads2[14].value_has_listener(self._pads2_n14):
            self._pads2[14].add_value_listener(self._pads2_n14, identify_sender=False)
        if not self._pads2[15].value_has_listener(self._pads2_n15):
            self._pads2[15].add_value_listener(self._pads2_n15, identify_sender=False)
            
            # encoders listener
        if not self._return_a_encoder.value_has_listener(self._encoder_n5):
            self._return_a_encoder.add_value_listener(self._encoder_n5, identify_sender=False)
        if not self._return_b_encoder.value_has_listener(self._encoder_n13):
            self._return_b_encoder.add_value_listener(self._encoder_n13, identify_sender=False)
        if not self._send_a_encoder.value_has_listener(self._encoder_n6):
            self._send_a_encoder.add_value_listener(self._encoder_n6, identify_sender=False)
        if not self._send_b_encoder.value_has_listener(self._encoder_n14):
            self._send_b_encoder.add_value_listener(self._encoder_n14, identify_sender=False)
        if not self._pan_encoder.value_has_listener(self._encoder_n7):
            self._pan_encoder.add_value_listener(self._encoder_n7, identify_sender=False)
        if not self._volume_encoder.value_has_listener(self._encoder_n15):
            self._volume_encoder.add_value_listener(self._encoder_n15, identify_sender=False)
            
        # encoder number 0
        if not self._horizontal_scroll_encoder.value_has_listener(self._encoder_n0):
            self._horizontal_scroll_encoder.add_value_listener(self._encoder_n0, identify_sender=False)
            # push button
        if not self._change_focus_button.value_has_listener(self._encoder_n0_button):
            self._change_focus_button.add_value_listener(self._encoder_n0_button, identify_sender=False)
        
        # if not self._alt_encoder0.value_has_listener(self._alt_encoder_n0):
        #     self._alt_encoder0.add_value_listener(self._alt_encoder_n0, identify_sender=False)
        
            
        # encoder number 8
        if not self._vertical_scroll_encoder.value_has_listener(self._encoder_n8):
            self._vertical_scroll_encoder.add_value_listener(self._encoder_n8, identify_sender=False)
            # push button
        if not self._arm_button.value_has_listener(self._encoder_n8_button):
            self._arm_button.add_value_listener(self._encoder_n8_button, identify_sender=False)

        # if not self._alt_encoder8.value_has_listener(self._alt_encoder_n8):
        #     self._alt_encoder8.add_value_listener(self._alt_encoder_n8, identify_sender=False)
            
        if not self._switchpad_button.value_has_listener(self._switchpad_value_on_press):
            self._switchpad_button.add_value_listener(self._switchpad_value_on_press, identify_sender=False)
            
        if not self._shift_button.value_has_listener(self._shift_value_on_press):
            self._shift_button.add_value_listener(self._shift_value_on_press, identify_sender=False)
            
    def _create_hardware_settings(self):
        self._hardware_settings = HardwareSettingsComponent(name=u'Hardware_Settings', is_enabled=False, layer=Layer(
            memory_slot_selection=self._memory_slot_selection,
            hardware_live_mode_switch=self._hardware_live_mode_switch))
        self._on_live_mode_changed.subject = self._hardware_settings
        self._hardware_settings.set_enabled(True)
        
    @subject_slot(u'live_mode')
    def _on_live_mode_changed(self, is_live_mode_on):
        _off_leds(self)
        self._transport.set_enabled(is_live_mode_on)
        self._session.set_enabled(is_live_mode_on)
        self._mixer.set_enabled(is_live_mode_on)
        self._device.set_enabled(is_live_mode_on)
        if is_live_mode_on:
            self.show_message("Modo Live On")
            logger.info("Modo Live On" )
            self.live_mode = True
            self._setup_control_listeners()
            self._update_leds()
        else:
            self.show_message("Modo Live Off")
            logger.info("Modo Live Off")
            self.live_mode = False
            _off_leds(self)
            self.disconnect()
            
    def _create_device(self):
        self._device = DeviceComponent(name=u'Device', is_enabled=False,
                                       layer=Layer(parameter_controls=self._device_controls),#on_off_button=self._arm_button),
                                       device_selection_follows_track_selection=True)
        
        self.set_device_component(self._device)
        self._device.set_on_off_button(None)
        
    def _create_transport(self):
        self._transport = TransportComponent(name=u'Transport', is_enabled=False,
                                             layer=Layer(play_button=self._pads2[8],
                                                         stop_button=self._pads2[9],
                                                         overdub_button=self._pads2[10]))
        self._live = Live.Application.get_application()
        self.app_instance = self._live.view
        self.song_instance = self._transport.song()
    
    def _create_session(self):
        self._session = self.session_component_type(num_tracks=self._pads.width(), num_scenes=1,  # self._pads.height(),
                                                    name=u'Session', is_enabled=False,
                                                    layer=Layer(clip_launch_buttons=self._pads,
                                                                scene_select_control=self._vertical_scroll_encoder))
        self.set_highlighting_session_component(self._session)
        self._session.set_clip_slot_leds(self._pad_leds)
    
    def _create_mixer(self):
        self._mixer = MixerComponent(name=u'Mixer', is_enabled=False, num_returns=2,
                                     layer=Layer(track_select_encoder=self._horizontal_scroll_encoder,
                                                 selected_track_volume_control=self._volume_encoder,
                                                 selected_track_pan_control=self._pan_encoder,
                                                 selected_track_send_controls=self._send_encoders,
                                                 return_volume_controls=self._return_encoders,
                                                 selected_track_arm_control=self._arm_button))
    
    def _collect_setup_messages(self):
        for cc_id, encoder_id in izip(self.encoder_msg_ids, HARDWARE_ENCODER_IDS):
            # logger.info("encoder - cc_id :: " + str(cc_id) + " id :: " + str(encoder_id) + " channel :: " + str(self.encoder_msg_channel))
            self._setup_hardware_encoder(encoder_id, cc_id, channel=self.encoder_msg_channel)
            
        for index, pad_id in enumerate(HARDWARE_BUTTON_IDS):
            # logger.info("index ::::::::::::::: " + str(index))
            # logger.info("pad_id ::::::::::::::: " + str(pad_id))
            # logger.info("pad_channel ::::::::::::::: " + str(self.pad_channel))
            self._setup_hardware_button(pad_id, index + PAD_IDENTIFIER_OFFSET, self.pad_channel)
            
        self._messages_to_send.append(
            SETUP_MSG_PREFIX + (STORE_IN_MEMORY_COMMAND, LIVE_MEMORY_SLOT_ID) + SETUP_MSG_SUFFIX)
        self._messages_to_send.append(
            SETUP_MSG_PREFIX + (LOAD_MEMORY_COMMAND, ANALOG_LAB_MEMORY_SLOT_ID) + SETUP_MSG_SUFFIX)
        
    def _setup_hardware(self):
        def send_subsequence(subseq):
            for msg in subseq:
                self._send_midi(msg)
                
        sequence_to_run = [Task.run(partial(send_subsequence, subsequence)) for subsequence in
                           split_list(self._messages_to_send, 20)]
        self._tasks.add(Task.sequence(*sequence_to_run))
        self._messages_to_send = []
        
    def disconnect(self):
        """clean things up on disconnect"""
        logger.info("MMINILABMK2 remove listeners")
        if self._pads2[8].value_has_listener(self._pads2_n8):
            self._pads2[8].remove_value_listener(self._pads2_n8)
        if self._pads2[9].value_has_listener(self._pads2_n9):
            self._pads2[9].remove_value_listener(self._pads2_n9)
        if self._pads2[10].value_has_listener(self._pads2_n10):
            self._pads2[10].remove_value_listener(self._pads2_n10)
        if self._pads2[11].value_has_listener(self._pads2_n11):
            self._pads2[11].remove_value_listener(self._pads2_n11)
        if self._pads2[12].value_has_listener(self._pads2_n12):
            self._pads2[12].remove_value_listener(self._pads2_n12)
        if self._pads2[13].value_has_listener(self._pads2_n13):
            self._pads2[13].remove_value_listener(self._pads2_n13)
        if self._pads2[14].value_has_listener(self._pads2_n14):
            self._pads2[14].remove_value_listener(self._pads2_n14)
        if self._pads2[15].value_has_listener(self._pads2_n15):
            self._pads2[15].remove_value_listener(self._pads2_n15)
            
        if self._horizontal_scroll_encoder.value_has_listener(self._encoder_n0):
            self._horizontal_scroll_encoder.remove_value_listener(self._encoder_n0)
        if self._change_focus_button.value_has_listener(self._encoder_n0_button):
            self._change_focus_button.remove_value_listener(self._encoder_n0_button)
            
        if self._vertical_scroll_encoder.value_has_listener(self._encoder_n8):
            self._vertical_scroll_encoder.remove_value_listener(self._encoder_n8)
        if self._arm_button.value_has_listener(self._encoder_n8_button):
            self._arm_button.remove_value_listener(self._encoder_n8_button)
            
        if self._switchpad_button.value_has_listener(self._switchpad_value_on_press):
            self._switchpad_button.remove_value_listener(self._switchpad_value_on_press)
            
        if self._shift_button.value_has_listener(self._shift_value_on_press):
            self._shift_button.remove_value_listener(self._shift_value_on_press)
            
        self.shift_active = False
        self.altpad_pushed = False
        self.modo_clip_activo = False
        
        logger.info(" MMINILABMK2 log CLOSE ")
        return None
    
    # * Boton Shift pulsado
    def _shift_value_on_press(self, value):
        self._update_leds()
        logger.info("mMiniLabMk2 = SHIFT BUTTON PRESSED")
        if value[0] > 0:
            self.modo_clip_activo = False
            self.shift_active = True
            self._mixer.set_track_select_encoder(None)
            self._mixer.set_selected_track_arm_control(None)
            self._transport.set_overdub_button(None)
            self.show_message("SHIFT activo")
        else:
            self.shift_active = False
            if self.modo_clip_activo:
                _shift_led(self, True)
                # self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, 46, 127, 247))
            self._mixer.set_track_select_encoder(self._horizontal_scroll_encoder)
            self._mixer.set_selected_track_arm_control(self._arm_button)
            self._transport.set_overdub_button(self._pads2[10])
            self.show_message("SHIFT inactivo")
        self._update_leds()
        
    # * no implementado
    def _switchpad_value_on_press(self, value):
        if value[0] > 0:
            self.altpad_pushed = True
            self._update_leds()
            logger.info("mMiniLabMk2 = PAD SELECT BUTTON PRESSED")
            # self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, 47, 127, 247)) # test para encender el boton PAD SELECT
        else:
            self._update_leds()

    def _alt_encoder_n0(self, value):
        if value > 0:
            logger.info("::::::::::::_alt_encoder_n0 ::::::::::::: " + str(value))

    def _alt_encoder_n8(self, value):
        if value > 0:
            logger.info("::::::::::::_alt_encoder_n8 ::::::::::::: " + str(value))

    # * Knob 1 (0), sin shift pulsado cambia entre tracks,
    # * con shift cambia entre devices
    def _encoder_n0(self, value):
        # * shift, device change
        # logger.info("track_or_device ::::::::::::: " + str(value))
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_track_select_encoder(None)
            if value > 0:
                if self.application().view.is_view_visible(u'Detail/Clip'):
                    self.application().view.focus_view("Detail/Clip")
                    clip = self.song_instance.view.detail_clip
                    if clip:
                        clip.view.show_loop()
                        self.clip_properties(clip)
                        
                elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                    track = self.song_instance.view.selected_track
                    if track.devices:
                        logger.info("track.devices len :: " + str(len(track.devices)))
                        devices_tot = []
                        for device in track.devices:
                            devices_tot.append(device)
                            logger.info("device name :: " + str(device.name))
                            
                        device_sel = track.view.selected_device
                        # * si el Dispositivo esta en un rack, da fallo ya que no esta en la lista
                        if not device_sel in devices_tot:
                            # * seleccionamos la Cadena (Chain)
                            device_sel = device_sel.canonical_parent
                            # * seleccionamos el Dispositivo superior
                            device_sel = device_sel.canonical_parent
                            logger.info("appo_device :: " + str(device_sel.name))
                            
                        logger.info("appo_device :: " + str(device_sel.name))
                        logger.info("devices_tot len :: " + str(len(devices_tot)))
                        logger.info("device parent :: " + str(device_sel.canonical_parent))
                        logger.info("device view parent :: " + str(device_sel.view.canonical_parent))
                        
                        sel_index = devices_tot.index(device_sel)
                        
                        logger.info("sel_index :: " + str(sel_index))
                        
                        if value > 64:
                            
                            if device_sel is not None:
                                if not sel_index == 0:
                                    prev_device = devices_tot[sel_index - 1]
                                    self.song_instance.view.select_device(prev_device, True)
                                    if IN_DEVICE_VIEW_COLLAPSED:
                                        device_sel.view.is_collapsed = True
                                    # * show properties
                                    # self.device_properties(prev_device)
                                    prev_device.view.is_collapsed = False
                                    if prev_device.can_have_chains:
                                        chain_selected = prev_device.view.selected_chain
                                        chain_devices = chain_selected.devices
                                        if chain_devices:
                                            prev_device.view.is_showing_chain_devices = True
                                            for ch_dev in chain_devices:
                                                ch_dev.view.is_collapsed = True
                                    
                        else:
                            if device_sel is not None:
                                if sel_index + 1 < len(devices_tot):
                                    next_device = devices_tot[sel_index + 1]
                                    self.song_instance.view.select_device(next_device, True)
                                    if IN_DEVICE_VIEW_COLLAPSED:
                                        device_sel.view.is_collapsed = True
                                    # * show properties
                                    # self.device_properties(next_device)
                                    next_device.view.is_collapsed = False
                                    if next_device.can_have_chains:
                                        chain_selected = next_device.view.selected_chain
                                        chain_devices = chain_selected.devices
                                        if chain_devices:
                                            next_device.view.is_showing_chain_devices = True
                                            for ch_dev in chain_devices:
                                                ch_dev.view.is_collapsed = True

        # * normal, track change
        else:
            self._mixer.set_track_select_encoder(self._horizontal_scroll_encoder)
    
    
    
    # * Boton de knob 1 (0), Cambia  de vista entre clip y device tambien hace zoom al loop del clip,
    # *  con shift pulsado oculta la vista de detalle
    def _encoder_n0_button(self, value):
        # logger.info("change_focus_listener ::::::::::::: " + str(value))
        # * shift, hide / show detail
        if self.shift_active:
            if value > 0:
                if self.application().view.is_view_visible(u'Detail'):
                    self.application().view.hide_view("Detail")
                else:
                    self.application().view.focus_view("Detail")
                    self.application().view.zoom_view(1, "Detail", True)
        # * Modo Clip y Normal, change view (device - clip)
        else:
            if value > 0:
                # * Detail
                if not self.application().view.is_view_visible(u'Detail'):
                    self.application().view.focus_view("Detail")
                    self.application().view.zoom_view(1, "Detail", True)
                # * Detail/Clip, Detail/DeviceChain
                if not self.application().view.is_view_visible(u'Detail/DeviceChain'):
                    self.application().view.focus_view("Detail/DeviceChain")
                else:
                    track = self.song_instance.view.selected_track
                    if track.is_foldable:
                        if track.fold_state:
                            track.fold_state = False
                        else:
                            track.fold_state = True
                    
                    clip = self.song_instance.view.detail_clip
                    if clip:
                        self.application().view.focus_view("Detail/Clip")
                        logger.info("mMiniLabMk2 = Detail/Clip: " + str(clip.name))
                        clip.view.show_loop()


    # * no implementado
    def _encoder_n8(self, value):
        # * detectar Movimiento Vertical
        # scene_selected = self.song_instance.view.selected_scene
        if value > 0:
            self._update_leds()
    
    # *Boton de knob 9(8), sin shift pulsado arma el track para grabacion
    # * con shift entra en Modo Clip, si ya esta el Modo Clip cambia la cuantizacion general
    def _encoder_n8_button(self, value):
        # * shift, enter Modo Clip
        if self.shift_active:
            self.show_message("Modo Clip activo")
            self.modo_clip_activo = True
            _shift_led(self, True)
            # self._send_midi((240, 0, 32, 107, 127, 66, 2, 0, 16, 46, 127, 247))
        # * Modo Clip
        elif self.modo_clip_activo:
            self._mixer.set_selected_track_arm_control(None)
            # * Detail/Clip, nope
            if self.application().view.is_view_visible(u'Detail/Clip'):
                self._device.set_on_off_button(None)
                if value > 0:
                    return
            # * Detail/DeviceChain, activate device
            elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                self._device.set_on_off_button(self._arm_button)
                if value > 0:
                    track = self.song_instance.view.selected_track
                    if track.devices:
                        appo_device = self.song_instance.appointed_device
                        logger.info("mMiniLabMk2 = DEVICES class name : " + str(appo_device.class_name) + "  name : " + str(appo_device.name))
                        self.song_instance.view.select_device(appo_device, True)
                        # appo_device.view.is_collapsed = False
                        if appo_device.can_have_chains:
                            logger.info("DEVICE tiene macros : " + str(appo_device.has_macro_mappings))
                            for chain in appo_device.chains:
                                logger.info("DEVICE chain : " + str(chain))
                        if appo_device.is_active:
                            appo_device.is_enabled = False
                        else:
                            appo_device.is_enabled = True
                            
        else:
            self._device.set_on_off_button(None)
            self._mixer.set_selected_track_arm_control(self._arm_button)
    
    # * vol send a / loop position, select device bank
    def _encoder_n5(self, value):
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_return_volume_controls(None)
            # * shift, change loop position
            if self.application().view.is_view_visible(u'Detail/Clip'):
                clip = self.song_instance.view.detail_clip
                if clip:
                    if value > 0:
                        end = clip.length
                        p_advance = self.move_quantity(clip)
                        position = clip.position
                        if value > 64:
                            clip.position = position - p_advance
                        else:
                            clip.position = position + p_advance
            # * shift, select device bank
            elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                self.application().view.focus_view("Detail/DeviceChain")
                if value > 0:
                    appo_device = self.song_instance.appointed_device
                    # type = appo_device.type
                    # logger.info("device type :: " + str(type))
                    presets = None
                    actual_preset = None
                    
                    if appo_device.can_have_chains:
                        chain_selected = appo_device.view.selected_chain
                        chain_devices = chain_selected.devices
                        if len(chain_devices) > 0:
                            # appo_device.view.is_showing_chain_devices = True
                            for device in chain_devices:
                                if presets is not None:
                                    break
                                try:
                                    if device.presets:
                                        presets = device.presets
                                        actual_preset = device.selected_preset_index
                                        appo_device = device
                                except:
                                    pass
                    else:
                        try:
                            if appo_device.presets:
                                presets = appo_device.presets
                                actual_preset = appo_device.selected_preset_index
                        except:
                            pass
                        
                    if presets is not None:
                        # for pre in presets:
                        #     logger.info(str(appo_device.name) + " preset: " + str(pre))
                        total_presets = len(presets) - 1
                        # logger.info("total presets: " + str(total_presets))
                        if value > 64:
                            if actual_preset == 0:
                                actual_preset = total_presets
                            else:
                                actual_preset = actual_preset - 1
                            appo_device.selected_preset_index = actual_preset
                            self.show_message(str(appo_device.name) + " < " + str(actual_preset) + " - " + str(presets[actual_preset]))
                        else:
                            
                            if actual_preset == total_presets:
                                actual_preset = 0
                            else:
                                actual_preset = actual_preset + 1
                            appo_device.selected_preset_index = actual_preset
                            self.show_message(str(appo_device.name) + " > " + str(actual_preset) + " - " + str(presets[actual_preset]))
                
        # * normal, volumen de send a
        else:
            self._mixer.set_return_volume_controls(self._return_encoders)
    
    # * send a / loop start
    def _encoder_n6(self, value):
        # * shift, change loop start
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_selected_track_send_controls(None)
            if value > 0:
                clip = self.song_instance.view.detail_clip
                if clip and self.application().view.is_view_visible(u'Detail/Clip'):
                    
                    start = clip.loop_start
                    end = clip.loop_end
                    l_advance = self.move_quantity(clip)
                    if start < end:
                        if value > 64:
                            clip.loop_start = start - l_advance
                        else:
                            if start + l_advance < end:
                                clip.loop_start = start + l_advance
        # * normal, envio send a
        else:
            self._mixer.set_selected_track_send_controls(self._send_encoders)
    
    # * pan / loop_end
    def _encoder_n7(self, value):
        # * shift, set loop end
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_selected_track_pan_control(None)
            if value > 0:
                clip = self.song_instance.view.detail_clip
                if clip and self.application().view.is_view_visible(u'Detail/Clip'):
                    start = clip.loop_start
                    end = clip.loop_end
                    l_advance = self.move_quantity(clip)
                    
                    if value > 64:
                        l_end = end - l_advance
                        if start < l_end:
                            clip.loop_end = l_end
                    else:
                        clip.loop_end = end + l_advance
        # * normal, track pannig
        else:
            self._mixer.set_selected_track_pan_control(self._pan_encoder)
    
    # * vol send b / change clip view grid
    def _encoder_n13(self, value):
        # * shift, change view grid
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_return_volume_controls(None)
            if value > 0:
                clip = self.song_instance.view.detail_clip
                if clip and self.application().view.is_view_visible(u'Detail/Clip'):
                    qg_actual_index = 0
                    qg_actual = clip.view.grid_quantization
                    GRID_QUANTIZATION_LIST = [Live.Clip.GridQuantization.no_grid,
                                              Live.Clip.GridQuantization.g_thirtysecond,
                                              Live.Clip.GridQuantization.g_sixteenth,
                                              Live.Clip.GridQuantization.g_eighth,
                                              Live.Clip.GridQuantization.g_quarter,
                                              Live.Clip.GridQuantization.g_half,
                                              Live.Clip.GridQuantization.g_bar,
                                              Live.Clip.GridQuantization.g_2_bars,
                                              Live.Clip.GridQuantization.g_4_bars,
                                              Live.Clip.GridQuantization.g_8_bars]
                    if qg_actual in GRID_QUANTIZATION_LIST:
                        qg_actual_index = GRID_QUANTIZATION_LIST.index(qg_actual)
                    if value > 64:
                        qg_actual_index = qg_actual_index + 1
                        if qg_actual_index > 9:
                            qg_actual_index = 0
                            
                    else:
                        qg_actual_index = qg_actual_index - 1
                        if qg_actual_index < 0:
                            qg_actual_index = 9
                    clip.view.grid_quantization = GRID_QUANTIZATION_LIST[qg_actual_index]
                    logger.info("GridQuantization : " + str(clip.view.grid_quantization) + " - index: " + str(qg_actual_index))
                    # if value > 64:
                    #     clip.move_playing_pos(-int(Live.Song.Quantization.q_8_bars))
                    # else:
                    #     clip.move_playing_pos(int(Live.Song.Quantization.q_8_bars))
        # * normal, volumen de send b
        else:
            self._mixer.set_return_volume_controls(self._return_encoders)
    
    # * send b / ( start_marker / device change )
    def _encoder_n14(self, value):
        # * shift, set start marker, change device
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_selected_track_send_controls(None)
            if value > 0:
                clip = self.song_instance.view.detail_clip
                if clip and self.application().view.is_view_visible(u'Detail/Clip'):
                    
                    s_start = round(clip.start_marker,2)
                    s_marker = clip.end_marker
                    s_advance = self.move_quantity(clip)
                    if value > 64:
                        clip.start_marker = s_start - s_advance
                    else:
                        if s_start + s_advance < clip.end_marker:
                            clip.start_marker = s_start + s_advance
                
                elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                    if value > 60:
                        self.application().view.scroll_view(self.app_instance.NavDirection.left, u'Detail/DeviceChain',
                                                            False)
                    else:
                        self.application().view.scroll_view(self.app_instance.NavDirection.right, u'Detail/DeviceChain',
                                                            False)
        # * normal, envio send b
        else:
            self._mixer.set_selected_track_send_controls(self._send_encoders)
    
    # * vol / ( end_marker / device change )
    def _encoder_n15(self, value):
        # * shift, set end marker, change device
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_selected_track_volume_control(None)
            if value > 0:
                clip = self.song_instance.view.detail_clip
                if clip and self.application().view.is_view_visible(u'Detail/Clip'):
                    e_marker = clip.end_marker
                    e_advance = self.move_quantity(clip)
                    if value > 64:
                        if e_marker - e_advance > clip.start_marker:
                            clip.end_marker = e_marker - e_advance
                    else:
                        clip.end_marker = e_marker + e_advance
                
                # elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                #     if value > 64:
                #         self.application().view.scroll_view(self.app_instance.NavDirection.left,
                #                                             u'Detail/DeviceChain',
                #                                             False)
                #     else:
                #         self.application().view.scroll_view(self.app_instance.NavDirection.right,
                #                                             u'Detail/DeviceChain',
                #                                             False)
        # * normal, track volumen
        else:
            self._mixer.set_selected_track_volume_control(self._volume_encoder)
    
    # ? PADS 2
    
    # * n120 - play button / arm track and overdub
    def _pads2_n8(self, value):
        # * shift, arm track and overdub
        if self.shift_active or self.modo_clip_activo:
            self._transport.set_play_button(None)
            if value > 0:
                current_track = self.song_instance.view.selected_track
                if current_track.arm:
                    current_track.arm = False
                    self.song_instance.overdub = False
                else:
                    current_track.arm = True
                    self.song_instance.overdub = True
        # * normal, play button
        else:
            self._transport.set_play_button(self._pads2[8])
            if value > 0:
                if self.song_instance.is_playing:
                    self.song_instance.stop_playing()
                else:
                    if self.song_instance.current_song_time > 0:
                        self.song_instance.continue_playing()
                    self.song_instance.start_playing()
        self._update_leds()

    # * n121 - stop / undo
    def _pads2_n9(self, value):
        # * shift, undo
        if self.shift_active or self.modo_clip_activo:
            self._transport.set_stop_button(None)
            if value > 0:
                self.song_instance.undo()
        # * normal, stop
        else:
            self._transport.set_stop_button(self._pads2[9])
            if value > 0:
                if self.song_instance.is_playing:
                    self.song_instance.stop_playing()
                else:
                    self.song_instance.stop_playing()
        self._update_leds()

    # * n122 - overdub / nope
    def _pads2_n10(self, value):
        # * shift,
        if self.shift_active or self.modo_clip_activo:
            self._transport.set_overdub_button(None)
            if value > 0:
                return
        # * normal, overdub
        else:
            self._transport.set_overdub_button(self._pads2[10])
            if value > 0:
                if self.song_instance.overdub:
                    self.song_instance.overdub = False
                else:
                    self.song_instance.overdub = True
        self._update_leds()
    
    # * n123 - undo / quantize
    def _pads2_n11(self, value):
        # * shift, quantize
        if self.shift_active or self.modo_clip_activo:
            q_actual = self.song_instance.clip_trigger_quantization
            QUANTIZATIONS = [Live.Song.Quantization.q_no_q,
                             Live.Song.Quantization.q_8_bars,
                             Live.Song.Quantization.q_4_bars,
                             Live.Song.Quantization.q_2_bars,
                             Live.Song.Quantization.q_bar,
                             Live.Song.Quantization.q_half,
                             Live.Song.Quantization.q_half_triplet,
                             Live.Song.Quantization.q_quarter,
                             Live.Song.Quantization.q_quarter_triplet,
                             Live.Song.Quantization.q_eight,
                             Live.Song.Quantization.q_eight_triplet,
                             Live.Song.Quantization.q_sixtenth,
                             Live.Song.Quantization.q_sixtenth_triplet,
                             Live.Song.Quantization.q_thirtytwoth]
            if value > 0:
                if q_actual in QUANTIZATIONS:
                    q_actual_index = QUANTIZATIONS.index(q_actual)
                    q_actual_index = q_actual_index + 1
                    if q_actual_index > 13:
                        q_actual_index = 0
                    self.song_instance.clip_trigger_quantization = QUANTIZATIONS[q_actual_index]
            
            
            
            if value > 0:
                return
        # * normal, undo
        else:
            if value > 0:
                self.song_instance.undo()
        self._update_leds()
    
    
    # * n124 - nope / scrub
    def _pads2_n12(self, value):
        # * shift, scrub
        if self.shift_active or self.modo_clip_activo:
            clip = self.song_instance.view.detail_clip
            if clip and self.application().view.is_view_visible(u'Detail/Clip'):
                if value > 0:
                    if clip.is_playing:
                        clip.scrub(clip.playing_position)
                        _send_color(self, 124, GREEN)
                        _send_color(self, 125, YELLOW)
                    else:
                        clip.scrub(clip.start_marker)
                        _send_color(self, 124, GREEN)
                        _send_color(self, 125, YELLOW)
        # * normal,
        else:
            self._update_leds()
        self._update_leds()
    
    # *n125 - nope /  play stop clip
    def _pads2_n13(self, value):
        # * shift, play stop clip
        if self.shift_active or self.modo_clip_activo:
            self._transport.set_stop_button(None)
            clip = self.song_instance.view.detail_clip
            if clip and self.application().view.is_view_visible(u'Detail/Clip'):
                if value > 0:
                    if clip.is_playing:
                        clip.stop_scrub()
                        _send_color(self, 125, GREEN)
                        _send_color(self, 124, YELLOW)
                    else:
                        clipslot = self.song_instance.view.highlighted_clip_slot
                        clipslot.fire(force_legato=True)
                        # clip.fire()
                        _send_color(self, 125, GREEN)
                        _send_color(self, 124, YELLOW)
        
        # * normal,
        else:
            self._update_leds()
        self._update_leds()
    
    # *n126 - new scene / consolidate loop
    def _pads2_n14(self, value):
        # * shift, consolidate loop
        if self.shift_active or self.modo_clip_activo:
            clip = self.song_instance.view.detail_clip
            if clip and self.application().view.is_view_visible(u'Detail/Clip'):
                if clip.looping:
                    if value > 0:
                        loop_length = clip.loop_end - clip.loop_start
                        if loop_length < 1:
                            loop_length = round(loop_length, 2)
                        else:
                            loop_length = round(loop_length)
                        clip.loop_end = clip.loop_start + loop_length
                        # logger.info("loop.length : " + str(loop_length) + " clip.loop_end: " + str(clip.loop_end))
        
        # * normal, new scene from play
        else:
            if value > 0:
                self.song_instance.capture_and_insert_scene()
        self._update_leds()
    
    # * n127 - play stop scene / set loop
    def _pads2_n15(self, value):
        # * shift, set loop
        if self.shift_active or self.modo_clip_activo:
            clip = self.song_instance.view.detail_clip
            if clip and self.application().view.is_view_visible(u'Detail/Clip'):
                if clip.is_audio_clip:
                    if not clip.warping:
                        clip.warp_mode
                if value > 0:
                    if clip.looping:
                        clip.looping = False
                    else:
                        clip.looping = True
        
        # * normal, play stop scene
        else:
            scene_selected = self.song_instance.view.selected_scene
            if value > 0:
                if not scene_selected.is_empty:
                    playing_count = 0
                    for clip in scene_selected.clip_slots:
                        if clip.is_playing:
                            clip.stop()
                            playing_count = playing_count + 1
                    if playing_count == 0:
                        scene_selected.fire_as_selected(force_legato=True)
                else:
                    self.song_instance.stop_all_clips(Quantized=True)
        self._update_leds()
   
    # ? TODO: no implementado
    def _unfold_track(self, track):
        # track = self.song_instance.selected_track
        if track.is_foldable:
            if track.fold_state:
                track.fold_state = False
            else:
                track.fold_state = True
                
    def move_quantity(self,clip):
        current_gridquantization = clip.view.grid_quantization
        GRID_QUANTIZATION_LIST = [Live.Clip.GridQuantization.no_grid,
                                  Live.Clip.GridQuantization.g_thirtysecond,
                                  Live.Clip.GridQuantization.g_sixteenth,
                                  Live.Clip.GridQuantization.g_eighth,
                                  Live.Clip.GridQuantization.g_quarter,
                                  Live.Clip.GridQuantization.g_half,
                                  Live.Clip.GridQuantization.g_bar,
                                  Live.Clip.GridQuantization.g_2_bars,
                                  Live.Clip.GridQuantization.g_4_bars,
                                  Live.Clip.GridQuantization.g_8_bars]
        GRID_QUANTIZATION_NUMBERS = [0, 0.03125, 0.0625, 0.125, 0.25, 0.5,1,2,4,8]
        q_actual_index = GRID_QUANTIZATION_LIST.index(current_gridquantization)
        valor = GRID_QUANTIZATION_NUMBERS[q_actual_index]
        
        return valor
    
    
    def clip_properties(self, clip):
        if clip.is_audio_clip:
            CLIP_TYPE = "Audio clip"
        else:
            CLIP_TYPE = "Midi clip"

        logger.info(CLIP_TYPE + " - start_time : " + str(clip.start_time))
        logger.info(CLIP_TYPE + " - end_time : " + str(clip.end_time))
        logger.info(CLIP_TYPE + " - start_marker : " + str(clip.start_marker))
        logger.info(CLIP_TYPE + " - end_marker : " + str(clip.end_marker))
        logger.info(CLIP_TYPE + " - loop position : " + str(clip.position))
        logger.info(CLIP_TYPE + " - length : " + str(clip.length))
        logger.info(CLIP_TYPE + " - loop_start : " + str(clip.loop_start))
        logger.info(CLIP_TYPE + " - loop_end : " + str(clip.loop_end))
        clip_long = clip.loop_end - clip.loop_start
        logger.info(CLIP_TYPE + " - loop_length : " + str(clip_long))
        if clip.is_audio_clip:
            logger.info(CLIP_TYPE + " - sample_length : " + str(clip.sample_length) + " (sample time)")
            if clip.warping:
                time = clip.beat_to_sample_time(clip.length)
                logger.info("BEATS to Sample TIME : " + str(time))
                time = clip.sample_to_beat_time(clip.length)
                logger.info("SAMPLE to Beat TIME : " + str(time))
            else:
                time = clip.seconds_to_sample_time(clip.length)
                logger.info(CLIP_TYPE + " - SECONDS to Sample TIME : " + str(time) + " (sample time)")

    def device_properties(self, device):
        logger.info("device PROPERTIES ::::::::::::: ")
        type = device.type
        logger.info("device type :: " + str(type))
        class_name = device.class_name
        logger.info("device class_name :: " + str(class_name))
        class_display_name = device.class_display_name
        logger.info("device class_display_name :: " + str(class_display_name))
        name = device.name
        logger.info("device name :: " + str(name))
        collapsed = device.view.is_collapsed
        logger.info("device collapsed :: " + str(collapsed))
        parent_view = device.view.canonical_parent
        logger.info("device parent_view :: " + str(parent_view))
        parent = device.canonical_parent
        logger.info("device parent :: " + str(parent))
        can_have_chains = device.can_have_chains
        logger.info("device can_have_chains :: " + str(can_have_chains))
        if can_have_chains:
            logger.info("device is a Rack :: ")
            can_show_chains = device.can_show_chains
            logger.info("device is a Rack :: can_show_chains :: " + str(can_show_chains))
            is_showing_chain_devices = device.view.is_showing_chain_devices
            logger.info("device is a Rack :: is showing chain devices :: " + str(is_showing_chain_devices))
            chain_selected = device.view.selected_chain
            logger.info("device is a Rack :: chain selected :: " + str(chain_selected))
            chain_selected_name = chain_selected.name
            logger.info("device is a Rack :: chain selected name :: " + str(chain_selected_name))
            chain_devices = chain_selected.devices
            if chain_devices:
                chain_devices_total = len(chain_devices)
                logger.info("device is a Rack :: chain selected devices count :: " + str(chain_devices_total))
                if chain_devices_total > 0:
                    for ch_device in chain_devices:
                        ch_dev_name = ch_device.name
                        logger.info("device is a Rack :: chain selected devices name :: " + str(ch_dev_name))
        can_have_drum_pads = device.can_have_drum_pads
        logger.info("device can_have_drum_pads :: " + str(can_have_drum_pads))
        is_active = device.is_active
        logger.info("device is_active :: " + str(is_active))
        if device.parameters:
            parameters_list = device.parameters
            parameters_count = len(parameters_list)
            logger.info("device parameters_count :: " + str(parameters_count))
            for param in parameters_list:
                logger.info("device parameter :: " + str(param.name))
        try:
            presets = device.presets
            logger.info("device presets :: " + str(presets))
        except:
            logger.info("device presets :: no tiene")
        try:
            bank_count = device.get_bank_count()
            logger.info("device bank_count :: " + str(bank_count))
        except:
            logger.info("device bank_count :: no tiene")

    # ? Leds stuff
    def _update_leds(self):
        if self.shift_active or self.modo_clip_activo:
            _leds_ClipMode(self, self.song_instance)
        else:
            _leds_NormalMode(self, self.song_instance)
