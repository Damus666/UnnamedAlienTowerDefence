#version 300 es

in vec4 fCol;
in vec2 fUV;
in float fTexID;

layout (location = 0) out vec4 oCol;

uniform sampler2D textures[3];

void main() {
    oCol = texture(textures[int(fTexID)], fUV) * fCol ;
    if (oCol.a <= 0.0) {
        discard;
    }
}
