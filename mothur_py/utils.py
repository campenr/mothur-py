"""
Copyright (c) 2018 Richard Campen
All rights reserved.

Licensed under the Modified BSD License.
For full license terms see LICENSE.txt

"""

import collections


def format_mothur_params(*args, **kwargs):
    """Formats mothur command paramters from python variables into a string formatted for mothur."""

    # list of available converter functions for making python variables mothur compatible
    converters = [
        convert_mothur_bool,
        convert_mothur_iterable
    ]

    # use the converters to alter parameter values as necessary for mothur compatibility
    formatted_args = ''
    if args:
        for arg in args:
            for converter in converters:
                arg = converter(arg)
        formatted_args = ','.join(args)

    formatted_kwargs = ''
    if kwargs:
        for k, v in kwargs.items():
            for converter in converters:
                kwargs[k] = converter(v)
        formatted_kwargs = ','.join('%s=%s' % (k, v) for k, v in kwargs.items())

    # format command string from available command parameters
    if len(formatted_args) == 0:
        mothur_args = formatted_kwargs
    else:
        mothur_args = formatted_args
        if len(formatted_kwargs) > 0:
            mothur_args = mothur_args + ',' + formatted_kwargs

    return mothur_args


def convert_mothur_bool(item):
    """Converts python bool into a format that is compatible with mothur."""

    if item is True:
        return 'T'
    elif item is False:
        return 'F'
    else:
        return item


def convert_mothur_iterable(item):
    """Converts python iterable into a format that is compatible with mothur."""

    # convert python iterable, excluding strings, to mothur list
    if isinstance(item, collections.Sequence) and not isinstance(item, str):
        # mothur lists are hyphen separated
        return ('-').join(item)
    else:
        return item