import { useRef, useEffect } from 'react';

const VERTEX_SHADER = `
attribute vec2 a_position;
varying vec2 v_texCoord;
void main() {
  v_texCoord = a_position * 0.5 + 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}`;

const FRAGMENT_SHADER = `
precision highp float;
uniform float u_time;
uniform vec2 u_resolution;
uniform vec2 u_mouse;
varying vec2 v_texCoord;

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

void main() {
    vec2 uv = v_texCoord;
    vec2 screen_uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.y, u_resolution.x);
    vec2 mouse_uv = (u_mouse.xy - 0.5 * u_resolution.xy) / min(u_resolution.y, u_resolution.x);

    vec3 color = vec3(0.02, 0.03, 0.05);

    for (float i = 0.0; i < 60.0; i++) {
        float h = hash(vec2(i, 1.23));
        float speed = 0.1 + h * 0.2;
        vec2 p = vec2(
            fract(h * 13.4 + u_time * 0.02 * (h - 0.5)),
            fract(h * 45.6 + u_time * 0.03)
        );
        vec2 pos = (p - 0.5) * 2.0;
        float mouse_dist = length(pos - mouse_uv);
        float mouse_factor = smoothstep(0.3, 0.0, mouse_dist);
        float dist = length(screen_uv - pos);
        float size = 0.002 + h * 0.003;
        float brightness = (0.5 + 0.5 * sin(u_time * 2.5 + h * 6.28)) * (1.0 + mouse_factor * 4.0);
        vec3 p_color = mix(vec3(0.91, 0.12, 0.39), vec3(0.0, 0.74, 0.83), h);
        color += p_color * (size / (dist + 0.001)) * brightness;
    }

    float d = length(screen_uv - mouse_uv);
    color += vec3(0.12, 0.06, 0.18) * exp(-d * 8.0);

    gl_FragColor = vec4(color, 1.0);
}`;

function createShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  return shader;
}

export default function WebGLBackground() {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: 0, y: 0 });
  const targetMouseRef = useRef({ x: 0, y: 0 });
  const animRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const syncSize = () => {
      const w = canvas.clientWidth || 1280;
      const h = canvas.clientHeight || 720;
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
    };

    let resizeObserver;
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(syncSize);
      resizeObserver.observe(canvas);
    }
    syncSize();

    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) return;

    const prog = gl.createProgram();
    gl.attachShader(prog, createShader(gl, gl.VERTEX_SHADER, VERTEX_SHADER));
    gl.attachShader(prog, createShader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const pos = gl.getAttribLocation(prog, 'a_position');
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

    const uTime = gl.getUniformLocation(prog, 'u_time');
    const uRes = gl.getUniformLocation(prog, 'u_resolution');
    const uMouse = gl.getUniformLocation(prog, 'u_mouse');

    const handleMouseMove = (event) => {
      const rect = canvas.getBoundingClientRect();
      if (rect.width && rect.height) {
        targetMouseRef.current.x = ((event.clientX - rect.left) / rect.width) * canvas.width;
        targetMouseRef.current.y = (1.0 - (event.clientY - rect.top) / rect.height) * canvas.height;
      }
    };
    window.addEventListener('mousemove', handleMouseMove);

    const render = (t) => {
      if (typeof ResizeObserver === 'undefined') syncSize();

      const m = mouseRef.current;
      const tm = targetMouseRef.current;
      m.x += (tm.x - m.x) * 0.25;
      m.y += (tm.y - m.y) * 0.25;

      gl.viewport(0, 0, canvas.width, canvas.height);
      if (uTime) gl.uniform1f(uTime, t * 0.001);
      if (uRes) gl.uniform2f(uRes, canvas.width, canvas.height);
      if (uMouse) gl.uniform2f(uMouse, m.x, m.y);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      animRef.current = requestAnimationFrame(render);
    };
    animRef.current = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (animRef.current) cancelAnimationFrame(animRef.current);
      if (resizeObserver) resizeObserver.disconnect();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-[-1]">
      <div className="fixed inset-0 w-full h-full" style={{ display: 'block' }}>
        <canvas
          ref={canvasRef}
          id="shader-canvas-home"
          style={{ display: 'block', width: '100%', height: '100%' }}
        />
      </div>
      <div className="absolute inset-0 bg-background/80 mix-blend-multiply pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/40 to-background pointer-events-none mix-blend-overlay" />
    </div>
  );
}
