## Apuntes
- En modo clip, vista device, cambiar presets con pads
  
  
- modo normal pads2 - pad5 
    ~~cambiar entre clip- device~~
el cambio tiene que ser en cualquier circunstancia al igual que
  modo normal vista device shift + knob9 activar desactivar device

- select subdevice si tien parametros enlazados tiene que abrirlos
- Hacer que pueda elegir a que device del rack le cambio los parametros
- si es un drum rack, activar drum pads



- Quizas poner anterior/siguiente escena en modo transporte normal
    - ~~En modo sesion pantalla de transporte el play escena no debe parar la escena, debe reiniciarla~~

- ~~¿Hacer fija la rejilla del clip? Es demasiado dificil ajustar un loop en el clip~~
- ~~Buscar la forma de mutear / solo / arm en modo sesion~~

- ~~permitir elegir entre dos o cuatro envios~~
- BLINK
  
`_D:\Documentos\Arturia Minilab MK2 Ableton control\AbletonLive10.1_MIDIRemoteScripts-master\ableton\v2\control_surface\control_surface.py`

`def schedule_message(self, delay_in_ticks, callback, parameter = None):_`

- ~~mensajes cuando los pads hagan algo~~

  # TODO: ampliar esto
        # reduce sensitivity to make it easier to select items
        # https://raphaelquast.github.io/beatstep/
        self.__enc_moveon_topdevice_cnt = (self.__enc_moveon_topdevice_cnt + 1) % 3
        logger.info(" :enc_moveon_topdevice: " +str(self.__enc_moveon_topdevice_cnt))
        if self.__enc_moveon_topdevice_cnt != 0:
            return
        self.__enc_moveon_topdevice_cnt = 1
        logger.info(" :enc_moveon_topdevice: ")



___
###Urge


