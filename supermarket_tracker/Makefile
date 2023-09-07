update_mbudget:
	/bin/bash update_all.sh mbudget

build_apache:
	docker build -f container/Dockerfile_Apache -t apache-own:latest .

run_apache:
	docker run -d --name apache -p 8081:80 --rm apache-own:latest

build_apache_php:
	docker build -f container/Dockerfile_Apache_PHP -t apache-php:test .

run_apache_php:
	docker run -d --name apache-php -p 8081:80 --rm apache-php:test
