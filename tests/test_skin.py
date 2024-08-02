from __future__ import annotations

import pytest
from pathlib import Path
from itertools import product

import numpy as np
from PIL import Image

from skinpy import (
    Skin,
    BodyPart,
    Face,
    Perspective,
    RGBA,
    BodyPartId,
    FaceId,
    XFaceId,
    YFaceId,
    ZFaceId,
)

# fixture base path
FIXTURE_PATH = Path(__file__).parent / "fixtures"

# marked with marker pixels in corners
STEVE_PATH = FIXTURE_PATH / "skins" / "steve.png"

# different at every voxel
LAB_PATH = FIXTURE_PATH / "skins" / "lab.png"

# where iso images are stored
ISO_PATH = FIXTURE_PATH / "iso"

RED: RGBA = (255, 0, 0, 255)
GREEN: RGBA = (0, 255, 0, 255)
WHITE: RGBA = (255, 255, 255, 255)
BLACK: RGBA = (0, 0, 0, 255)


def test_round_trip():
    """
    Test that we can round trip from image -> model -> image and get the same result.
    This ensures we're not doing any unbalanced transforms.
    """
    im = Image.open(STEVE_PATH)
    rt = Skin.from_image(im).to_image()

    np_img1 = np.array(im)
    np_img2 = np.array(rt)

    assert np.array_equal(np_img1, np_img2), f"Image {STEVE_PATH} did not round trip."


@pytest.mark.parametrize(
    "face_id",
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
    "body_part_id",
    [
        "head",
        "torso",
        "right_arm",
        "left_arm",
        "right_leg",
        "left_leg",
    ],
)
def test_orientation(body_part_id: BodyPartId, face_id: FaceId):
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
    skin = Skin.from_image(im)

    body_part: BodyPart = skin.get_body_part_for_id(body_part_id)
    face: Face = body_part.get_face_for_id(face_id)

    x0y0 = face.get_color(0, 0)
    x0y1 = face.get_color(0, -1)
    x1y0 = face.get_color(-1, 0)
    x1y1 = face.get_color(-1, -1)

    assert np.array_equal(x0y0, WHITE), "(0, 0) pixel not white"
    assert np.array_equal(x0y1, GREEN), "(0, end) pixel not green"
    assert np.array_equal(x1y0, RED), "(end, 0) pixel not red"
    assert np.array_equal(x1y1, BLACK), "(end, end) pixel not black"


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
    skin = Skin.filled(BLACK)

    skin.set_color(4, 0, 24, "front", WHITE)

    skin_image_color = skin.image_color[8, 15]
    skin_model_color = skin.get_color(4, 0, 24, "front")
    body_part_image_color = skin.head.image_color[8, 15]
    body_part_model_color = skin.head.get_color(0, 0, 0, "front")
    face_image_color = skin.head.front.image_color[0, 7]
    face_model_color = skin.head.front.get_color(0, 0)

    assert np.array_equal(skin_image_color, WHITE), "Skin.image_color not updated"
    assert np.array_equal(skin_model_color, WHITE), "Skin.model_color not updated"
    assert np.array_equal(
        body_part_image_color, WHITE
    ), "BodyPart.image_color not updated"
    assert np.array_equal(
        body_part_model_color, WHITE
    ), "BodyPart.model_color not updated"
    assert np.array_equal(face_image_color, WHITE), "Face.image_color not updated"
    assert np.array_equal(face_model_color, WHITE), "Face.model_color not updated"


def create_iso_fixtures():
    """
    Should only need to run this to initialize the iso fixtures with known working code.
    """
    im = Image.open(LAB_PATH)
    skin = Skin.from_image(im)

    for xp, yp, zp in product(("left", "right"), ("front", "back"), ("up", "down")):
        perspective = Perspective(x=xp, y=yp, z=zp)
        skin.to_isometric_image(perspective=perspective).save(
            ISO_PATH / f"skin-{xp}-{yp}-{zp}.png"
        )

        for body_part in skin.body_parts:
            body_part.to_isometric_image(perspective=perspective).save(
                ISO_PATH / f"{body_part.id_}-{xp}-{yp}-{zp}.png"
            )


# uncomment to create iso fixtures during test run
# create_iso_fixtures()


@pytest.mark.parametrize(
    "xp",
    ("left", "right"),
)
@pytest.mark.parametrize(
    "yp",
    ("front", "back"),
)
@pytest.mark.parametrize(
    "zp",
    ("up", "down"),
)
@pytest.mark.parametrize(
    "body_part_id",
    (
        None,
        "head",
        "torso",
        "right_arm",
        "left_arm",
        "right_leg",
        "left_leg",
    ),
)
def test_iso_image(
    xp: XFaceId, yp: YFaceId, zp: ZFaceId, body_part_id: BodyPartId | None
):
    """
    Test that the isometric image is correct.
    """
    im = Image.open(LAB_PATH)
    skin = Skin.from_image(im)

    perspective = Perspective(x=xp, y=yp, z=zp)

    if body_part_id is None:
        actual_iso = skin.to_isometric_image(perspective=perspective)
        fixture_path = ISO_PATH / f"skin-{xp}-{yp}-{zp}.png"
    else:
        body_part = skin.get_body_part_for_id(body_part_id)
        actual_iso = body_part.to_isometric_image(perspective=perspective)
        fixture_path = ISO_PATH / f"{body_part_id}-{xp}-{yp}-{zp}.png"

    expected_iso = Image.open(fixture_path)

    actual = np.array(actual_iso)
    expected = np.array(expected_iso)

    assert np.array_equal(
        actual, expected
    ), f"Generated isometric image did not match fixture at ({fixture_path})."
