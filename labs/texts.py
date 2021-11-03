import logging

from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Global text store, can be referenced by group:key combo
#
# Typical use is to set group=django's app_label and then store all messages used in that app
# under that group. Text's can have placeholder which can be filled at use-time
#
#   register_texts('my_app_label', {'key1': "Message One", 'key2': "Message with placeholder={0}"})
#
# and then
#
#   get_text('my_app_label', 'key1')
#   get_text('my_app_label', 'key2', placeholder_value)
#
# Also, creating following shortcuts for the above methods in app.init file would save on passing 'group' everytime
#
#   def register_app_text(txt_dict):
#       utils.register_text('my_app_label', txt_dict)
#
#   def get_app_text(key, ...):
#       utils.get_text('my_app_label', key, ...)
#

_global_texts = {
    '*': {
        # put global/generic/reusable texts here..
        'param{0}_required': _("Missing required parameter: `{0}`"),
        'param{0}_invalid': _("Invalid parameter: `{0}`"),
        'param{0}_not_allowed': _("Parameter `{0}` not allowed"),
        'param{0}_has_no_effect': _("Parameter `{0}` has no effect or not allowed at this time"),
        'invalid_email': _("Invalid email id"),
        'invalid_mobile': _("Invalid mobile number, should be a 10-digit India number"),
    },
}


def register_texts(group, txt_dict):
    try:
        text_group = _global_texts[group]
    except KeyError:
        text_group = {}
        _global_texts[group] = text_group

    for key, msg in txt_dict.items():
        assert msg, "Empty message text?"
        if key in text_group:
            logger.info("Duplicate message text, overwriting '{0}': {1}".format(key, msg))
        text_group[key] = msg


def get_text(group, key, *args, **kwargs):
    try:
        msg = _global_texts[group][key]
        return msg.format(*args, **kwargs) if (args or kwargs) else msg
    except KeyError as e:
        if group == '*':
            # we reached end.. just complain
            return "Missing text group or key='{0}.{1}', forgot to register it in your class?".format(group, key)

        if '.' in group:
            return get_text(group.rsplit('.', maxsplit=1)[0], key, *args, **kwargs)
        else:
            return get_text('*', key, *args, **kwargs)  # check globals


def register_global_texts(txt_dict):
    register_texts('*', txt_dict)


def get_global_text(key, *args, **kwargs):
    return get_text('*', key, *args, **kwargs)
