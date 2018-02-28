


import os
import sys
import re
import tempfile
import platform
import tarfile
import json  

from cerbero.build.cookbook import CookBook
from cerbero.packages.packagesstore import PackagesStore
from cerbero.packages.package import SDKPackage
from cerbero.utils import messages as m
from cerbero.utils import shell, parse_file

from cerbero.packages import PackageType
from cerbero.packages.disttarball import DistTarball
from hacks.utils import MD5
from cerbero.errors import FatalError

from cerbero.bootstrap.build_tools import BuildTools as Build_Tools


class Package(object):



    def __init__(self,config ):
        self.config = config
        self.store  = PackagesStore(config)
        self.cookbook = CookBook(config)
        self.packages_ = None

    
    def _recipes(self,package):
        '''
        return the recipes (name:version) dict included in the package (not include in deps packages)
        
        '''
        
        all = package.recipes_dependencies()
        
        rdeps=[]
        for pkg in self.store.get_package_deps( package.name):
            rdeps.extend( pkg.recipes_dependencies())
        rnames = list(set(all).difference(set(rdeps)))
        recipes ={}
        for name in rnames:
            recipes[name] = self.cookbook.get_recipe(name).version
        return recipes


    def get_recipes(self,package):
        '''
        return the recipes (name:version) dict included in the package (not include in deps packages)
        
        '''

        if isinstance (package,SDKPackage):
            recipes={}
            for p in self.store.get_package_deps(package):
                recipes.update( self._recipes( p) )
            return recipes
        
        return self._recipes(package)

    def get_packages_deps(self,package):
        '''
        return the packages of the SDK/package dependent.
        
        '''

        dependencies = []

        if isinstance (package,SDKPackage):
            if hasattr(package, 'dependencies'):
                dependencies = package.dependencies
            return []
        else:
            dependencies = [p.name for p in self.store.get_package_deps(package.name, False)]

        deps = {}
        for name in dependencies:            
            version = self.store.get_package(name).version
            deps[name] = version
        return deps



    def _pkg(self,package):

        

        t = DistTarball(self.config,package,self.store)
        tarball={}

        for ptype in [PackageType.DEVEL,PackageType.RUNTIME]:
            TNAME={PackageType.DEVEL:'devel',PackageType.RUNTIME:'runtime'}
            tarball[TNAME[ptype]]={
                'filename':t._get_name(ptype)
            }
        
        return {
            'name':package.name,
            'version':package.version,
            'platform':self.config.target_platform,
            'arch':self.config.target_arch,
            'recipes': self.get_recipes(package),
            'dependencies': self.get_packages_deps(package),

            #'deps': [p.name for p in self.store.get_package_deps(package.name, True)],
            #'direct.deps': [p.name for p in self.store.get_package_deps(package.name, False)],
            'tarball': tarball
        }

    def get(self,name):
        if self.packages_ is None:
            self.packages()
        return self.packages_[name]

    def packages(self):
        if self.packages_ is None:
            self.packages_ = {}
            for pkg in self.store.get_packages_list():
                #if isinstance (pkg,SDKPackage):
                #    continue
                self.packages_[pkg.name] = self._pkg( pkg )

        return self.packages_


class BuildTools(object):

    def __init__(self, config):
        self.config = config
        self._profile = None


    def _get(self):

        tools = Build_Tools(self.config)
        store  = PackagesStore(self.config)
        cookbook = CookBook(self.config)

        names  = tools.BUILD_TOOLS
        names += tools.PLAT_BUILD_TOOLS.get(self.config.platform, [])
        recipes ={}
        path = os.path.join(self.config.packages_dir,'custom.py')
        d={}
        parse_file(path,d )
        version = d['GStreamer'].version

        for name in names:
            recipes[name] = cookbook.get_recipe(name).version

        pkgname ='build-tools'

        tarball = '%s-%s-%s-%s'%( pkgname,
            self.config.platform,
            self.config.arch,
            version
        )

        return {
            'name':pkgname,
            'version': version,
            'prefix':self.config.build_tools_prefix,
            'deps':[],
            'platform':self.config.platform,
            'arch':self.config.arch,

            'tarball':{
                'runtime':{ 'filename':tarball +'.tar.bz2'}
            },
            'recipes': recipes
        }

    def get(self):
        if self._profile is None:
            self._profile = self._get()
        return self._profile

