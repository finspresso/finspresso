import argparse
import json
import logging.config
import pandas as pd

from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    MetaData,
    ForeignKey,
    and_,
    or_,
    BigInteger,
    Text,
    Float,
    Date,
)
from sqlalchemy.sql import text, select, func

logger = logging.getLogger("db_interace")


class DBInterface:
    def __init__(self, credentials, print_all_tables=False, echo=False):
        self.engine = create_engine(
            "mysql://"
            + credentials["user"]
            + ":"
            + credentials["password"]
            + "@"
            + credentials["hostname"]
            + ":"
            + credentials["port"]
            + "/"
            + credentials["db_name"],
            echo=echo,
        )
        self.connect()
        if print_all_tables:
            self.print_all_tables()
        self.close()

    def create_table(self, meta):
        meta.create_all(self.engine)

    def print_all_tables(self):
        meta = MetaData()
        meta.reflect(bind=self.engine)
        for table_name in meta.tables.keys():
            logger.info("Found table %s", table_name)

    def delete_tables(self, tables_to_delete):
        meta = MetaData()
        meta.reflect(bind=self.engine)
        for table_name in meta.tables.keys():
            if table_name in tables_to_delete:
                logger.info("Deleting table %s", table_name)
                meta.tables[table_name].drop(self.engine)

    def get_all_tables(self):
        meta = MetaData()
        meta.reflect(bind=self.engine)
        table_names = []
        if len(meta.tables) > 0:
            table_names = list(meta.tables.keys())
        return table_names

    def print_all_records(self, table_name):
        logger.info("Calling print_all_records on table %s", table_name)
        self.connect()
        df = pd.read_sql_table(table_name, self.conn)
        self.close()
        logger.info(df.to_string())

    def get_all_columns(self, table_name):
        columns = []
        self.connect()
        if table_name in self.get_all_tables():
            df = pd.read_sql_table(table_name, self.conn)
            columns = df.columns
        self.close()
        return columns

    def add_new_columns(self, table_name, new_columns, type_dict):
        self.connect()
        for column_name in new_columns:
            column_type = str(type_dict[column_name]())
            logger.info("Adding column %s of type %s", column_name, column_type)
            query = f"ALTER TABLE {table_name} ADD `{str(column_name)}` {column_type} ;"
            self.conn.execute(query)
        self.close()

    def close(self):
        self.conn.close()

    def connect(self):
        self.conn = self.engine.connect()

    @classmethod
    def infer_sqlalchemy_datatypes(cls, df):
        type_dict = {}
        for column in df.columns:
            type_dict[column] = Text
            if df[column].dtype == "int64":
                type_dict[column] = BigInteger
            elif df[column].dtype == "float64":
                type_dict[column] = Float
            elif df[column].dtype == "datetime64[ns]":
                type_dict[column] = Date
            elif df[column].dtype == "<M8[ns]":
                type_dict[column] = Date
        return type_dict

    @staticmethod
    def load_db_credentials(credential_file):
        with open(credential_file, "r") as read_file:
            credentials = json.load(read_file)
        return credentials


def setup_logger(config_path):
    with open(config_path, "rt") as f:
        config = json.load(f)
        logging.config.dictConfig(config)


def create_test_table(db_interface):
    logger.info("Creating test tables")
    meta = MetaData()
    Table(
        "test_table",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", String(12)),
        Column("lastname", String(12)),
    )
    Table(
        "test_table_addresses",
        meta,
        Column("id", Integer, primary_key=True),
        Column("st_id", Integer, ForeignKey("test_table.id")),
        Column("postal_add", String(40)),
        Column("email_add", String(25)),
    )
    meta.create_all(db_interface.engine)


