#version 300 es
precision highp float;

layout (location = 0) in vec2 vPos;
layout (location = 1) in vec4 vCol;
layout (location = 2) in vec2 vUV;
layout (location = 3) in float vTexID;

uniform mat4 proj;
uniform mat4 view;

out vec4 fCol;
out vec2 fUV;
out float fTexID;

void main() {
    gl_Position = proj*view*vec4(vec3(vPos, 0), 1.0);
    fCol = vCol;
    fUV = vUV;
    fTexID = vTexID;
}