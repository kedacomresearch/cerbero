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
from cerbero.utils import _, N_, ArgparseArgument

from cerbero.utils import messages as m
from hacks.build.profile import Package, BuildTools
from cerbero.errors import FatalError
from hacks.utils import MD5

class ProfileCommand(Command):
    doc = N_('Profile for package')
    name = 'profile'

    def __init__(self, force=None, no_deps=None):
            args = [
                ArgparseArgument('name', nargs='*',
                    help=_('name of the package')),

                ArgparseArgument('--gen-file', action='store_true',
                    default=False,
                    help=_('generate profile report (yaml)')),

                ArgparseArgument('--pkg-location', type=str,
                    default='.',
                    help=_('directory of package stored'))
                ]
            
            Command.__init__(self, args)

    def run(self, config, args):
        import datetime

        start = datetime.datetime.now()

        pm = Package(config)
        
        #_deps_graph(pm.packages())
        if args.gen_file and args.pkg_location is None:
            raise FatalError(_("You must set --pkg-location, if you wanto gen files."))

        for name in args.name:

            if name == 'build-tools':
                profile = BuildTools(config).get()
            else:
                profile = pm.get(name)

            pkgdir = args.pkg_location

            import yaml
            if args.gen_file:

                suffix='.yaml'
                if config.build_type == 'debug':
                    suffix = '-debug.yaml'

                filename = '%(name)s-%(platform)s-%(arch)s-%(version)s'%profile
                filename = filename + suffix
                for k,v in profile['tarball'].viewitems():
                    tarball = os.path.join(pkgdir,v['filename'])
                    if not os.path.exists(tarball):
                        raise FatalError(_("[%s] %s not exists."%(k,tarball)))

                    v['MD5Sum'] = MD5(tarball)
                    
                    


                path = os.path.join(pkgdir,filename)

                f = open( path,'w')
                yaml.dump( profile, f ,default_flow_style=False)
                f.close()
            else:
                print yaml.dump( profile, default_flow_style=False)

   


register_command(ProfileCommand)
