import re


PALETTES = {
	'8': 3,
	'256': 8,
	'xterm-256': 8,
	'rgb': 24
}

ANSI_TEMPLATES = {
	3:  '\33[3{}m',          # Basic 8 colors
	8:  '\33[38;5;{}m',      # 256 colors palette
	24: '\33[38;2;{};{};{}m' # 24-bit RGB true colors
}

ANSI_RESET = '\33[0m'

BASIC_COLORS = [
	'black',
	'red',
	'green',
	'yellow',
	'blue',
	'magenta',
	'cyan',
	'white'
]

BASIC_RGB = [
	(0, 0, 0),
	(255, 0, 0),
	(0, 255, 0),
	(255, 255, 0),
	(0, 0, 255),
	(255, 0, 255),
	(0, 255, 255),
	(255, 255, 255)
]

RGB_REGEX = 'rgb\(([0-9]{1,3}),([0-9]{1,3}),([0-9]{1,3})\)'

XTERM_JUMPS = [95, 40, 40, 40, 40]
XTERM_COEFF = [36, 6, 1]
XTERM_GRAY_LEVELS_START = 8
XTERM_GRAY_LEVELS_OFFSET = 232
XTERM_COLORS_OFFSET = 16

DEFAULT = 'default'


def get_color_values(color, palette):
	level = PALETTES[palette]
	rgb = None
	if color in BASIC_COLORS:
		index = BASIC_COLORS.index(color)
		if level == 3:
			return (index,)
		else:
			rgb = BASIC_RGB[index]
	elif is_in_palette(color):
		if level == 8:
			return (color,)
		else:
			converter = get_to_rgb_converter(palette)
			rgb = converter(color)
	else:
		rgb_match = re.match(RGB_REGEX, color)
		if rgb_match is not None:
			rgb = rgb_match.groups()
			rgb = tuple(int(c) for c in rgb)
			if level == 24:
				return rgb
	if rgb is not None:
		if level == 3:
			return (rgb_to_basic(rgb),)
		elif level == 8:
			converter = get_from_rgb_converter(palette)
			return converter(rgb)
		elif level == 24:
			return rgb


def is_in_palette(color):
	try:
		value = int(color)
	except ValueError:
		return False
	return 0 <= value <= 255


def get_to_rgb_converter(palette):
	if palette == '256':
		return standard_palette_to_rgb
	elif palette == 'xterm-256':
		return xterm_palette_to_rgb


def get_from_rgb_converter(palette):
	if palette == '256':
		return rgb_to_standard_palette
	elif palette == 'xterm-256':
		return rgb_to_xterm_palette


def rgb_to_basic(rgb):
	bits = tuple(255 if c >= 128 else 0 for c in rgb)
	return BASIC_RGB.index(bits)


def standard_palette_to_rgb(color):
	bits = bin(int(color))[2:].zfill(8)
	rgb = bits[0:3], bits[4:7], bits[7:]
	return tuple(int(int(s, 2) * 255 / (2**len(s)-1)) for s in rgb)


def rgb_to_standard_palette(rgb):
	bits = ''
	for i, j in zip(rgb, [3, 3, 2]):
		print(i * (2**j-1) / 255, bin(int(i * (2**j-1) / 255))[2:])
		bits += bin(int(i * (2**j-1) / 255))[2:].zfill(j)
	return int(bits, 2)


def xterm_palette_to_rgb(color):
	color = int(color)
	# Basic colors
	if color <= 7:
		return BASIC_RGB[color]
	if 8 <= color <= 15:
		return tuple(c + 128 for c in BASIC_RGB[color-8])
	# Gray levels
	if XTERM_GRAY_LEVELS_OFFSET <= color <= 255:
		return (8 * (color - XTERM_GRAY_LEVELS_OFFSET + 1),) * 3
	# Other colors
	value = color - XTERM_COLORS_OFFSET
	mod = value
	rgb = []
	for c in XTERM_COEFF:
		val, mod = divmod(mod, c)
		rgb.append(sum(XTERM_JUMPS[:val]))
	return tuple(rgb)


def rgb_to_xterm_palette(rgb):
	result = None
	r, g, b = rgb
	# Gray levels
	if r == g == b:
		if r < 4:
			result = 0
		if r > 246:
			result = 15
		if 238 <= r <= 246:
			result = 255
		value, mod = divmod(r - XTERM_GRAY_LEVELS_START, 10)
		if mod > 4:
			value += 1
		result = XTERM_GRAY_LEVELS_OFFSET + value
	# Other colors
	total = 0
	for index, c in enumerate(rgb):
		prev_tot, tot = 0, 0
		i = 0
		while tot < c and i < len(XTERM_JUMPS):
			prev_tot = tot
			tot += XTERM_JUMPS[i]
			i += 1
		val = i if abs(tot - c) <= abs(prev_tot - c) else i-1
		total += val * XTERM_COEFF[index]
	result = XTERM_COLORS_OFFSET + total
	return (result,)


class ColoredStr(str):

	def __new__(cls, string, color, palette='xterm-256'):
		if color == DEFAULT:
			return string
		values = get_color_values(color.lower(), palette)
		level = PALETTES[palette]
		ansi_seq = ANSI_TEMPLATES[level].format(*values)
		literal = ansi_seq + string + ANSI_RESET
		the_string = super().__new__(cls, literal)
		setattr(the_string, 'length', len(string))
		setattr(the_string, 'true_length', len(the_string))
		setattr(the_string, 'lenesc', len(ansi_seq) + len(ANSI_RESET))
		return the_string

	def __len__(self):
		return self.length


if __name__ == '__main__':
	print(ColoredStr('hello, world', 'blue', 'xterm-256'))
