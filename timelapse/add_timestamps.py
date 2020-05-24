import argparse
import sys
import pathlib
import datetime
from dataclasses import dataclass
import imageio
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
import tqdm
import numpy as np
from loguru import logger


@dataclass
class TimeConverter:
    end_time: datetime.datetime
    frame_count: int

    fps_video = 30
    spf_real = 5

    @classmethod
    def create_from_path(cls, filename: pathlib.Path):
        """
        Assumes the "modified" timestamp is the end time
        :param filename: The path to the video
        :return: An instance of this class
        """
        end_time = datetime.datetime.fromtimestamp(filename.stat().st_mtime)
        frame_count = imageio_ffmpeg.count_frames_and_secs(str(filename))[0]
        return TimeConverter(end_time=end_time, frame_count=frame_count)

    @property
    def fps_real(self) -> float:
        return 1 / self.spf_real

    @property
    def start_time(self) -> datetime.datetime:
        return self.end_time - self.duration_real

    def time_at_frame(self, frame) -> datetime.datetime:
        return self.start_time + datetime.timedelta(seconds=self.spf_real * frame)

    @property
    def duration_real(self) -> datetime.timedelta:
        return datetime.timedelta(seconds=self.frame_count / self.fps_real)

    @property
    def duration_video(self) -> datetime.timedelta:
        return datetime.timedelta(seconds=self.frame_count / self.fps_video)


def shrink_to_fit(old_img: Image, desired_size: tuple) -> Image:
    """
    https://jdhao.github.io/2017/11/06/resize-image-to-square-with-padding/
    :param old_img: PIL Image. Not altered
    :param desired_size: Size in (width, height)
    :return: New PIL image
    """
    old_size = old_img.size

    ratio_w = desired_size[0] / old_size[0]
    ratio_h = desired_size[1] / old_size[1]

    ratio = min(ratio_h, ratio_w)

    new_size = tuple([int(x * ratio) for x in old_size])

    img = old_img.resize(new_size, Image.ANTIALIAS)

    new_img = Image.new(old_img.mode, desired_size)
    new_img.paste(img, ((desired_size[0] - new_size[0])//2,
                        (desired_size[1] - new_size[1])//2))

    return new_img

def main(argv):

    parser = argparse.ArgumentParser(description="Create timestamp labels on a time lapse video clip")

    parser.add_argument("input_filename", type=pathlib.Path, help="Path to input video (read-only)")
    parser.add_argument("-o", dest="output_filename", type=pathlib.Path, help="Path to output file")
    parser.add_argument("-f", dest="force", action="store_true", help="Force overwrite of output file")
    parser.add_argument("--rotate", dest="rotate", choices=["left", "right", "flip"], default=None,
                        help="Whether to rotate the frame")

    args = parser.parse_args(argv)

    input_filename = args.input_filename
    output_filename = args.output_filename
    overwrite_output = args.force

    time_converter = TimeConverter.create_from_path(input_filename)

    rotations = {None: 0, "right": 3, "flip": 2, "left": 1}[args.rotate]
    font = ImageFont.truetype('arial', 180)

    if output_filename.exists():
        if overwrite_output:
            logger.warning(f"Overwriting {output_filename}")
        else:
            raise FileExistsError(f"Output file already exists {output_filename}")


    with tqdm.tqdm(smoothing=0, unit='frame', total=time_converter.frame_count) as progress_bar:
        with imageio.get_reader(str(input_filename)) as reader:
            with imageio.get_writer(str(output_filename), fps=30) as writer:
                for framei, frame in enumerate(reader):

                    height, width, _ = frame.shape

                    # Rotate image
                    img = np.rot90(frame, rotations)

                    # Convert to PIL
                    img = Image.fromarray(img)
                    img = shrink_to_fit(img, (width, height))

                    # Draw the timestamp
                    draw = ImageDraw.Draw(img)
                    timestamp = time_converter.time_at_frame(framei)
                    # Round to 10 minutes
                    resolution = 60 * 10
                    timestamp = datetime.datetime.fromtimestamp(timestamp.timestamp() // resolution * resolution)
                    draw.text((width * 0.05, height * 0.2),
                              f'{timestamp.strftime("%#I:%M")}'
                              f'{"a" if timestamp.hour < 12 else "p"}',
                              font=font)

                    # Add to video
                    writer.append_data(np.array(img))
                    progress_bar.update()


if __name__ == "__main__":
    main(sys.argv[1:])
