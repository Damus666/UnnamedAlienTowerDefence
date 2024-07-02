#version 300 es
precision highp float;

in vec2 fPos;
in vec4 fCol;
in vec2 fUV;
in float fTexID;

layout (location = 0) out vec4 oCol;

uniform float numLights;
uniform sampler2D textures[3];
uniform float lightData[100*7];

const vec4 BASE_LIGHT = vec4(0.15, 0.15, 0.15, 1);

void main() {
    vec4 originalCol = vec4(1.0, 1.0, 1.0, 1.0);
    switch (int(fTexID)) {
        case 0:
            originalCol = texture(textures[0], fUV) *fCol;
            break;
        case 1:
            originalCol = texture(textures[1], fUV) *fCol;
            break;
        case 2:
            originalCol = texture(textures[2], fUV) *fCol;
            break;
    }
    // vec4 originalCol = texture(textures[int(fTexID)], fUV) * fCol;
    if (originalCol.a <= 0.01) {
        discard;
    }
    vec4 finalCol = originalCol * BASE_LIGHT;
    
    for (int i = 0; i < int(numLights)*7; i+=7) {
        vec2 direction = fPos - vec2(lightData[i], lightData[i+1]);
        float distanceSq = dot(direction, direction);
        float rangeSq = lightData[i+5] * lightData[i+5];
        float attenuation = max(1.0 - distanceSq / rangeSq, 0.0);
        finalCol += vec4(lightData[i+2], lightData[i+3], lightData[i+4], 1.0) *
                    originalCol *
                    attenuation *
                    lightData[i+6];
    }
    oCol = finalCol;
}