#!/bin/bash
#set -e



local_run=$1

if [ "$local_run" = "True" ]
then
    echo "Updating MBudget prices locally"
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
        sudo $lampp_path/apache2/scripts/ctl.sh start
    fi

    /opt/google/chrome/chrome http://localhost/supermarket_tracker/html/mbudget_tracker.html > /dev/null 2>&1 &

    read -p "Do you see data in mbudget_tracker.html? (y/n) "

    if [ $REPLY != "y" ]
    then
        echo "Error with local MYSQL database"
        exit 1
    fi

    ./update_all.sh mbudget

    read -p "Do you see new data in mbudge_tracker.html? (y/n) "

    if [ $REPLY != "y" ]
    then
        echo "Error with local MYSQL database"
        exit 1
    fi

    echo "Setting links to credentials correctly"
    softLinkMYSQLFinspresso

    echo "Enabling portforwarding to finspresso"
    portforwarding_finspresso


    python supermarket_tracker.py --name mbudget --credentials_file credentials/sql_credentials.json --update_metadata_table --update_prices_table
else
    cd $FINSPRESSO_ROOT/supermarket_tracker
    mkdir -p data/mbudget
    git checkout $BASE_BRANCH
    git fetch origin
    git merge orgin/$BASE_BRANCH
    auto_upload="True"
    ./update_all.sh mbudget $BASE_BRANCH $auto_upload
    ssh -4 -v -fN finspresso_mysql_portforward
    python supermarket_tracker.py --name mbudget --credentials_file credentials/sql_credentials_finspresso.json --update_metadata_table --update_prices_table
    #Next make docker volume for credentials folder in which you copy in sql_credentials.json of MYSQL docker container ans sql_credentials_finspresso.json of MYSQL finspresso db
    echo "Updating MBudget prices in container"
fi
