import logging
import os
import unittest

from mswh.comm.sql import Sql

import pandas as pd
logging.basicConfig(level=logging.DEBUG)


# has setUpClass method, thus run the test on the entire class
class SqlTests(unittest.TestCase):
    """Tests the db-python read-write capabilities.
    """

    @classmethod
    def setUpClass(cls):
        """Initiates the sqlite db engine
        for the test db file.
        """
        test_db_name = 'test.db'
        test_db_fulpath = os.path.join(
            os.path.dirname(__file__), test_db_name)
        cls.test_db_fulpath = test_db_fulpath

        print(test_db_fulpath)
        # create test db if it does not exist

        if not os.path.exists(test_db_fulpath):
            os.system('touch ' + test_db_fulpath)

        cls.sql_api = Sql(test_db_fulpath)

        # example dict to write to db
        cls.df = pd.DataFrame(
            data=[['a', 1], ['b', 2]],
            columns=['comp', 'cost'])

        # example dict to write to db as table
        cls.dict = {'k1': [12, 13, 14],
                    'k2': ['a', 'b', 'c']}

        # example csv data
        cls.path_to_csv = os.path.join(
            os.path.dirname(__file__), 'table.csv')

        # sql code to execute
        cls.raw_sql = '''CREATE TABLE sys_components
(
 Component TEXT NOT NULL ,
 Function  TEXT NOT NULL ,

PRIMARY KEY (Component)
);'''

    @classmethod
    def tearDownClass(cls):
        """Clean up for any reinitiation of the test,
        but keep the result. Any new run will overwrite
        the result.
        """
        store_db_name = 'test_done.db'
        # close the test db
        cls.sql_api.db.close()
        store_db_fulpath = os.path.join(
            os.path.dirname(__file__), store_db_name)
        # rename file, overwrite if exists
        if os.path.exists(store_db_fulpath):
            os.remove(store_db_fulpath)

        os.rename(cls.test_db_fulpath, store_db_fulpath)

    def test_a_pd2table(self):
        """Tests write pandas dataframe to
        db as a table.
        """
        self.sql_api.pd2table(self.df, 'pd2table')

    def test_b_csv2table(self):
        """Tests write csv file to
        db as a table.
        """
        self.sql_api.csv2table(self.path_to_csv, 'csv2table')

    def test_c_table2pd(self):
        """Reads a single table from db as a pd.df
        """
        df = self.sql_api.table2pd('pd2table')
        self.assertTrue((df == self.df).all().all())

    def test_d_commit(self):
        """Use sql to write to db (e.g. create, alter)
        """
        self.assertTrue(self.sql_api.commit(self.raw_sql))

    def test_e_tables2dict(self):
        """Read all tables from db into a dictionary
        of dataframes.
        """
        data = self.sql_api.tables2dict()
        self.assertEqual(data['pd2table'].iloc[1, 1], 2)
