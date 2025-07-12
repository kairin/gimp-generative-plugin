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

    # Parameters will be defined in main.py's do_create_procedure
    # For reference, old params were:
    # (gimpfu.PF_STRING, 'prompt', 'Prompt', ''),
    # (gimpfu.PF_STRING, 'negative_prompt', 'Negative prompt', ''),
    # (gimpfu.PF_STRING, 'seed', 'Seed', '-1'),
    # (gimpfu.PF_SLIDER, 'steps', 'Steps', 25, (1, 150, 25)),
    # (gimpfu.PF_OPTION, 'sampler_index', 'Sampler', 0, sb.constants.SAMPLERS),
    # (gimpfu.PF_BOOL, 'restore_faces', 'Restore faces', False),
    # (gimpfu.PF_SLIDER, 'cfg_scale', 'CFG', 7.5, (0, 20, 0.5)),
    # (gimpfu.PF_SLIDER, 'num_images', 'Number of images', 1, (1, 4, 1)),
    # (gimpfu.PF_OPTION, 'img_target', 'Results as', 0, sb.constants.IMAGE_TARGETS),

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
