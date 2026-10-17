#!/usr/bin/python3
import sys
import widget_store as store
if len(sys.argv)!=3:raise SystemExit('Usage: widget-action.py launch|remove <widget-id>')
if sys.argv[1]=='launch':store.launch_web(sys.argv[2])
elif sys.argv[1]=='remove':store.remove(sys.argv[2])
else:raise SystemExit('Unknown action')
