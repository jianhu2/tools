<template>
  <header class="app-nav">
    <div class="brand">
      <span class="brand-mark">MS</span>
      <div>
        <strong>OAuth2 Mail</strong>
        <small>Graph / IMAP</small>
      </div>
    </div>
    <el-menu :default-active="activeIndex" class="nav-menu" mode="horizontal" @select="handleSelect">
      <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">{{ item.title }}</el-menu-item>
    </el-menu>
  </header>
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
    title: '邮箱管理',
    routeName: 'email'
  },
  {
    index: '2',
    title: '说明',
    routeName: 'home'
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

<style scoped>
.app-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  height: 64px;
  padding: 0 18px;
  border-bottom: 1px solid #d9e1ec;
  background: #ffffff;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 220px;
}

.brand-mark {
  display: inline-grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: 8px;
  background: #2563eb;
  color: #ffffff;
  font-weight: 800;
}

.brand strong,
.brand small {
  display: block;
  line-height: 1.2;
}

.brand strong {
  color: #172033;
  font-size: 15px;
}

.brand small {
  margin-top: 2px;
  color: #64748b;
  font-size: 12px;
}

.nav-menu {
  flex: 1;
  justify-content: flex-end;
  border-bottom: none;
}

@media (max-width: 680px) {
  .app-nav {
    align-items: stretch;
    height: auto;
    flex-direction: column;
    padding: 12px;
  }

  .brand {
    min-width: 0;
  }

  .nav-menu {
    justify-content: flex-start;
  }
}
</style>
