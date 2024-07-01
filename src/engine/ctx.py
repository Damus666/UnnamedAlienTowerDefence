from .usezen import USE_ZEN, zengl, moderngl
import typing
import struct
import glm
import numpy
import warnings

ctx: typing.Union["moderngl.Context", "zengl.Context"] = None
shaders: dict[str, typing.Union[dict, "moderngl.Program"]] = {}
zen_image: "zengl.Image" = None
zen_pipelines: dict["zengl.Pipeline", str] = {}
zen_resources = []

def new_frame():
    if not USE_ZEN:
        return
    ctx.new_frame()

def end_frame():
    if not USE_ZEN:
        return
    ctx.end_frame()

def create_ctx():
    global ctx, zen_image
    if USE_ZEN:
        ctx = zengl.context()
        zen_image = ctx.image((1920, 1080), "rgba8unorm", samples=4)#, ctx.image((1920, 1080), "depth24plus", samples=4)
    else:
        ctx = moderngl.create_context()
        ctx.enable(moderngl.BLEND)
        ctx.blend_func = ctx.SRC_ALPHA, ctx.ONE_MINUS_SRC_ALPHA

def clear(color: tuple[float, float, float, float]):
    if USE_ZEN:
        zen_image.clear()
    else:
        ctx.clear(*color)

def make_pipeline(shader, vbo, ibo, vbo_layout, vertex_count, layout):
    UNIFORMS = {
        "lit": {
            "proj": None,
            "view": None,
            "numLights": None,
            "lightData": None
        },
        "unlit": {
            "proj": None,
            "view": None,
        },
        "replace": {
            "proj": None,
            "view": None,
        },
        "ui": {
            "projUI": None,
        },
    }
    return ctx.pipeline(
        vertex_shader=shaders[shader]["vert"],
        fragment_shader=shaders[shader]["frag"],
        framebuffer=[zen_image],
        topology="triangles",
        blend={
            'enable': True,
            'src_color': 'src_alpha',
            'dst_color': 'one_minus_src_alpha',
        },
        uniforms=UNIFORMS[shader],
        layout=layout,
        resources=zen_resources.copy(),
        vertex_buffers=zengl.bind(vbo, vbo_layout, *list(range(len(vbo_layout.split(" "))))),
        index_buffer=ibo,
        vertex_count=vertex_count,
    )

def register_resources(*images):
    global zen_resources
    res = []
    for i, img in enumerate(images):
        res.append({"type": "sampler", "binding": i, "image": img, "mag_filter": "nearest", "min_filter": "nearest"})
    zen_resources = res

def register_pipeline(obj, shader):
    zen_pipelines[obj] = shader

def unregister_pipeline(obj):
    if obj in zen_pipelines:
        zen_pipelines.pop(obj)

def load_shaders(folder: str, *names: str):
    if ctx is None:
        create_ctx()
    for name in names:
        with open(f"{folder}/{name}.vert", "r") as vert_file:
            with open(f"{folder}/{name}.frag", "r") as frag_file:
                if USE_ZEN:
                    shaders[name] = {"vert": vert_file.read(), "frag": frag_file.read()}
                else:
                    shaders[name] = ctx.program(vertex_shader=vert_file.read(),
                                                fragment_shader=frag_file.read())
                    
def zen_get_value(inval):
    if isinstance(inval, int):
        return struct.pack("i", inval)
    if isinstance(inval, float):
        return struct.pack("f", inval)
    if isinstance(inval, glm.mat4):
        return inval.to_bytes()
    if isinstance(inval, numpy.ndarray):
        return inval.tobytes()
    if isinstance(inval, bytes):
        return inval
    warnings.warn(f"Trying to convert to zengl value of type {type(inval)} which has currently no path", UserWarning)
    return inval
                
def get_shader(name: str) -> typing.Union[dict, "moderngl.Program"]:
    return shaders[name]

def shader_write_to(uniform_name: str, value, *shader_names: str):
    if USE_ZEN:
        for pipeline, sn in zen_pipelines.items():
            if sn in shader_names:
                pipeline.uniforms[uniform_name][:] = zen_get_value(value)
        return
    for name in shader_names:
        shaders[name][uniform_name].write(value)
        
def shader_write(shader_name, uniform_name, value):
    if USE_ZEN:
        for pipeline, sn in zen_pipelines.items():
            if sn == shader_name:
                pipeline.uniforms[uniform_name][:] = zen_get_value(value)
        return
    shaders[shader_name][uniform_name].write(value)
        
def shader_writes(shader_name, *uniform_name_value):
    if USE_ZEN:
        for pipeline, sn in zen_pipelines.items():
            if sn == shader_name:
                for uname, uval in uniform_name_value:
                    pipeline.uniforms[uname][:] = zen_get_value(uval)
        return
    shader = shaders[shader_name]
    for uname, uvalue in uniform_name_value:
        shader[uname].write(uvalue)

#

def shader_set_to(uniform_name: str, value, *shader_names: str):
    if USE_ZEN:
        for pipeline, sn in zen_pipelines.items():
            if sn in shader_names:
                pipeline.uniforms[uniform_name][:] = zen_get_value(value)
        return
    for name in shader_names:
        shaders[name][uniform_name] = value 
        
def shader_set(shader_name, uniform_name, value):
    if USE_ZEN:
        for pipeline, sn in zen_pipelines.items():
            if sn == shader_name:
                pipeline.uniforms[uniform_name][:] = zen_get_value(value)
        return
    shaders[shader_name][uniform_name] = value
        
def shader_sets(shader_name, *uniform_name_value):
    if USE_ZEN:
        for pipeline, sn in zen_pipelines.items():
            if sn == shader_name:
                for uname, uval in uniform_name_value:
                    pipeline.uniforms[uname][:] = zen_get_value(uval)
        return
    shader = shaders[shader_name]
    for uname, uvalue in uniform_name_value:
        shader[uname] = uvalue
        
    