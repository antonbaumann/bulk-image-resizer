# coding=utf-8

import argparse
import os
import pathlib
from PIL import Image
import time
from multiprocessing import Pool
import tqdm

# constants
POSSIBLE_RESULT_FORMATS = ['jpeg', 'png', 'gif']


# functions
def init_parser():
	p = argparse.ArgumentParser(description='resize images')

	p.add_argument('root_path', metavar='PATH_ROOT', type=str, help='path to root directory of images')
	p.add_argument('result_path', metavar='PATH_RESULT', type=str, help='path to resized images')
	p.add_argument('--height', metavar='H', type=int, help='height of resized image')
	p.add_argument('--width', metavar='W', type=int, help='width of resized image')
	p.add_argument('--format', metavar='F', type=str, default='jpeg',
						help='format of resized image {}'.format(POSSIBLE_RESULT_FORMATS))
	p.add_argument('--processes', metavar='P', type=int, default='4', help='number of processes')
	p.add_argument('--verbose', action='store_true', default=False, help='verbose output')
	return p


def validate_arguments(p, a):
	if not os.path.isdir(a.root_path):
		p.error('Input directory [{}] does not exist'.format(a.root_path))

	if not os.path.isdir(a.result_path):
		p.error('Output directory [{}] does not exist'.format(a.result_path))

	if a.root_path in a.result_path and a.root_path != a.result_path:
		p.error('Output directory must not be in input directory')

	if a.root_path == a.result_path:
		print('[!] WARNING: With this configuration your images could get overwritten!')
		input_str = '-----'
		while input_str.upper() not in ['Y', 'N', '']:
			input_str = input('[?] Do you want to proceed? [y|N]: ')
			if input_str in ['N', '']:
				exit(0)

	if a.format not in POSSIBLE_RESULT_FORMATS:
		p.error('result image format not supported')

	if a.height is not None and a.width is not None:
		p.error('you can either set height or width')


def get_new_size(size, args):
	if args.height is not None:
		ratio = args.height / size[1]
		return int(size[0] * ratio), args.height
	if args.width is not None:
		ratio = args.width // size[0]
		return args.height, int(size[1] / ratio)
	return size


def get_relative_path_from_root(r, p):
	root_abs = os.path.abspath(r)
	path_abs = os.path.abspath(p)

	i = 0
	for _ in range(min(len(root_abs), len(path_abs))):
		if root_abs[i] != path_abs[i]:
			break
		i += 1

	return root_abs[i:]


def parse_name(file_name, suffix):
	return file_name.split('.')[0] + '.' + suffix


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
		str(nr_done).zfill(len(str(nr_images))),
		nr_images,
		time_left_str
	)


def resize_image(path):
	root, file_name = os.path.split(path)
	relative_path = get_relative_path_from_root(root, args.result_path)
	abs_root_of_new_file = os.path.join(args.result_path, relative_path)
	try:
		im = Image.open(path)
		icc_profile = im.info.get('icc_profile')
		size = get_new_size(im.size, args)
		im = im.resize(size, Image.ANTIALIAS)
		pathlib.Path(abs_root_of_new_file).mkdir(parents=True, exist_ok=True)
		im.save(os.path.join(abs_root_of_new_file, parse_name(file_name, args.format)), args.format, icc_profile=icc_profile)
	except IOError:
		if args.verbose:
			print('[i] skipping {}: file not supported'.format(file_name))
	except ValueError:
		if args.verbose:
			print('[i] skipping {}: file not supported'.format(file_name))


parser = init_parser()
args = parser.parse_args()


def main():
	print(args)
	args.root_path = os.path.abspath(args.root_path)
	args.result_path = os.path.abspath(args.result_path)

	validate_arguments(parser, args)

	# create a list of all files
	files_to_resize = []
	print('[i] counting files ...')
	for root, _, files in os.walk(args.root_path):
		for file in files:
			files_to_resize.append(os.path.join(root, file))
	print('[i] {} files to resize'.format(len(files_to_resize)))

	p = Pool(processes=args.processes)
	for _ in tqdm.tqdm(p.imap_unordered(resize_image, files_to_resize), total=len(files_to_resize)):
		pass


if __name__ == '__main__':
	main()
