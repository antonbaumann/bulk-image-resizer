# coding=utf-8

import argparse
import os
import pathlib
from PIL import Image
import time
from multiprocessing import Pool
import tqdm
from functools import partial

# constants
POSSIBLE_RESULT_FORMATS = ['jpeg', 'png', 'gif']


def init_parser():
    parser = argparse.ArgumentParser(description='resize images')

    parser.add_argument(
        'root_path',
        metavar='PATH_ROOT',
        type=str,
        help='path to root directory of images')
    parser.add_argument(
        'result_path',
        metavar='PATH_RESULT',
        type=str,
        help='path to resized images')
    parser.add_argument(
        '--height',
        metavar='HEIGHT',
        type=int,
        help='height of resized image')
    parser.add_argument(
        '--width',
        metavar='WIDTH',
        type=int,
        help='width of resized image')
    parser.add_argument(
        '--max-px-long-side',
        metavar='LONG',
        type=int,
        help='maximum pixels for longer side')
    parser.add_argument(
        '--format',
        metavar='FORMAT',
        type=str,
        default='jpeg',
        help='format of resized image {}'.format(POSSIBLE_RESULT_FORMATS))
    parser.add_argument(
        '--processes',
        metavar='PROCESSES',
        type=int,
        default='2',
        help='number of processes')
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='verbose output')
    return parser


def validate_arguments(parser, args):
    if not os.path.isdir(args.root_path):
        parser.error(
            'Input directory [{}] does not exist'.format(args.root_path))

    if not os.path.isdir(args.result_path):
        parser.error('Output directory [{}] does not exist'.format(
            args.result_path))

    if path_is_parent(args.root_path,
                      args.result_path) and args.root_path != args.result_path:
        parser.error('Output directory must not be in input directory')

    if args.root_path == args.result_path:
        print(
            '[!] WARNING: With this configuration your original images will be overwritten!'
        )
        input_str = '-----'
        while input_str.upper() not in ['Y', 'N', '']:
            input_str = input('[?] Do you want to proceed? [y|N]: ')
            if input_str in ['N', '']:
                exit(0)

    if args.format not in POSSIBLE_RESULT_FORMATS:
        parser.error('result image format not supported')

    if args.height is not None and args.width is not None:
        parser.error('you can either set height or width')


def create_file_list(root_path):
    file_list = []
    for root, _, files in os.walk(root_path):
        for f in files:
            file_list.append(os.path.join(root, f))
    return file_list


def get_new_size(size, width, height, max_px_long_side):
    new_size = size

    if height is not None and height < size[1]:
        scale = height / size[1]
        new_size = int(size[0] * scale), height
    if width is not None and width < size[0]:
        scale = width / size[0]
        new_size = width, int(size[1] * scale)

    if max_px_long_side is not None:
        ratio = size[0] / size[1]
        if max(new_size) > max_px_long_side:
            if new_size[0] >= new_size[1]:
                new_size = max_px_long_side, int(max_px_long_side / ratio)
            else:
                new_size = int(max_px_long_side * ratio), max_px_long_side

    return new_size


def format_name(file_name, suffix):
    return file_name.split('.')[0] + '.' + suffix


def path_is_parent(parent_path, child_path):
    return os.path.commonpath([parent_path]) == os.path.commonpath(
        [parent_path, child_path])


def progress(t_start, nr_images, nr_done):
    time_per_image = (time.time() - t_start) / nr_done if nr_done != 0 else 1
    time_left_in_seconds = int(time_per_image * (nr_images - nr_done))

    hours = (time_left_in_seconds // 3600)
    minutes = str((time_left_in_seconds // 60) % 60).zfill(2)
    seconds = str(time_left_in_seconds % 60).zfill(2)

    time_left_str = ''
    if hours > 0:
        time_left_str += '{}h {}min {}s'.format(hours, minutes, seconds)
    else:
        time_left_str += '{}min {}s'.format(minutes, seconds)

    return '{} of {} | {}'.format(
        str(nr_done).zfill(len(str(nr_images))), nr_images, time_left_str)


def resize_image(root_path, result_path, width, height, max_px_long_side,
                 result_format, verbose, image_path):
    image_root, image_name = os.path.split(image_path)
    relative_path = os.path.relpath(image_root, root_path)
    abs_root_of_new_file = os.path.join(result_path, relative_path)

    try:
        im = Image.open(image_path)
        icc_profile = im.info.get('icc_profile')
        size = get_new_size(im.size, width, height, max_px_long_side)
        im = im.resize(size, Image.ANTIALIAS)
        pathlib.Path(abs_root_of_new_file).mkdir(parents=True, exist_ok=True)
        im.save(
            os.path.join(abs_root_of_new_file,
                         format_name(image_name, result_format)),
            result_format,
            icc_profile=icc_profile)
    except IOError:
        if verbose:
            print('[i] skipping {}: file not supported'.format(image_name))
    except ValueError:
        if verbose:
            print('[i] skipping {}: file not supported'.format(image_name))


def main():
    parser = init_parser()
    args = parser.parse_args()
    args.root_path = os.path.abspath(args.root_path)
    args.result_path = os.path.abspath(args.result_path)

    validate_arguments(parser, args)

    # create a list of all files
    print('[i] counting files ...')
    files_to_resize = create_file_list(args.root_path)
    print('[i] {} files to resize'.format(len(files_to_resize)))

    p = Pool(processes=args.processes)
    f = partial(resize_image, args.root_path, args.result_path, args.width,
                args.height, args.max_px_long_side, args.format, args.verbose)
    for _ in tqdm.tqdm(p.imap(f, files_to_resize), total=len(files_to_resize)):
        pass


if __name__ == '__main__':
    main()
