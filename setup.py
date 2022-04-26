#!/usr/bin/env python

from setuptools.command import build_py
from setuptools import setup

import distutils
from distutils import errors

class BuildPyCommand(build_py.build_py):
  """Custom build command."""

  def run(self):
    self.run_command('js_build')
    build_py.build_py.run(self)

class JSBuildCommand(build_py.build_py):

  description = 'Build JS frontend'
  user_options = []


  def run(self):
    import subprocess
    import os
    import shutil
    
    """Run command."""
    if not self.dry_run:
      target_dir = os.path.join(self.build_lib, 'manus_webshell/frontend')

      self.mkpath(target_dir)

    self.run_command('js_deps')

    env = dict(**os.environ)
    env["BUILD_DIRECTORY"] = target_dir

    npm = shutil.which("npm")

    if npm is None:
      raise errors.DistutilsExecError("NPM executable not found")

    command = [npm, 'run', 'build']
    self.announce(
        'Running command: %s' % str(command),
        level=distutils.log.INFO)
    subprocess.check_call(command, env=env)
    self.announce("Done", level=distutils.log.INFO)


class JSNpmCommand(build_py.build_py):

  description = 'Install JS dependencies'
  user_options = []


  def run(self):
    import subprocess
    import shutil

    npm = shutil.which("npm")

    if npm is None:
      raise errors.DistutilsExecError("NPM executable not found")

    command = ['/usr/bin/npm', 'install']
    self.announce(
        'Running command: %s' % str(command),
        level=distutils.log.INFO)
    subprocess.check_call(command)


setup(name='manus_webshell',
	version='0.1',
	description='Web interface for the Manus project',
	author='Luka Cehovin Zajc',
	author_email='luka.cehovin@gmail.com',
	url='https://github.com/vicoslab/manus/',
	packages=['manus_webshell', 'manus_webshell.static'],
	package_data = {
		'manus_webshell.static': ['*.*'],
	},
	include_package_data=True,
  requires=['manus' 'tornado', 'echolib'],
  cmdclass={
      'js_deps': JSNpmCommand,
      'js_build': JSBuildCommand,
      'build_py': BuildPyCommand,
  },
)


