import argparse
import os
import pathlib
from PIL import Image

# constants
POSSIBLE_RESULT_FORMATS = ['jpeg', 'png', 'gif']


# functions
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


# parser
parser = argparse.ArgumentParser(description='resize images')

parser.add_argument('root_path', metavar='PATH_ROOT', type=str, help='path to root directory of images')
parser.add_argument('result_path', metavar='PATH_RESULT', type=str, help='path to resized images')
parser.add_argument('--height', metavar='H', type=int, help='height of resized image')
parser.add_argument('--width', metavar='W', type=int, help='width of resized image')
parser.add_argument('--format', metavar='F', type=str, default='jpeg',
					help='format of resized image {}'.format(POSSIBLE_RESULT_FORMATS))

args = parser.parse_args()

args.root_path = os.path.abspath(args.root_path)
args.result_path = os.path.abspath(args.result_path)

# check if arguments are valid
if not os.path.isdir(args.root_path):
	parser.error('Input directory [{}] does not exist'.format(args.root_path))

if not os.path.isdir(args.result_path):
	parser.error('Output directory [{}] does not exist'.format(args.result_path))

if args.root_path in args.result_path and args.root_path != args.result_path:
	parser.error('Output directory must not be in input directory')

if args.root_path == args.result_path:
	print('[!] WARNING: With this configuration your images could be overwritten!')
	input_str = '-----'
	while input_str.upper() not in ['Y', 'N', '']:
		input_str = input('[?] Do you want to proceed? [y|N]: ')
		if input_str in ['N', '']:
			exit(0)

if args.format not in POSSIBLE_RESULT_FORMATS:
	parser.error('result image format not supported')

if args.height is not None and args.width is not None:
	parser.error('you can either set height or width')


# iterate through every file in the root directory and all child-directories
for root, directory, files in os.walk(args.root_path):
	for file in files:
		try:
			structure = get_relative_path_from_root(root, args.result_path)
			path_in = os.path.join(root, file)
			root_out = os.path.abspath(os.path.join(args.result_path + '/' + structure))
			im = Image.open(path_in)
			icc_profile = im.info.get('icc_profile')
			size = get_new_size(im.size, args)
			im = im.resize(size, Image.ANTIALIAS)
			pathlib.Path(root_out).mkdir(parents=True, exist_ok=True)
			im.save(os.path.join(root_out, parse_name(file, args.format)), args.format, icc_profile=icc_profile)
			print('resized {}'.format(path_in))
		except IOError:
			pass
