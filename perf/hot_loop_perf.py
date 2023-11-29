from ex_funcs.ex_loop import do_nothing
from timeit import timeit
from ducktools.lazyimporter import LazyImporter, FromImport

laz = LazyImporter([
    FromImport("ex_funcs.ex_loop", "do_nothing")
])


blank_obj = object()


def ex_imported_func(obj):
    return do_nothing(obj)


def ex_inline_import(obj):
    from ex_funcs.ex_loop import do_nothing
    return do_nothing(obj)


def ex_lazy_import(obj):
    return laz.do_nothing(obj)


_ = timeit(lambda: ex_imported_func(blank_obj), number=500_000)
_ = timeit(lambda: ex_inline_import(blank_obj), number=500_000)
_ = timeit(lambda: ex_lazy_import(blank_obj), number=500_000)

eager_time = timeit(lambda: ex_imported_func(blank_obj), number=1_000_000)
inline_time = timeit(lambda: ex_inline_import(blank_obj), number=1_000_000)
lazy_time = timeit(lambda: ex_lazy_import(blank_obj), number=1_000_000)

print(f"Timings:\n{eager_time=:.3f}s\n{inline_time=:.3f}s\n{lazy_time=:.3f}s")
