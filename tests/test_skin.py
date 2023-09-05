import pytest
from PIL import Image
from pathlib import Path
import numpy as np

from mc_skin.skin import Skin, BodyPart, Face

INPUT_PATH = Path(__file__).parent / "input"
INPUT_IMAGES = INPUT_PATH.glob("*.png")
STEVE_PATH = INPUT_PATH / "steve.png"


RED: np.ndarray[tuple[int], np.dtype[np.uint8]] = np.array([255, 0, 0, 255])
GREEN: np.ndarray[tuple[int], np.dtype[np.uint8]] = np.array([0, 255, 0, 255])
WHITE: np.ndarray[tuple[int], np.dtype[np.uint8]] = np.array([255, 255, 255, 255])
BLACK: np.ndarray[tuple[int], np.dtype[np.uint8]] = np.array([0, 0, 0, 255])


@pytest.mark.parametrize("image_path", INPUT_IMAGES)
def test_round_trip(image_path: Path):
    """
    Test that we can round trip from image -> model -> image and get the same result.
    This ensures we're not doing any unbalanced transforms.
    """
    im = Image.open(image_path)
    rt = Skin.from_pil_image(im).get_pil_image()

    np_img1 = np.array(im)
    np_img2 = np.array(rt)

    assert np.array_equal(np_img1, np_img2), f"Image {image_path} did not round trip."


@pytest.mark.parametrize(
    "face_attr",
    [
        "front",
        "back",
        "left",
        "right",
        "up",
        "down",
    ],
)
@pytest.mark.parametrize(
    "body_part_attr",
    [
        "head",
        "torso",
        "right_arm",
        "left_arm",
        "right_leg",
        "left_leg",
    ],
)
def test_orientation(body_part_attr: str, face_attr: str):
    """
    Test that the orientation of pixels on the model is correctly loaded from an
    image.

    For this test, we use a specially "marked" image, where known color is set
    to a speficic pixel on each face, as viewed in the image:
    - white in bottom left (x=0, y=0)
    - green in top left (x=0, y=end)
    - red in bottom right (x=end, y=0)
    - black in top right (x=end, y=end)

    We then check that the position of that pixel is correct on the model.
    """
    im = Image.open(STEVE_PATH)
    skin = Skin.from_pil_image(im)

    body_part: BodyPart = getattr(skin, body_part_attr)
    face: Face = getattr(body_part, face_attr)

    x0y0 = face.get_color(0, 0)
    x0y1 = face.get_color(0, -1)
    x1y0 = face.get_color(-1, 0)
    x1y1 = face.get_color(-1, -1)

    assert np.array_equal(x0y0, WHITE)
    assert np.array_equal(x0y1, GREEN)
    assert np.array_equal(x1y0, RED)
    assert np.array_equal(x1y1, BLACK)


def test_mapping():
    """
    There are a few ways to set the colors:

    - Skin.image_colors
    - Skin.model_colors
    - BodyPart.image_colors
    - BodyPart.model_colors
    - Face.image_colors
    - Face.model_colors

    Updating any of these should result in the others being updated too
    (assuming they all represent the same pixel/voxel face).
    """
    skin = Skin.fill_color(BLACK)

    skin.set_color(4, 0, 24, "front", WHITE)

    skin_image_color = skin.image_color[8, 15]
    skin_model_color = skin.get_color(4, 0, 24, "front")
    body_part_image_color = skin.head.image_color[8, 15]
    body_part_model_color = skin.head.get_color(0, 0, 0, "front")
    face_image_color = skin.head.front.image_color[0, 7]
    face_model_color = skin.head.front.get_color(0, 0)

    assert np.array_equal(skin_image_color, WHITE)
    assert np.array_equal(skin_model_color, WHITE)
    assert np.array_equal(body_part_image_color, WHITE)
    assert np.array_equal(body_part_model_color, WHITE)
    assert np.array_equal(face_image_color, WHITE)
    assert np.array_equal(face_model_color, WHITE)
