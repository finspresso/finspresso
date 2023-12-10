GH_TOKEN_ARG := $(shell cat gh_token.txt)
USER_NAME := $(shell cat user_name.txt)
USER_EMAIL := $(shell cat user_email.txt)


build_apache:
	docker build -f container/Dockerfile_Apache -t apache-own:test .

run_apache:
	docker run -d --name apache -p 8081:80 --rm apache-own:latest

build_apache_php:
	docker build -f container/Apache_PHP.Dockerfile -t apache-php:test .

run_apache_php:
	docker run -d --name apache-php -p 8081:80 --rm apache-php:test

build_mysql_server:
	docker build -f container/MYSQL.Dockerfile -t mysql-server:test .

build_supermarket_tracker:
	docker build --build-arg GH_TOKEN_ARG=$(GH_TOKEN_ARG) --build-arg USER_NAME=$(USER_NAME) --build-arg USER_EMAIL=$(USER_EMAIL) -f container/supermarket_tracker.Dockerfile -t supermarket_tracker .

run_supermarket_tracker:
	docker run -d --name supermarket_tracker  --rm supermarket_tracker

build_all: build_apache_php build_mysql_server build_supermarket_tracker
