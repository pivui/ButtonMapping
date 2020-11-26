#!/usr/bin/python3
#
# Button remapping program for XP-PEN Innovator 16 tablet
#
# Inspired by:
#   https://www.reddit.com/r/archlinux/comments/bivbih/request_help_remapping_keycodes/
#   https://gist.github.com/t184256/f4994037a2a204774ef3b9a2b38736dc
#
# More robust solutions can certainly be achieved with existing tools such as :
# https://github.com/kempniu/evmapy
# https://github.com/philipl/evdevremapkeys
import evdev
import asyncio
import os
#
# To work, this program requires a preliminary remapping of the scancodes sent
# by the tablet. This can be achieved through a .hwdb config file as follows:
#
#evdev:input:b0003v28BDp092Ce0100*
# KEYBOARD_KEY_70005=a   	# FRAME BTNS - Top button of the frame
# KEYBOARD_KEY_70008=b
# KEYBOARD_KEY_700e2=c
# KEYBOARD_KEY_7002c=d
# KEYBOARD_KEY_70019=e   	  # After wheels
# KEYBOARD_KEY_70016=f
# KEYBOARD_KEY_700e0=unknown  # This button sends 700e0 + 7001d
# KEYBOARD_KEY_7001d=h   	  #
# KEYBOARD_KEY_70011=i		  # Last button sends 700e0 + 700e2 + 70011
# KEYBOARD_KEY_70057=j		  # Outer wheel clockwise turn
# KEYBOARD_KEY_70056=k   	  # Outer wheel anti-clockwise
# KEYBOARD_KEY_D0044=btn_middle 	      # PEND BTNS - Mouse button towards tip
# KEYBOARD_KEY_D0045=btn_right 	      # Mouse button towards rear
#
# The latter can be placed e.g. in /etc/udev/hwdb.d/90-xppeninnov16.hwdb
# And the configuration can be reloaded with:
# sudo systemd-hwdb update
# sudo udevadm control --reload
# sudo udevadm trigger
#
# The reminder could be used to remap also the pen buttons, but as the latter are
# attached to the display itself, I found that it was not very efficient to catch
# the whole devise for pen inputs....

# Frame buttons remapping.
# Change the right column to set your own mapping
map = {
'b1':[evdev.ecodes.KEY_S, evdev.ecodes.KEY_LEFTCTRL],        # btn 1
'b2':evdev.ecodes.KEY_2,        # btn 2
'b3':evdev.ecodes.KEY_3,        # btn 3
'b4':evdev.ecodes.KEY_4,        # btn 4
'b5':evdev.ecodes.KEY_5,        # btn 5
'b6':evdev.ecodes.KEY_6,        # btn 6
'b7':evdev.ecodes.KEY_7,        # btn 7
'b8':evdev.ecodes.KEY_8,        # btn 8
'owr':evdev.ecodes.KEY_C,    # Outer wheel clockwise
'owl':evdev.ecodes.KEY_D,   # Outer wheel anti-clockwise
'iwt':evdev.ecodes.KEY_A,       # Inner wheel top
'iwb':evdev.ecodes.KEY_B        # Inner wheel bottom
# 'pt':evdev.ecodes.BTN_MIDDLE,   # pen btn near tip
# 'pr':evdev.ecodes.BTN_RIGHT,    # pen btn near rear
}
#
btn_remap = {
    evdev.ecodes.KEY_A: 'b1',
    evdev.ecodes.KEY_B: 'b2',
    evdev.ecodes.KEY_C: ['b3','b8'],
    evdev.ecodes.KEY_D: 'b4',
    evdev.ecodes.KEY_E: 'b5',
    evdev.ecodes.KEY_F: 'b6',
    evdev.ecodes.KEY_H: 'b7',
    evdev.ecodes.KEY_I: 'b8',
    evdev.ecodes.KEY_J: 'owr',
    evdev.ecodes.KEY_K: 'owl',
    # evdev.ecodes.KEY_L: 'pt',
    # evdev.ecodes.KEY_M: 'pr',
}
#
def remap_and_trigger(btn_id, state, vkbd):
    if btn_id in map:
        out = map[btn_id]
        if isinstance(out,int):
            # no modifier
            vkbd.write(evdev.ecodes.EV_KEY, out, state)
        else:
            vkbd.write(evdev.ecodes.EV_KEY, out[1], state)
            vkbd.write(evdev.ecodes.EV_KEY, out[0], state)
    vkbd.syn()
# Keyboard remapping function
async def remap_kbd(kbd,vkbd):
    last_ev     = []
    async for ev in kbd.async_read_loop():
        if ev.type == evdev.ecodes.EV_KEY:
            if ev.code in btn_remap:
                btn = btn_remap[ev.code]
                if isinstance(btn, str):
                    remap_and_trigger(btn, ev.value, vkbd)
                    # print_key_status(btn, ev.value)
                else:
                    if ev.value == 2:
                        # Key held: one can pass event
                        print_key_status(btn[0], ev.value)
                    elif ev.value == 0:
                        # Key is released
                        if last_ev.code == ev.code:
                            # Same key code as before
                            if last_ev.value == 2:
                                # key was held before, print release
                                print_key_status(btn[0], ev.value)
                            else:
                                # launch key-press event filtered before
                                print_key_status(btn[0], 1)
                                print_key_status(btn[0], 0)
                        else:
                            # Other key code before, then it was indeed a modifier
                            pass
                    else:
                        # Key pressed, need to wait
                        pass
                # Saving previous event
                last_ev = ev
            else:
                # rethrow other events
                vkbd.write_event(ev)


##
def print_key_status(key, val):
    if val == 1:
        print('Key {} pressed'.format(key))
    elif val == 2:
        print('Key {} held'.format(key))
    else:
        print('Key {} released'.format(key))
#

# Find the device based on vendor/product id
vendor   = int('028bd',16)
product  = int('092c',16)
#
# Find specifically the keyboard and mouse instances
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
kbd     = [] # will be the keyboard
mou     = [] # will be the mouse
pen     = [] # will be the pen
for d in devices:
    if d.info.vendor==vendor and d.info.product==product:
        if 'Keyboard' in d.name:
            kbd = d
        elif 'Mouse' in d.name:
            mou = d
# Find specifically the keyboard and mouse instances
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
kbd     = [] # will be the keyboard
mou     = [] # will be the mouse
for d in devices:
    if d.info.vendor==vendor and d.info.product==product:
        if 'Keyboard' in d.name:
            kbd = d
        elif 'Mouse' in d.name:
            mou = d
# Create virtual keyboard
list_of_keys = []
for key, value in map.items():
    if isinstance(map[key], int):
        list_of_keys.append(value)
    else:
        list_of_keys = list_of_keys + value
cap = {evdev.ecodes.EV_KEY: list_of_keys}

vkbd = evdev.UInput(cap,name="XP-Pen Innovator 16 Buttons")
# Monopolize the original one
kbd.grab()
asyncio.ensure_future(remap_kbd(kbd, vkbd))



# Launch the listener
event_loop = asyncio.get_event_loop()
event_loop.run_forever()
