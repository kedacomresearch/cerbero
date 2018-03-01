# cerbero - a multi-platform build system for Open Source software
# Copyright (C) 2012 Andoni Morales Alastruey <ylatuya@gmail.com>
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
import hashlib
import yaml

from cerbero.commands import Command, register_command
from cerbero.build.cookbook import CookBook
from cerbero.build.oven import Oven
from cerbero.utils import _, N_, ArgparseArgument ,shell
from cerbero.utils import messages as m

#from hacks.build.abstract import Abstract
from hacks.utils.shell import cache

from hacks.build.profile import Package,BuildTools
from cerbero.errors import FatalError


class InstLog(object):

    def __init__(self,profile,prefix, cat):
        self.profile = profile
        self.prefix  = prefix
        self.cat     = cat
        self.path    = os.path.join(prefix, profile['name'] +'@'+ cat + '.yaml')
        self.info = None
        if os.path.exists(self.path):
            self.info = yaml.load(open(self.path))


    def is_installed(self):
        if self.info is None:
            return False

        assert self.info['version'] == self.profile['version']
        assert self.info['name'] == self.profile['name']
        assert self.info['version'] == self.profile['version']
        assert self.info['type'] == self.cat
        assert self.info['filename'] ==self.profile['tarball'][self.cat]['filename']
        assert self.info['MD5Sum'] == self.profile['tarball'][self.cat]['MD5Sum']

        return True

    def write(self):
        f = open(self.path,'w')
        yaml.dump({
            'name':self.profile['name'],
            'version':self.profile['version'],
            'type':self.cat,
            'filename':self.profile['tarball'][self.cat]['filename'],
            'MD5Sum': self.profile['tarball'][self.cat]['MD5Sum']
        },f,default_flow_style=False)
        f.close()
        
class Installer(Command):
    doc = N_('Install package .')
    name = 'install'

    def __init__(self, force=None, no_deps=None):
        args = [
            ArgparseArgument('name', nargs='*',
                help=_('name of the elements to be installed')),

            ArgparseArgument('--repo', type=str,                    
                help=_('respsitory of the package.')),
                
            ArgparseArgument('--deps-only', action='store_true',
                default=False,
                help=_('install dependent packages only.')),

            ArgparseArgument('--no-deps', action='store_true',
                default=False,
                help=_('not install dependent packages only.')),

            ArgparseArgument('--no-devel', action='store_true',
                default=False,
                help=_('not install devel package.')),

            ArgparseArgument('--cache-dir', type=str, default='.',
                help=_('directory where dowanlod packaged to store')),

            ArgparseArgument('--prefix', type=str, default=None,
                help=_('destination dir to install.'))

            ]
        
        Command.__init__(self, args)

    def _build_tools(self):
        self._unpack('build-tools')

    def _package(self,name):
        profile = self.profile[name]

        if self.args.deps_only:
            packages = []
            for name, p in profile['dependencies'].viewitems():
                packages.append(name)

        elif self.args.no_deps:
            packages = [name]
        else:
            packages = [name]
            for k ,v in profile.get('dependencies',{}).viewitems():
                packages.append(k)

        cats = ['runtime','devel']
        if self.args.no_devel:
            cats =['runtime']

        for pkg in packages:
            self._unpack( pkg , cats )


    def _cache_bundle(self,path):
        bundle = yaml.load( open(path))
        packages = bundle['packages']

        platform = self.config.target_platform
        arch = self.config.target_arch

        for name, pkg in bundle['packages'].viewitems():
            profile = pkg.get('profile',None)

            if profile:                
                for name in profile.get(platform,{}).get(arch ,[]):
                    url = os.path.join(self.args.repo,name)

                    path = cache( url, self.args.cache_dir )

                    p = yaml.load( open(path) )
                    pkgname = p['name']
                    p['__dir__'] = self.args.repo
                    if self.config.build_type == 'debug':
                        if p.get('debug',False):
                            self.profile[pkgname] = p
                        else:
                            if self.profile.get(pkgname,None) is None:
                                self.profile[pkgname] = p
                    else:
                        if not p.get('debug',False):
                            self.profile[pkgname] = p
            else:
                assert(0)



    def _load_release(self):
        rls = os.path.join(self.args.repo,'bundle.yaml')

        if os.path.exists(self.args.repo) and not os.path.exists(rls):
            pkgs = Package(self.config).packages()
            pkgs['build-tools'] = BuildTools(self.config).get()
            for name,profile in pkgs.viewitems():
                filename = '%(name)s-%(platform)s-%(arch)s-%(version)s.yaml'%profile
                path = os.path.join(self.args.repo,filename)
                if os.path.exists(path):
                    pro = yaml.load(open(path))
                    pro['__file__'] = path

                    if pro['version'] != profile['version']:
                        m.warning('skip %s since %s != %s'%(name,pro['version'] , profile['version'] ))
                    else:
                        self.profile[profile['name']] = pro
                else:
                    self.profile[profile['name']] = profile
        else:
            
            url  = os.path.join( self.args.repo , 'bundle.yaml' )
            path = cache( url, self.args.cache_dir )
            self._cache_bundle(path)
            

    def _unpack(self,name, cats=['devel','runtime'], version = None):
        profile = self.profile[name]
        #ppath = profile.get('__file__',None)
        #if ppath is None or not os.path.exists( ppath ):
        #    m.error('package <%s> not exists!'%name)
        #    raise FatalError('install package failed')

        path = profile.get('__file__',None)
        if path:
            if not os.path.exists(path):
                m.error('package <%s> not exists!'%name)
                raise FatalError('install package failed')
            d = os.path.dirname(profile['__file__'])
        else:
            d = profile.get('__dir__',None)
        assert d,'!!!!!!!'

        prefix = self.args.prefix
        if prefix is None:
            if name == 'build-tools':
                prefix = self.config.build_tools_prefix
            else:
                prefix = self.config.prefix

        #profile path
        ip = os.path.join(prefix,name +'.yaml')
        if os.path.exists( ip ):
            pro = yaml.load(open(ip))
            if version:
                m.error('installed package %s version %s not consistent with require %s'%(
                    name, pro['version'],version
                ))
                raise FatalError("install package failed.")
            else:
                m.message('package %s (%s) already installed.'%(name,pro['version']))
                return

        for cat,info in profile['tarball'].viewitems():

            filename = info['filename']
            url = os.path.join( d , filename )
            path = cache( url, self.args.cache_dir )
            assert os.path.exists(path)

            shell.unpack( path, prefix)

        yaml.dump( profile, open( ip,'w') ,default_flow_style=False)
        m.message('package <%s> installation done.'%name)


    def run(self, config, args):
        self.config = config
        self.args = args
        self.profile={}

        self._load_release()
        for name in args.name:
            if self.profile.get(name,None) is None \
               and  not self.args.deps_only:
               m.error("can not find package of %s from profiles."%name)
               raise FatalError("can not find package of %s from profiles."%name)
            if name == 'build-tools':
                self._build_tools()
            else:
                self._package(name)

register_command(Installer)
