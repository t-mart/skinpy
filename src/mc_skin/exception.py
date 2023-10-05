class McSkinException(Exception):
    pass


# tenet: You shouldn't be allowed to index onto unmapped voxels/pixels.
class UnmappedVoxelError(McSkinException):
    """
    Raised when a voxel is accessed that is not mapped to a pixel on the skin.
    """


class InputImageException(McSkinException):
    """
    Raised when there's something wrong with the input image.
    """
