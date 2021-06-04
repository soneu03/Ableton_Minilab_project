## Ableton mMimiLabMk2

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
>*En realidad todo empezó porque por defecto en un pad que estaba reproduciendo en la sesión 
> no había forma de pararlo (sí la hay y es tan sencillo como cambiar en las preferencias de 
> Ableton el modo de lanzamiento de clips a TRIGGER, si lo supiera antes quizás no empezaría 
> este proyecto). Recomendable poner el modo de lanzamiento de clips por defecto en Toggle,
en Preferencias > Lanzamiento > Modo Lanzar por defecto, asi se consigue que
los clips en modo sesión se puedan parar.*

###### Bugs, bugs
El principal bug tiene que ver con el programa MIDI CONTROL CENTER de Arturia, harían falta varias pruebas pero diría que al 
guardar la plantilla de el progama 8, el de Ableton, no guarda todos los ajustes como debería (o yo no entiendo
bien como funciona el sistema),ya que se me cambiaron varias veces el canal de los _encoders_, por lo que tube de cambiar el canal 
varias veces, es como si no guardara bien la plantilla. De hecho los _encoders_ 0 y 8 (o 1 y 9) tienen un modo de funcionamiento
con la tecla shift pulsada de fábrica pero no encuentro el canal, de hecho creo que usa el id 7 pero en dos canales distintos.
Como no necesito otra capa de complejidad más, por ahora así se queda.
Mi plantilla de MCC es esta:
TODO
Pero no garantizo que no haya que cambiar el canal en el archivo mMiniLabMk2.py, si no te funciona cambia el canal (de 0 a 16)
y carga de nuevo Ableton con _ctrl + N_.

### Funcionamiento 

*El funcionamiento es muy modificable, yo hago uso de la tecla SHIFT para añadir un "modo de funcionamiento", el ModoClip. Pero *en teoría* se puede
usar cualquier pad para que actúe de modificador.*

El funcionamiento en líneas generales hace uso de las dos líneas de pads, así como de la tecla SHIFT.
Como me interesaba el funcionamiento de modo session que viene por defecto en el script original de 
Arturia, lo decidí mantener, pero solo en una línea de pads (considero dos líneas, la 1, que 
corresponderían a los pads del 1 al 8, y la 2, que serían los pads del 9 al 16 cuando la tecla de cambio de pads está activada).
Pero no me interesaba la línea 2 (pads 9-16) en el funcionamiento original.

- _PADS_1 = 1, 2, 3, 4, 5, 6, 7, 8_
- _PADS_2 = 9, 10, 11, 12, 13, 14, 15, 16_

Ahora, los pads 9-16 quedan así:

    Pad_9 = Global Play;
    Pad_10: Global Stop; 
    Pad_11 = Overdub; 
    Pad_12 = Undo; 
    Pad_13 = Cambiar la vista de detalle entre Clip y Devices
    Pad_14 = Sin asignación
    Pad_15 = Nueva escena a partir de lo reproducido, si no hay nada reproduciendo crea una escena en blanco;
    Pad_16 = Play / Stop escena

_(gracias @LilSmeag >
[MiniLab Mk2 Ableton Mode modified functionality](https://forum.arturia.com/index.php?topic=102839.0))_


#### Knobs 1 al 16

###### Knob 1:
Permite desplazarse entre pistas, si lo mantenemos pulsado podemos ver (y activar / desactivar) las pistas que
están muteadas (_solo PADS_1_). Si la pista es un grupo podemos abrirlo y cerrarlo pulsando _shift_ y presionando.

###### Knob 9:
Permite desplazarse entre sesiones (verticalmente). Si lo mantenemos pulsado podemos ver y activar / desactivar
 las pistas que están armadas y armarlas (_solo PADS_1_).

###### Knobs 2, 3, 4, 5 y 10, 11, 12 y 13:
Siempre controlan los parámetros de los devices, recomiendo hacer grupos con los devices a usar, ya sean plugins o
instrumentos, así será más ágil la modificación de los parámetros. Interesante la página 
[“The Blue Hand” for Instant Mapping in Ableton Live](https://performodule.com/2015/08/09/the-blue-hand-for-instant-mapping-in-ableton-live/).

###### Knobs 6, 7, 14 y 8:
OPCION 1:
Volumen de envío A

###### Knob 7:
Volumen de retorno A. Se puede cambiar en las opciones como Volumen de envío B

###### Knob 14:
Volumen de envío B

###### Knob 15:
Volumen de retorno B

###### Knob 8:
Paneo de pista

###### Knob 16:
Volumen de pista


```general view                                                plugin preset
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

# ?  arm & overdub    undo                      g. quant     scrub      play/stop scrub   cons loop    set loop```
