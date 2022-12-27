import argparse
import json
import logging.config

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData

logger = logging.getLogger("db_interace")
# logger.setLevel(logging.DEBUG)


class DBInterface:
    def __init__(self):
        self.engine = create_engine("mysql://root:@127.0.0.1/dummy", echo=True)
        # print(self.engine.table_names())

    def create_table(self, meta):
        meta.create_all(self.engine)


def setup_logger(config_path):
    with open(config_path, "rt") as f:
        config = json.load(f)
        logging.config.dictConfig(config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create_test_table", action="store_true")
    args = parser.parse_args()
    setup_logger("logging_config.json")
    logger.info("test")
    db_interface = DBInterface()
    if args.create_test_table:
        create_test_table(db_interface)


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


if __name__ == "__main__":
    main()
