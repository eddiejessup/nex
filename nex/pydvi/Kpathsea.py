"""
This module provides a wrapper for the **Kpathsea** library, cf. http://www.tug.org/kpathsea.
"""

__all__ = ['kpsewhich']

import logging
import subprocess

_module_logger = logging.getLogger(__name__)

_cache = {}


def kpsewhich(filename, file_format=None, options=None):
    """Wrapper around the :command:`kpsewhich` command, cf. kpsewhich(1).

    *file_format*
      used to specify the file format, see :command:`kpsewhich` help for the file format list.

    *options*
      additional option for :command:`kpsewhich`.

    Examples::

       >>> kpsewhich('cmr10', file_format='tfm')
       '/usr/share/texmf/fonts/tfm/public/cm/cmr10.tfm'
    """
    key = '{}-{}-{}'.format(filename, file_format, options)
    if key in _cache:
        return _cache[key]

    command = ['kpsewhich']
    if file_format is not None:
        command.append("--format='%s'" % (file_format))
    if options is not None:
        command.append(options)
    command.append(filename)

    shell_command = ' '.join(command)
    _module_logger.debug('Run shell command: ' + shell_command)
    pipe = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE)
    stdout = pipe.communicate()[0]
    _module_logger.debug('stdout:\n' + stdout.decode('utf-8'))
    path = stdout.rstrip().decode('utf-8')
    path = path if path else None  # Fixme: could raise an exception

    _cache[key] = path
    return path
