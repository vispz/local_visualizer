Simple python api to visualize the plots in a script.

* Free software: MIT license
* Documentation: https://local-visualizer.readthedocs.io.


### Motivation
* When moving from an IPython notebook to a script, we lose the diagnostics
    of visualizing pandas as tables and matplotlib plots.
* :class:`LocalViz` starts a local http server and creates a html file to
    which pandas tables and matplotlib plots can be sent over.
* The html file is dynamically updated for long running scripts.

### Usage
``` python

    import logging, sys, numpy as np, pandas as pd, matplotlib.pyplot as plt
    import local_visualizer

    plt.style.use('fivethirtyeight')
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    # Create the local visualizer instance
    lviz = local_visualizer.LocalViz(html_file='lviz_test.html', port=9112)
    # INFO:root:Starting background server at: http://localhost:9112/.
    # INFO:local_visualizer:Click: http://carpediem:9112/lviz_test.html or http://localhost:9112/lviz_test.html

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
```

### Output
This starts a HTTPServer and creates a html file which is dynamically updated
each time ``lviz`` is called.

![Output image]( https://i.imgur.com/jjwvAX2.png "The output of the above commands")

### Support and Requirements
Python 2.7 (requires only std libraries).

### API methods
1. `p`: paragraph
2. `br`: line break
3. `hr`: Horizontal rule with line breaks
4. `h1`, `h2`, ..., `h6`: Headers
5. `write`: Directly write text to the html document (or pass in a `pandas.DataFrame`)
6. `figure`: Context manager which accepts the kwargs of `plt.figure` and returns a `plt.figure` object
7. `start`: Applicable if `LocalViz` was initialized with `lazy=True`. Starts the server and creates the html file
8. `close`: Deletes the html file

### Credits
This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
