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
from ._command import StableDiffusionCommand


class Txt2ImgCommand(StableDiffusionCommand):
    uri = 'sdapi/v1/txt2img'

    proc_name = "stable-boy-txt2img"
    blurb = "Stable Boy " + sb.__version__ + " - Text to Image"
    help_text = "Stable Diffusion plugin for AUTOMATIC1111's WebUI API"
    menu_label = "Text to Image"
    # menu_path is already defined in StableBoyCommand

    @classmethod
    def add_arguments(cls, procedure):
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

    def _make_request_data(self):
        data = super()._make_request_data()
        # Txt2Img specific parameters can be added here if any
        return data

    def _process_response(self, resp):
        super()._process_response(resp)
        if self.images:
            sb.gimp.open_images(self.images)
        elif self.layers:
            sb.gimp.create_layers(self.img, self.layers, self.x, self.y)
