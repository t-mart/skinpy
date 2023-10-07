from pathlib import Path

import click

from skinpy import Skin, Perspective, XFaceId, YFaceId, ZFaceId


@click.group()
def cli():
    pass


@cli.command()
@click.argument(
    "input-path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "-x",
    type=click.Choice(["left", "right"]),
    default="left",
    show_default=True,
    help="Show from the left or right perspective.",
)
@click.option(
    "-y",
    type=click.Choice(["front", "back"]),
    default="front",
    show_default=True,
    help="Show from the front or back perspective.",
)
@click.option(
    "-z",
    type=click.Choice(["up", "down"]),
    default="up",
    show_default=True,
    help="Show from the up or down perspective.",
)
@click.option(
    "-s",
    "--scaling-factor",
    type=int,
    default=10,
    show_default=True,
    help="Scaling factor for the image, with bigger numbers producing bigger images",
)
@click.option(
    "-o",
    "--output-path",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    required=True,
    help="Path to write the rendered image to.",
)
def render(
    input_path: Path,
    x: XFaceId,
    y: YFaceId,
    z: ZFaceId,
    scaling_factor: int,
    output_path: Path,
):
    """
    Render the minecraft skin at INPUT_PATH to an isometric image.
    """
    perspective = Perspective.new(x=x, y=y, z=z, scaling_factor=scaling_factor)
    skin = Skin.from_path(input_path)
    image = skin.to_isometric_image(perspective=perspective)
    image.save(output_path)
    print(f"Rendered image to {output_path}")


if __name__ == "__main__":
    cli()
