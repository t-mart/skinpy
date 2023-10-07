from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

import numpy as np
from numpy import s_
from attrs import frozen
from PIL import Image

from skinpy.render import (
    Polygon,
    get_iso_polys,
    Perspective,
    render_isometric,
)
from skinpy.exception import UnmappedVoxelError, InputImageException

if TYPE_CHECKING:
    from skinpy.types import (
        ImageColor,
        R3,
        R2,
        RGBA,
        FaceId,
        BodyPartId,
        StrPath
    )

# TODO: Fix upside down renders
# TODO: Second layer


def _subarray(*, data: ImageColor, origin: R2, offset: R2) -> ImageColor:
    """
    Extract a subarray from a given numpy array using origin and shape.

    Parameters:
    - data: numpy array from which the subarray is to be extracted.
    - origin: a tuple containing the starting indices of the subarray.
    - shape: a tuple containing the dimensions of the subarray.

    Returns:
    - numpy array containing the subarray.
    """
    assert len(origin) == len(offset)
    slices = tuple(slice(o, o + s) for o, s in zip(origin, offset))
    return data[slices]

FORWARD_SLICE = s_[:]
REVERSE_SLICE = s_[::-1]


@frozen
class Face:
    image_color: ImageColor
    id_: FaceId
    order: tuple[slice, slice]

    @classmethod
    def new(
        cls,
        part_image_color: ImageColor,
        id_: FaceId,
        part_shape: R3,
    ) -> Face:
        x_shape, y_shape, z_shape = part_shape
        order_x = FORWARD_SLICE
        order_y = REVERSE_SLICE
        if id_ in ("up", "down"):
            image_color_shape = (x_shape, y_shape)
            if id_ == "up":
                face_image_origin = (y_shape, 0)
            else:  # down
                face_image_origin = (y_shape + x_shape, 0)
        elif id_ in ("left", "right"):
            image_color_shape = (y_shape, z_shape)
            if id_ == "left":
                face_image_origin = (0, y_shape)
                order_x = REVERSE_SLICE
            else:  # right
                face_image_origin = (y_shape + x_shape, y_shape)
        else:  # front or back
            image_color_shape = (x_shape, z_shape)
            if id_ == "front":
                face_image_origin = (y_shape, y_shape)
            else:  # back
                face_image_origin = (y_shape + x_shape + y_shape, y_shape)
                order_x = REVERSE_SLICE

        image_color = _subarray(
            data=part_image_color,
            origin=face_image_origin,
            offset=image_color_shape,
        )

        return cls(
            image_color=image_color,
            id_=id_,
            order=(order_x, order_y),
        )

    def enumerate_color(self) -> Iterable[tuple[R2, ImageColor]]:
        """
        Return an iterator of ((x, y), color) for each pixel of the face.
        """
        for x, y in np.ndindex(self.image_color.shape[:2]):
            coord = (x, y)
            color = self.image_color[self.order][x, y]
            yield coord, color

    def get_color(self, x: int | slice, y: int | slice) -> ImageColor:
        try:
            return self.image_color[self.order][x, y]
        except IndexError:
            coord = (x, y)
            raise UnmappedVoxelError(f"{coord} contains unmapped voxels")

    def set_color(self, x: int | slice, y: int | slice, color: RGBA):
        self.get_color(x, y)[:] = color

    @property
    def shape(self) -> tuple[int, int]:
        return (self.image_color.shape[0], self.image_color.shape[1])


