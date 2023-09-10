update_mbudget:
	/bin/bash update_all.sh mbudget

build_apache:
	docker build -f container/Dockerfile_Apache -t apache-own:latest .

run_apache:
	docker run -d --name apache -p 8081:80 --rm apache-own:latest

build_apache_php:
	docker build -f container/Apache_PHP.Dockerfile -t apache-php:test .

run_apache_php:
	docker run -d --name apache-php -p 8081:80 --rm apache-php:test

build_mysql_server:
	docker build -f container/MYSQL.Dockerfile -t mysql-server:test .

build_supermarket_tracker:
	docker build -f container/supermarket_tracker.Dockerfile -t supermarket_tracker .

run_supermarket_tracker:
	docker run -d --name supermarket_tracker  --rm supermarket_tracker

build_all: build_apache_php build_mysql_server build_supermarket_tracker
