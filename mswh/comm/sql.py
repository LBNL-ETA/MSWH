import logging
import sqlite3

import pandas as pd

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Sql(object):
    """Performs python-sqlite db communication.

    Parameters:

        path_OR_dbconn: str or a database connection instance
            Full path to a database file or an already
            instantiated connection object
    """

    def __init__(self, path_OR_dbconn):
        # recognize or create the connection object
        if type(path_OR_dbconn) == str:
            self.db = sqlite3.connect(path_OR_dbconn)
        elif type(path_OR_dbconn) == sqlite3.Connection:
            self.db = path_OR_dbconn
        else:
            log.error(
                "Neither a path to a db file, "
                "nor a database connection got passed."
            )
            raise ValueError

    def tables2dict(self, close=True):
        """Reads all tables contained in a
        sql database and converts them to a
        pandas dataframe.

        Parameters:

            close: boolean, default=True
                If True, closes the connection to db

        Returns:

            data: dict of pandas dataframes
                Saves each of the sql tables as a
                pandas dataframe under a sql table
                name as a key
        """

        cursor = self.db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        data = dict()
        for table_name in tables:
            table_name = table_name[0]
            data[table_name] = pd.read_sql_query(
                """ SELECT * FROM '{}' """.format(table_name), self.db
            )

        if close:
            self.db.close()

        return data

    def table2pd(self, table_name, column_label_row=0):
        """Reads in a single sql table.

        Parameters:

            table_name: str
                sql table name

            column_label_row: int, default=0
                Index of the row which gets
                converted into column labels

        Returns:

            df: pandas dataframe
                Sql table read in as a pandas df.
        """
        df = pd.read_sql(
            """ SELECT * FROM '{}' """.format(table_name),
            self.db,
            index_col=None,
        )

        return df

    def pd2table(self, df, table_name, close=False):
        """Write a dataframe out to the database.
        If same named table exists, it gets replaced

        Parameters:

            table_name: str
                sql table name

            close: boolean, default=False
                If True, closes the connection to db
        """

        df.to_sql(table_name, self.db, if_exists="replace", index=False)

        if close:
            self.db.close()

        return True

    def csv2table(
        self,
        path_to_csv,
        table_name,
        column_label_row=0,
        converters=None,
        close=False,
    ):
        """Use to update bulk price or performance data.
        If same named table exists, it gets replaced

        Parameters:

            path_to_csv: str
                Full path to the csv table

            table_name: str
                sql table name of choice

            column_label_row: int, default=0
                Index of the row which gets
                converted into column labels

            converters: dict, default=None
                According to pandas documentation:
                Dict of functions for converting
                values in columns. Keys can be integers
                or column labels.

            close: boolean, default=False
                If True, closes the connection to db
        """

        csv = pd.read_csv(
            path_to_csv, converters=converters, header=column_label_row
        )

        csv.to_sql(table_name, self.db, if_exists="replace", index=False)

        if close:
            self.db.close()

        return True

    def commit(self, sql_command, close=False):
        """Execute a custom sql command

        Parameters:

            sql_command: string
                sql_command to execute

        Returns:

            close: boolean, default=False
                If True, closes the connection to db
        """

        self.db.cursor().execute(sql_command)
        self.db.commit()
        if close:
            self.db.close()

        return True
