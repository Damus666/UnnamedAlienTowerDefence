#version 450 core

layout (location = 0) in vec2 vPos;
layout (location = 1) in vec4 vCol;
layout (location = 2) in vec2 vUV;
layout (location = 3) in float vTexID;

uniform mat4 projUI;

out vec4 fCol;
out vec2 fUV;
flat out float fTexID;

void main() {
    gl_Position = projUI * vec4(vPos, 0.0, 1.0);
    fCol = vCol;
    fUV = vUV;
    fTexID = vTexID;
}
/*#version 450 core

layout (location = 0) in vec2 vPos;
layout (location = 1) in vec4 vCol;
layout (location = 2) in vec2 vUV;
layout (location = 3) in float vTexID;

uniform mat4 projUI;

out vec4 fCol;
out vec2 fUV;
out float fTexID;

void main() {
    gl_Position = projUI*vec4(vec3(vPos, 0), 1.0);
    fCol = vCol;
    fUV = vUV;
    fTexID = vTexID;
}*/