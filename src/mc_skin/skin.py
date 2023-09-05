from __future__ import annotations

from typing import TypeAlias, Any, Collection, Literal, Iterator

import numpy as np
from numpy import s_
from attrs import frozen
from PIL import Image

# x, y, z, face, color
ModelColor: TypeAlias = np.ndarray[tuple[int, int, int, int, int], np.dtype[np.uint8]]

# x, y, color
ImageColor: TypeAlias = np.ndarray[tuple[int, int, int], np.dtype[np.uint8]]

# x, y, z
Coord3: TypeAlias = np.ndarray[tuple[int], np.dtype[np.uint8]]

# x, y
Coord2: TypeAlias = np.ndarray[tuple[int], np.dtype[np.uint8]]

# r, g, b, a
Color: TypeAlias = np.ndarray[tuple[int], np.dtype[np.uint8]]

# face identifiers
FaceId = Literal["up", "down", "left", "right", "front", "back"]

# body part names
BodyPartId = Literal["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]


# Tenet: You shouldn't be allowed to index onto unmapped voxels/pixels.
class UnmappedVoxelError(Exception):
    """
    Raised when a voxel is accessed that is not mapped to a pixel on the skin.
    """


def arr(*args: int) -> np.ndarray[tuple[int], np.dtype[np.uint8]]:
    """
    Helper to create an ndarray without needing to create an intermediate sequence.
    """
    return np.array(args)


def subarray(
    *, data: np.ndarray[Any, Any], origin: Collection[int], shape: Collection[int]
) -> np.ndarray[Any, Any]:
    """
    Extract a subarray from a given numpy array using origin and shape.

    Parameters:
    - data: numpy array from which the subarray is to be extracted.
    - origin: a tuple containing the starting indices of the subarray.
    - shape: a tuple containing the dimensions of the subarray.

    Returns:
    - numpy array containing the subarray.
    """
    assert len(origin) == len(shape)
    slices = tuple(slice(o, o + s) for o, s in zip(origin, shape))
    return data[slices]


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
        part_shape: Coord3,
    ) -> Face:
        x_shape, y_shape, z_shape = part_shape
        order = [s_[:], s_[::-1]]
        if id_ in ("up", "down"):
            image_color_shape = arr(x_shape, y_shape)
            if id_ == "up":
                face_image_origin = arr(y_shape, 0)
            else:  # down
                face_image_origin = arr(y_shape + x_shape, 0)
                # order[0] = s_[::-1]
        elif id_ in ("left", "right"):
            image_color_shape = arr(y_shape, z_shape)
            if id_ == "left":
                face_image_origin = arr(0, y_shape)
                order[0] = s_[::-1]
            else:  # right
                face_image_origin = arr(y_shape + x_shape, y_shape)
        else:  # front or back
            image_color_shape = arr(x_shape, z_shape)
            if id_ == "front":
                face_image_origin = arr(y_shape, y_shape)
            else:  # back
                face_image_origin = arr(y_shape + x_shape + y_shape, y_shape)
                order[0] = s_[::-1]

        image_color = subarray(
            data=part_image_color,
            origin=face_image_origin,
            shape=image_color_shape,
        )

        return cls(
            image_color=image_color,
            id_=id_,
            order=tuple(order),
        )

    def enumerate_color(self) -> Iterator[tuple[Coord2, ImageColor]]:
        """
        Return an iterator of ((x, y), color) for each pixel of the face.
        """
        for x, y in np.ndindex(self.image_color.shape[:2]):
            coord = arr(x, y)
            color = self.get_color(x, y)
            yield coord, color

    def get_color(self, x: int | slice, y: int | slice) -> ImageColor:
        try:
            return self.image_color[self.order][x, y]
        except IndexError:
            coord = tuple([x, y])
            raise UnmappedVoxelError(f"{coord} contains unmapped voxels")

    def set_color(self, x: int, y: int, color: Color):
        self.get_color(x, y)[:] = color


