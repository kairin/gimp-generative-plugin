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


class Img2ImgCommand(StableDiffusionCommand):
    uri = 'sdapi/v1/img2img'

    proc_name = "stable-boy-img2img"
    blurb = "Stable Boy " + sb.__version__ + " - Image to Image"
    help_text = "Stable Diffusion plugin for AUTOMATIC1111's WebUI API"
    menu_label = "Image to Image"

    # Parameters will be defined in main.py's do_create_procedure

    def _make_request_data(self):
        req_data = super()._make_request_data()
        req_data['denoising_strength'] = float(self.config.get_property('denoising_strength')) / 100
        req_data['init_images'] = [sb.gimp.encode_img(self.img, self.x, self.y, self.width, self.height)]
        return req_data

    def _process_response(self, resp):
        super()._process_response(resp)
        if self.images:
            sb.gimp.open_images(self.images)
        elif self.layers:
            sb.gimp.create_layers(self.img, self.layers, self.x, self.y)