# Cerbero Package Manager ,Inspire by ArchLinux Pacman
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import os

from cerbero.commands import Command, register_command
from cerbero.build.cookbook import CookBook
from cerbero.build.oven import Oven
from cerbero.utils import _, N_, ArgparseArgument,shell

from cerbero.utils import messages as m
from hacks.build.profile import BuildTools
from cerbero.errors import FatalError

class Tar(Command):
    doc = N_('Tar and pckage specifal item (build-tools, prefix )')
    name = 'tar'

    def __init__(self, force=None, no_deps=None):
            args = [
                ArgparseArgument('name', nargs='*',
                    help=_('name of the package')),

                ArgparseArgument('--output-dir', type=str,
                    default='.',
                    help=_('directory of package stored'))
                ]
            
            Command.__init__(self, args)

    def run(self, config, args):

        import tarfile
        for name in args.name:

            if name == 'build-tools':
                profile = BuildTools( config ).get()
                filename = profile['tarball']['runtime']['filename']
                path = os.path.join(args.output_dir,filename)
                srcd = config.build_tools_prefix
            else:
                print "invalid tar object %s, (build-tools)."%name
                raise FatalError(_("invalid tar object %s, (build-tools)."%name))

            tar = tarfile.open(path, "w:bz2")
            for name in os.listdir(srcd):
                tar.add(os.path.join(srcd,name),name)
            tar.close()

   


register_command( Tar )
