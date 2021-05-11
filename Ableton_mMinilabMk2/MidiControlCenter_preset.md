## Anatomia de un preset de Midi Control Center:
	"device": "MiniLab mkII",
Explicacion:

    112 a 127 son los pads
    1 a 14 son los knobs
    _1 es el CHANNEL (empieza en 1 noen 0, por lo que habrá que restarle 1)
    _3 es la identificación del hardware (encoder_msg_ids (36 + idx))
    
    
    10_1 = HARDWARE_ENCODER_IDS
    112_1 = HARDWARE_BUTTON_IDS
    _1, _2, ... = 
    
    "80_3": 64, sustain
    
    
