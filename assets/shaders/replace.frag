#version 450 core

in vec4 fCol;
in vec2 fUV;
in float fTexID;
out vec4 oCol;

uniform sampler2D textures[3];

void main() {
    vec4 texCol = texture2D(textures[int(fTexID)], fUV);
    if (texCol.a <= 0) {
        discard;
    }
    oCol = vec4(fCol.xyz * ((texCol.r+texCol.g+texCol.b)/3.0), fCol.a*texCol.a);
}