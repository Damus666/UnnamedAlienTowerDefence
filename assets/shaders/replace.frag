#version 300 es
precision highp float;

in vec4 fCol;
in vec2 fUV;
in float fTexID;
layout (location = 0) out vec4 oCol;

uniform sampler2D textures[3];

void main() {
    vec4 texCol = vec4(1.0, 1.0, 1.0, 1.0);
    switch (int(fTexID)) {
        case 0:
            texCol = texture(textures[0], fUV) *fCol;
            break;
        case 1:
            texCol = texture(textures[1], fUV) *fCol;
            break;
        case 2:
            texCol = texture(textures[2], fUV) *fCol;
            break;
    }
    // vec4 texCol = texture(textures[int(fTexID)], fUV);
    if (texCol.a <= 0.0) {
        discard;
    }
    oCol = vec4(fCol.xyz * ((texCol.r+texCol.g+texCol.b)/3.0), fCol.a*texCol.a);
}