def insert_test_record(db_interface, test_table_name="test_table"):
    logger.info("Calling insert_test_record on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    ins = meta.tables[test_table_name].insert().values(name="John", lastname="Doe")
    db_interface.conn.execute(ins)


def insert_multiple_test_records(db_interface, test_table_name="test_table"):
    logger.info("Calling insert_multiple_test_records on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name]
    db_interface.conn.execute(
        test_table.insert(),
        [
            {"name": "Rajiv", "lastname": "Khanna"},
            {"name": "Komal", "lastname": "Bhandari"},
            {"name": "Abdul", "lastname": "Sattar"},
            {"name": "Priya", "lastname": "Rajhans"},
        ],
    )

    test_table_addresses = meta.tables[test_table_name + "_addresses"]
    db_interface.conn.execute(
        test_table_addresses.insert(),
        [
            {
                "st_id": 1,
                "postal_add": "Shivajinagar Pune",
                "email_add": "ravi@gmail.com",
            },
            {
                "st_id": 1,
                "postal_add": "ChurchGate Mumbai",
                "email_add": "kapoor@gmail.com",
            },
            {
                "st_id": 3,
                "postal_add": "Jubilee Hills Hyderabad",
                "email_add": "komal@gmail.com",
            },
            {
                "st_id": 5,
                "postal_add": "MG Road Bangaluru",
                "email_add": "as@yahoo.com",
            },
            {
                "st_id": 2,
                "postal_add": "Cannought Place new Delhi",
                "email_add": "admin@khanna.com",
            },
        ],
    )
    result = db_interface.conn.execute(test_table.select()).fetchall()
    logger.info(result)


def select_test_records(db_interface, test_table_name="test_table", id_where=2):
    logger.info("Calling select_test_records on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name]
    result = db_interface.conn.execute(
        test_table.select().where(test_table.c.id > id_where)
    )
    for row in result:
        logger.info(row)
    test_table_addresses = meta.tables[test_table_name + "_addresses"]
    sql_call = select([test_table, test_table_addresses]).where(
        test_table.c.id == test_table_addresses.c.st_id
    )
    result = db_interface.conn.execute(sql_call)
    for row in result:
        logger.info(row)


def text_test_call(db_interface, test_table_name="test_table"):
    logger.info("Calling text_test_call on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    text_call = text(
        f"select {test_table_name}.name, {test_table_name}.lastname from {test_table_name} where {test_table_name}.name between :x and :y"
    )
    result = db_interface.conn.execute(text_call, x="I", y="K")
    for row in result:
        logger.info(row)


def test_aliases(db_interface, test_table_name="test_table"):
    logger.info("Calling test_aliases on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name].alias("a")
    result = db_interface.conn.execute(
        select([test_table]).where(test_table.c.id > 2)
    ).fetchall()
    logger.info(result)


def test_delete(db_interface, test_table_name="test_table"):
    logger.info("Calling test_delete on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name]
    sql_call = test_table.delete().where(test_table.c.id > 2)
    db_interface.conn.execute(sql_call)
    result = db_interface.conn.execute(test_table.select()).fetchall()
    logger.info(result)


def test_update(db_interface, test_table_name="test_table"):
    logger.info("Calling test_update on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name]
    test_call = (
        test_table.update().where(test_table.c.name == "John").values(name="Jane")
    )
    db_interface.conn.execute(test_call)
    result = db_interface.conn.execute(test_table.select()).fetchall()
    logger.info(result)


def test_update_multiple(db_interface, test_table_name="test_table"):
    logger.info("Calling test_update on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name]
    test_table_addresses = meta.tables[test_table_name + "_addresses"]
    sql_call = (
        test_table.delete()
        .where(test_table.c.id == test_table_addresses.c.id)
        .where(test_table_addresses.c.email_add.startswith("kapoor%"))
    )
    db_interface.conn.execute(sql_call)
    result = db_interface.conn.execute(test_table.select()).fetchall()
    logger.info(result)


def test_join(db_interface, test_table_name="test_table"):
    logger.info("Calling test_join on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name]
    test_table_addresses = meta.tables[test_table_name + "_addresses"]
    join_sql_call = test_table.join(
        test_table_addresses,
        test_table.c.id == test_table_addresses.c.st_id,
        isouter=True,
    )
    sql_call = select(
        [test_table.c.name, test_table.c.lastname, test_table_addresses.c.postal_add]
    ).select_from(join_sql_call)
    result = db_interface.conn.execute(sql_call)
    for row in result:
        logger.info(row)


def test_and_conjunctive(db_interface, test_table_name="test_table"):
    logger.info("Calling test_and_conjunctive on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name]
    sql_call = select([test_table]).where(
        and_(test_table.c.name == "Hans", test_table.c.id < 12)
    )
    result = db_interface.conn.execute(sql_call)
    for row in result:
        logger.info(row)


def test_or_conjunctive(db_interface, test_table_name="test_table"):
    logger.info("Calling test_or_conjunctive on table %s", test_table_name)
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name]
    sql_call = select([test_table]).where(
        or_(test_table.c.name == "Hans", test_table.c.id < 1)
    )
    result = db_interface.conn.execute(sql_call)
    for row in result:
        logger.info(row)


def test_sqlalchemy_func(db_interface, test_table_name="test_table"):
    logger.info("Calling test_sqlalchemy_func on table %s", test_table_name)
    result = db_interface.conn.execute(select([func.now()]))
    logger.info(result.fetchone())
    meta = MetaData()
    meta.reflect(bind=db_interface.engine)
    test_table = meta.tables[test_table_name]
    sql_call = select([func.count(test_table.c.id)])
    result = db_interface.conn.execute(sql_call)
    logger.info(result.fetchone())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--credentials_file",
        help="Path to .json file containing db credentials",
        default="",
    )
    parser.add_argument("--create_test_table", action="store_true")
    parser.add_argument("--print_all_tables", action="store_true")
    parser.add_argument("--insert_test_records", action="store_true")
    parser.add_argument("--select_test_records", action="store_true")
    parser.add_argument("--text_test", action="store_true")
    parser.add_argument("--test_alias", action="store_true")
    parser.add_argument("--test_update", action="store_true")
    parser.add_argument("--test_delete", action="store_true")
    parser.add_argument("--test_join", action="store_true")
    parser.add_argument("--test_conjunctive", action="store_true")
    parser.add_argument("--test_sqlalchemy_func", action="store_true")
    args = parser.parse_args()
    setup_logger("logging_config.json")
    credentials = {
        "hostname": "127.0.0.1",
        "user": "root",
        "password": "",
        "db_name": "dummy",
        "port": "3306",
    }
    if args.credentials_file != "":
        credentials = DBInterface.load_db_credentials(args.credentials_file)
    db_interface = DBInterface(
        credentials=credentials, print_all_tables=args.print_all_tables
    )
    if args.create_test_table:
        create_test_table(db_interface)
    if args.insert_test_records:
        insert_test_record(db_interface)
        insert_multiple_test_records(db_interface)
    if args.select_test_records:
        select_test_records(db_interface)
    if args.text_test:
        text_test_call(db_interface)
    if args.test_alias:
        test_aliases(db_interface)
    if args.test_update:
        test_update(db_interface)
        test_update_multiple(db_interface)
    if args.test_delete:
        test_delete(db_interface)
    if args.test_join:
        test_join(db_interface)
    if args.test_conjunctive:
        test_and_conjunctive(db_interface)
        test_or_conjunctive(db_interface)
    if args.test_sqlalchemy_func:
        test_sqlalchemy_func(db_interface)


if __name__ == "__main__":
    main()

# Next: https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_core_using_conjunctions.htm
