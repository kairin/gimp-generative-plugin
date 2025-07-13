#!/usr/bin/env python
#
# Stable Boy
# Copyright (C) 2022-2023 Torben Giesselmann
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ssl
from glob import glob
import os, sys
from importlib import import_module
import inspect

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gimp, GimpUi, Gio

# Fix relative imports in Windows
path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, path)
import gimp_stable_boy as sb


def is_cmd(obj):
    return inspect.isclass(obj) and obj.__name__ not in ['StableBoyCommand', 'StableDiffusionCommand'] \
        and 'StableBoyCommand' in [cls.__name__ for cls in inspect.getmro(obj)]


# GIMP 3.0 requires plugins to be classes that inherit from Gimp.PlugIn.
class StableBoy(Gimp.PlugIn):

    # This method is called by GIMP to query the procedures that this plugin provides.
    def do_query_procedures(self):
        cmd_module_locations = [['gimp_stable_boy', 'commands']]
        if sb.config.ENABLE_SCRIPTS:
            cmd_module_locations.append(['gimp_stable_boy', 'commands', 'scripts'])

        procedures = []
        for cmd_module_loc in cmd_module_locations:
            cmd_module_names = ['.'.join(cmd_module_loc) + '.' + os.path.splitext(os.path.basename(c))[0]
                                for c in glob(os.path.join(os.path.dirname(__file__), *(cmd_module_loc + ['*.py'])))]
            for cmd_module_name in cmd_module_names:
                for _, cmd_cls in (inspect.getmembers(import_module(cmd_module_name), is_cmd)):
                    if cmd_cls.proc_name not in procedures:
                        procedures.append(cmd_cls.proc_name)
        return procedures

    # This method is called by GIMP to create a new procedure.
    def do_create_procedure(self, name):
        cmd_module_locations = [['gimp_stable_boy', 'commands']]
        if sb.config.ENABLE_SCRIPTS:
            cmd_module_locations.append(['gimp_stable_boy', 'commands', 'scripts'])

        for cmd_module_loc in cmd_module_locations:
            cmd_module_names = ['.'.join(cmd_module_loc) + '.' + os.path.splitext(os.path.basename(c))[0]
                                for c in glob(os.path.join(os.path.dirname(__file__), *(cmd_module_loc + ['*.py'])))]
            for cmd_module_name in cmd_module_names:
                for _, cmd_cls in (inspect.getmembers(import_module(cmd_module_name), is_cmd)):
                    if cmd_cls.proc_name == name:
                        # Create a new Gimp.ImageProcedure.
                        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, cmd_cls.run, None)
                        procedure.set_image_types(cmd_cls.image_types)
                        procedure.set_sensitivity_mask(cmd_cls.sensitivity_mask)
                        procedure.set_menu_label(cmd_cls.menu_label)
                        procedure.add_menu_path(cmd_cls.menu_path)
                        procedure.set_documentation(cmd_cls.blurb, cmd_cls.help_text, name)
                        cmd_cls.add_arguments(procedure)
                        return procedure

        return None


Gimp.main(StableBoy.__gtype__, sys.argv)
