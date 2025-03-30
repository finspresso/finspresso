#!/bin/bash
#set -e

shopt -s expand_aliases
source $HOME/.bash_aliases

mysqldump="/opt/lampp/bin/mysqldump"
mysql="/opt/lampp/bin/mysql"

$mysqldump -u root -p supermarket > dump.sql
$mysql -u root -p --port 3308 --host 127.0.0.1 supermarket < dump.sql
