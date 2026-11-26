// src/router/index.js (适用于 Vue 3)
import { createRouter, createWebHistory } from 'vue-router'

const AgentSelector = () => import('@/components/AgentSelector.vue')
const ChatInterface = () => import('@/components/ChatInterface.vue')
const TroubleshootingGuide = () => import('@/components/TroubleshootingGuide.vue')
const QuestionViewer = () => import('@/components/QuestionViewer.vue')
const DigitalCircuitExperiments = () => import('@/components/DigitalCircuitExperiments.vue')
const DigitalExperimentDetail = () => import('@/components/DigitalExperimentDetail.vue')
const RfCircuitExperiments = () => import('@/components/RfCircuitExperiments.vue')
const RfExperimentDetail = () => import('@/components/RfExperimentDetail.vue')
const BasicComponents = () => import('@/components/BasicComponents.vue')
const AnalogCircuitExperiments = () => import('@/components/AnalogCircuitExperiments.vue')
const AnalogExperimentDetail = () => import('@/components/AnalogExperimentDetail.vue')
const InstrumentUsage = () => import('@/components/InstrumentUsage.vue')
const FeedbackForm = () => import('@/components/FeedbackForm.vue')



const routes = [
  { path: '/', component: AgentSelector },
  { path: '/chat', component: ChatInterface, meta: { title: "AI自由问答" , showBack: true }, },
  { path: '/troubleshooting-guide', name: 'TroubleshootingGuide', component: TroubleshootingGuide, meta: { title: "实验技能与故障排查", showBack: true }},
  { path: '/questions', name: 'QuestionViewer', component: QuestionViewer, meta: {title: "试题练习" , showBack: true } },
  { path: '/digital-circuit-experiments', name: 'DigitalCircuitExperiments', component: DigitalCircuitExperiments, meta: { title: "数字电路实验", showBack: true } },
  {
    path: '/digital-circuit-experiments/:id',
    name: 'DigitalExperimentDetail',
    component: DigitalExperimentDetail,
    meta: { title: '数字电路实验详情', showBack: true },
    beforeEnter(to) {
      return import('@/data/digitalExperimentContent').then(({ digitalExperimentContent }) => {
        const doc = digitalExperimentContent[to.params.id]
        if (doc && doc.title) {
          to.meta.title = doc.title
        }
      })
    }
  },
  { path: '/rf-circuit-experiments', name: 'RfCircuitExperiments', component: RfCircuitExperiments, meta: { title: "射频电路实验", showBack: true } },
  {
    path: '/rf-circuit-experiments/:id',
    name: 'RfExperimentDetail',
    component: RfExperimentDetail,
    meta: { title: '射频电路实验详情', showBack: true },
    beforeEnter(to) {
      return import('@/data/rfExperimentContent').then(({ rfExperimentContent }) => {
        const doc = rfExperimentContent[to.params.id]
        if (doc && doc.title) {
          to.meta.title = doc.title
        }
      })
    }
  },
  { path: '/basic-components', name: 'BasicComponents', component: BasicComponents, meta: { title: "基础元器件", showBack: true } },
  { path: '/analog-circuit-experiments', name: 'AnalogCircuitExperiments', component: AnalogCircuitExperiments, meta: { title: "模拟电路实验", showBack: true } },
  {
    path: '/analog-circuit-experiments/:id',
    name: 'AnalogExperimentDetail',
    component: AnalogExperimentDetail,
    meta: { title: '模拟电路实验详情', showBack: true },
    beforeEnter(to) {
      return import('@/data/analogExperimentContent').then(({ analogExperimentContent }) => {
        const doc = analogExperimentContent[to.params.id]
        if (doc && doc.title) {
          to.meta.title = doc.title
        }
      })
    }
  },
  { path: '/instrument-usage', name: 'InstrumentUsage', component: InstrumentUsage, meta: { title: "仪器设备使用", showBack: true } },
  { path: '/feedback', name: 'Feedback', component: FeedbackForm, meta: { title: "用户留言反馈", showBack: true } }  
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
