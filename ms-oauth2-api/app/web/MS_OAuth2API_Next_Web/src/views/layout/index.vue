<template>
  <el-menu :default-active="activeIndex" class="el-menu-demo" mode="horizontal" @select="handleSelect">
    <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">{{ item.title }}</el-menu-item>
  </el-menu>
  <router-view></router-view>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import router from '@/router'

interface MenuItem {
  index: string
  title: string
  routeName?: string
  disabled?: boolean
  children?: MenuItem[]
}

const menuItems = ref<MenuItem[]>([
  {
    index: '1',
    title: '首页',
    routeName: 'home'
  },
  {
    index: '2',
    title: '邮箱管理',
    routeName: 'email'
  }
])

const route = useRoute()

// 根据当前路由动态计算activeIndex
const activeIndex = computed(() => {
  // 查找当前路由对应的菜单index
  const currentMenuItem = menuItems.value.find(item => item.routeName === route.name)
  return currentMenuItem?.index || '1' // 默认选中首页
})

const handleSelect = (key: string) => {
  let index = Number(key) - 1 || 0

  if (index < 0) {
    index = 0
  } else if (index >= menuItems.value.length) {
    index = menuItems.value.length - 1
  }

  const selectedItem = menuItems.value[index]
  if (selectedItem?.routeName) {
    router.push({ name: selectedItem.routeName })
  }
}
</script>
