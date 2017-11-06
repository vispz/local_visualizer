# -*- coding: utf-8 -*-
"""Simple api to visualize the plots in a script.

Motivation
==========
* When moving from an IPython notebook to a script, we lose the diagnostics
    of visualizing pandas as tables and matplotlib plots.
* :class:`LocalViz` starts a local http server and creates a html file to
    which pandas tables and matplotlib plots can be sent over.
* The html file is dynamically updated for long running scripts.

Usage
=====

Sample Usage::

    import logging, sys, numpy as np, pandas as pd, matplotlib.pyplot as plt
    import local_viz

    plt.style.use('fivethirtyeight')
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    # Create the local visualizer instance
    lviz = local_viz.LocalViz(html_file='lviz_test.html', port=9112)
    # INFO:root:Starting background server at: http://localhost:9112/.
    # INFO:local_viz:Click: http://carpediem:9112/lviz_test.html or http://localhost:9112/lviz_test.html # noqa

    # Create plots which will be streamed to the html file.
    lviz.h3('Matplotlib :o')
    lviz.p(
        'Wrap your plots in the figure context manager which takes '
        'in the kwargs of plt.figure and returns a plt.figure object.',
    )

    with lviz.figure(figsize=(10, 8)) as fig:
        x = np.linspace(-10, 10, 1000)
        plt.plot(x, np.sin(x))
        plt.title('Sine test')

    lviz.hr()

    # Visualize pandas dataframes as tables.
    lviz.h3('Pandas dataframes')

    df = pd.DataFrame({'A': np.linspace(1, 10, 10)})
    df = pd.concat(
        [df, pd.DataFrame(np.random.randn(10, 4), columns=list('BCDE'))],
        axis=1,
    )
    lviz.write(df)

Output
======

This starts a HTTPServer and creates a html file which is dynamically updated
each time ``lviz`` is called. See https://i.imgur.com/jjwvAX2.png for the
output of the above commands.
"""
import base64
try:
    import BaseHTTPServer
    import SimpleHTTPServer
except ModuleNotFoundError: # noqa (Python 3 only)
    import http.server as SimpleHTTPServer
    import http.server as BaseHTTPServer
import contextlib
import functools
import io
import logging
import os
import socket
import tempfile
import threading

import matplotlib.pyplot as plt


log = logging.getLogger(__name__)


HEADER_LEVELS = range(1, 6)
HTML_BOILERPLATE = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>Local Visualizer</title>
        <style>
            body {
                -webkit-font-smoothing: antialiased;
                -webkit-text-size-adjust: none;
                margin: 50px !important;
                font-size:20px;
                font-family:Helvetica, sans-serif;
                font-weight: 100;
            }
            table.dataframe {
                border-collapse: collapse;
                border: none;
            }
            table.dataframe tr {
                border: none;
            }
            table.dataframe td, table.dataframe th {
                margin: 2px;
                border: 1px solid white;
                padding-left: 0.25em;
                padding-right: 0.25em;
            }
            table.dataframe th:not(:empty) {
                background-color: #fec;
                text-align: left;
                font-weight: 100;
            }
            table.dataframe tr:nth-child(2) th:empty {
                border-left: none;
                border-right: 1px dashed #888;
            }
            table.dataframe td {
                border: 2px solid #ccf;
                background-color: #f4f4ff;
            }
        </style>
    </head>
    <body>
"""


class LocalViz(object):

    """API for creating a html visualizer for python scripts.

    All the public methods of :class:`HtmlGenerator` are also exposed by
    this class.

    See module docstring for usage.
    """

    def __init__(self, lazy=False, html_file=None, run_server=True, port=9111):
        self.html_file = html_file
        self.port = port
        self.run_server = run_server
        if not lazy:
            self.start()

    def start(self):
        if self.run_server:
            run_bgd_server(port=self.port, host='localhost')
        if self.html_file:
            # Erase and create a new file.
            open(self.html_file, 'w').close()
        else:
            _, self.html_file = tempfile.mkstemp(
                dir=os.getcwd(),
                suffix='.html',
            )
        self._html_gen = HtmlGenerator(output_fl=self.html_file)
        for name in dir(self._html_gen):
            if name.startswith('_'):
                continue
            member = getattr(self._html_gen, name)
            if callable(member):
                setattr(self, name, member)
        log.info(
            'Click: http://{hn}:{p}/{fl} or http://{h}:{p}/{fl}'.format(
                hn=socket.gethostname(),
                h='localhost',
                p=self.port,
                fl=self.html_file.split('/')[-1],
            ),
        )

    def inform_cleanup(self):
        if self.html_file:
            log.info(
                'After viewing the plots, please delete the '
                'file: `{fl}`'.format(fl=self.html_file),
            )

    def close(self):
        delete_files_silently([self.html_file])
        self.html_file = None


class HtmlGenerator(object):

    """A class which updates a html file and exposes API for the same.

    The class also exposes the methods ``h1``, ``h2``, ..., ``h6`` for writing
    headers.
    """

    def __init__(self, output_fl=None):
        self.output_fl = output_fl
        self.write(HTML_BOILERPLATE)
        for lvl in HEADER_LEVELS:
            setattr(
                self,
                'h{lvl}'.format(lvl=lvl),
                functools.partial(self.header, level=lvl),
            )

    def header(self, text, level=4):
        self.write('<h{lvl}>{text}</h{lvl}>'.format(text=text, lvl=level))

    def p(self, text):
        self.write('<p>{t}</p>'.format(t=text))

    def br(self):
        self.write('<br/>')

    def hr(self):
        self.write('<br/><hr/><br/>')

    @contextlib.contextmanager
    def figure(self, **figure_kwargs):
        """Context manager as a stand it replacement for ``plt.figure``.

        Example usage::

            with html_gen.figure(figsize=(10, 10)) as fig:
                plt.plot(x, y)
                plt.title('This is a title')
        """
        fig = plt.figure(**figure_kwargs)
        fig_fl = io.BytesIO()
        yield fig
        plt.savefig(fig_fl, format='png')
        fig_fl.seek(0)
        fig_png = base64.b64encode(fig_fl.getvalue())
        fig_png = fig_png.decode('ascii')
        self.write(
            '<img src="data:image/png;base64,{fig_png}" '
            'width="500"><br/>'.format(fig_png=fig_png),
        )
        fig_fl.close()

    def write(self, text_or_df):
        """Appends the text or a pandas df to the output file.

        :param text_or_df: The string or the pandas dataframe to be written to
            file.
        :type text_or_df: str or pandas.DataFrame
        """
        if isinstance(text_or_df, str):
            text = text_or_df
        else:
            # Assume it is a pandas dataframe
            text = text_or_df.to_html()
        with open(self.output_fl, 'a+') as outfile:
            outfile.write('{s}\n'.format(s=text))


def run_bgd_server(port, host='localhost'):
    """Creates a simple http server in a daemon thread."""
    logging.info(
        'Starting background server at: '
        'http://{h}:{p}/.'.format(h=host, p=port),
    )
    server = BaseHTTPServer.HTTPServer(
        server_address=(host, port),
        RequestHandlerClass=SimpleHTTPServer.SimpleHTTPRequestHandler,
    )
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()


def delete_files_silently(files):
    """Deletes a list of files if they exist.

    :param files: A list of file paths.
    :type files: list of str
    """
    for each_file in files:
        try:
            os.remove(each_file)
        except OSError:
            pass
