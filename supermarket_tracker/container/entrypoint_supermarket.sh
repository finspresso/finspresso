#!/bin/bash

echo "Calling entrypoint_supermarket.sh"
python $FINSPRESSO_ROOT/supermarket_tracker/supermarket_webui.py --index-file $FINSPRESSO_ROOT/supermarket_tracker/index_supermarket.html --exec-file $FINSPRESSO_ROOT/supermarket_tracker/update_mbudget.sh

while true;
do
    sleep 3

done
