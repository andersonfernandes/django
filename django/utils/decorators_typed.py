from functools import partial, update_wrapper, wraps
from typing import Any, Callable, List, Optional, Type, Union


class classonlymethod(classmethod):
    def __get__(self, instance, cls=None) -> Any:
        if instance is not None:
            raise AttributeError(
                "This method is available only on the class, not on instances."
            )
        return super().__get__(instance, cls)


def _update_method_wrapper(_wrapper: Callable, decorator: Callable) -> None:
    @decorator
    def dummy(*args, **kwargs):
        pass

    update_wrapper(_wrapper, dummy)


def _multi_decorate(
    decorators: Union[Callable, List[Callable]], method: Callable
) -> Callable:
    if hasattr(decorators, "__iter__"):
        decorators = decorators[::-1]
    else:
        decorators = [decorators]

    def _wrapper(self, *args, **kwargs) -> Any:
        bound_method = wraps(method)(partial(method.__get__(self, type(self))))
        for dec in decorators:
            bound_method = dec(bound_method)
        return bound_method(*args, **kwargs)

    for dec in decorators:
        _update_method_wrapper(_wrapper, dec)
    update_wrapper(_wrapper, method)
    return _wrapper


def method_decorator(decorator: Callable, name: str = "") -> Callable:
    def _dec(obj: Union[Type, Callable]) -> Union[Type, Callable]:
        if not isinstance(obj, type):
            return _multi_decorate(decorator, obj)
        if not (name and hasattr(obj, name)):
            raise ValueError(
                "The keyword argument `name` must be the name of a method "
                "of the decorated class: %s. Got '%s' instead." % (obj, name)
            )
        method = getattr(obj, name)
        if not callable(method):
            raise TypeError(
                "Cannot decorate '%s' as it isn't a callable attribute of "
                "%s (%s)." % (name, obj, method)
            )
        _wrapper = _multi_decorate(decorator, method)
        setattr(obj, name, _wrapper)
        return obj

    if not hasattr(decorator, "__iter__"):
        update_wrapper(_dec, decorator)
    obj = decorator if hasattr(decorator, "__name__") else decorator.__class__
    _dec.__name__ = "method_decorator(%s)" % obj.__name__
    return _dec


def decorator_from_middleware_with_args(
    middleware_class: Type[object],
) -> Callable[..., Callable]:
    return make_middleware_decorator(middleware_class)


def decorator_from_middleware(
    middleware_class: Type[object],
) -> Callable[..., Callable]:
    return make_middleware_decorator(middleware_class)()


def make_middleware_decorator(
    middleware_class: Type[object],
) -> Callable[..., Callable[..., Any]]:
    def _make_decorator(*m_args: Any, **m_kwargs: Any) -> Callable[..., Any]:
        def _decorator(view_func: Callable[..., Any]) -> Callable[..., Any]:
            middleware = middleware_class(view_func, *m_args, **m_kwargs)

            @wraps(view_func)
            def _wrapper_view(
                request: Any, *args: Any, **kwargs: Any
            ) -> Union[Any, None]:
                if hasattr(middleware, "process_request"):
                    result = middleware.process_request(request)
                    if result is not None:
                        return result
                if hasattr(middleware, "process_view"):
                    result = middleware.process_view(request, view_func, args, kwargs)
                    if result is not None:
                        return result
                try:
                    response = view_func(request, *args, **kwargs)
                except Exception as e:
                    if hasattr(middleware, "process_exception"):
                        result = middleware.process_exception(request, e)
                        if result is not None:
                            return result
                    raise
                if hasattr(response, "render") and callable(response.render):
                    if hasattr(middleware, "process_template_response"):
                        response = middleware.process_template_response(
                            request, response
                        )

                    def callback(response: Any) -> Any:
                        return middleware.process_response(request, response)

                    response.add_post_render_callback(callback)
                else:
                    if hasattr(middleware, "process_response"):
                        return middleware.process_response(request, response)
                return response

            return _wrapper_view

        return _decorator

    return _make_decorator


def sync_and_async_middleware(func: Callable) -> Callable:
    func.sync_capable = True
    func.async_capable = True
    return func


def sync_only_middleware(func: Callable) -> Callable:
    func.sync_capable = True
    func.async_capable = False
    return func


def async_only_middleware(func: Callable) -> Callable:
    func.sync_capable = False
    func.async_capable = True
    return func
