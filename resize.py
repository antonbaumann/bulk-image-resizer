import argparse
import os
import pathlib
from PIL import Image
import time

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
	return p


def validate_arguments(p, a):
	if not os.path.isdir(a.root_path):
		p.error('Input directory [{}] does not exist'.format(a.root_path))

	if not os.path.isdir(a.result_path):
		p.error('Output directory [{}] does not exist'.format(a.result_path))

	if a.root_path in a.result_path and a.root_path != a.result_path:
		p.error('Output directory must not be in input directory')

	if a.root_path == a.result_path:
		print('[!] WARNING: With this configuration your images could be overwritten!')
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


def main():
	parser = init_parser()
	args = parser.parse_args()

	args.root_path = os.path.abspath(args.root_path)
	args.result_path = os.path.abspath(args.result_path)

	validate_arguments(parser, args)

	# count files
	nr_files_to_resize = 0
	print('[i] counting files ...')
	for _, _, files in os.walk(args.root_path):
		nr_files_to_resize += len(files)
	print('[i] {} files to resize'.format(nr_files_to_resize))

	# iterate through every file in the root directory and all child-directories
	time_start = time.time()
	nr_files_resized = 0
	for root, directory, files in os.walk(args.root_path):
		for file in files:
			structure = get_relative_path_from_root(root, args.result_path)
			path_in = os.path.join(root, file)
			root_out = os.path.abspath(os.path.join(args.result_path + '/' + structure))
			try:
				im = Image.open(path_in)
				icc_profile = im.info.get('icc_profile')
				size = get_new_size(im.size, args)
				im = im.resize(size, Image.ANTIALIAS)
				pathlib.Path(root_out).mkdir(parents=True, exist_ok=True)
				im.save(os.path.join(root_out, parse_name(file, args.format)), args.format, icc_profile=icc_profile)
				print('[✓] [{}] resized  {}'.format(
					progress(time_start, nr_files_to_resize, nr_files_resized), path_in)
				)
			except IOError:
				print('[i] [{}] skipping {}: file not supported'.format(
					progress(time_start, nr_files_to_resize, nr_files_resized), path_in)
				)
			except ValueError:
				print('[i] [{}] skipping {}: file not supported'.format(
					progress(time_start, nr_files_to_resize, nr_files_resized), path_in)
				)
			finally:
				nr_files_resized += 1


if __name__ == '__main__':
	main()
