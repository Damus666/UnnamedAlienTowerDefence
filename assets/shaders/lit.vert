#version 300 es

layout (location = 0) in vec2 vPos;
layout (location = 1) in vec4 vCol;
layout (location = 2) in vec2 vUV;
layout (location = 3) in float vTexID;

out vec2 fPos;
out vec4 fCol;
out vec2 fUV;
out float fTexID;

uniform mat4 proj;
uniform mat4 view;

void main() {
    gl_Position = proj * view * vec4(vPos, 0.0, 1.0);
    fPos = vPos;
    fCol = vCol;
    fUV = vUV;
    fTexID = vTexID;
}
