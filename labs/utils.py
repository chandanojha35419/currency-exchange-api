import importlib
import logging
import sys

__author__ = 'chandanojha'

logger = logging.getLogger(__name__)


def split_fullname(name):
    try:
        first, last = name.rsplit(maxsplit=1)
        return first, last
    except (ValueError, AttributeError) as e:
        return name, ''


def get_client_token(request):
    if hasattr(request, '_request'):
        request = getattr(request, '_request')

    if hasattr(request, 'META'):
        return request.META.get('HTTP_CLIENT_TOKEN', '')
    return ''


def as_bool(value):
    from distutils.util import strtobool
    if isinstance(value, str):
        value = strtobool(value)
    return bool(value)


def is_migrating(commands=None):
    default_command_list = {'migrate', 'showmigrations', 'makemigrations'}
    ignore_commands = default_command_list.union(commands or [])
    return any(arg in ignore_commands for arg in sys.argv)


def load_class_from_string(dotted_name):
    module_name, class_name = dotted_name.rsplit(".", 1)
    return getattr(importlib.import_module(module_name), class_name)


def str_list(strs):
    if strs is None or not isinstance(strs, str):
        return strs
    strs = strs.strip('[{( )}]')
    return [s for s in (s.strip() for s in strs.split(',') if s) if s]


def int_list(ints):
    ints = str_list(ints)
    if ints is None:
        return None
    ret = []
    for n in ints:
        try:
            ret.append(int(n))
        except ValueError:
            pass
    return ret


def query_param(request, key, default_value=None):
    qp = getattr(request, 'query_params', None)
    return qp.get(key, default_value) if qp else default_value


def or_filter(**kwargs):
    from django.db.models import Q
    q = Q()
    for k, v in kwargs.items():
        if v is not None:
            if k.endswith('__in') and isinstance(v, (list, tuple)):
                # special case handling, where we have multiple filter values for same key
                for s in v:
                    q |= Q(**{k: s})
            else:
                q |= Q(**{k: v})
    return q if q else None


def model_does_not_exists(view):
    if getattr(view, 'model_class', None):
        return view.model_class.DoesNotExist

    class DummyException(Exception):
        pass

    return DummyException


def get_class_name(instance):
    import re
    cls = getattr(instance, 'model_class', None)
    if cls:
        return cls.__name__

    class_name = instance.__class__.__name__
    return re.sub('View', '', class_name)
