#!/usr/bin/env bash
# POSIX launcher; Windows calls the Python file directly.
exec python3 "$(dirname -- "$0")/log.py" "$@"
