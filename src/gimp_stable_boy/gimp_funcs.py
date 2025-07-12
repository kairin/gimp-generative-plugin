import os
import tempfile
import base64
import math

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('Gegl', '0.4')
from gi.repository import Gimp, Gio, GLib, Gegl

import gimp_stable_boy.constants as constants
# from gimpshelf import shelf # gimp-python gimpshelf is not available for GIMP 3

# TODO: Replace gimpshelf with Gimp.Parasite or GApplicationSettings

def save_prefs(group_name, **kwargs):
    # for pref_key in (key for key in kwargs.keys() if key not in ['image', 'drawable']):
    #     shelf[group_name + '_' + pref_key] = kwargs[pref_key]
    print(f"Warning: gimp_funcs.save_prefs is not implemented for GIMP 3 yet for group {group_name}")
    pass

def pref_value(group_name, key_name, default=None):
    # full_key = group_name + '_' + key_name
    # return shelf[full_key] if shelf.has_key(full_key) else default
    print(f"Warning: gimp_funcs.pref_value is not implemented for GIMP 3 yet for group {group_name}, key {key_name}. Returning default.")
    return default

def encode_png(img_path):
    with open(img_path, "rb") as img:
        return 'data:image/png;base64,' + str(base64.b64encode(img.read()))

# This function encodes an image to a base64 string.
# It first duplicates the image, removes the mask layer, and selects the active area.
# Then, it copies the visible layers and pastes them as a new image.
# Finally, it saves the new image as a PNG file and returns the base64-encoded string.
def encode_img(img, x, y, width, height):
    img_cpy = img.duplicate()
    inp_layer = img_cpy.get_layer_by_name(constants.MASK_LAYER_NAME)
    if inp_layer:
        img_cpy.remove_layer(inp_layer)

    img_cpy.select_rectangle(Gimp.ChannelOps.REPLACE, x, y, width, height)

    floating_sel = Gimp.edit_copy_visible(img_cpy)
    if not floating_sel:
        img_cpy.delete()
        return None

    temp_image = Gimp.edit_paste_as_new_image(floating_sel)
    if not temp_image:
        img_cpy.delete()
        return None

    img_flat_path = os.path.join(tempfile.gettempdir(), tempfile.mktemp(suffix='.png'))

    file_obj = Gio.File.new_for_path(img_flat_path)
    save_proc = Gimp.get_pdb().lookup_procedure("file-png-save")
    if save_proc:
        config = save_proc.create_config()
        config.set_property("image", temp_image)
        config.set_property("drawable", temp_image.get_active_layer())
        config.set_property("filename", img_flat_path)
        save_proc.run(config)
    else:
        print("Error: Could not find 'file-png-save' procedure.")
        temp_image.delete()
        img_cpy.delete()
        return None

    encoded_img = encode_png(img_flat_path)
    os.remove(img_flat_path)
    temp_image.delete()
    img_cpy.delete()
    return encoded_img

# This function returns the active selection, or the entire image if there is no selection.
def active_area(img):
    non_empty, x, y, x2, y2 = img.selection_bounds()
    if non_empty:
        return x, y, x2 - x, y2 - y
    else:
        # If no selection, use the whole image
        return 0, 0, img.get_width(), img.get_height()


# This function calculates the area to be used for inpainting.
# It is based on the bounding box of the mask layer.
def autofit_inpainting_area(img):
    mask_layer = img.get_layer_by_name(constants.MASK_LAYER_NAME)
    if not mask_layer:
        raise Exception("Couldn't find layer named '" + constants.MASK_LAYER_NAME + "'")

    non_empty, mask_x1, mask_y1, mask_x2, mask_y2 = mask_layer.mask_bounds()
    if not non_empty:
         raise Exception("Inpainting mask is empty.")

    mask_width = mask_x2 - mask_x1
    mask_height = mask_y2 - mask_y1

    target_width = math.ceil(float(mask_width) / 256) * 256
    target_width = max(512, target_width)
    target_height = math.ceil(float(mask_height) / 256) * 256
    target_height = max(512, target_height)

    mask_center_x = mask_x1 + int(mask_width / 2)
    mask_center_y = mask_y1 + int(mask_height / 2)

    x, y = mask_center_x - target_width / 2, mask_center_y - target_height / 2

    if x + target_width > img.get_width():
        x = img.get_width() - target_width
    if y + target_height > img.get_height():
        y = img.get_height() - target_height
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    return int(x), int(y), int(target_width), int(target_height)

