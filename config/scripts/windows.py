#!/usr/bin/python3
"""Widget lifecycle shared by desktop controls, launcher and gallery."""
import sys
from widget_store import open_visible,remove,restore
if __name__=='__main__':
    action=sys.argv[1] if len(sys.argv)>1 else 'open'
    if action=='open':open_visible()
    elif action=='remove' and len(sys.argv)==3:remove(sys.argv[2])
    elif action=='restore':restore()
    else:raise SystemExit('Usage: windows.py open | remove <widget-name> | restore')
