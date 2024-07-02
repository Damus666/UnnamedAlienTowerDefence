#version 300 es
precision highp float;

in vec4 fCol;
in vec2 fUV;
in float fTexID;

layout (location = 0) out vec4 oCol;

uniform sampler2D textures[3];

void main() {
    switch (int(fTexID)) {
        case 0:
            oCol = texture(textures[0], fUV) *fCol;
            break;
        case 1:
            oCol = texture(textures[1], fUV) *fCol;
            break;
        case 2:
            oCol = texture(textures[2], fUV) *fCol;
            break;
    }
    // oCol = texture(textures[int(fTexID)], fUV) * fCol;
    if (oCol.a <= 0.0) {
        discard;
    }
}
