# -*- coding: utf-8 -*

DEFAULT_SETTINGS = {}


def apply_settings():
    """Updates django.conf.settings with application settings."""
    # Don't import settings globally, so that settings loading happens lazily
    from django.conf import settings

    DEFAULT_SETTINGS['FIELD_ENCRYPTION_KEYS'] = getattr(settings, 'FIELD_ENCRYPTION_KEYS',
                                                        [str.encode(settings.SECRET_KEY).hex()])

    for key, value in DEFAULT_SETTINGS.items():
        if not hasattr(settings, key):
            setattr(settings, key, value)
