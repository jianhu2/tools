<template>
  <div class="home-container">
    <div class="content-box">
      <h3>介绍</h3>
      <p>这是MS_OAuth2API_Next的配套使用工具。</p>
      <p>MS_OAuth2API_Next项目的代码仓库地址：<a href="https://github.com/HChaoHui/MS_OAuth2API_Next" target="_blank">MS_OAuth2API_Next</a></p>

      <h3>邮箱管理</h3>
      <ul>
        <li>导入邮箱(支持导入方式: 文件上传、粘贴导入)</li>
        <li>邮箱列表(支持分页查询、搜索)</li>
        <li>删除邮箱(支持批量删除)</li>
        <li>导出邮箱(支持导出方式: 文件下载)</li>
        <li>邮箱详情(查看邮箱的详细信息)</li>
        <li>邮件列表(收件箱/垃圾箱、清空收件箱/垃圾箱)</li>
      </ul>

      <h3>联系作者</h3>
      <p>如果您有任何问题或建议，请通过以下方式联系我：</p>
      <ul>
        <li>邮箱：<a href="mailto:infoq@seek.li">infoq@seek.li</a></li>
      </ul>
    </div>
  </div>
</template>

<script lang="ts" setup>

</script>

<style scoped>
.content-box {
  background: #fff;
  border-radius: 8px;
}

h3 {
  color: #2c3e50;
  font-size: 1.5rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
  font-weight: 600;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.5rem;
}

p {
  margin-bottom: 1rem;
  color: #555;
}

a {
  color: #3498db;
  text-decoration: none;
  transition: color 0.2s ease;
}

a:hover {
  color: #2980b9;
  text-decoration: underline;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

li {
  padding: 0.5rem 0;
  padding-left: 1.5rem;
  position: relative;
  color: #555;
}

li:before {
  content: '•';
  color: #3498db;
  font-weight: bold;
  position: absolute;
  left: 0;
}

/* 第一个h3不需要顶部margin */
h3:first-of-type {
  margin-top: 0;
}

@media (max-width: 768px) {
  .home-container {
    padding: 1rem;
  }
  
  .content-box {
    padding: 1.5rem;
  }
  
  h3 {
    font-size: 1.3rem;
  }
}
</style>
