import logging
import os

import numpy as np
import pandas as pd

from plotly.offline import iplot, init_notebook_mode

import plotly.graph_objs as go
import plotly.io as pio

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Plot(object):
    """Creates and saves plots to visualize and
    correlate arrays, usually timeseries

    Parameters:

        title: str
            Plot title

        data_headers: list
            A list of labels in the same order as the corresponding data
            If None the labels will be the df column labels, or integer
            indices if a list got provided

        label_h: str
            Horizontal axis label

        label_v: str
            Vertical axis label

        legend: boolean
            Plot the legend or not

        save_image: boolean
            If True saves the created image with either
            a given or default path and filename. Supported
            file types are 'png' and 'pdf', as specified in
            the filename.

        duration_curve: boolean
            If True it sorts the columns (df or arrays)
            and plots the duration_curve, returns a
            duration_curve metric as a real

        outpath: string or '' (for current directory)
            Path to save the png image of the plot

        boxmean: True, False, 'sd', 'Only Mean'

        notebook_mode: boolean
            Plot in the notebook if True

        width: int
            Image width

        height: int
            Image height

        fontsize: int
            Axis label font size

    Returns:

        fig: plotly figure if self.interactive
              else True
    """

    def __init__(
        self,
        title="",
        label_h="Time [h]",
        label_v="Component performance",
        data_headers=None,
        save_image=True,
        legend=True,
        outpath="",
        duration_curve=False,
        boxmode="group",
        notebook_mode=False,
        width=1200,
        height=800,
        fontsize=28,
        legend_x=0.4,
        legend_y=1.0,
        margin_l=200.0,
        margin_b=200.0,
    ):

        self.data_headers = data_headers
        self.save_image = save_image
        self.outpath = outpath
        self.interactive = notebook_mode
        self.duration_curve = duration_curve

        # plot formatting, see
        # https://plot.ly/python/reference/#layout-titlefont
        self.layout = go.Layout(
            font=dict(size=fontsize, family="arial"),
            title=title,
            titlefont=dict(size=fontsize * 1.0, family="arial"),
            xaxis=dict(
                title=label_h,
                titlefont=dict(
                    # family='Courier New, monospace',
                    size=fontsize,
                    color="#7f7f7f",
                ),
                tickfont=dict(size=fontsize * 0.8),
                gridcolor='lightgrey',
            ),
            yaxis=dict(
                title=label_v,
                titlefont=dict(
                    # family='Courier New, monospace',
                    size=fontsize,
                    color="#7f7f7f",
                ),
                tickfont=dict(size=fontsize * 0.8),
                gridcolor='lightgrey',
            ),
            showlegend=legend,
            width=width,
            height=height,
            margin=dict(l=margin_l, b=margin_b),
            legend=dict(
                bgcolor='rgba(255, 255, 255, 0.5)',
                x=legend_x,
                y=legend_y,
                font=dict(family="arial", size=fontsize * 0.8),
            ),
            plot_bgcolor='white'
        )

        self.boxlayout = go.Layout(
            font=dict(size=fontsize, family="arial"),
            title=title,
            titlefont=dict(size=fontsize * 1., family="arial"),
            xaxis=dict(
                title=label_h,
                titlefont=dict(
                    # family='Courier New, monospace',
                    size=fontsize,
                    color="#7f7f7f",
                ),
                tickfont=dict(size=fontsize * 0.8),
            ),
            yaxis=dict(
                title=label_v,
                titlefont=dict(
                    # family='Courier New, monospace',
                    size=fontsize,
                    color="#7f7f7f",
                ),
                tickfont=dict(size=fontsize * 0.8),
            ),
            showlegend=legend,
            width=width,
            height=height,
            margin=dict(l=margin_l, b=margin_b),
            legend=dict(x=legend_x, y=legend_y),
            boxmode=boxmode,
        )

    def scatter(self, data, outfile="scatter.png", modes="lines+markers"):
        """Creates a scatter plot

        Parameters:

            data: array/list, pd series, list of arrays/lists, pd df
                Provide a list or arrays/lists or a pandas dataframe.
                The variables should be ordered in pairs such that
                each odd variable in the list/first column in the df
                gets assigned to the horizontal axis, each even
                variable to the vertical axes. Each pair needs
                to have the same length, but pairs can be of
                a different length.

            outfile: str
                Filename, include .png, .png .pdf

            modes: str or list of str
                'markers', 'lines', 'lines + markers' or
                a list of the above to assign to each plot
                (one string in a list for each pair of data)

        Returns:

            fig: plotly figure if self.interactive
                  else True
        """
        # some input format error handling, not exhaustive
        if (isinstance(data, list)) and (len(data) < 2):
            msg = (
                "Provide at least two arrays or columns to"
                "create a scatter plot. Or try Series plot "
                "for a single column of data versus its index."
            )
            log.error(msg)
            raise Exception

        if (isinstance(data, pd.Series)) or (
            (isinstance(data, pd.DataFrame)) and (data.shape[1] == 1)
        ):
            msg = (
                "Provide a dataframe with no less than two"
                "columns. Series plot can plot a single column"
                "against its index."
            )
            log.error(msg)
            raise Exception

        # rectangles the data if passed as a list of lists/arrays
        # if some of the lists/arrays are shorter, the gaps are
        # filled with np.nan
        if isinstance(data, list):
            df_data = pd.DataFrame(
                data=np.empty(
                    (
                        len(max(data, key=len)),
                        len(data),
                    )
                )
                * np.nan
            )

            col_inx = 0
            for i in data:
                if isinstance(i, list):
                    i_list = i
                else:
                    i_list = i.tolist()
                df_data[col_inx] = (
                    i_list
                    + (np.empty(df_data.shape[0] - len(i)) * np.nan).tolist()
                )
                col_inx += 1

            data = df_data.copy()

        if self.duration_curve:
            for col_index in range(0, df_data.shape[1]):
                data.iloc[:, col_index] = (
                    data.iloc[:, col_index].sort_values(ascending=False).values
                )

        if self.data_headers:
            data.columns = self.data_headers

        num_columns = data.shape[1]

        if not isinstance(modes, list):
            list_modes = [modes] * int(num_columns / 2)
        else:
            list_modes = modes

        if num_columns % 2 != 0:
            msg = (
                "Provide an even number of columns,"
                "e.g. [x1, y1, x2, y2, ...]"
            )
            log.error(msg)
            raise Exception

        plot_data = []

        for col_index in range(0, num_columns, 2):
            plot_data.append(
                go.Scatter(
                    x=data.iloc[:, col_index],
                    y=data.iloc[:, col_index + 1],
                    mode=list_modes[int(col_index / 2.0)],
                    name=data.columns[col_index + 1],
                )
            )

        fig = go.Figure(data=plot_data, layout=self.layout)

        if self.save_image:

            if self.outpath == None:
                self.outpath = os.getcwd()
            if not os.path.exists(self.outpath):
                os.makedirs(self.outpath)
            pio.write_image(fig, os.path.join(self.outpath, outfile))

        if self.interactive:
            try:
                iplot(fig)
                return fig
            except:
                log.error("Interactive mode failed.")
                raise Exception

        return True

    def series(
        self,
        data,
        xtickvals=False,
        index_in_a_column=None,
        outfile="series.png",
        modes="lines+markers",
        dashes="solid",
        colors=False,
        width=0.5,
    ):
        """Plots all series data against either the index or the first
        provided series. It can sort the data and plot the duration_curve.

        Parameters:

            data: array/list, pd series, list of arrays/lists, pd df
                Provide an array or a list if plotting a single
                variable. If plotting multiple variables provide
                a list of arrays or a pandas dataframe.

                Horizontal axis corresponds to:

                    * if pd df: the index of the dataframe or the first columns of the dataframe
                    * if list or arrays/lists: a range of array length of the first array/list in the list

                All arrays in the list need to have the same length.

            index_in_a_column: boolean
                Horizontal axis labels
                If None, dataframe index is used, otherwise pass a
                column label for a column (it will not be considered
                as a series to plot)

            xtickvals: boolean or list/array
                Array or list of x-axis tick values.
                Default: False (uses all values passed to x-axis)

            outfile: str
                Filename, include .png, .png .pdf

            modes: str or list of str
                'markers', 'lines', 'lines+markers' or
                a list of the above to assign to each column
                of data, excluding the first column if
                index_in_a_column is not None

            dashes: str or list of str
                'solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot'
                a list of the above line types to assign to each column
                of data, excluding the first column if
                index_in_a_column is not None

            width: int between 0 and inf
                a list of the above integers indicating line thickness to
                assign to each column of data, excluding the first column if
                index_in_a_column is not None

            colors: list of line colors (hex), or False
                if False, will select from the default list
                if customized list passed, assign to each column of data,
                excluding the first column if index_in_a_column is not None

        Returns:

            fig: plotly figure if self.interactive
                else True
        """
        # rectangles the data if passed as a list of lists/arrays
        # if some of the lists/arrays are shorter, the gaps are
        # filled with np.nan
        if isinstance(data, list):
            df_data = pd.DataFrame(
                data=np.empty(
                    (
                        len(max(data, key=len)),
                        len(data),
                    )
                )
                * np.nan
            )

            col_inx = 0
            for i in data:
                if isinstance(i, np.ndarray):
                    df_data[col_inx] = np.concatenate(
                        (
                            i,
                            (
                                np.empty((1, df_data.shape[0] - len(i)))
                                * np.nan
                            )[0],
                        )
                    )

                if isinstance(i, list):
                    df_data[col_inx] = (
                        i
                        + (np.empty((1, df_data.shape[0] - len(i))) * np.nan)[
                            0
                        ].tolist()
                    )
                col_inx += 1

            data = df_data.copy()

        if index_in_a_column is not None:
            labels_h_axis = data.loc[:, index_in_a_column]
            data = data.drop(columns=[index_in_a_column])
        else:
            labels_h_axis = data.index

        if self.data_headers:
            data.columns = self.data_headers

        num_columns = data.shape[1]

        if not isinstance(modes, list):
            list_modes = [modes] * num_columns
        else:
            list_modes = modes

        if not isinstance(dashes, list):
            list_dashes = [dashes] * num_columns
        else:
            list_dashes = dashes

        if not isinstance(width, list):
            list_width = [width] * num_columns
        else:
            list_width = width

        # Plotly default colors
        default_colors=['rgb(31, 119, 180)', 'rgb(255, 127, 14)',
                            'rgb(44, 160, 44)', 'rgb(214, 39, 40)',
                            'rgb(148, 103, 189)', 'rgb(140, 86, 75)',
                            'rgb(227, 119, 194)', 'rgb(127, 127, 127)',
                            'rgb(188, 189, 34)', 'rgb(23, 190, 207)']

        if not isinstance(colors, list):
            list_colors = default_colors[0:num_columns]
        else:
            list_colors = colors

        if self.duration_curve:
            for col_index in range(0, num_columns):
                data.iloc[:, col_index] = (
                    data.iloc[:, col_index].sort_values(ascending=False).values
                )

        plot_data = []

        for col_index in range(num_columns):
            plot_data.append(
                go.Scatter(
                    x=labels_h_axis,
                    y=data.iloc[:, col_index],
                    mode=list_modes[col_index],
                    line= dict(dash=list_dashes[col_index],
                               width=list_width[col_index],
                               color=list_colors[col_index]),
                    name=data.columns[col_index],
                )
            )

        fig = go.Figure(data=plot_data, layout=self.layout)

        if type(xtickvals)!=bool:
            # Update x-axis to display the selected ticks
            fig.update_xaxes(tickvals=xtickvals)

        if self.save_image:

            if self.outpath == None:
                self.outpath = os.getcwd()
            if not os.path.exists(self.outpath):
                os.makedirs(self.outpath)
            pio.write_image(fig, os.path.join(self.outpath, outfile))

        if self.interactive:
            try:
                iplot(fig)
                return fig
            except:
                log.error("Interactive mode failed.")
                raise Exception

        return True

    def box(
        self,
        dfs,
        plot_cols=None,
        groupby_cols=None,
        df_cat=None,
        outfile="box.png",
        boxmean=False,
        colors=["#3D9970", "#FF4136", "#FF851B"],
        title="Energy Use",
        boxpoints="outliers",
    ):
        """Creates box plots for the chosen `plot_col` and can
        group plots by the `groupby_col`.

        Parameters:

            dfs: list of dfs

            df_cat: list of str
                Indicator of the category carried by the dfs
                (E.g. the dfs differ by housing type)

            plot_col: list of columns to plot, one from each df in
                dfs. If multiple dfs are passed, the values will be
                shown as groups on the plot

            groupby_cols: list of cols to use as x axis, from each
                df. Use the same column if it has the same elements.
                Use None if x axis category not used

            boxpoints: False, 'all', 'outliers', 'suspectedoutliers'
                See https://plot.ly/python/reference/#box

        Returns:

            fig: plotly figure if self.interactive
                else True
        """

        # Extract y values
        y = dict()
        x = dict()
        trace = dict()
        df_ctg = dict()
        data = list()
        i = 0

        for df in dfs:

            y[i] = df[plot_cols[i]].values.tolist()

            if (groupby_cols is not None) and (groupby_cols[i] is not None):
                x[i] = df[groupby_cols[i]].values.tolist()
            else:
                x[i] = None

            if df_cat[i] is not None:
                df_ctg[i] = df_cat[i]
            else:
                df_ctg[i] = ""

            trace[i] = go.Box(
                y=y[i],
                x=x[i],
                name=plot_cols[i] + " - " + df_ctg[i],
                boxpoints=boxpoints,
                marker=dict(color=colors[i]),
                boxmean=boxmean,
            )

            data.append(trace[i])
            i += 1

        fig = go.Figure(data=data, layout=self.boxlayout)

        if self.save_image:

            if self.outpath == None:
                self.outpath = os.getcwd()
            if not os.path.exists(self.outpath):
                os.makedirs(self.outpath)
            pio.write_image(fig, os.path.join(self.outpath, outfile))

        if self.interactive:
            try:
                iplot(fig)
                return fig
            except:
                log.error("Interactive mode failed.")
                raise Exception

        return True


# size and color modes:
#   .........
#                mode='markers',
#                marker={'size': sz,
#                        'color': colors,
#                        'opacity': 0.6,
#                        'colorscale': 'Viridis'
