## Ableton mMimiLabMk2

Disclaimer: this plugin has been developed by someone better described as a 'code bodger' rather than a programmer. Beware of spaghetti. The plugin works well for me personally, but unfortunately I can't guarantee it'll work well for people on other systems or machines.

En modo live, los 8 primeros pads actuan en modo sesion
y los siguientes actuan como Play, Stop, Overdub,.. y los
finales como Undo, Nueva escena a partir de lo reproducido, Play escena.
El knob 1 si se pulsa, cambia de vista entre Session y Arranger
si se pulsa junto con SHIFT, cambia la vista de los Device de ese Track
devices con los que nos moveremos con el knob 8 (si pulsamos SHIFT)
El knob 9 pulsado arma el Track seleccionado, (con SHIFT no implementado)

Recomendable poner el modo de lanzamiento de clips por defecto en Toggle,
en Preferencias > Lanzamiento > Modo Lanzar por defecto, asi se consigue que
los clips en modo sesion se puedan parar.

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
