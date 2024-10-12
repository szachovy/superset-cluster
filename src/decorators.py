"""
temp
"""

# mypy: disable-error-code=attr-defined

import functools
import threading
import typing


class Overlay(type):
    def __call__(cls, *args, **kwargs) -> typing.Any:
        instance = super().__call__(*args, **kwargs)
        for class_attribute in dir(instance):
            if class_attribute.startswith('_'):
                continue
            attribute = getattr(instance, class_attribute)
            if callable(attribute):
                if getattr(attribute, '_is_run_selected_methods_once', False):
                    attribute()
        return instance

    def run_all_methods(cls) -> typing.Any:
        for attribute in dir(cls):
            if callable(getattr(cls, attribute)) and not attribute.startswith('_'):
                getattr(cls, attribute)(cls)
        return cls

    @staticmethod
    def run_selected_methods_once(method: typing.Callable) -> typing.Callable:
        method._is_run_selected_methods_once = True  # pylint: disable=protected-access

        @functools.wraps(method)
        def method_wrapper(self, *args, **kwargs) -> typing.Callable:
            return method(self, *args, **kwargs)
        return method_wrapper

    @staticmethod
    def single_sign_on(method_reference: typing.Callable) -> typing.Callable:
        lock = threading.Lock()

        @functools.wraps(method_reference)
        def method_wrapper(*args, **kwargs) -> str | dict[str, str]:
            if not method_wrapper.object_created:
                with lock:
                    if not method_wrapper.object_created:
                        method_wrapper.tokens = method_reference(*args, **kwargs)
                        method_wrapper.object_created = True
            return method_wrapper.tokens
        method_wrapper.object_created = False
        return method_wrapper
