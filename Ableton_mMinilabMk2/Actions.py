from __future__ import absolute_import, print_function, unicode_literals

import logging

logger = logging.getLogger(__name__)
import Live
from .Constants import *

class Actions(object):
    def __init__(self, transport):
        # self._parent = parent
        self._transport = transport
        self.song_instance = self._transport.song()
        self.__moveon_topdevice_cnt = 1
        self.__moveinto_devices_cnt = 1
        self.__seldevice_preset_cnt = 1
        self.__nav_leftright_cnt = 1
        self.__nav_updown_cnt = 1
        self.__move_loop_cnt = 1
        self.__loop_start_cnt = 1
        self.__loop_end_cnt = 1
        self.__start_marker_cnt = 1
        self.__end_marker_cnt = 1
        self.__dupdiv_loop_cnt = 1
        self.__pitch_coarse_cnt = 1
        self.__pitch_fine_cnt = 1
        self.__set_gridquant_cnt = 1
    
    def application(self):
        return Live.Application.get_application()
    
    # * device change
    def enc_moveon_topdevice(self, value):
        # * reduce sensitivity to make it easier to select items
        # * https://github.com/raphaelquast/beatstep
        self.__moveon_topdevice_cnt = (self.__moveon_topdevice_cnt + 1) % 6
        # logger.info("__moveon_topdevice_cnt : " + str(self.__moveon_topdevice_cnt))
        if self.__moveon_topdevice_cnt != 0:
            return
        self.__moveon_topdevice_cnt = 1
        
        track = self.song_instance.view.selected_track
        if track.devices:
            devices_tot = []
            for device in track.devices:
                devices_tot.append(device)
            device_sel = track.view.selected_device
            # * si el Dispositivo esta en un rack, da fallo ya que no esta en la lista
            if not device_sel in devices_tot:
                # * seleccionamos la Cadena (Chain)
                device_sel = device_sel.canonical_parent
                # * seleccionamos el Dispositivo superior
                device_sel = device_sel.canonical_parent
            if device_sel in devices_tot:
                dev_index = devices_tot.index(device_sel)
                if value > 64:
                    if not dev_index == 0:
                        prev_device = devices_tot[dev_index - 1]
                    else:
                        prev_device = devices_tot[dev_index]
                    self.song_instance.view.select_device(prev_device, True)
                    self.device_collapsed(device_sel, prev_device, IN_DEVICE_VIEW_COLLAPSED)
                    
                
                else:
                    if dev_index + 1 < len(devices_tot):
                        next_device = devices_tot[dev_index + 1]
                        self.song_instance.view.select_device(next_device, True)
                        self.device_collapsed(device_sel, next_device, IN_DEVICE_VIEW_COLLAPSED)
                        

    def enc_moveinto_devices(self, value, selecteddevice, sub_devices):
        self.__moveinto_devices_cnt = (self.__moveinto_devices_cnt + 1) % 6
        # logger.info("__moveinto_devices_cnt : " + str(self.__moveinto_devices_cnt))
        if self.__moveinto_devices_cnt != 0:
            return
        self.__moveinto_devices_cnt = 1
        device_list = []
        if not selecteddevice:
            return
        if selecteddevice.can_have_drum_pads:
            device_list = self.get_devicetype_list(sub_devices, "OriginalSimpler")
        
        # * no actua si solo tiene un device
        elif len(sub_devices) > 1:
            device_list = self.get_device_list(sub_devices)
            # logger.info("__moveinto_devices : " + str(device_list))
        if len(device_list) == 0:
            return
        track = self.song_instance.view.selected_track
        device_sel = track.view.selected_device
        if device_sel in device_list:
            dev_index = device_list.index(device_sel)
        else:
            dev_index = 0
        if value > 64:
            if not dev_index == 0:
                prev_device = device_list[dev_index - 1]
            else:
                prev_device = device_list[dev_index]
            self.song_instance.view.select_device(prev_device, True)
            self.song_instance.appointed_device = prev_device
            # self.device_collapsed(device_sel, prev_device, True, "instrument")
            self.device_collapsed(device_sel, prev_device, True)
        
        else:
            if dev_index + 1 < len(device_list):
                next_device = device_list[dev_index + 1]
                self.song_instance.view.select_device(next_device, True)
                self.song_instance.appointed_device = next_device
                # self.device_collapsed(device_sel, next_device, True, "instrument")
                self.device_collapsed(device_sel, next_device, True)
    
    def device_collapsed(self, device_sel, prev_or_next_device, device_collapsed=False, device_excluded=None):
        if device_sel is not None:
            # logger.info(" device to collapse type: " + str(device_sel.type) + "  name : " + str(device_sel.name))
            device_sel.view.is_collapsed = device_collapsed
            if device_sel.can_have_chains:
                device_sel.view.is_collapsed = False
            if device_excluded is not None:
                if str(device_sel.type) == device_excluded:
                    device_sel.view.is_collapsed = False
        
        if prev_or_next_device is not None:
            prev_or_next_device.view.is_collapsed = False
    
    # * Navigation Left Right
    def _nav_view_leftright(self, value, visible_view):
        self.__nav_leftright_cnt = (self.__nav_leftright_cnt + 1) % 6
        # logger.info("__nav_leftright_cnt : " + str(self.__nav_leftright_cnt))
        if self.__nav_leftright_cnt != 0:
            return
        self.__nav_leftright_cnt = 1
        if value > 64:
            self.application().view.scroll_view(self.application().view.NavDirection.left, visible_view, False)
        else:
            self.application().view.scroll_view(self.application().view.NavDirection.right, visible_view, False)
        
        # * Navigation Up Down
    
    def _nav_view_updown(self, value, visible_view):
        self.__nav_updown_cnt = (self.__nav_updown_cnt + 1) % 6
        # logger.info("__nav_updown_cnt : " + str(self.__nav_updown_cnt))
        if self.__nav_updown_cnt != 0:
            return
        self.__nav_updown_cnt = 1
        if value > 20:
            self.application().view.scroll_view(self.application().view.NavDirection.up, visible_view, False)
        else:
            self.application().view.scroll_view(self.application().view.NavDirection.down, visible_view, False)
    
    # * move loop position
    def enc_move_loop(self, value):
        self.__move_loop_cnt = (self.__move_loop_cnt + 1) % 6
        # logger.info("__move_loop_cnt : " + str(self.__move_loop_cnt))
        if self.__move_loop_cnt != 0:
            return
        self.__move_loop_cnt = 1
        
        clip = self.song_instance.view.detail_clip
        if clip:
            p_advance = self.move_quantity(clip)
            position = clip.position
            if value > 64:
                clip.position = position - p_advance
            else:
                clip.position = position + p_advance
            clip.view.show_loop()
    
    # * change loop start
    def enc_set_loop_start(self, value):
        self.__loop_start_cnt = (self.__loop_start_cnt + 1) % 6
        # logger.info("__loop_start_cnt : " + str(self.__loop_start_cnt))
        if self.__loop_start_cnt != 0:
            return
        self.__loop_start_cnt = 1
        
        clip = self.song_instance.view.detail_clip
        if clip:
            start = clip.loop_start
            end = clip.loop_end
            l_advance = self.move_quantity(clip)
            if start < end:
                if value > 64:
                    clip.loop_start = start - l_advance
                else:
                    if start + l_advance < end:
                        clip.loop_start = start + l_advance
            clip.view.show_loop()
    
    # * change loop end
    def enc_set_loop_end(self, value):
        self.__loop_end_cnt = (self.__loop_end_cnt + 1) % 6
        # logger.info("__loop_end_cnt : " + str(self.__loop_end_cnt))
        if self.__loop_end_cnt != 0:
            return
        self.__loop_end_cnt = 1
        
        clip = self.song_instance.view.detail_clip
        if clip:
            start = clip.loop_start
            end = clip.loop_end
            l_advance = self.move_quantity(clip)
            if value > 64:
                l_end = end - l_advance
                if start < l_end:
                    clip.loop_end = l_end
            else:
                clip.loop_end = end + l_advance
            clip.view.show_loop()
    
    # * set start marker
    def enc_set_start_marker(self, value):
        self.__start_marker_cnt = (self.__start_marker_cnt + 1) % 6
        # logger.info("__start_marker_cnt : " + str(self.__start_marker_cnt))
        if self.__start_marker_cnt != 0:
            return
        self.__start_marker_cnt = 1
        
        clip = self.song_instance.view.detail_clip
        if clip:
            s_start = round(clip.start_marker, 2)
            s_marker = clip.end_marker
            s_advance = self.move_quantity(clip)
            if value > 64:
                clip.start_marker = s_start - s_advance
            else:
                if s_start + s_advance < s_marker:
                    clip.start_marker = s_start + s_advance
            clip.view.show_loop()
    
    # * set end marker
    def enc_set_end_marker(self, value):
        self.__end_marker_cnt = (self.__end_marker_cnt + 1) % 6
        # logger.info("__end_marker_cnt : " + str(self.__end_marker_cnt))
        if self.__end_marker_cnt != 0:
            return
        self.__end_marker_cnt = 1
        
        clip = self.song_instance.view.detail_clip
        if clip:
            e_marker = clip.end_marker
            e_advance = self.move_quantity(clip)
            if value > 64:
                if e_marker - e_advance > clip.start_marker:
                    clip.end_marker = e_marker - e_advance
            else:
                clip.end_marker = e_marker + e_advance
            clip.view.show_loop()

    def get_clip_inbeats(self, clip):
        # Clip in beats/seconds (unit depends on warping)
        if clip.is_audio_clip and not clip.warping:
            return None, None, None
        clipbeats_length = clip.length
        beats_loopend = clip.loop_end
        beats_loopstart = clip.loop_start
        return clipbeats_length, beats_loopend, beats_loopstart
    
    # * duplicate-divide loop marker
    def enc_dupdiv_loop_marker(self, value):
        self.__dupdiv_loop_cnt = (self.__dupdiv_loop_cnt + 1) % 6
        # logger.info("__dupdiv_loop_cnt : " + str(self.__dupdiv_loop_cnt))
        if self.__dupdiv_loop_cnt != 0:
            return
        self.__dupdiv_loop_cnt = 1
        
        clip = self.song_instance.view.detail_clip
        if clip:
            if clip.is_audio_clip and not clip.warping:
                return
            loop_end = clip.loop_end
            loop_start = clip.loop_start
            loop_length = loop_end - loop_start
            if value > 64:
                loop_length = loop_length / 2
            else:
                loop_length = loop_length * 2

            if loop_length >= LOOP_MAX_BEATS:
                loop_length = LOOP_MAX_BEATS
            if loop_length <= LOOP_MIN_BEATS:
                loop_length = LOOP_MIN_BEATS
            # clip_length = clip.length
            # logger.info("3. loop length: " + str(loop_length) + " - clip length: " + str(clip_length))
            # logger.info("4. loop end: " + str(loop_end) + " - loop start: " + str(loop_start))

            clip.loop_end = clip.loop_start + loop_length
            
            clip.view.show_loop()

    def enc_pitch_coarse(self, value):
        self.__pitch_coarse_cnt = (self.__pitch_coarse_cnt + 1) % 4
        # logger.info("__dupdiv_loop_cnt : " + str(self.__dupdiv_loop_cnt))
        if self.__pitch_coarse_cnt != 0:
            return
        self.__pitch_coarse_cnt = 1
        
        clip = self.song_instance.view.detail_clip
        if not clip.is_audio_clip:
            return
        pitch = clip.pitch_coarse
        if value > 64:
            pitch = pitch - 1
        else:
            pitch = pitch + 1
        if pitch > -49:
            if pitch < 49:
                clip.pitch_coarse = pitch

    def enc_pitch_fine(self, value):
        self.__pitch_fine_cnt = (self.__pitch_fine_cnt + 1) % 4
        # logger.info("__pitch_fine_cnt : " + str(self.__pitch_fine_cnt))
        if self.__pitch_fine_cnt != 0:
            return
        self.__pitch_fine_cnt = 1
        
        clip = self.song_instance.view.detail_clip
        if not clip.is_audio_clip:
            return
        pitch = clip.pitch_fine
        if value > 64:
            pitch = pitch - 1
        else:
            pitch = pitch + 1
        if pitch > -500:
            if pitch < 500:
                clip.pitch_fine = pitch
    
    def button_alternate_viewdetail(self):
        if not self.application().view.is_view_visible(u'Detail'):
            self.application().view.focus_view("Detail")
            self.application().view.zoom_view(1, "Detail", True)
        if not self.application().view.is_view_visible(u'Detail/DeviceChain'):
            self.application().view.focus_view("Detail/DeviceChain")
            return "Detail/DeviceChain"
        else:
            self.application().view.focus_view("Detail/Clip")
            return "Detail/Clip"
    
    # * hide / show detail
    def button_hide_viewdetail(self):
        if self.application().view.is_view_visible(u'Detail'):
            self.application().view.hide_view("Detail")
        else:
            self.application().view.focus_view("Detail")
            self.application().view.zoom_view(1, "Detail", True)
    
    def button_show_sessionview(self):
        if self.application().view.is_view_visible(u'Arranger'):
            self.application().view.focus_view("Session")
    
    def button_track_fold(self):
        track = self.song_instance.view.selected_track
        if track.is_foldable:
            self.button_show_sessionview()
            if track.fold_state:
                track.fold_state = False
            else:
                track.fold_state = True
            return track.is_foldable
    
    def button_focus_cliploop(self):
        clip = self.song_instance.view.detail_clip
        if clip:
            self.application().view.focus_view("Detail/Clip")
            logger.info("mMiniLabMk2 = Detail/Clip: " + str(clip.name))
            clip.view.show_loop()

    def focus_onplaying_clip(self):
        track = self.song_instance.view.selected_track
        slot_idx = track.playing_slot_index
        if slot_idx != -1:
            # logger.info(" : slot : " + str(slot_idx))
            slots = list(track.clip_slots)
            playing_slot = slots[slot_idx]
            if playing_slot.has_clip:
                clip = playing_slot.clip
                # highlighted_clip_slot
                self.song_instance.view.detail_clip = clip
                if SESSION_FOLLOWS_CLIP:
                    self.song_instance.view.highlighted_clip_slot = playing_slot

    
    
    def button_activate_device(self):
        track = self.song_instance.view.selected_track
        if track.devices:
            appo_device = self.song_instance.appointed_device
            self.song_instance.view.select_device(appo_device, True)
            # appo_device.view.is_collapsed = False
            # if appo_device.can_have_chains:
            #     logger.info("DEVICE tiene macros : " + str(appo_device.has_macro_mappings))
            #     logger.info("DEVICE chains number : " + str(len(appo_device.chains)))
            
            if appo_device.is_active:
                appo_device.is_enabled = False
            else:
                appo_device.is_enabled = True
    
    def button_armoverdub(self):
        current_track = self.song_instance.view.selected_track
        if current_track.arm:
            current_track.arm = False
            self.song_instance.overdub = False
        else:
            current_track.arm = True
            self.song_instance.overdub = True
        # logger.info(" Button :: button_armoverdub")
    
    def button_playpause(self):
        if self.song_instance.is_playing:
            self.song_instance.stop_playing()
        else:
            if self.song_instance.current_song_time > 0:
                self.song_instance.continue_playing()
            self.song_instance.start_playing()
        # logger.info(" Button :: button_playpause")
    
    def button_overdub(self):
        if self.song_instance.overdub:
            self.song_instance.overdub = False
        else:
            self.song_instance.overdub = True
    
    def button_quantize_song(self):
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
        if q_actual in QUANTIZATIONS:
            q_actual_index = QUANTIZATIONS.index(q_actual)
            q_actual_index = q_actual_index + 1
            if q_actual_index > 13:
                q_actual_index = 0
            self.song_instance.clip_trigger_quantization = QUANTIZATIONS[q_actual_index]
    
    def button_scrub(self, value):
        clip = self.song_instance.view.detail_clip
        if clip:
            if value > 0:
                if clip.is_playing:
                    clip.scrub(clip.playing_position)
                else:
                    clip.scrub(clip.start_marker)
    
    def button_playstop_clip(self, value):
        clip = self.song_instance.view.detail_clip
        if clip:
            if value > 0:
                if clip.is_playing:
                    clip.stop()
                else:
                    clipslot = self.song_instance.view.highlighted_clip_slot
                    clipslot.fire(force_legato=True)
    
    def button_aproximate_loop(self, value):
        clip = self.song_instance.view.detail_clip
        if clip:  # and clip.looping:
            
            # clipbeats_length, beats_loopend, beats_loopstart = self.get_clip_inbeats(clip)
            # if clipbeats_length != None:
            if clip.is_audio_clip and not clip.warping:
                return
            if value > 0:
                loop_end = clip.loop_end
                loop_start = clip.loop_start
                loop_length = loop_end - loop_start
                if loop_length < LOOP_MIN_BEATS:
                    loop_length = LOOP_MIN_BEATS
                if loop_length > LOOP_MAX_BEATS:
                    loop_length = LOOP_MAX_BEATS
                if LOOP_MAX_BEATS >= loop_length >= LOOP_MIN_BEATS:
                    if loop_length < 1:
                        loop_length = round(loop_length, 2)
                    else:
                        loop_length = round(loop_length)
                clip.loop_end = clip.loop_start + loop_length
                clip.view.show_loop()
    
    def button_consolidate_loop(self, value):
        clip = self.song_instance.view.detail_clip
        if clip and clip.looping:
            if value > 0:
                loop_length = clip.loop_end - clip.loop_start
                if loop_length < 1:
                    loop_length = round(loop_length, 2)
                else:
                    loop_length = round(loop_length)
                clip.loop_end = clip.loop_start + loop_length
                clip.view.show_loop()
    
    def button_newscene_fplay(self):
        self.song_instance.capture_and_insert_scene()
    
    def button_seton_loop(self, value):
        clip = self.song_instance.view.detail_clip
        if clip:
            if clip.is_audio_clip:
                if not clip.warping:
                    clip.warp_mode
            if value > 0:
                if clip.looping:
                    clip.looping = False
                else:
                    clip.looping = True

    # * ls nueva escena seleccionada reemplaza a la anterior,
    # * si es la misma escena los clip se alternan
    def button_play_scene(self, value):
        scene_selected = self.song_instance.view.selected_scene
        if value > 0:
            if scene_selected.is_empty:
                self.song_instance.stop_all_clips(Quantized=True)
            else:
                scene_selected.fire_as_selected(force_legato=True)
    
    # * ls nueva escena seleccionada se suma y reemplaza a los clip de la anterior escena
    def button_playstop_scene(self, value):
        scene_selected = self.song_instance.view.selected_scene
        if value > 0:
            if scene_selected.is_empty:
                self.song_instance.stop_all_clips(Quantized=True)
            else:
                for clipslt in scene_selected.clip_slots:
                    if clipslt.clip:
                        if not clipslt.is_playing:
                            clipslt.fire(force_legato=True)
    
    
    
    def enc_set_gridquant_value(self, value):
        self.__set_gridquant_cnt = (self.__set_gridquant_cnt + 1) % 6
        # logger.info("__set_gridquant_cnt : " + str(self.__set_gridquant_cnt))
        if self.__set_gridquant_cnt != 0:
            return
        self.__set_gridquant_cnt = 1
        
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
            clip.view.show_loop()
    
    def move_quantity(self, clip):
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
        GRID_QUANTIZATION_NUMBERS = [0, 0.03125, 0.0625, 0.125, 0.25, 0.5, 1, 2, 4, 8]
        q_actual_index = GRID_QUANTIZATION_LIST.index(current_gridquantization)
        valor = GRID_QUANTIZATION_NUMBERS[q_actual_index]
        return valor
    
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
        except AttributeError as e:
            logger.info("device presets :: " + str(e))
        try:
            bank_count = device.get_bank_count()
            logger.info("device bank_count :: " + str(bank_count))
        except AttributeError as e:
            logger.info("device bank_count :: " + str(e))
    
    def get_device_list(self, container):
        # add each device in order. if device is a rack, process each chain recursively
        # don't add racks that are not showing devices.
        # called this way: device_list = self.get_device_list(current_track.devices)
        # (The Rabbits) https://forum.ableton.com/viewtopic.php?p=1788986#p1788986
        lst = []
        for dev in container:
            lst.append(dev)
            try:
                if dev.can_have_chains:  # is a rack and it's open
                    if dev.view.is_showing_chain_devices:
                        for ch in dev.chains:
                            lst += self.get_device_list(ch.devices)
            except:
                continue
        return lst

    def get_devicetype_list(self, container, devclassnm=None):
        lst = []
        for dev in container:
            # logger.info("__moveinto_devices : " + str(dev.class_name))
            if devclassnm != None:
                if str(dev.class_name) == devclassnm:
                    # self.device_properties(dev)
                    lst.append(dev)
                    try:
                        if dev.can_have_chains:  # is a rack and it's open
                            if dev.view.is_showing_chain_devices:
                                for ch in dev.chains:
                                    lst += self.get_device_list(ch.devices)
                    except:
                        continue
        return lst

    def _enc_simpler_fadein(self, dev, value):
        # * shift, simpler fade in/attack
        params = list(dev.parameters)
        fade_in = None
        # * not classic mode
        if dev.playback_mode != 0:
            for p in params:
                if str(p.original_name) == "Fade In":
                    if p.is_enabled:
                        fade_in = p
        # * 1-shot or slice mode
        else:
            for p in params:
                if str(p.original_name) == "Ve Attack":
                    if p.is_enabled:
                        fade_in = p
        if fade_in:
            if value > 64:
                fade_in_value = fade_in.value - 0.001
            else:
                fade_in_value = fade_in.value + 0.001
            if fade_in_value >= fade_in.min:
                if fade_in_value <= fade_in.max:
                    fade_in.value = fade_in_value

    def _enc_simpler_fadeout(self, dev, value):
        params = list(dev.parameters)
        fade_out = None
        # * not classic mode
        if dev.playback_mode != 0:
            for p in params:
                if str(p.original_name) == "Fade Out":
                    if p.is_enabled:
                        fade_out = p
        # * 1-shot or slice mode
        else:
            for p in params:
                if str(p.original_name) == "Ve Release":
                    if p.is_enabled:
                        fade_out = p
        if fade_out:
            if value > 64:
                fade_out_value = fade_out.value - 0.001
            else:
                fade_out_value = fade_out.value + 0.001
            if fade_out_value >= fade_out.min:
                if fade_out_value <= fade_out.max:
                    fade_out.value = fade_out_value

    def _enc_seldevice_preset(self, value):
        self.__seldevice_preset_cnt = (self.__seldevice_preset_cnt + 1) % 6
        # logger.info("__seldevice_preset_cnt : " + str(self.__seldevice_preset_cnt))
        if self.__seldevice_preset_cnt != 0:
            return
        self.__seldevice_preset_cnt = 1
    
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
                message = str(appo_device.name) + " < " + str(actual_preset) + " - " + str(presets[actual_preset])
                return message
                # self.show_message(
                #     str(appo_device.name) + " < " + str(actual_preset) + " - " + str(
                #         presets[actual_preset]
                #     )
                # )
            else:
                if actual_preset == total_presets:
                    actual_preset = 0
                else:
                    actual_preset = actual_preset + 1
                appo_device.selected_preset_index = actual_preset
                # self.show_message(
                #     str(appo_device.name) + " > " + str(actual_preset) + " - " + str(
                #         presets[actual_preset]
                #     )
                # )
                message = str(appo_device.name) + " > " + str(actual_preset) + " - " + str(presets[actual_preset])
                return message
