#!/bin/bash
echo "Starting Xvfb on screen port 99"

Xvfb :99 -screen 0 1920x1080x24 &

echo "Calling entrypoint_supermarket.sh"
python $FINSPRESSO_ROOT/container/webui.py --index-file $FINSPRESSO_ROOT/container/index_container.html --exec-file $FINSPRESSO_ROOT/supermarket_tracker/update_mbudget.sh

while true;
do
    sleep 3

done
