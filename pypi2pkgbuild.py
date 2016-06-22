#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import xmlrpc.client
import argparse
import re

from os.path import isdir, join, exists
from os import mkdir, getcwd

SOURCEFILE_TYPE_RE = re.compile(".*\.(tar|zip|gz|z|bz2?|xz)", re.IGNORECASE)

BLANK_PKGBUILD = """\
pkgname={data.pyversion}-{data.name}
_realname={data.name}
pkgver={data.version}
pkgrel=1
pkgdesc="{data.summary}"
url="{data.home_page}"
depends=('{data.pyversion}')
license=('{data.license}')
arch=('any')
source=('{data.download_url}')
md5sums=('{data.md5}')

build() {{
    cd $srcdir/$_realname-$pkgver
    {data.pyversion} setup.py build
}}

package() {{
    cd $srcdir/$_realname-$pkgver
    {data.pyversion} setup.py install --root="$pkgdir" --optimize=1
}}
"""

LICENSES = {
"License :: OSI Approved :: Apache Software License": "APACHE",
"License :: OSI Approved :: Artistic License": "Artistic2.0",
"License :: OSI Approved :: Common Public License": "CPL",
"License :: OSI Approved :: GNU Affero General Public License v3": "AGPL",
"License :: OSI Approved :: GNU Free Documentation License (FDL)": "FDL",
"License :: OSI Approved :: GNU General Public License (GPL)": "GPL",
"""License :: OSI Approved :: \
GNU Library or Lesser General Public License (LGPL)""": "LGPL",
"License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)": "MPL",
"License :: OSI Approved :: Python Software Foundation License": "PSF",
"License :: OSI Approved :: Zope Public License": "ZPL",
}

class AttrDict(dict):
    def __init__(self, *a, **kw):
        dict.__init__(self, *a, **kw)
        self.__dict__ = self

def get_data(package, version, client):
    if version:
        data = client.release_data(package, version)
    else:
        # Find the highest version
        versions = client.package_releases(package, True)
        if versions:
            version = max(versions)
            data = client.release_data(package, version)
        else:
            exit("No versions found for %s" % package)
    return data

def determine_license(classifiers):
    for license in LICENSES:
        if license in classifiers:
            return LICENSES[license]
    return "CUSTOM"

def write_pkgbuild(data):
    dir = join(getcwd(), data.name + "-" + data.version)
    if not isdir(dir):
        mkdir(dir)
    if exists(join(dir, "PKGBUILD")):
        exit("PKGBUILD does exist")
    with open(join(dir,"PKGBUILD"), "w") as f:
        f.write(BLANK_PKGBUILD.format(data=data))

def main():
    """docstring for main"""
    parser = argparse.ArgumentParser()

    parser.add_argument('package', type=str, help='The package')
    parser.add_argument('-u', '--url', type=str,
                        default='https://pypi.python.org/pypi',
                        help='URL of the PyPI XML-RPC')
    parser.add_argument('-v', '--version', type=str, 
                        help='Version of the package')
    args = parser.parse_args()

    client = xmlrpc.client.ServerProxy(args.url)

    try:
        data = get_data(args.package, args.version, client)
    except xmlrpc.client.Fault as err:
        exit("""Unable to retrieve release data for %s, version %s
                %s"""
                % (args.package, args.version, err))

    if not data:
        exit("The requested package %s, version %s does not exist" %
                (args.package, args.version))

    data["name"] = data["name"][7:] if data["name"].startswith("python-")\
        else data["name"]

    #
    # Find the correct download_url
    # We need this to get the md5sum
    #
    try:
        urls = client.release_urls(args.package, data["version"])
    except xmlrpc.client.Fault as err:
        exit("""Unable to retrieve release data for %s, version %s
                %s"""
                % (args.package, args.version, err))
    for url in urls:
        if SOURCEFILE_TYPE_RE.match(url["filename"]):
            data["download_url"] = url["url"]
            data["md5"] = url["md5_digest"]
        else:
            print(url["url"])

    #
    # Figure out which version of python is needed
    # TODO find a reliable way to do this
    # assume python2 for now
    #

    data["pyversion"] = "python2"
    print(
    "The required python version has automatically been set to python2")
    print("If that is not correct, please change it")

    data["license"] = data["license"] or determine_license(data["classifiers"])

    if not "md5" in data:
        data["md5"] = "unknown"

    data = AttrDict(data)

    write_pkgbuild(data)

if __name__ == '__main__':
    main()