# This function encodes the inpainting mask to a base64 string.
def encode_mask(img, x, y, width, height):
    mask_layer = img.get_layer_by_name(constants.MASK_LAYER_NAME)
    if not mask_layer:
        raise Exception("Couldn't find layer named '" + constants.MASK_LAYER_NAME + "'")

    img_cpy = img.duplicate()

    for layer in img_cpy.get_layers():
        layer.set_visible(layer.get_name() == constants.MASK_LAYER_NAME)

    img_cpy.select_rectangle(Gimp.ChannelOps.REPLACE, x, y, width, height)

    floating_sel = Gimp.edit_copy_visible(img_cpy)
    if not floating_sel:
        img_cpy.delete()
        return None

    mask_img = Gimp.edit_paste_as_new_image(floating_sel)
    if not mask_img:
        img_cpy.delete()
        return None

    flat_layer = mask_img.flatten()
    if not flat_layer:
        print("Error flattening mask image")
        img_cpy.delete()
        mask_img.delete()
        return None

    mask_img_path = os.path.join(tempfile.gettempdir(), tempfile.mktemp(suffix='.png'))

    file_obj = Gio.File.new_for_path(mask_img_path)
    save_proc = Gimp.get_pdb().lookup_procedure("file-png-save")
    if save_proc:
        config = save_proc.create_config()
        config.set_property("image", mask_img)
        config.set_property("drawable", mask_img.get_active_layer())
        config.set_property("filename", mask_img_path)
        save_proc.run(config)
    else:
        print("Error: Could not find 'file-png-save' procedure.")
        img_cpy.delete()
        mask_img.delete()
        return None

    encoded_mask = encode_png(mask_img_path)
    os.remove(mask_img_path)
    img_cpy.delete()
    mask_img.delete()
    return encoded_mask

# This function decodes a base64 string to a PNG file.
def decode_png(encoded_png):
    png_img_path = os.path.join(tempfile.gettempdir(), tempfile.mktemp(suffix='.png'))
    with open(png_img_path, 'wb') as png_img_file:
        if "," in encoded_png:
            base64_data = encoded_png.split(",", 1)[1]
        else:
            base64_data = encoded_png
        png_img_file.write(base64.b64decode(base64_data))
    return png_img_path

# This function opens a list of base64-encoded images in GIMP.
def open_images(images_data):
    if not images_data:
        return
    for encoded_img in images_data:
        tmp_png_path = decode_png(encoded_img)

        file_obj = Gio.File.new_for_path(tmp_png_path)
        load_proc = Gimp.get_pdb().lookup_procedure("gimp-file-load")
        if load_proc:
            config = load_proc.create_config()
            config.set_property("uri", file_obj.get_uri())
            loaded_image_collection = load_proc.run(config)
            if loaded_image_collection.length() > 0:
                 loaded_image = loaded_image_collection.index(0).get_object()
                 Gimp.Display.new(loaded_image)
            else:
                print(f"Error loading image from {tmp_png_path}")
        else:
            print("Error: Could not find 'gimp-file-load' procedure.")

        os.remove(tmp_png_path)

# This function creates new layers in the image from a list of base64-encoded images.
def create_layers(img, layers_data, x, y, apply_inpainting_mask=False):
    if not layers_data:
        return

    inp_mask_layer = img.get_layer_by_name(constants.MASK_LAYER_NAME)

    def _create_nested_layers(parent_layer_group, current_layers_data):
        for layer_item in current_layers_data:
            if layer_item.children:
                gimp_layer_group = Gimp.Layer.new_group(img)
                gimp_layer_group.set_name(layer_item.name)
                img.insert_layer(gimp_layer_group, parent_layer_group, 0)
                _create_nested_layers(gimp_layer_group, layer_item.children)
            elif layer_item.img:
                tmp_png_path = decode_png(layer_item.img)

                file_obj = Gio.File.new_for_path(tmp_png_path)
                load_layer_proc = Gimp.get_pdb().lookup_procedure("gimp-file-load-layer")
                if load_layer_proc:
                    config = load_layer_proc.create_config()
                    config.set_property("image", img)
                    config.set_property("uri", file_obj.get_uri())
                    loaded_layers_collection = load_layer_proc.run(config)
                    if loaded_layers_collection.length() > 0:
                        gimp_layer = loaded_layers_collection.index(0).get_object()
                        gimp_layer.set_name(layer_item.name)
                        gimp_layer.set_offsets(x, y)
                        img.insert_layer(gimp_layer, parent_layer_group, 0)
                        gimp_layer.add_alpha()

                        if inp_mask_layer and apply_inpainting_mask:
                            img.set_active_layer(gimp_layer)
                            img.select_item(Gimp.ChannelOps.REPLACE, inp_mask_layer)
                            img.selection_invert()
                            Gimp.edit_clear(gimp_layer)
                    else:
                        print(f"Error loading layer from {tmp_png_path}")
                else:
                    print("Error: Could not find 'gimp-file-load-layer' procedure.")

                os.remove(tmp_png_path)

    _create_nested_layers(parent_layer_group=None, current_layers_data=layers_data)
    img.selection_none()
    if inp_mask_layer:
        img.raise_item_to_top(inp_mask_layer)
        inp_mask_layer.set_visible(False)