import argparse
import json
import logging.config

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData

logger = logging.getLogger("db_interace")
# logger.setLevel(logging.DEBUG)


class DBInterface:
    def __init__(self, print_all_tables=False):
        self.engine = create_engine("mysql://root:@127.0.0.1/dummy", echo=True)
        self.conn = self.engine.connect()
        if print_all_tables:
            self.print_all_tables()

    def create_table(self, meta):
        meta.create_all(self.engine)

    def print_all_tables(self):
        meta = MetaData()
        meta.reflect(bind=self.engine)
        for table_name in meta.tables.keys():
            logger.info("Found table %s", table_name)


def setup_logger(config_path):
    with open(config_path, "rt") as f:
        config = json.load(f)
        logging.config.dictConfig(config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create_test_table", action="store_true")
    parser.add_argument("--print_all_tables", action="store_true")
    parser.add_argument("--insert_test_records", action="store_true")
    parser.add_argument("--select_test_records", action="store_true")
    args = parser.parse_args()
    setup_logger("logging_config.json")
    db_interface = DBInterface(print_all_tables=args.print_all_tables)
    if args.create_test_table:
        create_test_table(db_interface)
    if args.insert_test_records:
        insert_test_record(db_interface)
        insert_multiple_test_records(db_interface)
    if args.select_test_records:
        select_test_records(db_interface)


def create_test_table(db_interface):
    logger.info("Creating test table")
    meta = MetaData()
    Table(
        "test_table",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", String(12)),
        Column("lastname", String(12)),
    )
    db_interface.create_table(meta)


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
    db_interface.conn.execute(
        meta.tables[test_table_name].insert(),
        [
            {"name": "Rajiv", "lastname": "Khanna"},
            {"name": "Komal", "lastname": "Bhandari"},
            {"name": "Abdul", "lastname": "Sattar"},
            {"name": "Priya", "lastname": "Rajhans"},
        ],
    )


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


if __name__ == "__main__":
    main()
