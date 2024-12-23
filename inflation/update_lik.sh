#!/bin/bash
#set -e
shopt -s expand_aliases
source $HOME/.bash_aliases

echo "Setting links to credentials correctly"
softLinkMYSQLDummy

lampp_path="/opt/lampp"
sudo $lampp_path/mysql/scripts/ctl.sh status | grep "mysql not running"

if [ $? == 0 ]
then
    echo "Starting MYSQL server"
    sudo $lampp_path/mysql/scripts/ctl.sh start
fi

sudo $lampp_path/apache2/scripts/ctl.sh status | grep "apache not running"

if [ $? == 0 ]
then
    echo "Starting Apache2 server"
    sudo $lampp_path/apache2/scripts/ctl.sh start 1> /dev/null
fi

/opt/google/chrome/chrome  http://localhost/inflation/html/lik_evolution.html > /dev/null 2>&1 &

read -p "Do you see data in lik_evolution.html? (y/n) "

if [ $REPLY != "y" ]
then
    echo "Error with local MYSQL database"
    exit 1
fi

python inflation_tracker.py --download_data_bfs


python inflation_tracker.py --lik_evolution latest --credentials_file credentials/sql_credentials.json --upload_to_sql


read -p "Do you see new data in lik_evolution.html? (y/n) "

if [ $REPLY != "y" ]
then
    echo "Error with local MYSQL database"
    exit 1
fi

echo "Setting links to credentials correctly"
softLinkMYSQLFinspresso

echo "Enabling portforwarding to finspresso"
portforwarding_finspresso

echo "Updating data to finspresso db"
python inflation_tracker.py --lik_evolution latest --credentials_file credentials/sql_credentials.json --upload_to_sql
