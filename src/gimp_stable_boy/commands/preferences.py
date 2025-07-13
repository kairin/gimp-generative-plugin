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

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp, GObject

import gimp_stable_boy as sb
from ._command import StableBoyCommand


class PreferencesCommand(StableBoyCommand):
    proc_name = "stable-boy-prefs"
    blurb = "Stable Boy " + sb.__version__ + " - Preferences"
    help_text = "Stable Diffusion plugin for AUTOMATIC1111's WebUI API"
    menu_label = "Preferences"

    @classmethod
    def add_arguments(cls, procedure):
        procedure.add_string_argument("api_base_url", "API URL", sb.constants.DEFAULT_API_URL, "")

    def __init__(self, image, config):
        self.config = config

    def run(self, procedure, run_mode, image, n_drawables, drawables, args, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(self.proc_name)
            dialog = GimpUi.ProcedureDialog(procedure)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

            config = dialog.get_config()
            dialog.destroy()
        else:
            config = procedure.create_config()

        # TODO: Implement preference saving for GIMP 3
        # sb.gimp.save_prefs(sb.constants.PREFERENCES_SHELF_GROUP, **config.get_properties())
        print("Warning: Preference saving is not yet implemented for GIMP 3.")

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())