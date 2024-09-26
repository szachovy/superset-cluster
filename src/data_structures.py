
import ctypes
import ctypes.util
import functools
import threading
import typing


class socket_address(ctypes.Structure):
    _fields_ = [
        ('socket_address_family', ctypes.c_ushort),
        ('socket_address_code', ctypes.c_byte * 14)
    ]


class socket_interface(ctypes.Structure):
    _fields_ = [
        ('socket_interface_family', ctypes.c_ushort),
        ('socket_interface_port', ctypes.c_uint16),
        ('socket_interface_address', ctypes.c_byte * 4)
    ]


class network_interface(ctypes.Structure):
    pass


class Overlay(type):
    def __call__(cls, *args, **kwargs) -> typing.Any:
        instance = super().__call__(*args, **kwargs)
        for class_attribute in dir(instance):
            if class_attribute.startswith('_'):
                continue
            attribute = getattr(instance, class_attribute)
            if callable(attribute) and getattr(attribute, '_is_post_init_hook', False):
                attribute()
        return instance

    @staticmethod
    def post_init_hook(method: typing.Callable) -> typing.Callable:
        # Logging what container on what node
        # {component} STATUS output after {command} is {output} ...
        method._is_post_init_hook = True
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
