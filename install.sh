#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 "$(dirname -- "$(readlink -f -- "$0")")/scripts/install.py" "$@"
