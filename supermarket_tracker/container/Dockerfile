FROM php:7.2-apache
ARG APACHE_PATH=/var/www/html
RUN mkdir $APACHE_PATH/supermarket_tracker
COPY browser/ $APACHE_PATH/supermarket_tracker/
RUN mv $APACHE_PATH/supermarket_tracker/php_files/db_credentials_docker.php $APACHE_PATH/supermarket_tracker/php_files/db_credentials.php
EXPOSE 80
# docker run -d --name apache-php -p 81:80 --rm apache-php:latest
#http://localhost:81/supermarket_tracker/html/mbudget_tracker.html
