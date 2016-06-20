#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A multiprocess `Pool` variant with a `ProgressBar` and ncurses/blessings """


import time
from multiprocessing.pool import Pool
from progressbar import ProgressBar, Percentage, Bar, ETA

from blessings import Terminal

term = Terminal()

location = (0, 20)



class Writer(object):
    """Create an object with a write method that writes to a
    specific place on the screen, defined at instantiation.
    This is the glue between blessings and progressbar.
    """
    def __init__(self, location):
        """
        Input: location - tuple of ints (x, y), the position
                          of the bar in the terminal
        """
        self.location = location

    def write(self, string):
        with term.location(*self.location):
            print(string)



class ProgressPool(Pool):
    """ Extension of `multiprocessing.Pool` with `ProgressBar`.

    The `map` function now displays a progress bar. The usual caveats about
    multiprocessing not working in an interactive interpreter apply.

    """

    def map(self, func, iterable, chunksize=1, pbar='ProgressPool'):
        """ Apply function on iterables in available subprocess workers.

        Parameters
        ----------
        func : callable
            the function to execute
        iterable : iterable
            the arguments to the func
        chunksize : int, default: 1
            the approximate number of tasks to distribute to a process at once
        pbar : str or ProgressBar
            if str, use the string in a standard ProgressBar, else use the
            given ProgressBar

        Returns
        -------
        results : list
            the result of applying func to each value in iterables

        Raises
        ------
        TypeError if the pbar argument has the wrong type

        """
        # need to get the length, for the progress bar
        if not hasattr(iterable, '__len__'):
            iterable = list(iterable)
        total_items = len(iterable)

        # initialize the progress bar
        if isinstance(pbar, str):
            writer = Writer(location)
            pbar = ProgressBar(widgets=['%s: ' % pbar,
                Percentage(), Bar(), ETA()],
                maxval=total_items,fd=writer).start()
        elif isinstance(pbar, ProgressBar):
            pass
        else:
            raise TypeError("pbar must be of type 'string' or, "+\
                    "'ProgressBar' you gave: "+\
                    "'%s' of type %s" % (pbar, type(pbar)))

        # get the pool working asynchronously
        a_map = self.map_async(func, iterable, chunksize)

        # Crux: monitor the _number_left of the a_map, and update the progress
        # bar accordingly
        # TODO should probably check for termination on each run here
        while True:
            time.sleep(0.1)
            left = a_map._number_left
            pbar.update(total_items-left)
            if left == 0:
                break
        pbar.finish()
        return a_map.get()

