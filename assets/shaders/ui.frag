#version 450 core

in vec4 fCol;
in vec2 fUV;
in float fTexID;
out vec4 oCol;

uniform sampler2D textures[20];

void main() {
    oCol = texture2D(textures[int(fTexID)], fUV) * fCol;
    if (oCol.a <= 0) {
        discard;
    }
}