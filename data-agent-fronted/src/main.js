// 创建 Vue 根实例，并在加载组件前引入全局基础样式。
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

createApp(App).mount('#app')
