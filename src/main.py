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

                        # Add arguments based on the command class
                        if name == "stable-boy-txt2img":
                            procedure.add_argument_from_pdb("image", "pdb-gimp-image", "Input Image", "")
                            procedure.add_argument_from_pdb("drawable", "pdb-gimp-drawable", "Input Drawable", "")
                            procedure.add_string_argument("prompt", "Prompt", "", "")
                            procedure.add_string_argument("negative_prompt", "Negative prompt", "", "")
                            procedure.add_string_argument("seed", "Seed", "-1", "")
                            procedure.add_int_argument("steps", "Steps", 25, 1, 150) # Min, Max
                            procedure.add_enum_argument("sampler_index", "Sampler", 0, sb.constants.SAMPLERS)
                            procedure.add_boolean_argument("restore_faces", "Restore faces", False)
                            procedure.add_double_argument("cfg_scale", "CFG", 7.5, 0, 20) # Min, Max
                            procedure.add_int_argument("num_images", "Number of images", 1, 1, 4) # Min, Max
                            procedure.add_enum_argument("img_target", "Results as", 0, sb.constants.IMAGE_TARGETS)
                        elif name == "stable-boy-inpaint":
                            procedure.add_argument_from_pdb("image", "pdb-gimp-image", "Input Image", "")
                            procedure.add_argument_from_pdb("drawable", "pdb-gimp-drawable", "Input Drawable", "")
                            procedure.add_string_argument("prompt", "Prompt", "", "")
                            procedure.add_string_argument("negative_prompt", "Negative prompt", "", "")
                            procedure.add_string_argument("seed", "Seed", "-1", "")
                            procedure.add_int_argument("steps", "Steps", 25, 1, 150)
                            procedure.add_enum_argument("sampler_index", "Sampler", 0, sb.constants.SAMPLERS)
                            procedure.add_boolean_argument("restore_faces", "Restore faces", False)
                            procedure.add_double_argument("cfg_scale", "CFG", 7.5, 0, 20)
                            procedure.add_double_argument("denoising_strength", "Denoising strength %", 50.0, 0, 100)
                            procedure.add_boolean_argument("autofit_inpainting", "Autofit inpainting region", True)
                            procedure.add_int_argument("mask_blur", "Mask blur", 4, 0, 32)
                            procedure.add_enum_argument("inpainting_fill", "Inpainting fill", 1, sb.constants.INPAINTING_FILL_MODE)
                            procedure.add_boolean_argument("inpaint_full_res", "Inpaint at full resolution", True)
                            procedure.add_int_argument("inpaint_full_res_padding", "Full res. inpainting padding", 0, 0, 256)
                            procedure.add_int_argument("num_images", "Number of images", 1, 1, 4)
                            procedure.add_enum_argument("img_target", "Results as", 0, sb.constants.IMAGE_TARGETS)
                            procedure.add_boolean_argument("apply_inpainting_mask", "Apply inpainting mask", True)
                        elif name == "stable-boy-img2img":
                            procedure.add_argument_from_pdb("image", "pdb-gimp-image", "Input Image", "")
                            procedure.add_argument_from_pdb("drawable", "pdb-gimp-drawable", "Input Drawable", "")
                            procedure.add_string_argument("prompt", "Prompt", "", "")
                            procedure.add_string_argument("negative_prompt", "Negative prompt", "", "")
                            procedure.add_string_argument("seed", "Seed", "-1", "")
                            procedure.add_int_argument("steps", "Steps", 25, 1, 150)
                            procedure.add_enum_argument("sampler_index", "Sampler", 0, sb.constants.SAMPLERS)
                            procedure.add_boolean_argument("restore_faces", "Restore faces", False)
                            procedure.add_double_argument("cfg_scale", "CFG", 7.5, 0, 20)
                            procedure.add_double_argument("denoising_strength", "Denoising strength %", 50.0, 0, 100)
                            procedure.add_int_argument("num_images", "Number of images", 1, 1, 4)
                            procedure.add_enum_argument("img_target", "Results as", 0, sb.constants.IMAGE_TARGETS)
                        elif name == "stable-boy-upscale":
                            procedure.add_argument_from_pdb("image", "pdb-gimp-image", "Input Image", "")
                            procedure.add_argument_from_pdb("drawable", "pdb-gimp-drawable", "Input Drawable", "")
                            procedure.add_int_argument("upscaling_resize", "Upscaling factor", 2, 1, 4)
                            procedure.add_enum_argument("upscaler_1", "Upscaler 1", 0, sb.constants.UPSCALERS)
                            procedure.add_enum_argument("upscaler_2", "Upscaler 2", 0, sb.constants.UPSCALERS)
                            procedure.add_double_argument("extras_upscaler_2_visibility", "Upscaler 2 visibility", 0, 0, 1)

                        # Add other commands' arguments here
                        elif name == "stable-boy-prefs":
                            procedure.add_string_argument("api_base_url", "API URL", sb.constants.DEFAULT_API_URL, "")

                        return procedure

        return None


Gimp.main(StableBoy.__gtype__, sys.argv)
