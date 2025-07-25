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
from .image_to_image import Img2ImgCommand
from ._command import StableDiffusionCommand


class InpaintingCommand(Img2ImgCommand):
    uri = 'sdapi/v1/img2img'

    proc_name = "stable-boy-inpaint"
    blurb = "Stable Boy " + sb.__version__ + " - Inpainting"
    help_text = "Stable Diffusion plugin for AUTOMATIC1111's WebUI API"
    menu_label = "Inpainting"

    @classmethod
    def add_arguments(cls, procedure):
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

    def __init__(self, image, config):
        super().__init__(image, config)
        self.autofit_inpainting = self.config.get_property('autofit_inpainting')
        self.apply_inpainting_mask = self.config.get_property('apply_inpainting_mask')


    def _make_request_data(self):
        req_data = super()._make_request_data()
        req_data['inpainting_mask_invert'] = 1
        req_data['inpainting_fill'] = self.config.get_property('inpainting_fill')
        req_data['mask_blur'] = self.config.get_property('mask_blur')
        req_data['inpaint_full_res'] = self.config.get_property('inpaint_full_res')
        req_data['inpaint_full_res_padding'] = self.config.get_property('inpaint_full_res_padding')
        req_data['mask'] = sb.gimp.encode_mask(self.img, self.x, self.y, self.width, self.height)
        return req_data

    def _determine_active_area(self):
        if self.autofit_inpainting:
            return sb.gimp.autofit_inpainting_area(self.img)
        else:
            # Need to call the grandparent's method directly
            return StableDiffusionCommand._determine_active_area(self)

    def _process_response(self, resp):
        super()._process_response(resp) # Calls Img2ImgCommand._process_response
        if self.images:
            sb.gimp.open_images(self.images)
        elif self.layers:
            sb.gimp.create_layers(self.img, self.layers, self.x, self.y, self.apply_inpainting_mask)
