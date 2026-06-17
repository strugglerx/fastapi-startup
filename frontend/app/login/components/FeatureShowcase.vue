<template>
  <div class="showcase-container">
    <div class="showcase-inner">
      <Transition name="slide-fade" mode="out-in">
        <div :key="activeFeature" class="feature-display">
          <div class="image-glass-wrap">
            <img :src="features[activeFeature].image" class="feature-img" />
          </div>
          <div class="feature-info">
            <h2 class="feature-title">{{ features[activeFeature].text }}</h2>
            <p class="feature-desc">{{ features[activeFeature].desc }}</p>
          </div>
        </div>
      </Transition>
      
      <div class="slider-indicators">
        <div 
          v-for="(f, i) in features" :key="i"
          class="indicator-dot" :class="{ active: activeFeature === i }"
          @click="setFeature(i)"
        >
          <div class="indicator-progress"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue"

const activeFeature = ref(0)
let sliderTimer = null

function startSlider() {
  stopSlider()
  sliderTimer = setInterval(() => {
    activeFeature.value = (activeFeature.value + 1) % features.length
  }, 6000)
}

function stopSlider() {
  if (sliderTimer) clearInterval(sliderTimer)
}

function setFeature(index) {
  activeFeature.value = index
  startSlider()
}

onMounted(() => {
  startSlider()
})

onUnmounted(() => {
  stopSlider()
})

const features = [
  {
    image: "/images/feature_template.png",
    text: "Agent 探索工作台",
    desc: "把提示、工具和任务上下文放进同一块空间，快速试验不同 Agent 行为与执行链路。"
  },
  {
    image: "/images/feature_queue.png",
    text: "多模型路由面板",
    desc: "集中管理模型供应商、成本与延迟，让每一次调用都能在质量和效率之间更好落位。"
  },
  {
    image: "/images/feature_security.png",
    text: "权限与观测控制",
    desc: "围绕调用日志、权限边界和运行指标建立基础控制面，方便排查、审计与协作。"
  },
  {
    image: "/images/feature_storage.png",
    text: "会话与工具追踪",
    desc: "沉淀每次 AI 对话、消息上下文和 Function Call 细节，让调试与复盘都有清晰线索。"
  },
]
</script>

<style scoped>
.showcase-container {
  display: none;
  flex: 1;
  padding: 40px;
}
@media (min-width: 1024px) {
  .showcase-container {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
.showcase-inner {
  max-width: 500px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 40px;
}
.feature-display {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.image-glass-wrap {
  width: 100%;
  height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.feature-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 20px 40px rgba(0,0,0,0.5));
  z-index: 2;
  animation: float-icon 8s ease-in-out infinite;
}
@keyframes float-icon {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); }
}

.feature-info {
  text-align: left;
}
.feature-title {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: 12px;
  background: linear-gradient(180deg, #FFFFFF 0%, #A1A1AA 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.feature-desc {
  font-size: 15px;
  color: #A1A1AA;
  line-height: 1.6;
}

/* Slider Dots */
.slider-indicators {
  display: flex;
  gap: 8px;
}
.indicator-dot {
  flex: 1;
  height: 3px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  cursor: pointer;
}
.indicator-progress {
  width: 100%;
  height: 100%;
  background: #FFFFFF;
  transform: translateX(-100%);
}
.indicator-dot.active .indicator-progress {
  animation: load 6s linear forwards;
}
@keyframes load {
  to { transform: translateX(0); }
}

/* Transitions */
.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.5s ease; }
.slide-fade-enter-from { opacity: 0; transform: translateX(20px); filter: blur(4px); }
.slide-fade-leave-to { opacity: 0; transform: translateX(-20px); filter: blur(4px); }
</style>
