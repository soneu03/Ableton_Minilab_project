## Ableton mMimiLabMk2

>*Atención, script altamente experimental, 
no me hago responsable de los posibles daños que pueda causar su uso.*

#### Descripción 
Script de python personalizado de conexión MIDI entre el teclado hardware Arturia Minilab MKII
y el software de audio Ableton Live, también conocido como Ableton script.

#### Intro y explicación
Este proyecto personal está desarrollado en un par de meses y mi conocimiento, por lo menos al 
principio, era casi nulo de python, y totalmente nulo de Ableton script.

Atención, si eres programador y miras el código seguro que ves formas no ortodoxas de usar python ;)
No soy programador y recién estoy aprendiendo python, seguramente alguien con conocimiento podría
agilizar el código, si tu eres ese alguien adelante, te animo a hacerlo, personalmente mi objetivo era aumentar la
funcionalidad del teclado, que fui adaptando y modificando poco a poco, así que te animo a hacerlo para adaptarlo a tus necesidades.

La mayoría del código es un copy paste de varios proyectos encontrados en la web, por lo que si miras 
el código puede que reconozcas alguna parte, si es así, gracias. En ningún caso me pretendo apropiar del trabajo ajeno y siempre que pueda te pondré en los créditos.
La verdad es que después de dos meses es difícil saber de donde cogí el código.

Dicho esto, a mí me funciona y está adaptado a mi modo de trabajo con Ableton (por ahora).



### Funcionamiento 

*El funcionamiento es muy modificable, yo hago uso de la tecla SHIFT para añadir un "modo de funcionamiento", el ModoClip. Pero *en teoría* se puede
usar cualquier pad para que actúe de modificador.*

El funcionamiento en líneas generales hace uso de las dos líneas de pads, así como de la tecla SHIFT.
Como me interesaba el funcionamiento de modo session que viene por defecto en el script original de 
Arturia, lo decidí mantener, pero solo en una línea de pads (considero dos líneas, la 1, que 
corresponderían a los pads del 1 al 8, y la 2, que serían los pads del 9 al 16 cuando la tecla de cambio de pads está activada).
Pero no me interesaba la línea 2 (pads 9-16) en el funcionamiento original.

- _PADS_1 = 1, 2, 3, 4, 5, 6, 7, 8_ 
  (Controlan las pistas en modo Sesion)
  

- _PADS_2 = 9, 10, 11, 12, 13, 14, 15, 16_
  
Ahora, los pads 9-16 quedan así:
 ######_Modo Normal_:

    Pad_9 = Global Play;
    Pad_10: Global Stop; 
    Pad_11 = Overdub; 
    Pad_12 = Undo; 
    Pad_13 = Cambiar la vista de detalle entre Clip y Devices;
    Pad_14 = Sin asignación;
    Pad_15 = Nueva escena a partir de lo reproducido, si no hay nada reproduciendo crea una escena en blanco;
    Pad_16 = Play / Stop escena

######_Modo Clip_:

    Pad_9 = Overdub;
    Pad_10: Undo; 
    Pad_11 = Sin asignación; 
    Pad_12 = Sin asignación; 
    Pad_13 = Cambiar la vista de detalle entre Clip y Devices;
    Pad_14 = Cambio de Cuantización Global;
    Pad_15 = Srub / Continue (stop Scrub) Clip;
    Pad_16 = Play / Pause Clip;

###Modo Clip
        Para entrar en modo Clip mantener pulsado _SHIFT_ y presionar el _Knob_ 9




### Controles rotatorios

##### Knob 1:
Permite desplazarse entre pistas, si lo mantenemos pulsado podemos ver (y activar / desactivar) las pistas que
están muteadas (_solo PADS_1_). Si la pista es un grupo podemos abrirlo y cerrarlo pulsando _shift_ y presionando;
en caso contrario, cambia de vista entre Device y Clip.

##### Knob 9:
Permite desplazarse entre sesiones (verticalmente). Si lo mantenemos pulsado podemos ver y activar / desactivar
 las pistas que están armadas y armarlas (_solo PADS_1_).

