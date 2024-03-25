import moderngl

ctx: moderngl.Context = None
shaders: dict[str, moderngl.Program] = {}

def create_ctx():
    """Create the opengl context"""
    global ctx
    ctx = moderngl.create_context()
    ctx.enable(moderngl.BLEND)
    ctx.blend_func = ctx.SRC_ALPHA, ctx.ONE_MINUS_SRC_ALPHA

def clear(color: tuple[float, float, float, float]):
    """Clear the ctx"""
    ctx.clear(*color)

def load_shaders(folder: str, *names: str):
    """Load and compile shaders from disk"""
    if ctx is None:
        create_ctx()
    for name in names:
        with open(f"{folder}/{name}.vert", "r") as vert_file:
            with open(f"{folder}/{name}.frag", "r") as frag_file:
                shaders[name] = ctx.program(vertex_shader=vert_file.read(),
                                                fragment_shader=frag_file.read())
                
def get_shader(name: str) -> moderngl.Program:
    """Get an opengl program"""
    return shaders[name]

def shader_write_to(uniform_name: str, value, *shader_names: str):
    """Write the same uniform to multiple shaders"""
    for name in shader_names:
        shaders[name][uniform_name].write(value)
        
def shader_write(shader_name, uniform_name, value):
    """Write a shader uniform"""
    shaders[shader_name][uniform_name].write(value)
        
def shader_writes(shader_name, *uniform_name_value):
    """Write multiple uniforms to the same shader"""
    shader = shaders[shader_name]
    for uname, uvalue in uniform_name_value:
        shader[uname].write(uvalue)

#

def shader_set_to(uniform_name: str, value, *shader_names: str):
    """Set the same uniform to multiple shaders"""
    for name in shader_names:
        shaders[name][uniform_name] = value 
        
def shader_set(shader_name, uniform_name, value):
    """Set a shader uniform"""
    shaders[shader_name][uniform_name] = value
        
def shader_sets(shader_name, *uniform_name_value):
    """Set multiple uniforms to the same shader"""
    shader = shaders[shader_name]
    for uname, uvalue in uniform_name_value:
        shader[uname] = uvalue
        
    