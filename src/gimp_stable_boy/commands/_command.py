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

import json
import socket
import hashlib
import tempfile
from threading import Thread
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from collections import namedtuple

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from gimp_stable_boy.command_runner import config
import gimp_stable_boy as sb
from gimp_stable_boy.constants import PREFERENCES_SHELF_GROUP as PREFS


class StableBoyCommand:
    LayerResult = namedtuple('LayerResult', 'name img children')

    proc_name = ""
    blurb = ""
    help_text = ""
    author = "Torben Giesselmann"
    copyright = "Torben Giesselmann"
    date = "2023"
    menu_label = ""
    menu_path = ["<Image>/Stable Boy"]
    image_types = "*"
    sensitivity_mask = Gimp.ProcedureSensitivityMask.DRAWABLE

    @classmethod
    def run(cls, procedure, run_mode, image, n_drawables, drawables, args, data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(cls.proc_name)
            dialog = GimpUi.ProcedureDialog(procedure)
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

            config = dialog.get_config()
            dialog.destroy()
        else:
            config = procedure.create_config()
            config.set_property("image", image)

        # Save preferences
        # sb.gimp.save_prefs(cls.proc_name, **config.get_properties())

        command = cls(image, config)
        command.start()
        Gimp.progress_init(f"Running {cls.menu_label}...")

        while command.is_alive():
            Gimp.progress_update(0.5)
            Gimp.context_pop()
            GLib.usleep(100000)
            Gimp.context_push()

        Gimp.progress_end()

        if command.status == 'ERROR':
            error = GLib.Error.new_literal(Gimp.PlugIn.error_quark(), command.error_msg, 0)
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, error)

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


class StableDiffusionCommand(StableBoyCommand, Thread):
    uri = ''

    def __init__(self, image, config):
        Thread.__init__(self)
        self.img = image
        self.config = config
        self.status = 'INITIALIZED'
        self.url = urljoin(sb.gimp.pref_value(PREFS, 'api_base_url', sb.constants.DEFAULT_API_URL), self.uri)
        self.images = None
        self.layers = None
        self.x, self.y, self.width, self.height = self._determine_active_area()
        print('x, y, w, h: ' + str(self.x) + ', ' + str(self.y) + ', ' + str(self.width) + ', ' + str(self.height))
        self.img_target = sb.constants.IMAGE_TARGETS[self.config.get_property('img_target')]  # layers are the default img_target
        self.req_data = self._make_request_data()
        if config.TIMEOUT_REQUESTS:
            self.timeout = self._estimate_timeout(self.req_data)
        else:
            self.timeout = socket._GLOBAL_DEFAULT_TIMEOUT  # type: ignore

    def run(self):
        self.status = 'RUNNING'
        try:
            if config.LOG_REQUESTS:
                req_path = tempfile.mktemp(prefix='req_', suffix='.json')
                with open(req_path, 'w') as req_file:
                    print('request: ' + req_path)
                    req_file.write(json.dumps(self.req_data))
            sd_request = Request(url=self.url,
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(self.req_data).encode('utf-8'))
            # print(self.req_data)
            self.sd_resp = urlopen(sd_request, timeout=self.timeout)
            if self.sd_resp:
                self.response = json.loads(self.sd_resp.read())
                if config.LOG_REQUESTS:
                    resp_path = tempfile.mktemp(prefix='resp_', suffix='.json')
                    with open(resp_path, 'w') as resp_file:
                        print('response: ' + resp_path)
                        resp_file.write(json.dumps(self.response))
                self._process_response(self.response)
            self.status = 'DONE'
        except Exception as e:
            self.status = 'ERROR'
            self.error_msg = str(e)
            print(e)
            # Re-raising the exception is not necessary here as it's handled in the main thread
            # raise e

    def _process_response(self, resp):

        def _mk_short_hash(img):
            return hashlib.sha1(img.encode("UTF-8")).hexdigest()[:7]

        all_imgs = resp['images']
        if self.img_target == 'Layers':
            self.layers = [StableDiffusionCommand.LayerResult(_mk_short_hash(img), img, None) for img in all_imgs]
        elif self.img_target == 'Images':
            self.images = all_imgs

    def _determine_active_area(self):
        return sb.gimp.active_area(self.img)

    def _make_request_data(self):
        return {
            'prompt': self.config.get_property('prompt'),
            'negative_prompt': self.config.get_property('negative_prompt'),
            'steps': self.config.get_property('steps'),
            'sampler_index': sb.constants.SAMPLERS[self.config.get_property('sampler_index')],
            'batch_size': int(self.config.get_property('num_images')),
            'cfg_scale': self.config.get_property('cfg_scale'),
            'seed': self.config.get_property('seed'),
            'restore_faces': self.config.get_property('restore_faces'),
            'width': self.width,
            'height': self.height,
        }

    def _estimate_timeout(self, req_data):
        timeout = int(int(req_data['steps']) * int(req_data['batch_size']) * config.TIMEOUT_FACTOR)
        if req_data['restore_faces']:
            timeout = int(timeout * 1.2 * config.TIMEOUT_FACTOR)
        return timeout