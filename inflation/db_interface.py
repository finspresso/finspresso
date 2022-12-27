import json
import sqlalchemy
import logging.config

logger = logging.getLogger("db_interace")
# logger.setLevel(logging.DEBUG)


class DBInterface:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(
            "mysql://root:@127.0.0.1/dummy", echo=True
        )
        print(self.engine.table_names())

    def create_table(self):
        pass


def setup_logger(config_path):
    with open(config_path, "rt") as f:
        config = json.load(f)
        logging.config.dictConfig(config)


def main():
    setup_logger("logging_config.json")
    logger.info("test")
    db_interface = DBInterface()
    db_interface.create_table()


if __name__ == "__main__":
    main()
