import sys

FORCE_USE = False

USE_ZEN = False
zengl = NotImplemented
moderngl = NotImplemented
if sys.platform in ("emscripten", "wasi") or FORCE_USE:
    import zengl
    USE_ZEN = True
else:
    import moderngl
    USE_ZEN = False
