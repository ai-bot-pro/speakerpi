# -*- coding: utf-8-*-
import os
import sys
import time
import socket
import subprocess
import pkgutil
import logging
import pip.req
import appPath

if sys.version_info < (3, 3):
    from distutils.spawn import find_executable
else:
    from shutil import which as find_executable

logger = logging.getLogger(__name__)

def check_network_connection(server="www.baidu.com"):
    """
    @Brief:
        Checks if pi can connect a network server.

    @Arguments:
        server -- (optional) the server to connect with (Default:
                  "www.baidu.com")

    @Returns:
        True or False
    """
    logger.debug("Checking network connection to server '%s'...", server)
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        host = socket.gethostbyname(server)
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection((host, 80), 2)
    except Exception:
        logger.debug("Network connection not working")
        return False
    else:
        logger.debug("Network connection working")
        return True


def check_executable(executable):
    """
    @brief:
        Checks if an executable exists in $PATH.

    @Arguments:
        executable -- the name of the executable (e.g. "echo")

    @Returns:
        True or False
    """
    logger.debug("Checking executable '%s'...", executable)
    executable_path = find_executable(executable)
    found = executable_path is not None
    if found:
        logger.debug("Executable '%s' found: '%s'", executable,
                     executable_path)
    else:
        logger.debug("Executable '%s' not found", executable)
    return found


def check_python_import(package_or_module):
    """
    @brief:
        Checks if a python package or module is importable.

    @Arguments:
        package_or_module -- the package or module name to check

    @Returns:
        True or False
    """
    logger.debug("Checking python import '%s'...", package_or_module)
    loader = pkgutil.get_loader(package_or_module)
    found = loader is not None
    if found:
        logger.debug("Python %s '%s' found: %r",
                     "package" if loader.is_package(package_or_module)
                     else "module", package_or_module, loader.get_filename())
    else:
        logger.debug("Python import '%s' not found", package_or_module)
    return found


def get_pip_requirements(fname=os.path.join(appPath.LIB_PATH, 'requirements.txt')):
    """
    Gets the PIP requirements from a text file. If the files does not exists
    or is not readable, it returns None

    Arguments:
        fname -- (optional) the requirement text file (Default:
                 "client/requirements.txt")

    Returns:
        A list of pip requirement objects or None
    """
    if os.access(fname, os.R_OK):
        reqs = list(pip.req.parse_requirements(fname))
        logger.debug("Found %d PIP requirements in file '%s'", len(reqs),
                     fname)
        return reqs
    else:
        logger.debug("PIP requirements file '%s' not found or not readable",
                     fname)


def get_git_revision():
    """
    Gets the current git revision hash as hex string. If the git executable is
    missing or git is unable to get the revision, None is returned

    Returns:
        A hex string or None
    """
    if not check_executable('git'):
        logger.warning("'git' command not found, git revision not detectable")
        return None
    output = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()
    if not output:
        logger.warning("Couldn't detect git revision (not a git repository?)")
        return None
    return output


