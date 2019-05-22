import logging
import os
import unittest

import numpy as np
import pandas as pd

from mswh.tools.plots import Plot

logging.basicConfig(level=logging.DEBUG)


class PlotTests(unittest.TestCase):
    """Basic functionality tests for plotting methods
    """

    @classmethod
    def setUp(self):
        """Instantiates a test object
        """
        self.df = pd.DataFrame(data=[[1, 2], [1, 2], [2, 3]])
        self.list = [[1, 2, 3], [5, 4], [1, 2, 3, 4], [4, 5, 6]]
        self.save_image = True
        self.outpath = os.path.dirname(__file__)


    def test_scatter(self):
        """Create scatter plot
        """
        fig_df = Plot(
            outpath=self.outpath,
            save_image=self.save_image).scatter(
                self.df,
                outfile='scatter_df.png')
        fig_list = Plot(
            outpath=self.outpath,
            save_image=self.save_image).scatter(
                self.list,
                outfile='scatter_list.png')

    def test_series(self):
        """Create scatter plot
        """
        fig_df = Plot(
            outpath=self.outpath,
            save_image=self.save_image).series(
                self.df,
                outfile='series_df.png')
        fig_list = Plot(
            outpath=self.outpath,
            save_image=self.save_image).series(
                self.list,
                outfile='series_list.png')

    def test_box(self):
        """Create box plot
        """

        df1 = pd.DataFrame(
            data=np.random.rand(120, 2),
            columns=['df1_1', 'df1_2'])
        df2 = pd.DataFrame(
            data=np.random.rand(100, 2) + 0.2,
            columns=['df2_1', 'df2_2'])
        df3 = pd.DataFrame(
            data=np.random.rand(80, 2) + 0.4,
            columns=['df3_1', 'df3_2'])
        df1['x'] = np.random.choice(3, 120)
        df2['x'] = np.random.choice(3, 100)
        df3['x'] = np.random.choice(3, 80)

        fig = Plot(
            outpath=self.outpath,
            save_image=self.save_image).box(
                dfs=[df1, df2, df3],
                plot_cols=['df1_1', 'df2_1', 'df3_1'],
                groupby_cols=['x', 'x', 'x'],
                df_cat=['red', 'blu', 'gre'],
                outfile='box.png')
