from __future__ import annotations

import numpy as np
from numpy import s_
from attrs import frozen
from PIL import Image

# faces
FACE_F = 0  # front
FACE_B = 1  # back
FACE_R = 3  # right
FACE_L = 2  # left
FACE_U = 4  # up
FACE_D = 5  # down


@frozen
class BodyPart:
    name: str
    shape_cuboid: np.ndarray
    origin_model: np.ndarray
    origin_image: np.ndarray

    @property
    def shape_x(self) -> int:
        return self.shape_cuboid[0]

    @property
    def shape_y(self) -> int:
        return self.shape_cuboid[1]

    @property
    def shape_z(self) -> int:
        return self.shape_cuboid[2]

    @property
    def model_x_slice(self) -> slice:
        return slice(self.origin_model[0], self.origin_model[0] + self.shape_x)

    @property
    def model_y_slice(self) -> slice:
        return slice(self.origin_model[1], self.origin_model[1] + self.shape_y)

    @property
    def model_z_slice(self) -> slice:
        return slice(self.origin_model[2], self.origin_model[2] + self.shape_z)

    @property
    def img_u_origin(self) -> np.ndarray:
        return self.origin_image + [
            self.shape_y,
            0,
        ]

    @property
    def img_d_origin(self) -> np.ndarray:
        return self.origin_image + [
            self.shape_y + self.shape_x,
            0,
        ]

    @property
    def img_l_origin(self) -> np.ndarray:
        return self.origin_image + [
            0,
            self.shape_y + self.shape_z - 1,
        ]

    @property
    def img_r_origin(self) -> np.ndarray:
        return self.origin_image + [
            self.shape_y + self.shape_x,
            self.shape_y + self.shape_z - 1,
        ]

    @property
    def img_f_origin(self) -> np.ndarray:
        return self.origin_image + [
            self.shape_y,
            self.shape_y + self.shape_z - 1,
        ]

    @property
    def img_b_origin(self) -> np.ndarray:
        return self.origin_image + [
            self.shape_y + self.shape_x + self.shape_y,
            self.shape_y + self.shape_z - 1,
        ]

    @property
    def mapping(self) -> dict:
        return {
            FACE_U: (
                (
                    self.model_x_slice,
                    self.model_y_slice,
                    self.model_z_slice.stop - 1,
                    FACE_U,
                ),
                (
                    s_[self.img_u_origin[0] : self.img_u_origin[0] + self.shape_x],
                    s_[self.img_u_origin[1] : self.img_u_origin[1] + self.shape_y],
                ),
                (
                    s_[:],
                    s_[::-1],
                ),
            ),
            FACE_D: (
                (
                    self.model_x_slice,
                    self.model_y_slice,
                    self.model_z_slice.start,
                    FACE_D,
                ),
                (
                    s_[self.img_d_origin[0] : self.img_d_origin[0] + self.shape_x],
                    s_[self.img_d_origin[1] : self.img_d_origin[1] + self.shape_y],
                ),
                (
                    s_[::-1],
                    s_[::-1],
                ),
            ),
        }

    def image_to_model(self, image: np.ndarray, model: np.ndarray) -> None:
        """
        Copy the image to the model.
        """

        # model[
        #     self.model_x_slice,
        #     self.model_y_slice,
        #     self.model_z_slice.stop - 1,
        #     FACE_U,
        # ] = image[
        #     self.img_u_origin[0] : self.img_u_origin[0] + self.shape_x,
        #     self.img_u_origin[1] : self.img_u_origin[1] + self.shape_y,
        # ][
        #     :, ::-1
        # ]
        m, i, s = self.mapping[FACE_U]
        model[m] = image[i][s]

        model[
            self.model_x_slice,
            self.model_y_slice,
            self.model_z_slice.start,
            FACE_D,
        ] = image[
            self.img_d_origin[0] : self.img_d_origin[0] + self.shape_x,
            self.img_d_origin[1] : self.img_d_origin[1] + self.shape_y,
        ][
            ::-1, ::-1
        ]

        model[
            self.model_x_slice.start,
            self.model_y_slice,
            self.model_z_slice,
            FACE_L,
        ] = image[
            self.img_l_origin[0] : self.img_l_origin[0] + self.shape_y,
            self.img_l_origin[1] : self.img_l_origin[1] - self.shape_z : -1,
        ][
            :, ::-1
        ]

        model[
            self.model_x_slice.stop - 1,
            self.model_y_slice,
            self.model_z_slice,
            FACE_R,
        ] = image[
            self.img_r_origin[0] : self.img_r_origin[0] + self.shape_y,
            self.img_r_origin[1] : self.img_r_origin[1] - self.shape_z : -1,
        ][
            :, ::-1
        ]

        model[
            self.model_x_slice,
            self.model_y_slice.start,
            self.model_z_slice,
            FACE_F,
        ] = image[
            self.img_f_origin[0] : self.img_f_origin[0] + self.shape_x,
            self.img_f_origin[1] : self.img_f_origin[1] - self.shape_z : -1,
        ][
            :, ::-1
        ]

        model[
            self.model_x_slice,
            self.model_y_slice.stop - 1,
            self.model_z_slice,
            FACE_B,
        ] = image[
            self.img_b_origin[0] : self.img_b_origin[0] + self.shape_x,
            self.img_b_origin[1] : self.img_b_origin[1] - self.shape_z : -1,
        ][
            :, ::-1
        ]

    def model_to_image(self, model: np.ndarray, image: np.ndarray) -> None:
        """
        Copy the model to the image.
        """
        m, i, s = self.mapping[FACE_U]
        image[i] = model[m][s]

        image[
            self.img_d_origin[0] : self.img_d_origin[0] + self.shape_x,
            self.img_d_origin[1] : self.img_d_origin[1] + self.shape_y,
        ] = model[
            self.model_x_slice,
            self.model_y_slice,
            self.model_z_slice.start,
            FACE_D,
        ][
            ::-1, ::-1
        ]

        image[
            self.img_l_origin[0] : self.img_l_origin[0] + self.shape_y,
            self.img_l_origin[1] : self.img_l_origin[1] - self.shape_z : -1,
        ] = model[
            self.model_x_slice.start,
            self.model_y_slice,
            self.model_z_slice,
            FACE_L,
        ][
            :, ::-1
        ]

        image[
            self.img_r_origin[0] : self.img_r_origin[0] + self.shape_y,
            self.img_r_origin[1] : self.img_r_origin[1] - self.shape_z : -1,
        ] = model[
            self.model_x_slice.stop - 1,
            self.model_y_slice,
            self.model_z_slice,
            FACE_R,
        ][
            :, ::-1
        ]

        image[
            self.img_f_origin[0] : self.img_f_origin[0] + self.shape_x,
            self.img_f_origin[1] : self.img_f_origin[1] - self.shape_z : -1,
        ] = model[
            self.model_x_slice,
            self.model_y_slice.start,
            self.model_z_slice,
            FACE_F,
        ][
            :, ::-1
        ]

        image[
            self.img_b_origin[0] : self.img_b_origin[0] + self.shape_x,
            self.img_b_origin[1] : self.img_b_origin[1] - self.shape_z : -1,
        ] = model[
            self.model_x_slice,
            self.model_y_slice.stop - 1,
            self.model_z_slice,
            FACE_B,
        ][
            :, ::-1
        ]


