#!/usr/bin/env bash

# Author: Jeffrey Grover
# Created: 11/2017
# Purpose: Count overlapping features from a file generated by bedtools window
# Also works with bedtools intersect -c output

# Pass through the file to run as a positional variable

awk '{sum+=$7;} END { print sum }' "$1" > "${1%.txt}_overlaps.txt"
