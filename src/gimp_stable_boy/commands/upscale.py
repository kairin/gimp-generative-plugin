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


class UpscaleCommand(StableDiffusionCommand):
    uri = 'sdapi/v1/extra-single-image'

    proc_name = "stable-boy-upscale"
    blurb = "Stable Boy " + sb.__version__ + " - Upscale"
    help_text = "Stable Diffusion plugin for AUTOMATIC1111's WebUI API"
    menu_label = "Upscale"

    @classmethod
    def add_arguments(cls, procedure):
        procedure.add_argument_from_pdb("image", "pdb-gimp-image", "Input Image", "")
        procedure.add_argument_from_pdb("drawable", "pdb-gimp-drawable", "Input Drawable", "")
        procedure.add_int_argument("upscaling_resize", "Upscaling factor", 2, 1, 4)
        procedure.add_enum_argument("upscaler_1", "Upscaler 1", 0, sb.constants.UPSCALERS)
        procedure.add_enum_argument("upscaler_2", "Upscaler 2", 0, sb.constants.UPSCALERS)
        procedure.add_double_argument("extras_upscaler_2_visibility", "Upscaler 2 visibility", 0, 0, 1)

    def _make_request_data(self):
        return {
            'upscaling_resize': int(self.config.get_property('upscaling_resize')),
            'upscaler_1': sb.constants.UPSCALERS[self.config.get_property('upscaler_1')],
            'upscaler_2': sb.constants.UPSCALERS[self.config.get_property('upscaler_2')],
            'extras_upscaler_2_visibility': self.config.get_property('extras_upscaler_2_visibility'),
            'image': sb.gimp.encode_img(self.img, self.x, self.y, self.width, self.height),
        }

    def _estimate_timeout(self, req_data):
        return (60 if float(req_data['extras_upscaler_2_visibility']) > 0 else 30) * sb.config.TIMEOUT_FACTOR

    def _process_response(self, resp):
        self.images = [resp['image']]
        if self.images:
            sb.gimp.open_images(self.images)