<template>
  <canvas ref="canvasRef" class="fluid-canvas" />
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from "vue"

const props = defineProps({
  simResolution: { type: Number, default: 128 },
  dyeResolution: { type: Number, default: 1440 },
  captureResolution: { type: Number, default: 512 },
  densityDissipation: { type: Number, default: 3.5 },
  velocityDissipation: { type: Number, default: 2 },
  pressure: { type: Number, default: 0.1 },
  pressureIterations: { type: Number, default: 20 },
  curl: { type: Number, default: 3 },
  splatRadius: { type: Number, default: 0.2 },
  splatForce: { type: Number, default: 6000 },
  shading: { type: Boolean, default: true },
  colorUpdateSpeed: { type: Number, default: 10 },
  backColor: { type: Object, default: () => ({ r: 0.06, g: 0.06, b: 0.1 }) },
  transparent: { type: Boolean, default: true },
  class: { type: String, default: "" },
})

// ---- P6-A 性能保护：自动降级档位（防无 GPU 加速/低配机 CPU 拉满卡死）----
// 档位 0 = 正常全配；档位越高渲染越省。软渲染（SwiftShader/llvmpipe）直接落最低档。
// 若最低档仍撑不住（软件渲染流体 10+ 次全屏运算，CPU 扛不动）→ 停帧保静态，CPU 归零。
const DEGRADES = [
  { dye: 1440, sim: 128, pressureIterations: 20, shading: true,  splatForce: 6000, label: 'full'   },
  { dye: 720,  sim: 96,  pressureIterations: 12, shading: false, splatForce: 4500, label: 'mid'    },
  { dye: 360,  sim: 64,  pressureIterations: 8,  shading: false, splatForce: 3000, label: 'safety' },
  { dye: 240,  sim: 48,  pressureIterations: 4,  shading: false, splatForce: 2200, label: 'ultra'  },
]

function pointerPrototype() {
  return {
    id: -1, texcoordX: 0, texcoordY: 0,
    prevTexcoordX: 0, prevTexcoordY: 0,
    deltaX: 0, deltaY: 0,
    down: false, moved: false,
    color: { r: 0, g: 0, b: 0 },
  }
}

