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
POSSIBLE_ROTATIONS = [90, 180, 270]


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
        '--rotation',
        metavar='ROTATION',
        type=int,
        help='degrees to rotate image')
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

    if args.rotation not in POSSIBLE_ROTATIONS:
        parser.error('rotation not supported')


def create_file_list(root_path):
    file_list = []
    for root, _, files in os.walk(root_path):
        for f in files:
            file_list.append(os.path.join(root, f))
    return file_list


def get_rotation_enum(rotation: int):
    if rotation == 90:
        return Image.ROTATE_90
    if rotation == 180:
        return Image.ROTATE_180
    if rotation == 270:
        return Image.ROTATE_270


def format_name(file_name, suffix):
    return file_name.split('.')[0] + '.' + suffix


def path_is_parent(parent_path, child_path):
    return os.path.commonpath([parent_path]) == os.path.commonpath(
        [parent_path, child_path])


def rotate_image(root_path, result_path, transformation, result_format, verbose, image_path):
    image_root, image_name = os.path.split(image_path)
    relative_path = os.path.relpath(image_root, root_path)
    abs_root_of_new_file = os.path.join(result_path, relative_path)

    try:
        im = Image.open(image_path)
        icc_profile = im.info.get('icc_profile')
        im = im.transpose(get_rotation_enum(transformation))
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
    f = partial(rotate_image, args.root_path, args.result_path, args.rotation, args.format, args.verbose)
    for _ in tqdm.tqdm(p.imap(f, files_to_resize), total=len(files_to_resize)):
        pass
    p.close()


if __name__ == '__main__':
    main()
