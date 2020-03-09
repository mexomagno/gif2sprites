"""
Converts an animated gif to a single image with frames stitched together.
Designed for 11x33 led screen animations.
""" 
import os
import argparse
from PIL import Image
from PIL import GifImagePlugin
from PIL import ImageOps 
import numpy

JUSTIFY_LEFT, JUSTIFY_CENTER, JUSTIFY_RIGHT = range(3)


"""
Image filters
"""
def _binarize_array(numpy_array, threshold=200):
    """Binarize a numpy array."""
    for i in range(len(numpy_array)):
        for j in range(len(numpy_array[0])):
            if numpy_array[i][j] > threshold:
                numpy_array[i][j] = 255
            else:
                numpy_array[i][j] = 0
    return numpy_array

def binarize_image(pillow_img, threshold):
    """Binarize an image."""
    image = pillow_img.convert('L')  # convert image to monochrome
    image = numpy.array(image)
    image = _binarize_array(image, threshold)

    return Image.fromarray(image)

"""
Main process
"""

def get_frames(file):
    i = Image.open(file)
    if not i.is_animated:
        raise ValueError("File is not animated. Abort")
    output = list()
    for index in range(i.n_frames):
        i.seek(index)
        outname = f'/tmp/{index}.bmp'
        i.save(outname)
        output.append(outname)
    return output

def rescale(images, width, height, binarize_thres=200, invert_colors=False, justify_width=33, bg_color=0, justify=JUSTIFY_LEFT):
    """
    Rescale all images to be contained inside a square of size width x height. Justify horizontally.

    This method assumes all frames have the same aspect ratio
    """
    desired_ratio = width*1.0/height
    actual_ratio = 0


    output = list()
    for path in images:
        i = Image.open(path)
        desired_ratio = width*1.0/height
        img_ratio = i.width*1.0/i.height

        if img_ratio < desired_ratio:
            # image is taller
            newsize = (int(height*img_ratio), height)            
        else:
            # image is wider
            newsize = (width, int(img_ratio/width))
        i = i.resize(newsize, resample=Image.LANCZOS)
        
        # create container        
        new_i = Image.new("L", (width, height), color=bg_color)
        
        # paste contained image
        if justify == JUSTIFY_LEFT:
            box_x = 0
        elif justify == JUSTIFY_CENTER:
            box_x = justify_width/2 - newsize[0]/2
        else:
            box_x = justify_width - newsize[0]

        # apply filters
        i = binarize_image(i, binarize_thres)
        if invert_colors:
            i = ImageOps.invert(i)

        new_i.paste(i, (int(box_x), 0))
        outname = f'{os.path.splitext(path)[0]}_resized.bmp'
        new_i.save(outname)
        output.append(outname)

    return output

def stitch_frames(images):
    """Concatenates images horizontally into one image."""
    pil_images = [Image.open(image) for image in images]
    widths, heights = zip(*(i.size for i in pil_images))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for im in pil_images:
      new_im.paste(im, (x_offset,0))
      x_offset += im.size[0]

    return new_im


def parse_args():
    def _supported_image_file(filename):
        if not os.path.exists(filename):
            raise argparse.ArgumentTypeError("File does not exist")
        _, ext = os.path.splitext(filename)
        if ext.strip().lower() != ".gif":
            raise argparse.ArgumentTypeError("Only .gif files are supported")
        return filename

    parser = argparse.ArgumentParser(description="Convert gif image to a single image with its frames")
    parser.add_argument('file', metavar="FILE", type=_supported_image_file, help="Gif file path")
    parser.add_argument('--bin-threshold', '-b', type=int, default=200, help="Binarization threshold (black and white conversion)")
    parser.add_argument('--invert', '-i', help="Invert colors", action="store_true")
    parser.add_argument('--white-bg', '-w', help="White background. By default, black is used.", action="store_true")
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    print(f'Binarization threshold set to {args.bin_threshold}')
    print(f'Invert colors: ', args.invert)
    print(f'White background: ', args.white_bg)

    print('')
    # Separate in frames
    frames = get_frames(file=args.file)
    print(f'Processing {len(frames)} frames...')

    # Rescale frames
    frames = rescale(
        frames, 
        width=40,
        height=11,
        binarize_thres=args.bin_threshold,
        invert_colors=args.invert,
        bg_color=255 if args.white_bg else 0,
        justify=JUSTIFY_CENTER)

    # Stitch together
    pil_image = stitch_frames(frames)

    # save file
    outfile = f'{os.path.splitext(args.file)[0]}.png'
    print(f"Saving as {outfile}")
    pil_image.save(outfile)
    print(f'Done')

if __name__ == "__main__": 
    main()