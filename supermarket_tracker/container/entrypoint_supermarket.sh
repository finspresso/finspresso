#!/bin/bash

echo "Calling entrypoint_supermarket.sh"
python $FINSPRESSO_ROOT/supermarket_tracker/supermarket_webui.py
while true;
do
    sleep 3

done
