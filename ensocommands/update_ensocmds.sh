#!/bin/bash

cat ~/.ensocommands > ~/.ensocommands

for cmd in $(find $(pwd) -name '*.py'); do
    echo "execfile(\"$cmd\")" >> ~/.ensocommands
done

cat ~/.ensocommands
