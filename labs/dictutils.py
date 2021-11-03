__author__ = 'chandanojha'


def dict_filter_keys(d, keys, comparator=None):
	if comparator is None:
		for k in keys:
			d.pop(k, None)
	else:
		assert callable(comparator), "'comparator' should be function taking two parameter"
		for k in tuple(d.keys()):
			for e in keys:
				if comparator(k, e):
					d.pop(k)
	return d


def xpath_get(d, key_path, default_val=None, separator='/'):
	elem = d
	try:
		for x in key_path.strip(separator).split(separator):
			try:
				x = int(x)
			except ValueError:
				pass
			elem = elem[x]
	except:
		return default_val

	return elem


def xpath_set(d, key_path, value, separator='/', create=False):
	elem = d
	default_val = 'some_default_value'
	key_parts = key_path.strip(separator).split(separator)
	leaf = key_parts.pop()
	if key_parts:
		elem = xpath_get(elem, separator.join(key_parts), default_val, separator)

	if elem != default_val and (leaf in elem or create):
		elem[leaf] = value
	else:
		raise KeyError("Invalid key path.")
