__author__ = 'chandanojha'


def get_int_config(config):
    configs = {
        'user.token.lifetime': 30,
        'user.token.length': 20,
        'user.otp.lifetime': 30,
        'user.otp.length': 6,
        
        'user.staff_default_password': 'password',
        'user.username.length': 12,
    }
    return configs[config]


def get_config(config):
    configs = {
        'user.otp.allowed_chars': '0123456789',

    }
    return configs[config]


def get_bool_config(config):
    configs = {
        'user.disable_permission_checks': True,

    }
    return configs[config]


def get_evaluated_config(config):
    configs = {
        'user.register_permissons_for_apps': (),
    }
    return configs[config]