@frozen
class BodyPart:
    """
    A body part on the skin.

    From a skin image, a body part is a cuboid with 6 faces. Each face is a
    2d image. The faces are laid out on the image as follows:

    +---+---+---+---+
    | - | U | D | - |
    +---+---+---+---+
    | L | F | R | B |
    +---+---+---+---+

    The origin is the top left corner of that diagram
    """

    id_: BodyPartId
    image_color: ImageColor
    # the front left down corner of the cuboid relative to the entire skin
    model_origin: R3

    up: Face
    down: Face
    left: Face
    right: Face
    front: Face
    back: Face

    @classmethod
    def new(
        cls,
        *,
        id_: BodyPartId,
        skin_image_color: ImageColor,
        part_shape: R3,
        part_model_origin: R3,
        part_image_origin: R2,
    ) -> BodyPart:
        image_color = _subarray(
            data=skin_image_color,
            origin=part_image_origin,
            offset=(
                part_shape[0] * 2 + part_shape[1] * 2,
                part_shape[1] + part_shape[2],
            ),
        )

        def face_for_id(face_name: FaceId) -> Face:
            return Face.new(
                part_image_color=image_color,
                id_=face_name,
                part_shape=part_shape,
            )

        return cls(
            id_=id_,
            image_color=image_color,
            model_origin=part_model_origin,
            up=face_for_id("up"),
            down=face_for_id("down"),
            left=face_for_id("left"),
            right=face_for_id("right"),
            front=face_for_id("front"),
            back=face_for_id("back"),
        )

    @property
    def faces(self) -> tuple[Face, ...]:
        return (self.up, self.down, self.left, self.right, self.front, self.back)

    def get_face_for_id(self, face_id: FaceId) -> Face:
        if face_id == "up":
            return self.up
        elif face_id == "down":
            return self.down
        elif face_id == "left":
            return self.left
        elif face_id == "right":
            return self.right
        elif face_id == "front":
            return self.front
        else:  # face_id == "back"
            return self.back

    @property
    def shape(self) -> tuple[int, int, int]:
        return (
            self.front.shape[0],
            self.left.shape[0],
            self.front.shape[1],
        )

    def enumerate_color(self) -> Iterable[tuple[R3, FaceId, ImageColor]]:
        """
        Return an iterator of (x, y, z, face, color) for each pixel of the body part.
        """
        for face in self.faces:
            for xy_coord, color in face.enumerate_color():
                if face.id_ in ("up", "down"):
                    x, y = xy_coord
                    if face.id_ == "down":
                        z = 0
                    else:  # up
                        z = self.shape[2] - 1
                elif face.id_ in ("left", "right"):
                    y, z = xy_coord
                    if face.id_ == "left":
                        x = 0
                    else:
                        x = self.shape[0] - 1
                else:  # front or back
                    x, z = xy_coord
                    if face.id_ == "front":
                        y = 0
                    else:
                        y = self.shape[1] - 1
                xyz_coord = (x, y, z)

                yield xyz_coord, face.id_, color

    def get_color(
        self, x: int | slice, y: int | slice, z: int | slice, face: FaceId
    ) -> ImageColor:
        if face == "up" and z == self.shape[2] - 1:
            return self.up.get_color(x, y)
        elif face == "down" and z == 0:
            return self.down.get_color(x, y)
        elif face == "left" and x == 0:
            return self.left.get_color(y, z)
        elif face == "right" and x == self.shape[0] - 1:
            return self.right.get_color(y, z)
        elif face == "front" and y == 0:
            return self.front.get_color(x, z)
        elif face == "back" and y == self.shape[1] - 1:
            return self.back.get_color(x, z)

        coord = (x, y, z, face)
        raise UnmappedVoxelError(f"{coord} contains unmapped voxels")

    def set_color(
        self,
        x: int | slice,
        y: int | slice,
        z: int | slice,
        face: FaceId,
        color: RGBA,
    ):
        self.get_color(x, y, z, face)[:] = color

    def get_iso_polys(self, perspective: Perspective) -> Iterable[Polygon]:
        yield from get_iso_polys(
            self.enumerate_color(),
            perspective=perspective,
        )

    def to_isometric_image(
        self,
        perspective: Perspective,
        background_color: tuple[int, int, int, int] | None = None,
    ) -> Image.Image:
        return render_isometric(
            polys=list(self.get_iso_polys(perspective)),
            background_color=background_color,
        )