@frozen
class BodyPart:
    id_: BodyPartId

    image_color: ImageColor

    # the front left bottom corner of the cuboid
    model_origin: Coord3

    # the top left corner of the image for each face
    # all faces are laid out on the image as follow:
    #
    #  +---+---+---+---+
    #  | - | U | D | - |
    #  +---+---+---+---+
    #  | L | F | R | B |
    #  +---+---+---+---+
    #
    # the origin is the top left corner of that diagram
    # image_origin: Coord2

    # todo: do we need this? can't we just use the face's image_color.shape?
    part_shape: Coord3

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
        part_shape: Coord3,
        part_model_origin: Coord3,
        part_image_origin: Coord2,
    ) -> BodyPart:
        image_color = subarray(
            data=skin_image_color,
            origin=part_image_origin,
            shape=(
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
            # image_origin=part_image_origin,
            part_shape=part_shape,
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

    def enumerate_color(self) -> Iterator[tuple[Coord3, FaceId, ImageColor]]:
        """
        Return an iterator of (x, y, z, face, color) for each pixel of the body part.
        """
        for face in self.faces:
            for xy_coord, color in face.enumerate_color():
                if face.id_ in ("up", "down"):
                    x, y = xy_coord
                    if face.id_ == "up":
                        z = self.part_shape[2] - 1
                    else:  # down
                        z = 0
                elif face.id_ in ("left", "right"):
                    y, z = xy_coord
                    if face.id_ == "left":
                        x = 0
                    else:
                        x = self.part_shape[0] - 1
                else:  # front or back
                    x, z = xy_coord
                    if face.id_ == "front":
                        y = 0
                    else:
                        y = self.part_shape[1] - 1
                xyz_coord = arr(x, y, z)

                yield xyz_coord, face.id_, color

    def get_color(
        self, x: int | slice, y: int | slice, z: int | slice, face: FaceId
    ) -> ImageColor:
        if face == "up" and z == self.part_shape[2] - 1:
            return self.up.get_color(x, y)
        elif face == "down" and z == 0:
            return self.down.get_color(x, y)
        elif face == "left" and x == 0:
            return self.left.get_color(y, z)
        elif face == "right" and x == self.part_shape[0] - 1:
            return self.right.get_color(y, z)
        elif face == "front" and y == 0:
            return self.front.get_color(x, z)
        elif face == "back" and y == self.part_shape[1] - 1:
            return self.back.get_color(x, z)

        coord = tuple([x, y, z, face])
        raise UnmappedVoxelError(f"{coord} contains unmapped voxels")

    def set_color(self, x: int, y: int, z: int, face: FaceId, color: Color):
        self.get_color(x, y, z, face)[:] = color


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
            part_shape=arr(8, 8, 8),
            part_model_origin=arr(4, 0, 24),
            part_image_origin=arr(0, 0),
        )
        torso = BodyPart.new(
            id_="torso",
            skin_image_color=image_color,
            part_shape=arr(8, 4, 12),
            part_model_origin=arr(4, 2, 12),
            part_image_origin=arr(16, 16),
        )
        left_arm = BodyPart.new(
            id_="left_arm",
            skin_image_color=image_color,
            part_shape=arr(4, 4, 12),
            part_model_origin=arr(0, 2, 12),
            part_image_origin=arr(40, 16),
        )
        right_arm = BodyPart.new(
            id_="right_arm",
            skin_image_color=image_color,
            part_shape=arr(4, 4, 12),
            part_model_origin=arr(12, 2, 12),
            part_image_origin=arr(32, 48),
        )
        left_leg = BodyPart.new(
            id_="left_leg",
            skin_image_color=image_color,
            part_shape=arr(4, 4, 12),
            part_model_origin=arr(4, 2, 0),
            part_image_origin=arr(0, 16),
        )
        right_leg = BodyPart.new(
            id_="right_leg",
            skin_image_color=image_color,
            part_shape=arr(4, 4, 12),
            part_model_origin=arr(8, 2, 0),
            part_image_origin=arr(16, 48),
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

    @property
    def body_parts(self) -> tuple[BodyPart, ...]:
        return (
            self.head,
            self.torso,
            self.left_arm,
            self.right_arm,
            self.left_leg,
            self.right_leg,
        )

    @property
    def shape(self) -> tuple[int, int, int, int, int]:
        # x, y, z, face, color
        return (16, 8, 32, 6, 4)

    def enumerate_color(
        self,
    ) -> Iterator[tuple[Coord3, BodyPartId, FaceId, ImageColor]]:
        """
        Return an iterator of (x, y, z, body_part, face, color) for each pixel
        of the skin.
        """
        for body_part in self.body_parts:
            for xyz_coord, face_id, color in body_part.enumerate_color():
                yield body_part.model_origin + xyz_coord, body_part.id_, face_id, color

    def get_color(self, x: int, y: int, z: int, face: FaceId) -> ImageColor:
        coord = arr(x, y, z)
        for body_part in self.body_parts:
            x_part = coord[0] - body_part.model_origin[0]
            y_part = coord[1] - body_part.model_origin[1]
            z_part = coord[2] - body_part.model_origin[2]
            try:
                return body_part.get_color(x_part, y_part, z_part, face)
            except UnmappedVoxelError:
                continue
        raise UnmappedVoxelError((x, y, z, face))

    def set_color(self, x: int, y: int, z: int, face: FaceId, color: Color):
        self.get_color(x, y, z, face)[:] = color

    @classmethod
    def fill_color(cls, color: Color | None = None) -> Skin:
        """
        Fill the skin with the given color. If no color is given, fill with black.
        """
        if color is None:
            color = arr(0, 0, 0, 255)
        skin = cls.new()
        for body_part in skin.body_parts:
            for face in body_part.faces:
                face.image_color[:] = color
        return skin

    # TODO: it would be nice if we could use views from PIL data such that
    # an update in the pillow image would be reflected in the skin and vice versa
    # consider using asarray() and fromarray() to convert between the two

    def load_image(self, skin_image: ImageColor):
        self.image_color[:] = skin_image

    def load_pil_image(self, image: Image.Image):
        """
        Set the skin to the given image. The image should be 64x64 pixels.
        """
        assert image.size == (64, 64)
        assert image.mode == "RGBA"

        # swap because images are indexed row-major (y first, then x), but we
        # want column-major (x first, then y) because its more natural
        image_arr = np.swapaxes(np.asarray(image), 0, 1)

        self.load_image(image_arr)

    @classmethod
    def from_pil_image(cls, image: Image.Image) -> Skin:
        """
        Create a skin from an image. The image should be 64x64 pixels.
        """
        skin = cls.new()
        skin.load_pil_image(image)
        return skin

    def get_pil_image(self) -> Image.Image:
        """
        Convert the skin to an image. The image will be 64x64 pixels.
        """

        image_arr = np.swapaxes(self.image_color, 0, 1)
        image = Image.fromarray(image_arr, mode="RGBA")  # type: ignore
        return image
