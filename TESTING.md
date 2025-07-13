# GIMP Generative Plugin Testing Guide

This guide provides instructions for testing the GIMP Generative Plugin.

## 1. Installation and Setup

1.  **Clone the Repository:**
    ```sh
    git clone https://github.com/kairin/gimp-generative-plugin.git
    ```

2.  **Configure GIMP Plugin Path:**
    *   Start GIMP 3.0.4.
    *   Go to `Edit` > `Preferences`.
    *   In the `Folders` section, select `Plug-ins`.
    *   Add the absolute path to the `src` sub-folder of the cloned repository to the list of plugin folders.
        *   **MacOS/Linux:** `/path/to/gimp-generative-plugin/src`
        *   **Windows:** `C:\path\to\gimp-generative-plugin\src`

3.  **Restart GIMP:**
    *   Close and restart GIMP for the plugin to be recognized.

4.  **Start AUTOMATIC1111 WebUI:**
    *   Start the AUTOMATIC1111 Stable Diffusion WebUI with the `--api` argument.

5.  **Set API URL in Plugin Preferences:**
    *   In GIMP, go to `Generative` > `Preferences`.
    *   Copy and paste the URL of your A1111 WebUI into the `API URL` field.

## 2. Testing Scenarios

### 2.1. Text to Image

1.  Open a new image in GIMP.
2.  Go to `Generative` > `Text to Image`.
3.  Enter a prompt in the `Prompt` field.
4.  Click `OK`.
5.  Verify that a new image is generated based on the prompt.

### 2.2. Image to Image

1.  Open an existing image in GIMP.
2.  Go to `Generative` > `Image to Image`.
3.  Enter a prompt in the `Prompt` field.
4.  Adjust the `Denoising strength` to control the amount of change.
5.  Click `OK`.
6.  Verify that the image is transformed based on the prompt.

### 2.3. Inpainting

1.  Open an image in GIMP.
2.  Create a new layer named `Inpainting Mask`.
3.  Use a paintbrush to paint the area you want to inpaint with black on the `Inpainting Mask` layer.
4.  Go to `Generative` > `Inpainting`.
5.  Enter a prompt in the `Prompt` field.
6.  Click `OK`.
7.  Verify that the selected area is inpainted based on the prompt.

### 2.4. Upscale

1.  Open an image in GIMP.
2.  Go to `Generative` > `Upscale`.
3.  Select an `Upscaling factor`.
4.  Click `OK`.
5.  Verify that the image is upscaled.

### 2.5. X/Y Plot

1.  Enable scripts by editing `src/gimp_stable_boy/config.py` and setting `Config.ENABLE_SCRIPTS` to `True`.
2.  Open an image in GIMP.
3.  Go to `Generative` > `Scripts` > `X/Y plot`.
4.  Select a mode (Text to Image, Image to Image, or Inpainting).
5.  Choose the parameters you want to compare in the X and Y axes.
6.  Click `OK`.
7.  Verify that a grid of images is generated, showing the results of different parameter combinations.

### 2.6. Rectangular Selections

1.  Open an image in GIMP.
2.  Use the `Rectangle Select Tool` to select a region of the image.
3.  Run any of the generation commands (Text to Image, Image to Image, etc.).
4.  Verify that the generation is only applied to the selected region.

### 2.7. Shared Settings

1.  Go to `Generative` > `Preferences`.
2.  Change the `API URL`.
3.  Close and reopen GIMP.
4.  Go to `Generative` > `Preferences`.
5.  Verify that the `API URL` has been saved.
