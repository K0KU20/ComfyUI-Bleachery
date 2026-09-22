import cv2
import numpy as np
import torch


class Bleachery:
    """
    ComfyUI custom node.

    Takes an image, converts it to LAB color space, and reduces yellow
    tint by shifting the B (blue-yellow) channel toward its neutral
    midpoint (128) whenever the image's average B value skews yellow.
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
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = "image/postprocessing"

    # ---- ComfyUI entry point -------------------------------------------------
    def run(self, image: torch.Tensor, strength: float):
        # ComfyUI IMAGE tensors are [batch, height, width, channels],
        # float32 in range 0..1, RGB channel order.
        batch = image.shape[0]
        outputs = []

        for i in range(batch):
            frame = image[i].cpu().numpy()
            frame_uint8 = np.clip(frame * 255.0, 0, 255).astype(np.uint8)

            # cv2 expects BGR
            bgr = cv2.cvtColor(frame_uint8, cv2.COLOR_RGB2BGR)
            neutral_bgr = self.neutralize_yellow(bgr, strength)
            neutral_rgb = cv2.cvtColor(neutral_bgr, cv2.COLOR_BGR2RGB)

            outputs.append(neutral_rgb.astype(np.float32) / 255.0)

        result = np.stack(outputs, axis=0)
        return (torch.from_numpy(result),)

    # ---- core algorithm (adapted from user-supplied function) --------------
    @staticmethod
    def neutralize_yellow(image_bgr: np.ndarray, strength: float = 0.8) -> np.ndarray:
        """
        Takes a BGR image (NumPy array, uint8) and reduces yellow tint to
        make colors more neutral. Returns a new neutralized image.
        """
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        L, A, B = cv2.split(lab)

        # Work in float to avoid uint8 wraparound during subtraction.
        B_f = B.astype(np.float32)

        # How much yellow there is (positive shift in B channel).
        yellow_strength = float(np.mean(B_f)) - 128.0  # 128 = neutral midpoint

        if yellow_strength > 0:
            corrected_B = np.clip(B_f - yellow_strength * strength, 0, 255).astype(np.uint8)
            lab = cv2.merge((L, A, corrected_B))
        # else: already neutral/blue-leaning, leave untouched

        neutral_img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        return neutral_img


NODE_CLASS_MAPPINGS = {
    "Bleachery": Bleachery,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Bleachery": "Bleachery (Remove Yellow Tint)",
}
