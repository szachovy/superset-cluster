"""
The Overlay metaclass adds functionality to automatically execute
certain methods upon instantiation, manage method calls with synchronization, and mark
methods for single execution with ensurance that certain methods can
only run once across multiple calls, even in a multithreaded environment.

Classes:
--------
- `Overlay`: A metaclass that enhances class behavior by allowing method execution
  control and automatic invocation of specified methods.

Key Functionalities:
--------------------
- Automatic Method Invocation: Run all non-private callable methods of a class
  when an instance is created.

- Method Execution Control: Mark methods to be executed once during the lifetime
  of the application.

- Single Sign-On Mechanism: Manage the execution of a method so that it runs only
  once, returning the same result for subsequent calls.

Usage Example:
--------------
class MyService(metaclass=Overlay):
    @Overlay.run_selected_methods_once
    def parse(self):
        self.config = {"setting1": "value1", "setting2": "value2"}

    @Overlay.single_sign_on
    def get_tokens(self) -> dict[str, str]:
        return {
            "token_2": "first_example",
            "token_2": "second_example"
        }

service_instance = MyService()  # This will automatically call `parse()`
tokens = service_instance.get_tokens()  # This will do not recreate tokens between subsequent stages

@Overlay.run_all_methods
class MyClass(metaclass=Overlay):
    def method_1(self):
        pass

    def method_2(self):
        pass

instance = MyClass()  # This will run all methods in the class
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