##### Knobs 2, 3, 4, 5 y 10, 11, 12 y 13:
Siempre controlan los parámetros de los devices, recomiendo hacer grupos con los devices a usar, ya sean plugins o
instrumentos, así será más ágil la modificación de los parámetros. Interesante la página 
[“The Blue Hand” for Instant Mapping in Ableton Live](https://performodule.com/2015/08/09/the-blue-hand-for-instant-mapping-in-ableton-live/).

##### Knob 6, 7, 14 y 15:
- ######_Modo Normal_:
      Knob 6:  
      Volumen de envío A
    
      Knob 7:
      Volumen de retorno A. Se puede cambiar en las opciones como Volumen de envío B
    
      Knob 14:
      Volumen de envío B. Se puede cambiar en las opciones como Volumen de envío C
    
      Knob 15:
      Volumen de retorno B. Se puede cambiar en las opciones como Volumen de envío D
    
      Knob 8:
      Paneo de pista

- ######_Modo Clip_ (vista Device):
      Knob 6:
      Si el Device tiene presets, cambia entre estos. Si el Device es un Sampler actúa sobre el
      ataque (Attack)
    
      Knob 7:
      Si el Device es un Sampler actúa sobre el Release
    
      Knob 14:
      Seleccionar Device *en* Rack
    
      Knob 15:
      Seleccionar Device o Rack
    
      Knob 8:
      Paneo de pista

- ######_Modo Clip_ (vista Clip):
      Knob 6:
      Mueve el marcador de inicio del clip
    
      Knob 7:
      Mueve el Loop entero (loops audio y MIDI)
    
      Knob 14:
      Detune el Loop (loops audio)
    
      Knob 15:
      Transpone el Loop (loops audio)
    
      Knob 8:
      Duplica / divide en 2 el Loop


##### Knob 16:
Siempre cambia el Volumen de pista


###Instalación
Para Ableton Live 10
En Windows 10 copia toda la carpeta en
\ProgramData\Ableton\Live x.x\Resources\MIDI Remote Scripts\
Selecciona el script _Ableton mMinilabMk2_ en las opciones MIDI de Live.
Por supuesto, conecta el MiniLab y selecciona el banco 8.


###### Bugs, bugs
El principal bug tiene que ver con el programa MIDI CONTROL CENTER de Arturia, harían falta varias pruebas pero diría que al
guardar la plantilla de el progama 8, el de Ableton, no guarda todos los ajustes como debería (o yo no entiendo
bien como funciona el sistema),ya que se me cambiaron varias veces el canal de los _encoders_, por lo que tube de cambiar el canal
varias veces, es como si no guardara bien la plantilla. De hecho los _encoders_ 0 y 8 (o 1 y 9) tienen un modo de funcionamiento
con la tecla shift pulsada de fábrica pero no encuentro el canal, creo que usa el id 7 pero en dos canales distintos.
Como no necesito otra capa de complejidad más, por ahora así se queda.

Mi plantilla de MCC es esta:

_Ableton_mMinilabMk2.minilabmk2_

Pero no garantizo que no haya que cambiar el canal en el archivo mMiniLabMk2.py, si no te funciona cambia el canal (de 0 a 16)
y carga de nuevo Ableton con _ctrl + N_.


```# ?                                                                plugin preset   move loop      pan
# ?   h.scroll        |----------  device controls ---------|  loop start/attack   release    dup-div loop
#     ((+))        (( ))        (( ))        (( ))        (( ))        (( ))        (( ))        (( ))
#     [ 1 ]        [ 2 ]        [ 3 ]        [ 4 ]        [ 5 ]        [ 6 ]        [ 7 ]        [ 8 ]
#       0            1            2            3            4            5            6            7
# !   h.scroll       |----------  device controls ---------|         send A   send B/vol send B    pan
# *  + mute track
#                                                                                     |---track----|
# *  + arm track
# !   v.scroll      |----------  device controls ----------|      send B/send C  vol send B/send D   volumen
#     ((+))        (( ))        (( ))        (( ))        (( ))        (( ))        (( ))        (( ))
#     [ 9 ]       [ 10 ]       [ 11 ]       [ 12 ]       [ 13 ]       [ 14 ]       [ 15 ]       [ 16 ]
#       8           9            10           11           12           13           14           15
# ?   v.scroll      |----------  device controls ---------|     select device  select into device   volumen
# ? + [Clip Mode]

# ? Clip Mode
# ?      |--------------------------------------scene clip controls---------------------------------------|
# !      |--------------------------------------scene clip controls---------------------------------------|
#    [  1  ]       [  2  ]       [  3  ]       [  4  ]       [  5  ]       [  6  ]       [  7  ]       [  8  ]
#       0             1             2             3             4             5             6             7

# !  global play   g. stop      g. overdub       undo                                   new scene     play scene
#    [  9  ]       [  10 ]       [  11 ]       [  12 ]       [  13 ]       [  14 ]       [  15 ]       [  16 ]
#       8             9             10            11            12            13            14            15
# ?  arm & overdub    undo                                 change view     g. quant       scrub      play/stop```
