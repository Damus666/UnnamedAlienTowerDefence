#version 450 core

in vec2 fPos;
in vec4 fCol;
in vec2 fUV;
in float fTexID;

out vec4 oCol;

uniform float numLights;
uniform sampler2D textures[2];
uniform float lightData[120*7];

const vec4 BASE_LIGHT = vec4(0.15, 0.15, 0.15, 1);

void main() {
    vec4 originalCol = texture2D(textures[int(fTexID)], fUV) * fCol;
    if (originalCol.a <= 0.01) {
        discard;
    }
    vec4 finalCol = originalCol * BASE_LIGHT;
    for (int i = 0; i < numLights*7; i+=7) {
        vec2 direction = fPos-vec2(lightData[i], lightData[i+1]);
        finalCol += vec4(lightData[i+2], lightData[i+3], lightData[i+4], 1) *
            originalCol *
            // intensity
            max((lightData[i+5]- // range
                sqrt(direction.x*direction.x + direction.y*direction.y)) // distance
            /lightData[i+5], 0) *
            //
            lightData[i+6]; // light intensity
    }
    oCol = finalCol;
}