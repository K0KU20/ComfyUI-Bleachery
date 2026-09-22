# ComfyUI-Bleachery

English | [繁體中文](README_CHT.md)

A ComfyUI custom node that removes yellow color cast (white balance correction) from images.

It converts the image to LAB color space, measures the average shift of the B
(blue-yellow) channel, and automatically pulls yellow-tinted images back toward
a neutral tone — handy for fixing old photos, fluorescent-lit shots, or the warm
yellowish tint that's common in AI-generated images.

## ✨ Features

- 🎨 White balance correction in LAB color space — adjusts hue without touching brightness
- 🎚️ Adjustable correction `strength`, from a subtle nudge to a strong de-yellow pass
- 📦 Batch support — processes multiple images in one pass
- 🧠 Smart by default: only corrects images that are actually yellow-tinted, leaves neutral ones untouched
- ⚡ Pure OpenCV computation — fast, and doesn't use extra GPU resources

## 📸 What it does

```
Original (yellow tint) ──▶ Bleachery ──▶ Corrected (neutral tone)
```

## 🔧 Installation

### Option 1: Manual install

1. Go to your ComfyUI custom nodes folder:
   ```bash
   cd ComfyUI/custom_nodes
   ```
2. Clone this repo:
   ```bash
   git clone https://github.com/K0KU20/ComfyUI-Bleachery.git
   ```
3. Install dependencies:
   ```bash
   cd ComfyUI-Bleachery
   pip install -r requirements.txt
   ```
4. Restart ComfyUI.

### Option 2: ComfyUI Manager

If you have [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager) installed,
you can search for `ComfyUI-Bleachery` and install it directly from there.

## 🚀 Usage

1. Right-click on the canvas → **Add Node** → **image** → **postprocessing** → **Bleachery**
   (or just search `Bleachery` in the node search box)
2. Connect a `Load Image` node's output to the `image` input on `Bleachery`
3. Adjust the `strength` parameter (default `0.8`)
4. Connect the output to `Save Image` or `Preview Image`

### Example workflow

```
Load Image → Bleachery → Save Image
```

### Node parameters

| Parameter  | Type    | Required | Default | Description                                                                 |
|------------|---------|----------|---------|-------------------------------------------------------------------------------|
| `image`    | IMAGE   | yes      | -       | Input image(s) to process. Supports batches and RGBA images with alpha.       |
| `strength` | FLOAT   | yes      | 0.8     | De-yellow strength, range 0.0–2.0. Higher = stronger.                         |
| `mask`     | MASK    | no       | -       | Opacity mask (e.g. from a background-removal node). When connected, the correction is only applied to opaque pixels, leaving the transparent background untouched. |

**Outputs**: `image` (processed image), `mask` (passed through unchanged, so you can wire it into whatever needs it next — compositing, saving as a transparent PNG, etc.)

### 🖼️ Working with cut-out / transparent-background images

If your source image already has its background removed, connect the `mask`
output from your cutout node into `Bleachery`'s `mask` input as well:

```
Load Image / cutout node ──(image)──▶ Bleachery ──(image)──▶ Save Image
                  └───────(mask)──────▶      │
                                              └──(mask)──▶ (wire to other nodes as needed)
```

This avoids two common problems:
- The transparent background being mistaken for a color cast and turning into a strange magenta tint
- The alpha (transparency) information being lost during processing, so the output loses its transparent background

## 🧪 How it works

Internally, the node:

1. Converts the image from RGB to **LAB color space** (L = lightness, A = green-red, B = blue-yellow)
2. Computes the mean of the B channel across the whole image and compares it to the neutral value `128` to get a "yellowness" score
3. If the image is yellow-tinted (mean > 128), shifts the B channel toward `128` proportionally to `strength`
4. Converts back to RGB and outputs the result

```python
yellow_strength = mean(B) - 128
if yellow_strength > 0:
    B_corrected = clip(B - yellow_strength * strength, 0, 255)
```

## 📁 Project structure

```
ComfyUI-Bleachery/
├── __init__.py        # Node registration entry point
├── nodes.py            # Core node logic
├── requirements.txt    # Dependencies
├── README.md            # Chinese README
└── README_EN.md         # This file
```

## 🛠️ Requirements

- ComfyUI (any recent version)
- Python packages: `opencv-python`, `numpy`

## 🤝 Contributing

Issues and pull requests are welcome — bug reports, feature suggestions, or
additional color-correction algorithms are all appreciated.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

The core white balance algorithm is based on B-channel offset correction in LAB
color space.

## 📝 Changelog

- **v1.1**: Added support for transparent-background / cut-out images. The node now handles RGBA images with an alpha channel and adds an optional `mask` input so the correction is only applied to opaque pixels — fixing the transparent background turning magenta and the output losing its transparency layer.
- **v1.0**: Initial release.