HEAD = BodyPart(
    name="head",
    shape_cuboid=np.array([8, 8, 8]),
    origin_model=np.array([4, 0, 24]),
    origin_image=np.array([0, 0]),
)
TORS0 = BodyPart(
    name="torso",
    shape_cuboid=np.array([8, 4, 12]),
    origin_model=np.array([4, 2, 12]),
    origin_image=np.array([16, 16]),
)
_LEG_ARM_SHAPE = np.array([4, 4, 12])
LEFT_ARM = BodyPart(
    name="left_arm",
    shape_cuboid=_LEG_ARM_SHAPE,
    origin_model=np.array([0, 2, 12]),
    origin_image=np.array([40, 16]),
)
RIGHT_ARM = BodyPart(
    name="right_arm",
    shape_cuboid=_LEG_ARM_SHAPE,
    origin_model=np.array([12, 2, 12]),
    origin_image=np.array([32, 48]),
)
LEFT_LEG = BodyPart(
    name="left_leg",
    shape_cuboid=_LEG_ARM_SHAPE,
    origin_model=np.array([4, 2, 0]),
    origin_image=np.array([0, 16]),
)
RIGHT_LEG = BodyPart(
    name="right_leg",
    shape_cuboid=_LEG_ARM_SHAPE,
    origin_model=np.array([8, 2, 0]),
    origin_image=np.array([16, 48]),
)
BODY_PARTS = [HEAD, TORS0, LEFT_ARM, RIGHT_ARM, LEFT_LEG, RIGHT_LEG]


@frozen
class Skin:
    """
    A Minecraft skin. There are 5 dimensions to a skin:

    - x: left to right (0-15)
    - y: front to back (0-7)
    - z: bottom to top (0-31)
    - face: front, back, left, right, top, bottom (0-5)
    - color: red, green, blue, alpha (0-3)

    The coordinate system to locate a voxel is done from the perspective of an
    observer looking at the front of the skin. The origin is at the bottom left
    front corner. Additionally, the face is oriented from the perspective of the
    observer. For example, the "left" face is the left side of the observer.
    """

    space: np.ndarray

    @classmethod
    def create(cls) -> Skin:
        return cls(
            space=np.zeros(
                (
                    16,  # 16 voxels x (left to right)
                    8,  # 8 voxels y (front to back)
                    32,  # 32 voxels z (bottom to top)
                    6,  # 6 faces (F, B, L, R, T, D)
                    4,  # 4 color channels (RGBA)
                ),
                dtype=np.uint8,
            )
        )

    @classmethod
    def from_image(cls, image: Image.Image) -> Skin:
        """
        Create a skin from an image. The image should be 64x64 pixels.
        """
        assert image.size == (64, 64)
        assert image.mode == "RGBA"

        # swap because images are indexed row-major (y first, then x) and we
        # want column-major (x first, then y). this is more natural and it maps
        # to our 3d space
        image_arr = np.swapaxes(np.asarray(image), 0, 1)

        skin = cls.create()

        for part in BODY_PARTS:
            print(f"from_image, part: {part.name}")
            part.image_to_model(image_arr, skin.space)

        return skin

    def to_image(self) -> Image.Image:
        """
        Convert the skin to an image. The image will be 64x64 pixels.
        """
        # just do the reverse of from_image
        image_arr = np.zeros((64, 64, 4), dtype=np.uint8)

        for part in BODY_PARTS:
            print(f"to_image, part: {part.name}")
            part.model_to_image(self.space, image_arr)

        image_arr = np.swapaxes(image_arr, 0, 1)
        image = Image.fromarray(image_arr, mode="RGBA")

        return image


if __name__ == "__main__":
    skin = Skin.from_image(Image.open("steve.png"))
    # print(skin.space[4:12, 0, 24:32, 0])
    # for x in (4, 11):  # x coordinates from 4 to 11
    #     for z in (24, 31):
    #         y = 7
    #         r, g, b, a = skin.space[x, y, z, FACE_B]
    #         print(f"({x=}, {y=}, {z=}) -> ({r=}, {g=}, {b=}, {a=})")

    skin.to_image().save("steve2.png")
