FROM mysql:8.0-debian
ENV MYSQL_ROOT_PASSWORD=mypassword
COPY container/my.cnf /etc/mysql/my.cnf
