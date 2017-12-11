# Copyright 2017 Sqwishy Trick. All rights reserved.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
''' winrustler is a python script that facilitates moving windows on MS Windows

winrustler can be invoked from a command prompt

winrustler can also imported as a library, although I have no idea why you
would want to do that.
'''

import sys
import argparse

from winrustler.core import get_module
from winrustler.windows import WindowCollection


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('function')

    args, remaining = parser.parse_known_args()
    module = get_module(args.function)
    args = module.parser.parse_args(remaining)
    module.run_from_args(WindowCollection(), args)


if __name__ == '__main__':
    main()
