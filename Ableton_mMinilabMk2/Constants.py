# * Numero maximo y minimo de subdivisiones de loop
LOOP_MIN_BEATS = 0.25
LOOP_MAX_BEATS = 32
# * Al cambiar de Device, se deben collapsar los no seleccionados?
IN_DEVICE_VIEW_COLLAPSED = False
# * Al seleccionar el modo clip, el indicador de sesion
# * debe enfocarse en el clip reproducido?
SESSION_FOLLOWS_CLIP = True
# * Led colors
BLACK = 0  # - apagado
RED = 1  # - rojo
GREEN = 4  # - verde
YELLOW = 5  # - amarillo
BLUE = 16  # - azul
MAGENTA = 17  # - magenta
CYAN = 20  # - cyan
WHITE = 127  # - blanco
# * Used led colors
EMPTY_VALUE = BLACK  # - apagado
SELECTED_VALUE = WHITE  # - blanco

STOPPED_VALUE = YELLOW  # - yellow

STARTED_VALUE = GREEN  # - green
TRIGGERED_TO_PLAY_VALUE = GREEN  # - green

RECORDING_VALUE = RED  # - red
TRIGGERED_TO_RECORD_VALUE = MAGENTA  # - magenta
TRACK_ARMED_VALUE = MAGENTA  # - magenta

TRACK_MUTED_VALUE = CYAN  # - cyan
TRACK_MUTED_STARTED_VALUE = BLUE  # - azul
TRACK_MUTED_STOPPED_VALUE = BLUE  # - azul
TRACK_ARMED_MUTED_VALUE = BLUE  # - azul
TRACK_MUTED_RECORDING_VALUE = BLUE  # - azul

BLINK_PERIOD = 0.1
