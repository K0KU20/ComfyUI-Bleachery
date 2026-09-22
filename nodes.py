import cv2
import numpy as np
import torch


class Bleachery:
    """
    ComfyUI custom node.

    Takes an image, converts it to LAB color space, and reduces yellow
    tint by shifting the B (blue-yellow) channel toward its neutral
    midpoint (128) whenever the image's average B value skews yellow.

    Alpha-aware: if the input image carries a 4th (alpha) channel, or an
    optional MASK is connected, only opaque/foreground pixels are used to
    compute the correction and the transparent background is left
    untouched, and the alpha channel is preserved in the output.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "strength": (
                    "FLOAT",
                    {
                        "default": 0.8,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "How aggressively to pull the B channel back toward neutral.",
                    },
                ),
            },
            "optional": {
                "mask": ("MASK",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "run"
    CATEGORY = "image/postprocessing"

    # ---- ComfyUI entry point -------------------------------------------------
    def run(self, image: torch.Tensor, strength: float, mask: torch.Tensor = None):
        # ComfyUI IMAGE tensors are [batch, height, width, channels],
        # float32 in range 0..1, RGB (or RGBA) channel order.
        batch, height, width, channels = image.shape
        has_alpha_channel = channels == 4

        mask_np = None
        if mask is not None:
            mask_np = mask.cpu().numpy()  # [batch or 1, H, W], 1 = opaque/foreground

        outputs = []
        for i in range(batch):
            frame = image[i].cpu().numpy()

            if has_alpha_channel:
                rgb = frame[..., :3]
                alpha = frame[..., 3]
            else:
                rgb = frame
                alpha = None

            rgb_uint8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
            bgr = cv2.cvtColor(rgb_uint8, cv2.COLOR_RGB2BGR)

            # Figure out which pixels are "opaque" so a transparent
            # background doesn't skew the color statistics or get painted.
            opacity_mask = None
            if mask_np is not None:
                m = mask_np[i] if mask_np.shape[0] == batch else mask_np[0]
                opacity_mask = m > 0.02
            elif alpha is not None:
                opacity_mask = alpha > 0.02

            neutral_bgr = self.neutralize_yellow(bgr, strength, opacity_mask)
            neutral_rgb = cv2.cvtColor(neutral_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

            if has_alpha_channel:
                out_frame = np.concatenate([neutral_rgb, alpha[..., None]], axis=-1)
            else:
                out_frame = neutral_rgb

            outputs.append(out_frame)

        result = np.stack(outputs, axis=0)

        if mask is not None:
            out_mask = mask
        else:
            out_mask = torch.ones((batch, height, width), dtype=torch.float32)

        return (torch.from_numpy(result), out_mask)

    # ---- core algorithm (adapted from user-supplied function) --------------
    @staticmethod
    def neutralize_yellow(image_bgr: np.ndarray, strength: float = 0.8, opacity_mask: np.ndarray = None) -> np.ndarray:
        """
        Takes a BGR image (NumPy array, uint8) and reduces yellow tint to
        make colors more neutral. Returns a new neutralized image.

        If `opacity_mask` (bool array, same H/W as the image, True = opaque)
        is given, only those pixels are used to compute the correction
        amount AND only those pixels are modified — transparent background
        pixels are left as-is.
        """
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        L, A, B = cv2.split(lab)
        B_f = B.astype(np.float32)

        if opacity_mask is not None and np.any(opacity_mask):
            sample = B_f[opacity_mask]
        else:
            sample = B_f

        # How much yellow there is (positive shift in B channel).
        yellow_strength = float(np.mean(sample)) - 128.0  # 128 = neutral midpoint

        if yellow_strength > 0:
            corrected_B = np.clip(B_f - yellow_strength * strength, 0, 255).astype(np.uint8)

            if opacity_mask is not None:
                # Only touch opaque/foreground pixels; leave transparent
                # background color data untouched.
                merged_B = B.copy()
                merged_B[opacity_mask] = corrected_B[opacity_mask]
                corrected_B = merged_B

            lab = cv2.merge((L, A, corrected_B))
        # else: already neutral/blue-leaning, leave untouched

        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


NODE_CLASS_MAPPINGS = {
    "Bleachery": Bleachery,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Bleachery": "Bleachery (Remove Yellow Tint)",
}
