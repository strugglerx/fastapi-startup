<template>
  <div class="login-bg-shell">
    <div class="parallax-bg" :style="parallaxStyle" />
    <div class="flashlight-overlay" :style="flashlightStyle" />
    <div ref="particlesContainer" class="particles-container" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue"

const particlesContainer = ref(null)

let reduceMotionQuery = null
let animationId = null
let mouseX = typeof window !== "undefined" ? window.innerWidth / 2 : 960
let mouseY = typeof window !== "undefined" ? window.innerHeight / 2 : 540

const currentMouseX = ref(mouseX)
const currentMouseY = ref(mouseY)
const targetAlpha = ref(0)
const currentAlpha = ref(0)
const backgroundImage = "/images/login-bg.png"

function onMouseMove(event) {
  if (event.target && typeof event.target.closest === "function" && event.target.closest(".login-card")) {
    targetAlpha.value = 0
    return
  }
  targetAlpha.value = 1
  mouseX = event.clientX
  mouseY = event.clientY
}

function onMouseLeave() {
  targetAlpha.value = 0
}

function animate() {
  currentMouseX.value += (mouseX - currentMouseX.value) * 0.05
  currentMouseY.value += (mouseY - currentMouseY.value) * 0.05
  currentAlpha.value += (targetAlpha.value - currentAlpha.value) * 0.05
  animationId = window.requestAnimationFrame(animate)
}

const parallaxStyle = computed(() => {
  const base = { backgroundImage: `url(${backgroundImage})` }
  if (reduceMotionQuery?.matches || typeof window === "undefined") {
    return base
  }

  const xOffset = (currentMouseX.value - window.innerWidth / 2) * -0.015
  const yOffset = (currentMouseY.value - window.innerHeight / 2) * -0.015
  return {
    ...base,
    transform: `translate(${xOffset}px, ${yOffset}px) scale(1.05)`,
  }
})

const flashlightStyle = computed(() => {
  if (reduceMotionQuery?.matches) {
    return { background: "rgba(0,0,0,0.85)" }
  }

  const centerAlpha = (0.95 - 0.95 * currentAlpha.value).toFixed(2)
  const midAlpha = (0.95 - 0.55 * currentAlpha.value).toFixed(2)

  return {
    background: `radial-gradient(circle 600px at ${currentMouseX.value}px ${currentMouseY.value}px, rgba(0,0,0,${centerAlpha}) 0%, rgba(0,0,0,${midAlpha}) 35%, rgba(0,0,0,0.95) 80%)`,
  }
})

function initParticles() {
  const container = particlesContainer.value
  if (!container) return
  container.innerHTML = ""

  const particleCount = reduceMotionQuery?.matches ? 18 : 32
  for (let i = 0; i < particleCount; i += 1) {
    const particle = document.createElement("div")
    particle.className = "particle"
    const size = Math.random() * 2.5 + 1
    particle.style.width = `${size}px`
    particle.style.height = `${size}px`
    particle.style.left = `${Math.random() * 100}%`
    particle.style.top = `${Math.random() * 100}%`
    particle.style.opacity = `${Math.random() * 0.42 + 0.18}`
    particle.style.animationDelay = `${-Math.random() * 12}s`
    particle.style.animationDuration = `${Math.random() * 8 + 12}s`
    container.appendChild(particle)
  }
}

onMounted(() => {
  reduceMotionQuery = window.matchMedia?.("(prefers-reduced-motion: reduce)")
  initParticles()
  window.addEventListener("mousemove", onMouseMove)
  document.addEventListener("mouseleave", onMouseLeave)
  if (!reduceMotionQuery?.matches) {
    animationId = window.requestAnimationFrame(animate)
  }
})

onUnmounted(() => {
  if (animationId) {
    window.cancelAnimationFrame(animationId)
  }
  window.removeEventListener("mousemove", onMouseMove)
  document.removeEventListener("mouseleave", onMouseLeave)
})
</script>

<style scoped>
.login-bg-shell {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}

.parallax-bg {
  position: absolute;
  inset: -5%;
  background-position: center;
  background-repeat: no-repeat;
  background-size: auto;
  z-index: 0;
  will-change: transform;
}

.flashlight-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  will-change: opacity, background;
}

.particles-container {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  overflow: hidden;
}
</style>

<style>
.particles-container .particle {
  position: absolute;
  background: #ffffff;
  border-radius: 50%;
  filter: blur(0.4px);
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.72);
  animation: particle-twinkle 16s ease-in-out infinite;
}

@keyframes particle-twinkle {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.45); }
}

@media (prefers-reduced-motion: reduce) {
  .particles-container .particle {
    animation: none;
  }
}
</style>
