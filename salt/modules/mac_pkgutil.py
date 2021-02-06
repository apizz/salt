"""
Installer support for macOS.

Installer is the native .pkg/.mpkg package manager for macOS.
"""

import os.path
import time
import urllib

import salt.utils.itertools
import salt.utils.mac_utils
import salt.utils.path
import salt.utils.platform
from salt.exceptions import SaltInvocationError

# Don't shadow built-in's.
__func_alias__ = {"list_": "list"}

__virtualname__ = "pkgutil"


def __virtual__():
    if not salt.utils.platform.is_darwin():
        return (False, "Only available on Mac OS systems")

    if not salt.utils.path.which("pkgutil"):
        return (False, "Missing pkgutil binary")

    return __virtualname__


def list_():
    """
    List the installed packages.

    :return: A list of installed packages
    :rtype: list

    CLI Example:

    .. code-block:: bash

        salt '*' pkgutil.list
    """
    cmd = "pkgutil --pkgs"
    ret = salt.utils.mac_utils.execute_return_result(cmd)
    return ret.splitlines()


def info(package_id):
    """
    Return information regarding a package id.

    :return: A dictionary of pkginfo for a package ID.
    :rtype: dict

    .. code-block:: bash

        salt '*' pkgutil.info com.apple.pkg.gcc4.2Leo
    """
    cmd = 'pkgutil --pkg-info {}'.format(package_id)
    if is_installed(package_id):
        result = salt.utils.mac_utils.execute_return_result(cmd)
        ret = dict(item.split(':') for item in result.splitlines())
    else:
        msg = 'Package ID {} is not installed'.format(package_id)
        raise SaltInvocationError(msg)
    return ret


def is_installed(package_id):
    """
    Returns whether a given package ID is installed.

    :return: True if installed, otherwise False
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' pkgutil.is_installed com.apple.pkg.gcc4.2Leo
    """
    return package_id in list_()


def _install_from_path(path):
    """
    Internal function to install a package from the given path
    """
    if not os.path.exists(path):
        msg = "File not found: {}".format(path)
        raise SaltInvocationError(msg)

    cmd = 'installer -pkg {} -target /'.format(path)
    return salt.utils.mac_utils.execute_return_success(cmd)


def install(source, package_id):
    """
    Install a .pkg from an URI or an absolute path.

    :param str source: The path to a package.

    :param str package_id: The package ID

    :return: True if successful, otherwise False
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' pkgutil.install source=/vagrant/build_essentials.pkg package_id=com.apple.pkg.gcc4.2Leo
    """
    if is_installed(package_id):
        return True

    uri = urllib.parse.urlparse(source)
    if not uri.scheme == "":
        msg = "Unsupported scheme for source uri: {}".format(uri.scheme)
        raise SaltInvocationError(msg)

    _install_from_path(source)

    return is_installed(package_id)


def install_time(package_id, convert=None):
    """
    Returns the install date and time of a given package ID in epoch time. Alternatively,
    converts to YYYY/MM/DD hh:mm:ss (%Y-%m-%d %H:%M:%S)

    :param bool convert

    :return: The install datetime of the given package ID
    :rtype: date

    CLI Example:

    .. code-block:: bash
        salt '*' pkgutil.install_date com.apple.pkg.gcc4.2Leo

    """
    time_fmt = '%Y-%m-%d %H:%M:%S'
    pkginfo = info(package_id)
    install_datetime = int(pkginfo['install-time'])
    if not convert:
        ret = install_datetime
    else:
        ret = time.strftime(time_fmt, time.localtime(install_datetime))
    return ret


def forget(package_id):
    """
    .. versionadded:: 2016.3.0

    Remove the receipt data about the specified package. Does not remove files.

    .. warning::
        DO NOT use this command to fix broken package design

    :param str package_id: The name of the package to forget

    :return: True if successful, otherwise False
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' pkgutil.forget com.apple.pkg.gcc4.2Leo
    """
    cmd = "pkgutil --forget {}".format(package_id)
    salt.utils.mac_utils.execute_return_success(cmd)
    return not is_installed(package_id)


def version(package_id):
    """
    Returns the version of a given package ID.

    :return: Package id version string
    :rtype: string

    CLI Example:

    .. code-block:: bash

        salt '*' pkgutil.version com.apple.pkg.gcc4.2Leo
    """
    ret = info(package_id)
    return ret['version']