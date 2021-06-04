# Embedded file name: /Users/versonator/Jenkins/live/output/Live/mac_64_static/Release/python-bundle/MIDI Remote Scripts/MiniLab_mkII/MiniLabMk2.py
from __future__ import absolute_import, print_function, unicode_literals
import time
import logging
from functools import partial
from itertools import izip
from itertools import cycle
from .Constants import *

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
from .LedUtils import _off_leds, _shift_led, _leds_NormalMode, _leds_ClipMode, blink_conditioned, _color_leds, _send_color
from .Actions import Actions

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
# !   h.scroll       |----------  device controls ---------|         send a     vol send a         pan
# *  + detail view
#                                                                                     |---track----|
# *  + arm track
# !   v.scroll      |----------  device controls ----------|         send b     vol send b       volumen
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
HARDWARE_BUTTON_IDS = xrange(112, 128)  #
PAD_IDENTIFIER_OFFSET = 36
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

NORMAL_MIDIMAPMODE = Live.MidiMap.MapMode.relative_smooth_two_compliment

TWO_SENDS = False


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
            self.enc0_button = False
            self.enc8_button = False
            self.sub_devices = []
            self.scrubbing_clips = []
            self.show_message("mMiniLabMk2 cargando...")
            logger.info("soneu remote script loaded")
            self._create_controls()
            self._create_hardware_settings()
            self._create_device()
            self._create_session()
            self._create_mixer()
            self._create_transport()
            _off_leds(self)
            self.show_message("mMiniLabMk2 Listo...!")
    
    def _create_controls(self):
        
        self._knob0_encoder = EncoderElement(
            MIDI_CC_TYPE, self.encoder_msg_channel,
            self.encoder_msg_ids[0],
            NORMAL_MIDIMAPMODE,
            name=u'Horizontal_Scroll_Encoder'
        )
        self._knob8_encoder = EncoderElement(
            MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[8],
            NORMAL_MIDIMAPMODE,
            name=u'Vertical_Scroll_Encoder'
        )
        
        self._device_controls = ButtonMatrixElement(
            rows=[[EncoderElement(
                MIDI_CC_TYPE, self.encoder_msg_channel,
                identifier,
                NORMAL_MIDIMAPMODE,
                name=u'Encoder_%d_%d' % (column_index, row_index)
            ) for
                column_index, identifier in enumerate(row)
            ]
                for row_index, row in enumerate((self.encoder_msg_ids[1:5], self.encoder_msg_ids[9:13]))
            ]
        )
        if TWO_SENDS:
            # envios de los send
            self._knob6_encoder = EncoderElement(
                MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[5],
                NORMAL_MIDIMAPMODE,
                name=u'Send_A_Encoder'
            )
            self._knob14_encoder = EncoderElement(
                MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[13],
                NORMAL_MIDIMAPMODE,
                name=u'Send_B_Encoder'
            )
            self._send_encoders = ButtonMatrixElement(rows=[[self._knob6_encoder, self._knob14_encoder]])
            
            # volumenes de los send tracks
            self._knob7_encoder = EncoderElement(
                MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[6],
                NORMAL_MIDIMAPMODE,
                name=u'Return_A_Encoder'
            )
            self._knob15_encoder = EncoderElement(
                MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[14],
                NORMAL_MIDIMAPMODE,
                name=u'Return_B_Encoder'
            )
            self._return_encoders = ButtonMatrixElement(rows=[[self._knob7_encoder, self._knob15_encoder]])
        else:
            # * Four sends
            # envios de los send
            self._knob6_encoder = EncoderElement(
                MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[5],
                NORMAL_MIDIMAPMODE,
                name=u'Send_A_Encoder'
            )
            self._knob7_encoder = EncoderElement(
                MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[6],
                NORMAL_MIDIMAPMODE,
                name=u'Send_B_Encoder'
            )
            self._knob14_encoder = EncoderElement(
                MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[13],
                NORMAL_MIDIMAPMODE,
                name=u'Send_C_Encoder'
            )
            self._knob15_encoder = EncoderElement(
                MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[14],
                NORMAL_MIDIMAPMODE,
                name=u'Send_D_Encoder'
            )
            self._send_encoders = ButtonMatrixElement(
                rows=[[self._knob6_encoder, self._knob7_encoder, self._knob14_encoder, self._knob15_encoder]]
            )
        
        self._pan_encoder = EncoderElement(
            MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[7],
            NORMAL_MIDIMAPMODE, name=u'Pan_Encoder'
        )
        
        self._volume_encoder = EncoderElement(
            MIDI_CC_TYPE, self.encoder_msg_channel, self.encoder_msg_ids[15],
            NORMAL_MIDIMAPMODE,
            name=u'Volume_Encoder'
        )
        
        self._pads = ButtonMatrixElement(
            rows=[
                [ButtonElement(
                    True, MIDI_NOTE_TYPE, self.pad_channel, col + 36 + 8 * row, name=u'Pad_%d_%d' % (col, row)
                )
                    for col in xrange(8)] for row in xrange(1)]
        )
        self._pads2 = ButtonMatrixElement(
            rows=[
                [ButtonElement(
                    True, MIDI_NOTE_TYPE, self.pad_channel, col + 36 + 8 * row, name=u'Pad_%d_%d' % (col, row)
                )
                    for col in xrange(8)] for row in xrange(2)]
        )
        
        
        self._pad_leds = ButtonMatrixElement(
            rows=[[SysexValueControl(
                message_prefix=SETUP_MSG_PREFIX + (
                    WRITE_COMMAND, WORKING_MEMORY_ID, COLOR_PROPERTY, column + 112 + row * 8), default_value=(0,),
                name=u'Pad_LED_%d' % (column,)
            ) for column in
                xrange(8)] for row in xrange(1)], name=u'Pad_LED_Matrix'
        )
        
        self._knob8_button = ButtonElement(True, MIDI_CC_TYPE, self.button_encoder_msg_channel, ENCODER_PUSH2,
                                         name='Arm_Button'
                                         )
        self._knob0_button = ButtonElement(
            True, MIDI_CC_TYPE, self.button_encoder_msg_channel, ENCODER_PUSH1,
            name='Change_Focus_Button'
        )
        
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
        
        self._memory_slot_selection = SysexValueControl(
            message_prefix=SETUP_MSG_PREFIX + (MEMORY_SLOT_PROPERTY,),
            name=u'Memory_Slot_Selection'
        )
        self._hardware_live_mode_switch = SysexValueControl(
            message_prefix=LIVE_MODE_MSG_HEAD,
            default_value=(OFF_VALUE,),
            name=u'Hardware_Live_Mode_Switch'
        )
    
    
    
    # region ::: region Create
    
    def _create_hardware_settings(self):
        self._hardware_settings = HardwareSettingsComponent(
            name=u'Hardware_Settings', is_enabled=False, layer=Layer(
                memory_slot_selection=self._memory_slot_selection,
                hardware_live_mode_switch=self._hardware_live_mode_switch
            )
        )
        self._on_live_mode_changed.subject = self._hardware_settings
        self._hardware_settings.set_enabled(True)
    
    # TODO: Hacer un modo de solo mezcla en otra memoria
    @subject_slot(u'live_mode')
    def _on_live_mode_changed(self, is_live_mode_on):
        _off_leds(self)
        
        self._transport.set_enabled(is_live_mode_on)
        self._session.set_enabled(is_live_mode_on)
        self._mixer.set_enabled(is_live_mode_on)
        self._device.set_enabled(is_live_mode_on)
        if is_live_mode_on:
            self.show_message("Modo Live On")
            logger.info("Modo Live On")
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
        self._device = DeviceComponent(
            name=u'Device', is_enabled=False,
            layer=Layer(parameter_controls=self._device_controls),
            # on_off_button=self._knob8_button),
            device_selection_follows_track_selection=True
        )
        
        self.set_device_component(self._device)
        self._device.set_on_off_button(None)
        
    def _create_transport(self):
        self._transport = TransportComponent(
            name=u'Transport', is_enabled=False,
            layer=Layer(
                play_button=self._pads2[8],
                stop_button=self._pads2[9],
                overdub_button=self._pads2[10]
            )
        )
        self._live = Live.Application.get_application()
        self.app_instance = self._live.view
        self.song_instance = self._transport.song()
        
    
    def _create_session(self):
        self._session = self.session_component_type(
            num_tracks=self._pads.width(), num_scenes=1,
            name=u'Session', is_enabled=False,
            layer=Layer(
                clip_launch_buttons=self._pads,
                scene_select_control=self._knob8_encoder
            )
        )
        self.set_highlighting_session_component(self._session)
        self._session.set_clip_slot_leds(self._pad_leds)
    
    def _create_mixer(self):
        
        self._mixer = MixerComponent(
            name=u'Mixer', is_enabled=False, num_returns=4,
            layer=Layer(
                track_select_encoder=self._knob0_encoder,
                selected_track_volume_control=self._volume_encoder,
                selected_track_pan_control=self._pan_encoder,
                selected_track_send_controls=self._send_encoders
            )
        )
        # self._mixer.set_selected_track_arm_control(self._knob8_button)
        self._mixer.set_selected_track_arm_control(None)
        
        if TWO_SENDS:
            self._mixer.set_return_volume_controls(self._return_encoders)
    
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
            SETUP_MSG_PREFIX + (STORE_IN_MEMORY_COMMAND, LIVE_MEMORY_SLOT_ID) + SETUP_MSG_SUFFIX
        )
        self._messages_to_send.append(
            SETUP_MSG_PREFIX + (LOAD_MEMORY_COMMAND, ANALOG_LAB_MEMORY_SLOT_ID) + SETUP_MSG_SUFFIX
        )
    
    def _setup_hardware(self):
        def send_subsequence(subseq):
            for msg in subseq:
                self._send_midi(msg)
        
        sequence_to_run = [Task.run(partial(send_subsequence, subsequence)) for subsequence in
                           split_list(self._messages_to_send, 20)]
        self._tasks.add(Task.sequence(*sequence_to_run))
        self._messages_to_send = []
    
    # endregion
    
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
    
        # * _pads1
        if not self._pads[0].value_has_listener(self._pads_n0):
            self._pads[0].add_value_listener(self._pads_n0, identify_sender=False)
        if not self._pads[1].value_has_listener(self._pads_n1):
            self._pads[1].add_value_listener(self._pads_n1, identify_sender=False)
        if not self._pads[2].value_has_listener(self._pads_n2):
            self._pads[2].add_value_listener(self._pads_n2, identify_sender=False)
        if not self._pads[3].value_has_listener(self._pads_n3):
            self._pads[3].add_value_listener(self._pads_n3, identify_sender=False)
        if not self._pads[4].value_has_listener(self._pads_n4):
            self._pads[4].add_value_listener(self._pads_n4, identify_sender=False)
        if not self._pads[5].value_has_listener(self._pads_n5):
            self._pads[5].add_value_listener(self._pads_n5, identify_sender=False)
        if not self._pads[6].value_has_listener(self._pads_n6):
            self._pads[6].add_value_listener(self._pads_n6, identify_sender=False)
        if not self._pads[7].value_has_listener(self._pads_n7):
            self._pads[7].add_value_listener(self._pads_n7, identify_sender=False)
        
            # encoders listener
        if not self._knob6_encoder.value_has_listener(self._encoder_n5):
            self._knob6_encoder.add_value_listener(self._encoder_n5, identify_sender=False)
        if not self._knob14_encoder.value_has_listener(self._encoder_n13):
            self._knob14_encoder.add_value_listener(self._encoder_n13, identify_sender=False)
        if not self._knob7_encoder.value_has_listener(self._encoder_n6):
            self._knob7_encoder.add_value_listener(self._encoder_n6, identify_sender=False)
        if not self._knob15_encoder.value_has_listener(self._encoder_n14):
            self._knob15_encoder.add_value_listener(self._encoder_n14, identify_sender=False)
        if not self._pan_encoder.value_has_listener(self._encoder_n7):
            self._pan_encoder.add_value_listener(self._encoder_n7, identify_sender=False)
        if not self._volume_encoder.value_has_listener(self._encoder_n15):
            self._volume_encoder.add_value_listener(self._encoder_n15, identify_sender=False)
    
        # _knob0_encoder
        if not self._knob0_encoder.value_has_listener(self._encoder_n0):
            self._knob0_encoder.add_value_listener(self._encoder_n0, identify_sender=False)
        if not self._knob0_button.value_has_listener(self._encoder_n0_button):
            self._knob0_button.add_value_listener(self._encoder_n0_button, identify_sender=False)
    
        if not self._knob8_encoder.value_has_listener(self._encoder_n8):
            self._knob8_encoder.add_value_listener(self._encoder_n8, identify_sender=False)
        if not self._knob8_button.value_has_listener(self._encoder_n8_button):
            self._knob8_button.add_value_listener(self._encoder_n8_button, identify_sender=False)
    
        if not self._switchpad_button.value_has_listener(self._switchpad_value_on_press):
            self._switchpad_button.add_value_listener(self._switchpad_value_on_press, identify_sender=False)
    
        if not self._shift_button.value_has_listener(self._shift_value_on_press):
            self._shift_button.add_value_listener(self._shift_value_on_press, identify_sender=False)

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
        
        if self._pads[0].value_has_listener(self._pads_n0):
            self._pads[0].remove_value_listener(self._pads_n0)
        if self._pads[1].value_has_listener(self._pads_n1):
            self._pads[1].remove_value_listener(self._pads_n1)
        if self._pads[2].value_has_listener(self._pads_n2):
            self._pads[2].remove_value_listener(self._pads_n2)
        if self._pads[3].value_has_listener(self._pads_n3):
            self._pads[3].remove_value_listener(self._pads_n3)
        if self._pads[4].value_has_listener(self._pads_n4):
            self._pads[4].remove_value_listener(self._pads_n4)
        if self._pads[5].value_has_listener(self._pads_n5):
            self._pads[5].remove_value_listener(self._pads_n5)
        if self._pads[6].value_has_listener(self._pads_n6):
            self._pads[6].remove_value_listener(self._pads_n6)
        if self._pads[7].value_has_listener(self._pads_n7):
            self._pads[7].remove_value_listener(self._pads_n7)
        
        # encoders
        if self._knob6_encoder.value_has_listener(self._encoder_n5):
            self._knob6_encoder.remove_value_listener(self._encoder_n5)
        if self._knob14_encoder.value_has_listener(self._encoder_n13):
            self._knob14_encoder.remove_value_listener(self._encoder_n13)
        if self._knob7_encoder.value_has_listener(self._encoder_n6):
            self._knob7_encoder.remove_value_listener(self._encoder_n6)
        if self._knob15_encoder.value_has_listener(self._encoder_n14):
            self._knob15_encoder.remove_value_listener(self._encoder_n14)
        if self._pan_encoder.value_has_listener(self._encoder_n7):
            self._pan_encoder.remove_value_listener(self._encoder_n7)
        if self._volume_encoder.value_has_listener(self._encoder_n15):
            self._volume_encoder.remove_value_listener(self._encoder_n15)
        
        if self._knob0_encoder.value_has_listener(self._encoder_n0):
            self._knob0_encoder.remove_value_listener(self._encoder_n0)
        if self._knob0_button.value_has_listener(self._encoder_n0_button):
            self._knob0_button.remove_value_listener(self._encoder_n0_button)
        
        if self._knob8_encoder.value_has_listener(self._encoder_n8):
            self._knob8_encoder.remove_value_listener(self._encoder_n8)
        if self._knob8_button.value_has_listener(self._encoder_n8_button):
            self._knob8_button.remove_value_listener(self._encoder_n8_button)
        
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
            self._mixer.set_track_select_encoder(self._knob0_encoder)
            self._transport.set_overdub_button(self._pads2[10])
            self.show_message("SHIFT inactivo")
        self._update_leds()
    
    # * no implementado
    def _switchpad_value_on_press(self, value):
        if value[0] > 0:
            self.altpad_pushed = True
            self._update_leds()
            logger.info("mMiniLabMk2 = PAD SELECT BUTTON PRESSED")
        else:
            self.altpad_pushed = False
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
        if self.modo_clip_activo:
            
            if value > 0:
                if self.application().view.is_view_visible(u'Detail/Clip'):
                    # * shift, track change when in clip view
                    clip = self.song_instance.view.detail_clip
                    if clip:
                        clip.view.show_loop()
                    # self._mixer.set_track_select_encoder(self._knob0_encoder)
                
                elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                    # self._mixer.set_track_select_encoder(None)
                    pass

        # * normal, track change
        else:
            self._mixer.set_track_select_encoder(self._knob0_encoder)
    
    # * Boton de knob 1 (0), Cambia  de vista entre clip y device tambien hace zoom al loop del clip,
    # *  con shift pulsado oculta la vista de detalle
    def _encoder_n0_button(self, value):
        if value > 0:
            self.enc0_button = True
            
            self._session.set_enabled(False)
            # self._session.clip_launch_buttons(False)
            session_tracks = self._session.current_tracks
            visible_session_pads_number = len(session_tracks)
            offset = self._session.track_offset()
            total_v_tracks = self.song().visible_tracks
            while visible_session_pads_number > 0:
                visible_session_pads_number -= 1
                pad_number = visible_session_pads_number
                # logger.info(" : pad n: " + str(pad_number))
                track_number = offset + pad_number
                pad_track = total_v_tracks[track_number]
                if pad_track.mute:
                    _send_color(self, 112 + pad_number, CYAN)
            
            # * shift, hide / show detail
            if self.shift_active:
                # * shift, hide / show detail
                # Actions(self._transport).button_hide_viewdetail()
                # * Fold / unfold track in session
                is_folder = Actions(self._transport).button_track_fold()
                if not is_folder:
            # * Modo Clip y Normal, change view (device - clip)
            # else:
                    # * Detail
                    if not self.application().view.is_view_visible(u'Detail'):
                        self.application().view.focus_view("Detail")
                        self.application().view.zoom_view(1, "Detail", True)
                    # * Detail/Clip, Detail/DeviceChain
                    if not self.application().view.is_view_visible(u'Detail/DeviceChain'):
                        self.application().view.focus_view("Detail/DeviceChain")
                    else:
                        self.application().view.focus_view("Detail/Clip")
        else:
            self.enc0_button = False
            self._session.set_enabled(True)
    
    # * no implementado
    def _encoder_n8(self, value):
        # * detectar Movimiento Vertical
        # scene_selected = self.song_instance.view.selected_scene
        if value > 0:
            self._update_leds()
    
    # *Boton de knob 9(8), mantenerlo pulsado permite armar el track para grabacion
    # * con shift entra en Modo Clip
    # * si ya esta el Modo Clip en Detail/Clip hace zoom al clip
    # *                         en Detail/DeviceChain activa el device
    def _encoder_n8_button(self, value):
        if value > 0:
            self.enc8_button = True
            
            self._session.set_enabled(False)
            session_tracks = self._session.current_tracks
            visible_session_pads_number = len(session_tracks)
            offset = self._session.track_offset()
            total_v_tracks = self.song_instance.visible_tracks
            while visible_session_pads_number > 0:
                visible_session_pads_number -= 1
                pad_number = visible_session_pads_number
                track_number = offset + pad_number
                pad_track = total_v_tracks[track_number]
                try:
                    if pad_track.can_be_armed:
                        if pad_track.arm:
                            _send_color(self, 112 + pad_number, RED)
                except RuntimeError as e:
                    logger.info(" : Error : " + str(pad_track.name))
                    logger.info(" : Error : " + str(e))
                    continue
            
            
            # * shift, enter Modo Clip
            if self.shift_active:
                self.show_message("Modo Clip activo")
                self.modo_clip_activo = True
                _shift_led(self, True)
                self._device.set_on_off_button(None)
                
                # ! !!!
                Actions(self._transport).focus_onplaying_clip()

            # * Modo Clip
            elif self.modo_clip_activo:
                # * Detail/Clip, nope
                if self.application().view.is_view_visible(u'Detail/Clip'):
                    self._device.set_on_off_button(None)
                    # * Focus on clip loop
                    Actions(self._transport).button_focus_cliploop()
                
                elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                    # if not self.shift_active:
                    self._device.set_on_off_button(self._knob8_button)
                    # * Detail/DeviceChain, activate device
                    Actions(self._transport).button_activate_device()
        else:
            self._device.set_on_off_button(None)
            self.enc8_button = False
            self._session.set_enabled(True)

    

    # * vol send a / set start marker, select device preset
    def _encoder_n5(self, value):
        if self.shift_active or self.modo_clip_activo:
            if TWO_SENDS:
                self._mixer.set_return_volume_controls(None)
            else:
                self._mixer.set_selected_track_send_controls(None)
            
            # * shift
            if self.application().view.is_view_visible(u'Detail/Clip'):
                if value > 0:
                    # * shift, set start marker
                    Actions(self._transport).enc_set_start_marker(value)
            
            elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                self.application().view.focus_view("Detail/DeviceChain")
                if value > 0:
                    # * shift, select device preset
                    self.enc_seldevice_preset(value)
        
        # * normal, volumen de send a
        else:
            if TWO_SENDS:
                self._mixer.set_return_volume_controls(self._return_encoders)
            else:
                self._mixer.set_selected_track_send_controls(self._send_encoders)
    
    def enc_seldevice_preset(self, value):
        presets = None
        actual_preset = None
        appo_device = self.song_instance.appointed_device
        if appo_device.can_have_chains:
            chain_selected = appo_device.view.selected_chain
            chain_devices = chain_selected.devices
            if len(chain_devices) > 0:
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
            total_presets = len(presets) - 1
            if value > 64:
                if actual_preset == 0:
                    actual_preset = total_presets
                else:
                    actual_preset = actual_preset - 1
                appo_device.selected_preset_index = actual_preset
                self.show_message(
                    str(appo_device.name) + " < " + str(actual_preset) + " - " + str(
                        presets[actual_preset]
                    )
                )
            else:
                if actual_preset == total_presets:
                    actual_preset = 0
                else:
                    actual_preset = actual_preset + 1
                appo_device.selected_preset_index = actual_preset
                self.show_message(
                    str(appo_device.name) + " > " + str(actual_preset) + " - " + str(
                        presets[actual_preset]
                    )
                )
    
    # * send a / move loop
    def _encoder_n6(self, value):
        # * shift,
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_selected_track_send_controls(None)
            if value > 0:
                if self.application().view.is_view_visible(u'Detail/Clip'):
                    # * shift, move loop
                    Actions(self._transport).enc_move_loop(value)
        # * normal, envio send a
        else:
            self._mixer.set_selected_track_send_controls(self._send_encoders)
    
    # * pan / track pannig , duplicate-divide loop marker
    def _encoder_n7(self, value):
        # * shift,
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_selected_track_pan_control(None)
            if value > 0:
                if self.application().view.is_view_visible(u'Detail/Clip'):
                    # * shift, duplicate-divide loop marker
                    Actions(self._transport).enc_dupdiv_loop_marker(value)
                if self.application().view.is_view_visible(u'Detail/DeviceChain'):
                    # * shift, track pannig
                    self._mixer.set_selected_track_pan_control(self._pan_encoder)
        # * normal, track pannig
        else:
            self._mixer.set_selected_track_pan_control(self._pan_encoder)
    
    # * vol send b / change indevice
    def _encoder_n13(self, value):
        # * shift,
        if self.shift_active or self.modo_clip_activo:
            if TWO_SENDS:
                self._mixer.set_return_volume_controls(None)
            else:
                self._mixer.set_selected_track_send_controls(None)
            if value > 0:
                if self.application().view.is_view_visible(u'Detail/Clip'):
                    Actions(self._transport).enc_pitch_fine(value)

                elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                    # * shift, change indevice
                    # * al borrar el listener "self.sub_devices" queda congelado
                    track = self.song_instance.view.selected_track
                    if track.view.selected_device_has_listener(self._device_changed):
                        track.view.remove_selected_device_listener(self._device_changed)
                    Actions(self._transport).enc_moveinto_devices(value, self.sub_devices)
        
        # * normal, volumen de send b
        else:
            if TWO_SENDS:
                self._mixer.set_return_volume_controls(self._return_encoders)
            else:
                self._mixer.set_selected_track_send_controls(self._send_encoders)

    # * send b / change device
    def _encoder_n14(self, value):
        # * shift,
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_selected_track_send_controls(None)
            if value > 0:
                if self.application().view.is_view_visible(u'Detail/Clip'):
                    Actions(self._transport).enc_pitch_coarse(value)

                elif self.application().view.is_view_visible(u'Detail/DeviceChain'):
                    # * shift, device change when in device view
                    Actions(self._transport).enc_moveon_topdevice(value)
                    track = self.song_instance.view.selected_track
                    if not track.view.selected_device_has_listener(self._device_changed):
                        track.view.add_selected_device_listener(self._device_changed)
        # * normal, envio send b
        else:
            self._mixer.set_selected_track_send_controls(self._send_encoders)

    # * vol / ( vol / vol )
    def _encoder_n15(self, value):
        # * shift,
        if self.shift_active or self.modo_clip_activo:
            self._mixer.set_selected_track_volume_control(None)
            if value > 0:
                if self.application().view.is_view_visible(u'Detail/Clip'):
                    # * shift, track volumen
                    self._mixer.set_selected_track_volume_control(self._volume_encoder)
                    
                    # Actions(self._transport).enc_set_end_marker(value)
                if self.application().view.is_view_visible(u'Detail/DeviceChain'):
                    # * shift, track volumen
                    self._mixer.set_selected_track_volume_control(self._volume_encoder)
        
        # * normal, track volumen
        else:
            self._mixer.set_selected_track_volume_control(self._volume_encoder)

        # * Controla el device que cambia, si tiene sub devices los mete en una lista
        # * para actuar en el eliminamos el listener en la funcion que queremos utilizar
        # * la lista

    def _device_changed(self):
        track = self.song_instance.view.selected_track
        device = track.view.selected_device
        # logger.info("_device_changed _listener ::::::::::::: " + str(device))
        sub_list = []
        if device.can_have_chains:
            for ch in device.chains:
                for dev in ch.devices:
                    sub_list.append(dev)
        self.sub_devices = sub_list
    
    # ? PADS 1
    def get_session_track(self, pad_id):
        total_v_tracks = self.song_instance.visible_tracks
        offset = self._session.track_offset()
        track_number = offset + pad_id
        # logger.info("_pads_n" + str(pad_id) + " : session track n: " + str(track_number))
        relevant_track = total_v_tracks[track_number]
        # logger.info("_pads_n" + str(pad_id) + " : session track name: " + str(relevant_track.name))
        return relevant_track
    
    def _pads_n0(self, value):
        pad_id = 0
        # logger.info("_pads_n" + str(pad_id) + " : value: " + str(value))
        relevant_track = self.get_session_track(pad_id)
        if value > 0:
            if self.enc8_button and relevant_track.can_be_armed:
                relevant_track.arm = not relevant_track.arm
            if self.enc0_button:
                relevant_track.mute = not relevant_track.mute
    
    def _pads_n1(self, value):
        pad_id = 1
        relevant_track = self.get_session_track(pad_id)
        if value > 0:
            if self.enc8_button and relevant_track.can_be_armed:
                relevant_track.arm = not relevant_track.arm
            if self.enc0_button:
                relevant_track.mute = not relevant_track.mute
    
    def _pads_n2(self, value):
        pad_id = 2
        relevant_track = self.get_session_track(pad_id)
        if value > 0:
            if self.enc8_button and relevant_track.can_be_armed:
                relevant_track.arm = not relevant_track.arm
            if self.enc0_button:
                relevant_track.mute = not relevant_track.mute
    
    def _pads_n3(self, value):
        pad_id = 3
        relevant_track = self.get_session_track(pad_id)
        if value > 0:
            if self.enc8_button and relevant_track.can_be_armed:
                relevant_track.arm = not relevant_track.arm
            if self.enc0_button:
                relevant_track.mute = not relevant_track.mute
    
    def _pads_n4(self, value):
        pad_id = 4
        relevant_track = self.get_session_track(pad_id)
        if value > 0:
            if self.enc8_button and relevant_track.can_be_armed:
                relevant_track.arm = not relevant_track.arm
            if self.enc0_button:
                relevant_track.mute = not relevant_track.mute
    
    def _pads_n5(self, value):
        pad_id = 5
        relevant_track = self.get_session_track(pad_id)
        if value > 0:
            if self.enc8_button and relevant_track.can_be_armed:
                relevant_track.arm = not relevant_track.arm
            if self.enc0_button:
                relevant_track.mute = not relevant_track.mute
    
    def _pads_n6(self, value):
        pad_id = 6
        relevant_track = self.get_session_track(pad_id)
        if value > 0:
            if self.enc8_button and relevant_track.can_be_armed:
                relevant_track.arm = not relevant_track.arm
            if self.enc0_button:
                relevant_track.mute = not relevant_track.mute
    
    def _pads_n7(self, value):
        pad_id = 7
        relevant_track = self.get_session_track(pad_id)
        if value > 0:
            if self.enc8_button and relevant_track.can_be_armed:
                relevant_track.arm = not relevant_track.arm
            if self.enc0_button:
                relevant_track.mute = not relevant_track.mute
    
    # ? PADS 2
    # * n120 - play button / arm track and overdub
    def _pads2_n8(self, value):
        if self.shift_active or self.modo_clip_activo:
            self._transport.set_play_button(None)
            if value > 0:
                # * shift, arm track and overdub
                Actions(self._transport).button_armoverdub()
        else:
            self._transport.set_play_button(self._pads2[8])
            if value > 0:
                # * normal, play pause button
                Actions(self._transport).button_playpause()
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
        self._update_leds()
    
    # TODO: Usar un pad para guardar el estado del loop y recuperarlo despues
    # * n122 - overdub / nope
    def _pads2_n10(self, value):
        # * shift,
        if self.shift_active or self.modo_clip_activo:
            self._transport.set_overdub_button(None)
            if value > 0:
                return
        
        else:
            self._transport.set_overdub_button(self._pads2[10])
            if value > 0:
                # * normal, overdub
                Actions(self._transport).button_overdub()
        self._update_leds()
    
    # * n123 - undo / none
    def _pads2_n11(self, value):
        if self.shift_active or self.modo_clip_activo:
            if value > 0:
                pass
        else:
            if value > 0:
                # * normal, undo
                self.song_instance.undo()
        self._update_leds()
    
    # * n124 - alternate_view detail
    def _pads2_n12(self, value):
        # * shift, alternate_view detail
        if self.shift_active or self.modo_clip_activo:
            if value > 0:
                Actions(self._transport).button_alternate_viewdetail()
                Actions(self._transport).focus_onplaying_clip()
        # * normal, alternate_view detail
        else:
            if value > 0:
                Actions(self._transport).button_alternate_viewdetail()
        self._update_leds()
    
    # *n125 - nope /  quantize
    def _pads2_n13(self, value):
        
        if self.shift_active or self.modo_clip_activo:
            self._transport.set_stop_button(None)
            if self.application().view.is_view_visible(u'Detail/Clip'):
                if value > 0:
                    # * shift, quantize
                    Actions(self._transport).button_quantize_song()
        # * normal,
        else:
            self._update_leds()
        self._update_leds()
    
    # *n126 - new scene / scrub
    def _pads2_n14(self, value):
        if self.shift_active or self.modo_clip_activo:
            if self.application().view.is_view_visible(u'Detail/Clip'):
                # * shift, scrub
                clip = self.song_instance.view.detail_clip
                if clip:
                    if value > 0:
                        if clip in self.scrubbing_clips:
                            clip.stop_scrub()
                            self.scrubbing_clips.remove(clip)
                        else:
                            if clip.is_playing:
                                clip.scrub(clip.playing_position)
                            else:
                                clip.scrub(clip.start_marker)
                            self.scrubbing_clips.append(clip)
        else:
            if value > 0:
                # * normal, new scene from play
                Actions(self._transport).button_newscene_fplay()
        self._update_leds()
    
    # * n127 - play stop scene / play stop clip
    def _pads2_n15(self, value):
        
        if self.shift_active or self.modo_clip_activo:
            if self.application().view.is_view_visible(u'Detail/Clip'):
                # * shift, play stop clip
                Actions(self._transport).button_playstop_clip(value)
        # * normal, play stop scene
        else:
            if self.enc8_button:
                Actions(self._transport).button_playstop_scene(value)
            else:
                Actions(self._transport).button_play_scene(value)
        self._update_leds()
    
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
        dtype = device.type
        logger.info("device type :: " + str(dtype))
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
    