@frozen
class Skin:
    """
    A Minecraft skin. There are 5 dimensions to a skin in 3d space:

    - x: left to right (0-15)
    - y: front to back (0-7)
    - z: bottom to top (0-31)
    - face: front, back, left, right, top, bottom (0-5)
    - color: red, green, blue, alpha (0-3)

    The coordinate system to locate a voxel is done from the perspective of an
    observer looking at the front of the skin. The origin is at the bottom left
    front corner. Additionally, the face is oriented from the perspective of the
    observer. For example, the "left" face is the left side of the observer.

    And, there are 3 dimensions to a skin in 2d space:

    - x: left to right (0-63)
    - y: top to bottom (0-63)
    - color: red, green, blue, alpha (0-3)

    The coordinate system for images has its origin at the top left corner.
    """

    image_color: ImageColor

    head: BodyPart
    torso: BodyPart
    left_arm: BodyPart
    right_arm: BodyPart
    left_leg: BodyPart
    right_leg: BodyPart

    @classmethod
    def new(cls, image_color: ImageColor | None = None) -> Skin:
        if image_color is None:
            image_color = np.zeros(
                (
                    64,  # 64 pixels x (left to right)
                    64,  # 64 pixels y (top to bottom)
                    4,  # 4 color channels (RGBA)
                ),
                dtype=np.uint8,
            )

        assert image_color.shape == (64, 64, 4)

        head = BodyPart.new(
            id_="head",
            skin_image_color=image_color,
            part_shape=(8, 8, 8),
            part_model_origin=(4, 0, 24),
            part_image_origin=(0, 0),
        )
        torso = BodyPart.new(
            id_="torso",
            skin_image_color=image_color,
            part_shape=(8, 4, 12),
            part_model_origin=(4, 2, 12),
            part_image_origin=(16, 16),
        )
        left_arm = BodyPart.new(
            id_="left_arm",
            skin_image_color=image_color,
            part_shape=(4, 4, 12),
            part_model_origin=(0, 2, 12),
            part_image_origin=(40, 16),
        )
        right_arm = BodyPart.new(
            id_="right_arm",
            skin_image_color=image_color,
            part_shape=(4, 4, 12),
            part_model_origin=(12, 2, 12),
            part_image_origin=(32, 48),
        )
        left_leg = BodyPart.new(
            id_="left_leg",
            skin_image_color=image_color,
            part_shape=(4, 4, 12),
            part_model_origin=(4, 2, 0),
            part_image_origin=(0, 16),
        )
        right_leg = BodyPart.new(
            id_="right_leg",
            skin_image_color=image_color,
            part_shape=(4, 4, 12),
            part_model_origin=(8, 2, 0),
            part_image_origin=(16, 48),
        )

        return cls(
            image_color=image_color,
            head=head,
            torso=torso,
            left_arm=left_arm,
            right_arm=right_arm,
            left_leg=left_leg,
            right_leg=right_leg,
        )

    @classmethod
    def filled(cls, color: RGBA) -> Skin:
        """
        Fill the skin with the given color.
        """
        skin = cls.new()
        for body_part in skin.body_parts:
            for face in body_part.faces:
                face.image_color[:] = color
        return skin

    @classmethod
    def from_image(cls, image: Image.Image) -> Skin:
        """
        Create a skin from a Pillow Image. The image must be 64x64 pixels and in RGBA
        mode, otherwise an InputImageException is raised.

        The image data is copied into the skin, so modifying the image after creating
        the skin will not affect the skin, and vice versa.
        """

        if image.size != (64, 64):
            raise InputImageException(
                f"Image size must be 64x64 pixels, but got {image.size}"
            )

        if image.mode != "RGBA":
            raise InputImageException(f"Image mode must be RGBA, but got {image.mode}")

        # swap because numpy indexes row-major (y first, then x), but we
        # want column-major (x first, then y) because its more natural
        image_arr = np.swapaxes(np.asarray(image), 0, 1)

        skin = cls.new()
        skin.image_color[:] = image_arr
        return skin

    @classmethod
    def from_path(cls, path: StrPath) -> Skin:
        """
        Create a skin from an image path.
        """
        import shutil
        shutil.copy(path, "test.png")
        image = Image.open(path)
        return cls.from_image(image)

    @property
    def body_parts(self) -> tuple[BodyPart, ...]:
        return (
            self.left_leg,
            self.right_leg,
            self.left_arm,
            self.torso,
            self.right_arm,
            self.head,
        )

    def get_body_part_for_id(self, body_part_id: BodyPartId) -> BodyPart:
        if body_part_id == "head":
            return self.head
        elif body_part_id == "torso":
            return self.torso
        elif body_part_id == "left_arm":
            return self.left_arm
        elif body_part_id == "right_arm":
            return self.right_arm
        elif body_part_id == "left_leg":
            return self.left_leg
        else:  # body_part_id == "right_leg"
            return self.right_leg

    @property
    def shape(self) -> R3:
        # x, y, z
        return (16, 8, 32)

    def enumerate_color(
        self,
    ) -> Iterable[tuple[R3, BodyPartId, FaceId, ImageColor]]:
        """
        Return an iterator of ((x, y, z), body_part, face, color) for each pixel
        of the skin.
        """
        for body_part in self.body_parts:
            for xyz_coord, face_id, color in body_part.enumerate_color():
                offset = (
                    body_part.model_origin[0] + xyz_coord[0],
                    body_part.model_origin[1] + xyz_coord[1],
                    body_part.model_origin[2] + xyz_coord[2],
                )
                yield offset, body_part.id_, face_id, color

    def get_color(self, x: int, y: int, z: int, face: FaceId) -> ImageColor:
        # search for the coordinates
        for bp in self.body_parts:
            # are we inside or on this body part? origin guaranteed to have min value
            if (
                (bp.model_origin[0] <= x < bp.model_origin[0] + bp.shape[0])
                and (bp.model_origin[1] <= y < bp.model_origin[1] + bp.shape[1])
                and (bp.model_origin[2] <= z < bp.model_origin[2] + bp.shape[2])
            ):
                x_rel = x - bp.model_origin[0]
                y_rel = y - bp.model_origin[1]
                z_rel = z - bp.model_origin[2]
                return bp.get_color(x_rel, y_rel, z_rel, face)

        raise UnmappedVoxelError((x, y, z, face))

    def set_color(self, x: int, y: int, z: int, face: FaceId, color: RGBA):
        self.get_color(x, y, z, face)[:] = color

    def to_image(self) -> Image.Image:
        """
        Convert the skin to an image. The image will be 64x64 pixels.

        The image data is copied into the image, so modifying the skin after
        creating the image will not affect the image, and vice versa.
        """

        image_arr = np.swapaxes(self.image_color, 0, 1)
        image = Image.fromarray(image_arr, mode="RGBA")  # type: ignore
        return image

    def to_isometric_image(
        self,
        perspective: Perspective,
        background_color: tuple[int, int, int, int] | None = None,
    ) -> Image.Image:
        origin = (
            0 if perspective.x == "left" else self.shape[0] - 1,
            0 if perspective.y == "front" else self.shape[1] - 1,
            0 if perspective.z == "down" else self.shape[2] - 1,
        )

        def dist_to_origin(body_part: BodyPart) -> float:
            return float(
                np.linalg.norm(np.array(body_part.model_origin) - np.array(origin))
            )

        # sort the body parts by distance to the origin, furthest first.
        # this is the painter's algorithm: draw the furthest away first, then
        # one closer, and so on, until the closest is drawn last.
        parts = sorted(self.body_parts, key=dist_to_origin, reverse=True)

        polys: list[Polygon] = []
        for part in parts:
            for poly in part.get_iso_polys(perspective):
                offset = perspective.map_iso(*part.model_origin)
                polys.append(poly.with_offset(offset))

        return render_isometric(
            polys=polys,
            background_color=background_color,
        )