const canvasRef = ref(null)

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  let rafId = null
  let disposed = false

  const pointers = [pointerPrototype()]

  const config = {
    SIM_RESOLUTION: props.simResolution,
    DYE_RESOLUTION: props.dyeResolution,
    CAPTURE_RESOLUTION: props.captureResolution,
    DENSITY_DISSIPATION: props.densityDissipation,
    VELOCITY_DISSIPATION: props.velocityDissipation,
    PRESSURE: props.pressure,
    PRESSURE_ITERATIONS: props.pressureIterations,
    CURL: props.curl,
    SPLAT_RADIUS: props.splatRadius,
    SPLAT_FORCE: props.splatForce,
    SHADING: props.shading,
    COLOR_UPDATE_SPEED: props.colorUpdateSpeed,
    PAUSED: false,
    BACK_COLOR: props.backColor,
    TRANSPARENT: props.transparent,
  }

  const { gl, ext } = getWebGLContext(canvas)
  if (!gl || !ext) return

  if (!ext.supportLinearFiltering) {
    config.DYE_RESOLUTION = 256
    config.SHADING = false
  }

  function getWebGLContext(canvas) {
    const params = { alpha: true, depth: false, stencil: false, antialias: false, preserveDrawingBuffer: false }

    let gl = canvas.getContext("webgl2", params)
    if (!gl) {
      gl = canvas.getContext("webgl", params) || canvas.getContext("experimental-webgl", params)
    }
    if (!gl) return { gl: null, ext: null }

    const isWebGL2 = "drawBuffers" in gl
    let supportLinearFiltering = false
    let halfFloat = null

    if (isWebGL2) {
      gl.getExtension("EXT_color_buffer_float")
      supportLinearFiltering = !!gl.getExtension("OES_texture_float_linear")
    } else {
      halfFloat = gl.getExtension("OES_texture_half_float")
      supportLinearFiltering = !!gl.getExtension("OES_texture_half_float_linear")
    }

    gl.clearColor(0, 0, 0, 1)

    const halfFloatTexType = isWebGL2 ? gl.HALF_FLOAT : (halfFloat && halfFloat.HALF_FLOAT_OES) || 0

    let formatRGBA, formatRG, formatR

    if (isWebGL2) {
      formatRGBA = getSupportedFormat(gl, gl.RGBA16F, gl.RGBA, halfFloatTexType)
      formatRG = getSupportedFormat(gl, gl.RG16F, gl.RG, halfFloatTexType)
      formatR = getSupportedFormat(gl, gl.R16F, gl.RED, halfFloatTexType)
    } else {
      formatRGBA = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType)
      formatRG = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType)
      formatR = getSupportedFormat(gl, gl.RGBA, gl.RGBA, halfFloatTexType)
    }

    return { gl, ext: { formatRGBA, formatRG, formatR, halfFloatTexType, supportLinearFiltering } }
  }

  function getSupportedFormat(gl, internalFormat, format, type) {
    if (!supportRenderTextureFormat(gl, internalFormat, format, type)) {
      if ("drawBuffers" in gl) {
        switch (internalFormat) {
          case gl.R16F: return getSupportedFormat(gl, gl.RG16F, gl.RG, type)
          case gl.RG16F: return getSupportedFormat(gl, gl.RGBA16F, gl.RGBA, type)
          default: return null
        }
      }
      return null
    }
    return { internalFormat, format }
  }

  function supportRenderTextureFormat(gl, internalFormat, format, type) {
    const texture = gl.createTexture()
    if (!texture) return false
    gl.bindTexture(gl.TEXTURE_2D, texture)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
    gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, 4, 4, 0, format, type, null)
    const fbo = gl.createFramebuffer()
    if (!fbo) return false
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo)
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0)
    return gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE
  }

  function hashCode(s) {
    if (!s.length) return 0
    let hash = 0
    for (let i = 0; i < s.length; i++) { hash = (hash << 5) - hash + s.charCodeAt(i); hash |= 0 }
    return hash
  }

  function addKeywords(source, keywords) {
    if (!keywords) return source
    let keywordsString = ""
    for (const keyword of keywords) keywordsString += "#define " + keyword + "\n"
    return keywordsString + source
  }

  function compileShader(type, source, keywords = null) {
    const shaderSource = addKeywords(source, keywords)
    const shader = gl.createShader(type)
    if (!shader) return null
    gl.shaderSource(shader, shaderSource)
    gl.compileShader(shader)
    return shader
  }

  function createProgram(vertexShader, fragmentShader) {
    if (!vertexShader || !fragmentShader) return null
    const program = gl.createProgram()
    if (!program) return null
    gl.attachShader(program, vertexShader)
    gl.attachShader(program, fragmentShader)
    gl.linkProgram(program)
    return program
  }

  function getUniforms(program) {
    const uniforms = {}
    const uniformCount = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS)
    for (let i = 0; i < uniformCount; i++) {
      const uniformInfo = gl.getActiveUniform(program, i)
      if (uniformInfo) uniforms[uniformInfo.name] = gl.getUniformLocation(program, uniformInfo.name)
    }
    return uniforms
  }

  class Program {
    constructor(vertexShader, fragmentShader) {
      this.program = createProgram(vertexShader, fragmentShader)
      this.uniforms = this.program ? getUniforms(this.program) : {}
    }
    bind() { if (this.program) gl.useProgram(this.program) }
  }

  class Material {
    constructor(vertexShader, fragmentShaderSource) {
      this.vertexShader = vertexShader
      this.fragmentShaderSource = fragmentShaderSource
      this.programs = {}
      this.activeProgram = null
      this.uniforms = {}
    }
    setKeywords(keywords) {
      let hash = 0
      for (const kw of keywords) hash += hashCode(kw)
      let program = this.programs[hash]
      if (program == null) {
        const fragmentShader = compileShader(gl.FRAGMENT_SHADER, this.fragmentShaderSource, keywords)
        program = createProgram(this.vertexShader, fragmentShader)
        this.programs[hash] = program
      }
      if (program === this.activeProgram) return
      if (program) this.uniforms = getUniforms(program)
      this.activeProgram = program
    }
    bind() { if (this.activeProgram) gl.useProgram(this.activeProgram) }
  }

  // Shaders
  const baseVertexShader = compileShader(gl.VERTEX_SHADER, `
    precision highp float;
    attribute vec2 aPosition;
    varying vec2 vUv;
    varying vec2 vL;
    varying vec2 vR;
    varying vec2 vT;
    varying vec2 vB;
    uniform vec2 texelSize;
    void main () {
      vUv = aPosition * 0.5 + 0.5;
      vL = vUv - vec2(texelSize.x, 0.0);
      vR = vUv + vec2(texelSize.x, 0.0);
      vT = vUv + vec2(0.0, texelSize.y);
      vB = vUv - vec2(0.0, texelSize.y);
      gl_Position = vec4(aPosition, 0.0, 1.0);
    }
  `)

  const copyShader = compileShader(gl.FRAGMENT_SHADER, `
    precision mediump float;
    precision mediump sampler2D;
    varying highp vec2 vUv;
    uniform sampler2D uTexture;
    void main () { gl_FragColor = texture2D(uTexture, vUv); }
  `)

  const clearShader = compileShader(gl.FRAGMENT_SHADER, `
    precision mediump float;
    precision mediump sampler2D;
    varying highp vec2 vUv;
    uniform sampler2D uTexture;
    uniform float value;
    void main () { gl_FragColor = value * texture2D(uTexture, vUv); }
  `)

  const displayShaderSource = `
    precision highp float;
    precision highp sampler2D;
    varying vec2 vUv;
    varying vec2 vL;
    varying vec2 vR;
    varying vec2 vT;
    varying vec2 vB;
    uniform sampler2D uTexture;
    uniform sampler2D uDithering;
    uniform vec2 ditherScale;
    uniform vec2 texelSize;
    vec3 linearToGamma (vec3 color) {
      color = max(color, vec3(0));
      return max(1.055 * pow(color, vec3(0.416666667)) - 0.055, vec3(0));
    }
    void main () {
      vec3 c = texture2D(uTexture, vUv).rgb;
      #ifdef SHADING
        vec3 lc = texture2D(uTexture, vL).rgb;
        vec3 rc = texture2D(uTexture, vR).rgb;
        vec3 tc = texture2D(uTexture, vT).rgb;
        vec3 bc = texture2D(uTexture, vB).rgb;
        float dx = length(rc) - length(lc);
        float dy = length(tc) - length(bc);
        vec3 n = normalize(vec3(dx, dy, length(texelSize)));
        vec3 l = vec3(0.0, 0.0, 1.0);
        float diffuse = clamp(dot(n, l) + 0.7, 0.7, 1.0);
        c *= diffuse;
      #endif
      float a = max(c.r, max(c.g, c.b));
      gl_FragColor = vec4(c, a);
    }
  `

  const splatShader = compileShader(gl.FRAGMENT_SHADER, `
    precision highp float;
    precision highp sampler2D;
    varying vec2 vUv;
    uniform sampler2D uTarget;
    uniform float aspectRatio;
    uniform vec3 color;
    uniform vec2 point;
    uniform float radius;
    void main () {
      vec2 p = vUv - point.xy;
      p.x *= aspectRatio;
      vec3 splat = exp(-dot(p, p) / radius) * color;
      vec3 base = texture2D(uTarget, vUv).xyz;
      gl_FragColor = vec4(base + splat, 1.0);
    }
  `)

  const advectionShader = compileShader(gl.FRAGMENT_SHADER, `
    precision highp float;
    precision highp sampler2D;
    varying vec2 vUv;
    uniform sampler2D uVelocity;
    uniform sampler2D uSource;
    uniform vec2 texelSize;
    uniform vec2 dyeTexelSize;
    uniform float dt;
    uniform float dissipation;
    vec4 bilerp (sampler2D sam, vec2 uv, vec2 tsize) {
      vec2 st = uv / tsize - 0.5;
      vec2 iuv = floor(st);
      vec2 fuv = fract(st);
      vec4 a = texture2D(sam, (iuv + vec2(0.5, 0.5)) * tsize);
      vec4 b = texture2D(sam, (iuv + vec2(1.5, 0.5)) * tsize);
      vec4 c = texture2D(sam, (iuv + vec2(0.5, 1.5)) * tsize);
      vec4 d = texture2D(sam, (iuv + vec2(1.5, 1.5)) * tsize);
      return mix(mix(a, b, fuv.x), mix(c, d, fuv.x), fuv.y);
    }
    void main () {
      #ifdef MANUAL_FILTERING
        vec2 coord = vUv - dt * bilerp(uVelocity, vUv, texelSize).xy * texelSize;
        vec4 result = bilerp(uSource, coord, dyeTexelSize);
      #else
        vec2 coord = vUv - dt * texture2D(uVelocity, vUv).xy * texelSize;
        vec4 result = texture2D(uSource, coord);
      #endif
      float decay = 1.0 + dissipation * dt;
      gl_FragColor = result / decay;
    }
  `, ext.supportLinearFiltering ? null : ["MANUAL_FILTERING"])

  const divergenceShader = compileShader(gl.FRAGMENT_SHADER, `
    precision mediump float;
    precision mediump sampler2D;
    varying highp vec2 vUv; varying highp vec2 vL; varying highp vec2 vR; varying highp vec2 vT; varying highp vec2 vB;
    uniform sampler2D uVelocity;
    void main () {
      float L = texture2D(uVelocity, vL).x;
      float R = texture2D(uVelocity, vR).x;
      float T = texture2D(uVelocity, vT).y;
      float B = texture2D(uVelocity, vB).y;
      vec2 C = texture2D(uVelocity, vUv).xy;
      if (vL.x < 0.0) { L = -C.x; }
      if (vR.x > 1.0) { R = -C.x; }
      if (vT.y > 1.0) { T = -C.y; }
      if (vB.y < 0.0) { B = -C.y; }
      float div = 0.5 * (R - L + T - B);
      gl_FragColor = vec4(div, 0.0, 0.0, 1.0);
    }
  `)

  const curlShader = compileShader(gl.FRAGMENT_SHADER, `
    precision mediump float;
    precision mediump sampler2D;
    varying highp vec2 vUv; varying highp vec2 vL; varying highp vec2 vR; varying highp vec2 vT; varying highp vec2 vB;
    uniform sampler2D uVelocity;
    void main () {
      float L = texture2D(uVelocity, vL).y;
      float R = texture2D(uVelocity, vR).y;
      float T = texture2D(uVelocity, vT).x;
      float B = texture2D(uVelocity, vB).x;
      float vorticity = R - L - T + B;
      gl_FragColor = vec4(0.5 * vorticity, 0.0, 0.0, 1.0);
    }
  `)

  const vorticityShader = compileShader(gl.FRAGMENT_SHADER, `
    precision highp float;
    precision highp sampler2D;
    varying vec2 vUv; varying vec2 vL; varying vec2 vR; varying vec2 vT; varying vec2 vB;
    uniform sampler2D uVelocity;
    uniform sampler2D uCurl;
    uniform float curl;
    uniform float dt;
    void main () {
      float L = texture2D(uCurl, vL).x;
      float R = texture2D(uCurl, vR).x;
      float T = texture2D(uCurl, vT).x;
      float B = texture2D(uCurl, vB).x;
      float C = texture2D(uCurl, vUv).x;
      vec2 force = 0.5 * vec2(abs(T) - abs(B), abs(R) - abs(L));
      force /= length(force) + 0.0001;
      force *= curl * C;
      force.y *= -1.0;
      vec2 velocity = texture2D(uVelocity, vUv).xy;
      velocity += force * dt;
      velocity = min(max(velocity, -1000.0), 1000.0);
      gl_FragColor = vec4(velocity, 0.0, 1.0);
    }
  `)

  const pressureShader = compileShader(gl.FRAGMENT_SHADER, `
    precision mediump float;
    precision mediump sampler2D;
    varying highp vec2 vUv; varying highp vec2 vL; varying highp vec2 vR; varying highp vec2 vT; varying highp vec2 vB;
    uniform sampler2D uPressure;
    uniform sampler2D uDivergence;
    void main () {
      float L = texture2D(uPressure, vL).x;
      float R = texture2D(uPressure, vR).x;
      float T = texture2D(uPressure, vT).x;
      float B = texture2D(uPressure, vB).x;
      float C = texture2D(uPressure, vUv).x;
      float divergence = texture2D(uDivergence, vUv).x;
      float pressure = (L + R + B + T - divergence) * 0.25;
      gl_FragColor = vec4(pressure, 0.0, 0.0, 1.0);
    }
  `)

  const gradientSubtractShader = compileShader(gl.FRAGMENT_SHADER, `
    precision mediump float;
    precision mediump sampler2D;
    varying highp vec2 vUv; varying highp vec2 vL; varying highp vec2 vR; varying highp vec2 vT; varying highp vec2 vB;
    uniform sampler2D uPressure;
    uniform sampler2D uVelocity;
    void main () {
      float L = texture2D(uPressure, vL).x;
      float R = texture2D(uPressure, vR).x;
      float T = texture2D(uPressure, vT).x;
      float B = texture2D(uPressure, vB).x;
      vec2 velocity = texture2D(uVelocity, vUv).xy;
      velocity.xy -= vec2(R - L, T - B);
      gl_FragColor = vec4(velocity, 0.0, 1.0);
    }
  `)

  // Fullscreen blit
  const blit = (() => {
    const buffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, -1, 1, 1, 1, 1, -1]), gl.STATIC_DRAW)
    const elemBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, elemBuffer)
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array([0, 1, 2, 0, 2, 3]), gl.STATIC_DRAW)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)
    gl.enableVertexAttribArray(0)

    return (target, doClear = false) => {
      if (!gl) return
      if (!target) {
        gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight)
        gl.bindFramebuffer(gl.FRAMEBUFFER, null)
      } else {
        gl.viewport(0, 0, target.width, target.height)
        gl.bindFramebuffer(gl.FRAMEBUFFER, target.fbo)
      }
      if (doClear) { gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT) }
      gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0)
    }
  })()

  // FBO management
  function createFBO(w, h, internalFormat, format, type, param) {
    gl.activeTexture(gl.TEXTURE0)
    const texture = gl.createTexture()
    gl.bindTexture(gl.TEXTURE_2D, texture)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, param)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, param)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
    gl.texImage2D(gl.TEXTURE_2D, 0, internalFormat, w, h, 0, format, type, null)
    const fbo = gl.createFramebuffer()
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo)
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0)
    gl.viewport(0, 0, w, h)
    gl.clear(gl.COLOR_BUFFER_BIT)
    return {
      texture, fbo, width: w, height: h,
      texelSizeX: 1 / w, texelSizeY: 1 / h,
      attach(id) { gl.activeTexture(gl.TEXTURE0 + id); gl.bindTexture(gl.TEXTURE_2D, texture); return id }
    }
  }

  function createDoubleFBO(w, h, internalFormat, format, type, param) {
    const fbo1 = createFBO(w, h, internalFormat, format, type, param)
    const fbo2 = createFBO(w, h, internalFormat, format, type, param)
    return {
      width: w, height: h, texelSizeX: fbo1.texelSizeX, texelSizeY: fbo1.texelSizeY,
      read: fbo1, write: fbo2,
      swap() { const tmp = this.read; this.read = this.write; this.write = tmp }
    }
  }

  function resizeFBO(target, w, h, internalFormat, format, type, param) {
    const newFBO = createFBO(w, h, internalFormat, format, type, param)
    copyProgram.bind()
    if (copyProgram.uniforms.uTexture) gl.uniform1i(copyProgram.uniforms.uTexture, target.attach(0))
    blit(newFBO, false)
    return newFBO
  }

  function resizeDoubleFBO(target, w, h, internalFormat, format, type, param) {
    if (target.width === w && target.height === h) return target
    target.read = resizeFBO(target.read, w, h, internalFormat, format, type, param)
    target.write = createFBO(w, h, internalFormat, format, type, param)
    target.width = w; target.height = h
    target.texelSizeX = 1 / w; target.texelSizeY = 1 / h
    return target
  }

  function getResolution(resolution) {
    const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight
    const aspectRatio = w / h
    const aspect = aspectRatio < 1 ? 1 / aspectRatio : aspectRatio
    const min = Math.round(resolution), max = Math.round(resolution * aspect)
    return w > h ? { width: max, height: min } : { width: min, height: max }
  }

  function scaleByPixelRatio(input) {
    return Math.floor(input * (window.devicePixelRatio || 1))
  }

  // FBOs
  let dye, velocity, divergence, curl, pressure
  const copyProgram = new Program(baseVertexShader, copyShader)
  const clearProgram = new Program(baseVertexShader, clearShader)
  const splatProgram = new Program(baseVertexShader, splatShader)
  const advectionProgram = new Program(baseVertexShader, advectionShader)
  const divergenceProgram = new Program(baseVertexShader, divergenceShader)
  const curlProgram = new Program(baseVertexShader, curlShader)
  const vorticityProgram = new Program(baseVertexShader, vorticityShader)
  const pressureProgram = new Program(baseVertexShader, pressureShader)
  const gradienSubtractProgram = new Program(baseVertexShader, gradientSubtractShader)
  const displayMaterial = new Material(baseVertexShader, displayShaderSource)

  function initFramebuffers() {
    const simRes = getResolution(config.SIM_RESOLUTION)
    const dyeRes = getResolution(config.DYE_RESOLUTION)
    const texType = ext.halfFloatTexType
    const rgba = ext.formatRGBA; const rg = ext.formatRG; const r = ext.formatR
    const filtering = ext.supportLinearFiltering ? gl.LINEAR : gl.NEAREST
    gl.disable(gl.BLEND)

    if (!dye) dye = createDoubleFBO(dyeRes.width, dyeRes.height, rgba.internalFormat, rgba.format, texType, filtering)
    else dye = resizeDoubleFBO(dye, dyeRes.width, dyeRes.height, rgba.internalFormat, rgba.format, texType, filtering)

    if (!velocity) velocity = createDoubleFBO(simRes.width, simRes.height, rg.internalFormat, rg.format, texType, filtering)
    else velocity = resizeDoubleFBO(velocity, simRes.width, simRes.height, rg.internalFormat, rg.format, texType, filtering)

    divergence = createFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST)
    curl = createFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST)
    pressure = createDoubleFBO(simRes.width, simRes.height, r.internalFormat, r.format, texType, gl.NEAREST)
  }

  function updateKeywords() {
    const displayKeywords = []
    if (config.SHADING) displayKeywords.push("SHADING")
    displayMaterial.setKeywords(displayKeywords)
  }

  updateKeywords()
  initFramebuffers()

  // ---- P6-A 性能保护：降级引擎 ----
  // config 默认取全配（档位 0），软渲染直降最低档；运行中帧率跌破阈值逐档降。
  let degradeLevel = 0
  const maxDegrade = DEGRADES.length - 1
  // 帧率监测窗口（在 applyDegrade 前声明，避免 TDZ）
  let _fpsFrames = 0
  let _fpsWindowStart = performance.now()
  const FPS_WINDOW_MS = 3000
  const FPS_THRESHOLD = 32
  // 终极兜底：最低档仍低于此帧率 → 停帧保静态（CPU 归零）。软渲染下流体多 pass 运算上限很低，
  // 20fps 以下对交互而言已明显迟钝，静态光晕对低配机是更安全的体验。
  const STOP_FPS = 20
  let _stopped = false

  function detectSoftwareRenderer() {
    try {
      const dbg = gl.getExtension('WEBGL_debug_renderer_info')
      if (!dbg) return false
      const r = String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) || '').toLowerCase()
      // 仅命中软渲染标识（SwiftShader/llvmpipe/软件驱动/基本显示适配器），
      // 并确保没有真实硬件厂商名（防止 ANGLE (NVIDIA/AMD/Intel... 被误判）
      const isSoft = /swiftshader|llvmpipe|softwar|basic render driver|microsoft basic/i.test(r)
      const isRealGPU = /nvidia|amd|ati|radeon|geforce|rtx|gtx|intel|iris|uhd|apple|qualcomm|mali|adreno/i.test(r)
      return isSoft && !isRealGPU
    } catch { return false }
  }

  function applyDegrade(nextLevel) {
    degradeLevel = Math.max(degradeLevel, nextLevel)
    const d = DEGRADES[degradeLevel]
    config.DYE_RESOLUTION = d.dye
    config.SIM_RESOLUTION = d.sim
    config.PRESSURE_ITERATIONS = d.pressureIterations
    config.SHADING = d.shading
    config.SPLAT_FORCE = d.splatForce
    if (degradeLevel > 0) console.info(`[FluidCursor] 性能降级 → ${d.label}（${d.dye} 分辨率）`)
    initFramebuffers()
    updateKeywords()
    // 帧率监测窗口重置
    _fpsFrames = 0
    _fpsWindowStart = performance.now()
  }

  if (detectSoftwareRenderer()) {
    // 无 GPU 加速直接最低档，避免 CPU 软渲染拉满（用户 Edge/教学机场景）
    applyDegrade(maxDegrade)
  }

  function checkFpsHealth() {
    const now = performance.now()
    const elapsed = now - _fpsWindowStart
    if (elapsed < FPS_WINDOW_MS) return
    const avgFps = (_fpsFrames * 1000) / elapsed
    _fpsFrames = 0
    _fpsWindowStart = now
    if (avgFps < FPS_THRESHOLD && degradeLevel < maxDegrade) {
      applyDegrade(degradeLevel + 1)
    }
    // 终极兜底：已到最低档仍撑不住 → 停帧，保留静态画面（CPU 归零，绝不卡死电脑）
    if (avgFps < STOP_FPS && degradeLevel >= maxDegrade && !_stopped) {
      _stopped = true
      console.info('[FluidCursor] 极端低配 → 停帧保静态')
      if (rafId) cancelAnimationFrame(rafId)
      rafId = null
    }
  }

  let lastUpdateTime = Date.now()
  let colorUpdateTimer = 0.0

  function updateFrame() {
    if (disposed || _stopped) return
    const dt = calcDeltaTime()
    if (resizeCanvas()) initFramebuffers()
    updateColors(dt)
    applyInputs()
    step(dt)
    render(null)
    _fpsFrames++
    checkFpsHealth()
    if (!_stopped) rafId = requestAnimationFrame(updateFrame)
  }

  function calcDeltaTime() {
    const now = Date.now()
    let dt = (now - lastUpdateTime) / 1000
    dt = Math.min(dt, 0.016666)
    lastUpdateTime = now
    return dt
  }

  function resizeCanvas() {
    const width = scaleByPixelRatio(canvas.clientWidth)
    const height = scaleByPixelRatio(canvas.clientHeight)
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width; canvas.height = height
      return true
    }
    return false
  }

  function updateColors(dt) {
    colorUpdateTimer += dt * config.COLOR_UPDATE_SPEED
    if (colorUpdateTimer >= 1) {
      colorUpdateTimer = wrap(colorUpdateTimer, 0, 1)
      pointers.forEach((p) => { p.color = generateColor() })
    }
  }

  function applyInputs() {
    for (const p of pointers) { if (p.moved) { p.moved = false; splatPointer(p) } }
  }

  function step(dt) {
    gl.disable(gl.BLEND)
    curlProgram.bind()
    if (curlProgram.uniforms.texelSize) gl.uniform2f(curlProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY)
    if (curlProgram.uniforms.uVelocity) gl.uniform1i(curlProgram.uniforms.uVelocity, velocity.read.attach(0))
    blit(curl)

    vorticityProgram.bind()
    if (vorticityProgram.uniforms.texelSize) gl.uniform2f(vorticityProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY)
    if (vorticityProgram.uniforms.uVelocity) gl.uniform1i(vorticityProgram.uniforms.uVelocity, velocity.read.attach(0))
    if (vorticityProgram.uniforms.uCurl) gl.uniform1i(vorticityProgram.uniforms.uCurl, curl.attach(1))
    if (vorticityProgram.uniforms.curl) gl.uniform1f(vorticityProgram.uniforms.curl, config.CURL)
    if (vorticityProgram.uniforms.dt) gl.uniform1f(vorticityProgram.uniforms.dt, dt)
    blit(velocity.write); velocity.swap()

    divergenceProgram.bind()
    if (divergenceProgram.uniforms.texelSize) gl.uniform2f(divergenceProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY)
    if (divergenceProgram.uniforms.uVelocity) gl.uniform1i(divergenceProgram.uniforms.uVelocity, velocity.read.attach(0))
    blit(divergence)

    clearProgram.bind()
    if (clearProgram.uniforms.uTexture) gl.uniform1i(clearProgram.uniforms.uTexture, pressure.read.attach(0))
    if (clearProgram.uniforms.value) gl.uniform1f(clearProgram.uniforms.value, config.PRESSURE)
    blit(pressure.write); pressure.swap()

    pressureProgram.bind()
    if (pressureProgram.uniforms.texelSize) gl.uniform2f(pressureProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY)
    if (pressureProgram.uniforms.uDivergence) gl.uniform1i(pressureProgram.uniforms.uDivergence, divergence.attach(0))
    for (let i = 0; i < config.PRESSURE_ITERATIONS; i++) {
      if (pressureProgram.uniforms.uPressure) gl.uniform1i(pressureProgram.uniforms.uPressure, pressure.read.attach(1))
      blit(pressure.write); pressure.swap()
    }

    gradienSubtractProgram.bind()
    if (gradienSubtractProgram.uniforms.texelSize) gl.uniform2f(gradienSubtractProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY)
    if (gradienSubtractProgram.uniforms.uPressure) gl.uniform1i(gradienSubtractProgram.uniforms.uPressure, pressure.read.attach(0))
    if (gradienSubtractProgram.uniforms.uVelocity) gl.uniform1i(gradienSubtractProgram.uniforms.uVelocity, velocity.read.attach(1))
    blit(velocity.write); velocity.swap()

    advectionProgram.bind()
    if (advectionProgram.uniforms.texelSize) gl.uniform2f(advectionProgram.uniforms.texelSize, velocity.texelSizeX, velocity.texelSizeY)
    if (!ext.supportLinearFiltering && advectionProgram.uniforms.dyeTexelSize) gl.uniform2f(advectionProgram.uniforms.dyeTexelSize, velocity.texelSizeX, velocity.texelSizeY)
    const velocityId = velocity.read.attach(0)
    if (advectionProgram.uniforms.uVelocity) gl.uniform1i(advectionProgram.uniforms.uVelocity, velocityId)
    if (advectionProgram.uniforms.uSource) gl.uniform1i(advectionProgram.uniforms.uSource, velocityId)
    if (advectionProgram.uniforms.dt) gl.uniform1f(advectionProgram.uniforms.dt, dt)
    if (advectionProgram.uniforms.dissipation) gl.uniform1f(advectionProgram.uniforms.dissipation, config.VELOCITY_DISSIPATION)
    blit(velocity.write); velocity.swap()

    if (!ext.supportLinearFiltering && advectionProgram.uniforms.dyeTexelSize) gl.uniform2f(advectionProgram.uniforms.dyeTexelSize, dye.texelSizeX, dye.texelSizeY)
    if (advectionProgram.uniforms.uVelocity) gl.uniform1i(advectionProgram.uniforms.uVelocity, velocity.read.attach(0))
    if (advectionProgram.uniforms.uSource) gl.uniform1i(advectionProgram.uniforms.uSource, dye.read.attach(1))
    if (advectionProgram.uniforms.dissipation) gl.uniform1f(advectionProgram.uniforms.dissipation, config.DENSITY_DISSIPATION)
    blit(dye.write); dye.swap()
  }

  function render(target) {
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)
    gl.enable(gl.BLEND)
    drawDisplay(target)
  }

  function drawDisplay(target) {
    const width = target ? target.width : gl.drawingBufferWidth
    const height = target ? target.height : gl.drawingBufferHeight
    displayMaterial.bind()
    if (config.SHADING && displayMaterial.uniforms.texelSize) gl.uniform2f(displayMaterial.uniforms.texelSize, 1 / width, 1 / height)
    if (displayMaterial.uniforms.uTexture) gl.uniform1i(displayMaterial.uniforms.uTexture, dye.read.attach(0))
    blit(target, false)
  }

  function splatPointer(pointer) {
    const dx = pointer.deltaX * config.SPLAT_FORCE
    const dy = pointer.deltaY * config.SPLAT_FORCE
    splat(pointer.texcoordX, pointer.texcoordY, dx, dy, pointer.color)
  }

  function clickSplat(pointer) {
    const color = generateColor()
    color.r *= 4; color.g *= 4; color.b *= 4
    const dx = 8 * (Math.random() - 0.5), dy = 20 * (Math.random() - 0.5)
    splat(pointer.texcoordX, pointer.texcoordY, dx, dy, color)
  }

  function splat(x, y, dx, dy, color) {
    splatProgram.bind()
    if (splatProgram.uniforms.uTarget) gl.uniform1i(splatProgram.uniforms.uTarget, velocity.read.attach(0))
    if (splatProgram.uniforms.aspectRatio) gl.uniform1f(splatProgram.uniforms.aspectRatio, canvas.width / canvas.height)
    if (splatProgram.uniforms.point) gl.uniform2f(splatProgram.uniforms.point, x, y)
    if (splatProgram.uniforms.color) gl.uniform3f(splatProgram.uniforms.color, dx, dy, 0)
    if (splatProgram.uniforms.radius) gl.uniform1f(splatProgram.uniforms.radius, correctRadius(config.SPLAT_RADIUS / 100))
    blit(velocity.write); velocity.swap()

    if (splatProgram.uniforms.uTarget) gl.uniform1i(splatProgram.uniforms.uTarget, dye.read.attach(0))
    if (splatProgram.uniforms.color) gl.uniform3f(splatProgram.uniforms.color, color.r, color.g, color.b)
    blit(dye.write); dye.swap()
  }

  function correctRadius(radius) {
    const aspectRatio = canvas.width / canvas.height
    if (aspectRatio > 1) radius *= aspectRatio
    return radius
  }

  function updatePointerDownData(pointer, id, posX, posY) {
    pointer.id = id; pointer.down = true; pointer.moved = false
    pointer.texcoordX = posX / canvas.width; pointer.texcoordY = 1 - posY / canvas.height
    pointer.prevTexcoordX = pointer.texcoordX; pointer.prevTexcoordY = pointer.texcoordY
    pointer.deltaX = 0; pointer.deltaY = 0
    pointer.color = generateColor()
  }

  function updatePointerMoveData(pointer, posX, posY, color) {
    pointer.prevTexcoordX = pointer.texcoordX; pointer.prevTexcoordY = pointer.texcoordY
    pointer.texcoordX = posX / canvas.width; pointer.texcoordY = 1 - posY / canvas.height
    pointer.deltaX = correctDeltaX(pointer.texcoordX - pointer.prevTexcoordX)
    pointer.deltaY = correctDeltaY(pointer.texcoordY - pointer.prevTexcoordY)
    pointer.moved = Math.abs(pointer.deltaX) > 0 || Math.abs(pointer.deltaY) > 0
    pointer.color = color
  }

  function updatePointerUpData(pointer) { pointer.down = false }

  function correctDeltaX(delta) {
    const aspectRatio = canvas.width / canvas.height
    if (aspectRatio < 1) delta *= aspectRatio
    return delta
  }

  function correctDeltaY(delta) {
    const aspectRatio = canvas.width / canvas.height
    if (aspectRatio > 1) delta /= aspectRatio
    return delta
  }

  function generateColor() {
    const gray = 0.04 + Math.random() * 0.12
    const blueShift = (Math.random() - 0.5) * 0.04
    const warmShift = (Math.random() - 0.5) * 0.03
    return { r: gray + warmShift, g: gray, b: gray + blueShift }
  }

  function HSVtoRGB(h, s, v) {
    let r = 0, g = 0, b = 0
    const i = Math.floor(h * 6)
    const f = h * 6 - i
    const p = v * (1 - s)
    const q = v * (1 - f * s)
    const t = v * (1 - (1 - f) * s)
    switch (i % 6) {
      case 0: r = v; g = t; b = p; break
      case 1: r = q; g = v; b = p; break
      case 2: r = p; g = v; b = t; break
      case 3: r = p; g = q; b = v; break
      case 4: r = t; g = p; b = v; break
      case 5: r = v; g = p; b = q; break
    }
    return { r, g, b }
  }

  function wrap(value, min, max) {
    const range = max - min
    if (range === 0) return min
    return ((value - min) % range) + min
  }

  // Events
  function handleMouseDown(e) {
    const pointer = pointers[0]
    updatePointerDownData(pointer, -1, scaleByPixelRatio(e.clientX), scaleByPixelRatio(e.clientY))
    clickSplat(pointer)
  }
  window.addEventListener("mousedown", handleMouseDown)

  function handleFirstMouseMove(e) {
    const pointer = pointers[0]
    const posX = scaleByPixelRatio(e.clientX), posY = scaleByPixelRatio(e.clientY)
    updateFrame()
    updatePointerMoveData(pointer, posX, posY, generateColor())
    document.body.removeEventListener("mousemove", handleFirstMouseMove)
  }
  document.body.addEventListener("mousemove", handleFirstMouseMove)

  function handleMouseMove(e) {
    const pointer = pointers[0]
    const posX = scaleByPixelRatio(e.clientX), posY = scaleByPixelRatio(e.clientY)
    updatePointerMoveData(pointer, posX, posY, pointer.color)
  }
  window.addEventListener("mousemove", handleMouseMove)

  function handleFirstTouchStart(e) {
    const touches = e.targetTouches
    const pointer = pointers[0]
    for (let i = 0; i < touches.length; i++) {
      updatePointerDownData(pointer, touches[i].identifier, scaleByPixelRatio(touches[i].clientX), scaleByPixelRatio(touches[i].clientY))
    }
    updateFrame()
    document.body.removeEventListener("touchstart", handleFirstTouchStart)
  }
  document.body.addEventListener("touchstart", handleFirstTouchStart)

  function handleTouchStart(e) {
    const touches = e.targetTouches, pointer = pointers[0]
    for (let i = 0; i < touches.length; i++) {
      updatePointerDownData(pointer, touches[i].identifier, scaleByPixelRatio(touches[i].clientX), scaleByPixelRatio(touches[i].clientY))
    }
  }
  window.addEventListener("touchstart", handleTouchStart, false)

  function handleTouchMove(e) {
    const touches = e.targetTouches, pointer = pointers[0]
    for (let i = 0; i < touches.length; i++) {
      updatePointerMoveData(pointer, scaleByPixelRatio(touches[i].clientX), scaleByPixelRatio(touches[i].clientY), pointer.color)
    }
  }
  window.addEventListener("touchmove", handleTouchMove, false)

  function handleTouchEnd(e) {
    updatePointerUpData(pointers[0])
  }
  window.addEventListener("touchend", handleTouchEnd)

  // Watchers
  watch(() => props.simResolution, (v) => { config.SIM_RESOLUTION = v; initFramebuffers() })
  watch(() => props.dyeResolution, (v) => { config.DYE_RESOLUTION = v; initFramebuffers() })
  watch(() => props.shading, (v) => { config.SHADING = v; updateKeywords() })

  // 后台标签暂停：切走停渲染（多个标签同时跑流体=白烧 CPU），切回恢复（已停帧则不恢复）
  function handleVisibilityChange() {
    if (document.hidden) {
      if (rafId) { cancelAnimationFrame(rafId); rafId = null }
      if (!disposed && !_stopped) console.info('[FluidCursor] 后台暂停渲染')
    } else if (!rafId && !disposed && !_stopped) {
      lastUpdateTime = Date.now()
      rafId = requestAnimationFrame(updateFrame)
      console.info('[FluidCursor] 恢复渲染')
    }
  }
  document.addEventListener('visibilitychange', handleVisibilityChange)

  updateFrame()

  onUnmounted(() => {
    disposed = true
    if (rafId) cancelAnimationFrame(rafId)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    window.removeEventListener("mousedown", handleMouseDown)
    window.removeEventListener("mousemove", handleMouseMove)
    document.body.removeEventListener("mousemove", handleFirstMouseMove)
    window.removeEventListener("touchstart", handleTouchStart)
    document.body.removeEventListener("touchstart", handleFirstTouchStart)
    window.removeEventListener("touchmove", handleTouchMove)
    window.removeEventListener("touchend", handleTouchEnd)
  })
})
</script>

<style scoped>
.fluid-canvas {
  display: block;
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
}
</style>
