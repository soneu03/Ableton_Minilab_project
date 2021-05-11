# Embedded file name: /Users/versonator/Jenkins/live/output/Live/mac_64_static/Release/python-bundle/MIDI Remote Scripts/MiniLab_mkII/__init__.py
from __future__ import absolute_import, print_function, unicode_literals
import _Framework.Capabilities as caps

from .mMiniLabMk2 import mMiniLabMk2
# this tells Live the filename in which to look for my code


# this is the standardized function with which Live loads
# any script. c_instance is the Control Surface slot in Live's
# prefs, as far as I can tell

def get_capabilities():
    return {caps.CONTROLLER_ID_KEY: caps.controller_id(vendor_id=7285, product_ids=[649], model_name=[u'Arturia MiniLab mkII']),
            caps.PORTS_KEY: [caps.inport(props=[caps.NOTES_CC, caps.SCRIPT, caps.REMOTE]), caps.outport(props=[caps.SCRIPT])]}


def create_instance(c_instance):
    return mMiniLabMk2(c_instance)
