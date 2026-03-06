#!/bin/bash
# Sample script for testing automation engine
# Usage: ./hello.sh [name]

NAME=${1:-"World"}
echo "Hello, $NAME!"
echo "Current time: $(date)"
echo "Script executed from: $(pwd)"
