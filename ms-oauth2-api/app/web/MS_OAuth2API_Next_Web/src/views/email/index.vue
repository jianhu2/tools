<template>
    <div class="mail-workspace">
        <aside class="account-panel">
            <div class="panel-head">
                <div>
                    <p class="eyebrow">MAILBOXES</p>
                    <h2>邮箱</h2>
                </div>
                <el-tag round>{{ mailList.length }}</el-tag>
            </div>

            <div class="account-tools">
                <el-input v-model="accountKeyword" clearable placeholder="搜索邮箱">
                    <template #prefix>
                        <el-icon><SearchIcon /></el-icon>
                    </template>
                </el-input>
                <div class="split-row">
                    <el-input v-model="toolForm.splitSymbol" placeholder="分隔符" />
                    <el-button type="primary" @click="dialogCopyVisible = true">
                        <el-icon><CopyDocumentIcon /></el-icon>
                    </el-button>
                    <el-upload ref="upload" :limit="1" :show-file-list="false" :on-exceed="handleExceed"
                        :auto-upload="false" :on-change="handleFileChange" accept=".txt,.csv" class="custom-upload">
                        <template #trigger>
                            <el-button>
                                <el-icon><FilesIcon /></el-icon>
                            </el-button>
                        </template>
                    </el-upload>
                    <el-button type="success" :disabled="emailList.length === 0" @click="handleAdd">
                        <el-icon><UploadIcon /></el-icon>
                    </el-button>
                </div>
                <div v-if="fileName" class="file-hint">{{ fileName }} · {{ emailList.length }} 行</div>
            </div>

            <div class="bulk-actions">
                <el-button size="small" @click="handleBatchExport">
                    <el-icon><DownloadIcon /></el-icon>
                    导出选中
                </el-button>
                <el-button size="small" @click="handleExportAll">
                    <el-icon><DownloadIcon /></el-icon>
                    导出全部
                </el-button>
                <el-button size="small" type="danger" plain @click="handleBatchDelete">
                    <el-icon><DeleteIcon /></el-icon>
                    删除选中
                </el-button>
                <el-button size="small" type="danger" @click="handleDeleteAll">
                    <el-icon><DeleteFilledIcon /></el-icon>
                    清空列表
                </el-button>
            </div>

            <el-table ref="multipleTableRef" class="account-table" :data="tableMailList" row-key="email"
                highlight-current-row height="calc(100vh - 298px)" size="default" @selection-change="handleSelectionChange"
                @row-click="handleAccountRowClick">
                <el-table-column type="selection" width="42" />
                <el-table-column label="账号" min-width="210">
                    <template #default="scope">
                        <div class="account-cell" :class="{ active: nowPost.email === scope.row.email }">
                            <span class="account-email">{{ scope.row.email }}</span>
                            <span class="account-client">{{ maskClientId(scope.row.client_id) }}</span>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="" width="102" align="right">
                    <template #default="scope">
                        <div class="row-actions" @click.stop>
                            <el-button size="small" circle @click="handleEdit(scope.row, scope.$index)">
                                <el-icon><EditIcon /></el-icon>
                            </el-button>
                            <el-button size="small" circle type="danger" plain @click="handleDelete(scope.row, scope.$index)">
                                <el-icon><DeleteIcon /></el-icon>
                            </el-button>
                        </div>
                    </template>
                </el-table-column>
            </el-table>

            <div class="pagination compact" ref="tablePaginationRef">
                <el-pagination background small v-model:current-page="tablePagination.currentPage"
                    v-model:page-size="tablePagination.pageSize" :page-sizes="[10, 20, 50, 100]"
                    layout="prev, pager, next" :total="filteredMailList.length" @size-change="handleTableSizeChange"
                    @current-change="handleTableCurrentChange" />
            </div>
        </aside>

        <main class="mail-panel">
            <div class="mail-toolbar">
                <div class="mail-title">
                    <p class="eyebrow">{{ boxType === 'INBOX' ? 'INBOX' : 'JUNK' }}</p>
                    <h1>{{ nowPost.email || '选择邮箱' }}</h1>
                </div>
                <div class="mail-actions">
                    <el-segmented v-model="boxType" :options="boxOptions" :disabled="!nowPost.email" @change="handleMailboxChange" />
                    <el-button type="primary" :loading="postLoading" :disabled="!nowPost.email" @click="handleReceive">
                        <el-icon><RefreshIcon /></el-icon>
                        收取
                    </el-button>
                    <el-button :disabled="!nowPost.email" @click="handleReceiveNew">
                        <el-icon><MessageIcon /></el-icon>
                        最新
                    </el-button>
                    <el-button type="danger" plain :disabled="!nowPost.email" @click="handleClear">
                        <el-icon><DeleteFilledIcon /></el-icon>
                    </el-button>
                </div>
            </div>

            <div class="mail-stats">
                <el-tag effect="plain">{{ postList.length }} 封</el-tag>
                <span v-if="lastFetchText">{{ lastFetchText }}</span>
                <span v-if="postLoading">取件中...</span>
            </div>

            <div v-if="!nowPost.email" class="empty-pane">
                <el-icon><MessageIcon /></el-icon>
                <p>选择左侧邮箱</p>
            </div>

            <div v-else-if="postLoading && postList.length === 0" class="mail-skeleton">
                <el-skeleton :rows="6" animated />
                <el-skeleton :rows="6" animated />
            </div>

            <div v-else-if="postList.length === 0" class="empty-pane">
                <el-icon><MessageIcon /></el-icon>
                <p>暂无邮件</p>
            </div>

            <div v-else class="message-list">
                <button v-for="post in postList" :key="messageKey(post)" class="message-card"
                    :class="{ active: selectedPost === post }" @click="selectPost(post)">
                    <div class="message-row">
                        <span class="sender">{{ normalizeSender(post.send) }}</span>
                        <span class="date">{{ formatDate(post.date) }}</span>
                    </div>
                    <div class="subject">{{ post.subject || '(无主题)' }}</div>
                    <div class="preview">{{ post.text || stripHtml(post.html) || '(无内容)' }}</div>
                </button>
            </div>
        </main>

        <section class="preview-panel">
            <template v-if="selectedPost">
                <div class="preview-head">
                    <p class="eyebrow">PREVIEW</p>
                    <h2>{{ selectedPost.subject || '(无主题)' }}</h2>
                    <div class="meta">
                        <span>{{ selectedPost.send }}</span>
                        <span>{{ formatDate(selectedPost.date, true) }}</span>
                    </div>
                </div>
                <div class="preview-body">
                    <iframe v-if="selectedPost.html" :srcdoc="selectedPost.html" sandbox="allow-same-origin"></iframe>
                    <pre v-else>{{ selectedPost.text || '(无内容)' }}</pre>
                </div>
            </template>
            <div v-else class="empty-preview">
                <el-icon><DocumentCopyIcon /></el-icon>
                <p>邮件内容</p>
            </div>
        </section>

        <el-dialog v-model="dialogCopyVisible" title="粘贴导入" width="820">
            <el-input v-model="copyTextarea" :rows="16" type="textarea"
                placeholder="user@outlook.com----password----client_id----refresh_token" />
            <template #footer>
                <div class="dialog-footer">
                    <el-button @click="dialogCopyVisible = false">取消</el-button>
                    <el-button type="primary" @click="handlePasteAdd">
                        <el-icon><UploadIcon /></el-icon>
                        导入
                    </el-button>
                </div>
            </template>
        </el-dialog>

        <el-dialog v-model="dialogEditVisible" title="编辑邮箱" width="760">
            <el-form :model="editForm" ref="editFormRef" label-width="110px">
                <el-form-item label="邮箱" prop="email">
                    <el-input v-model="editForm.email" placeholder="请输入邮箱" />
                </el-form-item>
                <el-form-item label="密码" prop="password">
                    <el-input v-model="editForm.password" type="password" placeholder="请输入密码" />
                </el-form-item>
                <el-form-item label="客户端ID" prop="client_id">
                    <el-input v-model="editForm.client_id" placeholder="请输入客户端ID" />
                </el-form-item>
                <el-form-item label="刷新令牌" prop="refresh_token">
                    <el-input v-model="editForm.refresh_token" type="textarea" :rows="8" placeholder="请输入刷新令牌" />
                </el-form-item>
            </el-form>
            <template #footer>
                <div class="dialog-footer">
                    <el-button @click="dialogEditVisible = false">取消</el-button>
                    <el-button type="primary" @click="handleSave">保存</el-button>
                </div>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { genFileId, ElMessage, ElMessageBox } from 'element-plus'
import {
    Upload as UploadIcon,
    Plus as FilesIcon,
    Download as DownloadIcon,
    Delete as DeleteIcon,
    DeleteFilled as DeleteFilledIcon,
    CopyDocument as CopyDocumentIcon,
    DocumentCopy as DocumentCopyIcon,
    Search as SearchIcon,
    Edit as EditIcon,
    Refresh as RefreshIcon,
    Message as MessageIcon,
} from '@element-plus/icons-vue'

import type { UploadInstance, UploadProps, UploadRawFile, TableInstance } from 'element-plus'

interface Email {
    email: string
    password: string
    client_id: string
    refresh_token: string
}

interface Post {
    send: string
    subject: string
    text: string
    html: string
    date: string
}

const upload = ref<UploadInstance>()
const multipleTableRef = ref<TableInstance>()
const emailList = ref<string[]>([])
const fileName = ref<string>('')
const accountKeyword = ref('')
const multipleSelection = ref<Email[]>([])
const mailList = ref<Email[]>(JSON.parse(localStorage.getItem('localMailList') || '[]') as Email[])
const postList = ref<Post[]>([])
const selectedPost = ref<Post | null>(null)
const postLoading = ref(false)
const lastFetchText = ref('')
const boxType = ref<'INBOX' | 'Junk'>('INBOX')
const dialogCopyVisible = ref(false)
const copyTextarea = ref('')
const dialogEditVisible = ref(false)
const editIndex = ref(-1)

const toolForm = ref({
    splitSymbol: '----'
})

const editForm = ref<Email>({
    email: '',
    password: '',
    client_id: '',
    refresh_token: ''
})

const nowPost = ref<Email>({
    email: '',
    password: '',
    client_id: '',
    refresh_token: ''
})

const tablePagination = ref({
    currentPage: 1,
    pageSize: 10,
    total: mailList.value.length
})

const boxOptions = [
    { label: '收件箱', value: 'INBOX' },
    { label: '垃圾箱', value: 'Junk' },
]

const filteredMailList = computed(() => {
    const keyword = accountKeyword.value.trim().toLowerCase()
    if (!keyword) return mailList.value
    return mailList.value.filter(item => item.email.toLowerCase().includes(keyword))
})

const tableMailList = computed(() => {
    const start = (tablePagination.value.currentPage - 1) * tablePagination.value.pageSize
    const end = start + tablePagination.value.pageSize
    return filteredMailList.value.slice(start, end)
})

// 去掉行尾注释（空白后的 # 或 //，或整行注释）。
// Microsoft 的 client_id / refresh_token 不含 '#'，所以按空白+# 截断是安全的。
const stripInlineComment = (line: string): string => {
    const trimmed = line.trim()
    if (trimmed.startsWith('#') || trimmed.startsWith('//')) return ''
    return trimmed.replace(/\s+(#|\/\/).*$/, '').trim()
}

// 把粘贴/文件文本拆成干净的账号行：去注释、去空白行。
const toCredentialLines = (raw: string): string[] =>
    raw.split(/\r?\n/).map(stripInlineComment).filter(Boolean)

const splitMailboxLine = (line: string, separator: string): Email => {
    const parts: string[] = []
    let rest = stripInlineComment(line)

    for (let i = 0; i < 3; i++) {
        const idx = rest.indexOf(separator)
        if (idx === -1) break
        parts.push(rest.slice(0, idx).trim())
        rest = rest.slice(idx + separator.length)
    }

    parts.push(stripInlineComment(rest))

    return {
        email: parts[0] || '',
        password: parts[1] || '',
        client_id: parts[2] || '',
        refresh_token: parts[3] || ''
    }
}

const saveMailList = () => {
    localStorage.setItem('localMailList', JSON.stringify(mailList.value))
    tablePagination.value.total = filteredMailList.value.length
}

const handleExceed: UploadProps['onExceed'] = (files) => {
    upload.value?.clearFiles()
    const file = files[0] as UploadRawFile
    file.uid = genFileId()
    upload.value?.handleStart(file)
}

const handleFileChange: UploadProps['onChange'] = (file, fileList = []) => {
    const rawFile = fileList[0]?.raw as UploadRawFile | undefined
    if (!rawFile) {
        fileName.value = ''
        return
    }

    if (!rawFile.type.match(/text\/(plain|csv)/) && !rawFile.name.endsWith('.txt') && !rawFile.name.endsWith('.csv')) {
        ElMessage.error('请上传 .txt 或 .csv 文件')
        upload.value?.clearFiles()
        fileName.value = ''
        return
    }

    fileName.value = rawFile.name.length > 18 ? rawFile.name.slice(0, 18) + '...' : rawFile.name
    parseFileContent(rawFile)
}

const parseFileContent = (file: UploadRawFile) => {
    const reader = new FileReader()

    reader.onload = (e) => {
        const content = e.target?.result as string
        if (!content) {
            ElMessage.error('文件内容为空')
            return
        }
        emailList.value = toCredentialLines(content)
    }

    reader.onerror = () => {
        ElMessage.error('读取文件失败')
    }

    reader.readAsText(file)
}

const handleSelectionChange = (val: Email[]) => {
    multipleSelection.value = val
}

const handleTableSizeChange = (val: number) => {
    tablePagination.value.pageSize = val
}

const handleTableCurrentChange = (val: number) => {
    tablePagination.value.currentPage = val
}

const handleAdd = () => {
    if (emailList.value.length === 0) {
        ElMessage.warning('请先选择文件或粘贴数据')
        return
    }

    const parsed = emailList.value.map(item => splitMailboxLine(item, toolForm.value.splitSymbol))
        .filter(item => item.email && item.client_id && item.refresh_token)

    if (parsed.length === 0) {
        ElMessage.error('没有可导入的有效邮箱')
        return
    }

    const existingIndex = new Map(mailList.value.map((item, index) => [item.email.toLowerCase(), index]))
    let addedCount = 0
    let updatedCount = 0

    parsed.forEach(item => {
        const emailKey = item.email.toLowerCase()
        const index = existingIndex.get(emailKey)

        localStorage.removeItem(item.email + 'INBOX')
        localStorage.removeItem(item.email + 'Junk')

        if (index === undefined) {
            mailList.value.push(item)
            existingIndex.set(emailKey, mailList.value.length - 1)
            addedCount++
            return
        }

        mailList.value[index] = item
        updatedCount++
    })

    saveMailList()
    ElMessage.success(`新增 ${addedCount} 个，更新 ${updatedCount} 个邮箱`)
    emailList.value = []
    copyTextarea.value = ''
    dialogCopyVisible.value = false
    fileName.value = ''
    upload.value?.clearFiles()
}

const handlePasteAdd = () => {
    emailList.value = toCredentialLines(copyTextarea.value)
    handleAdd()
}

const handleBatchDelete = () => {
    if (multipleSelection.value.length === 0) {
        ElMessage.warning('请选择要删除的邮箱')
        return
    }

    ElMessageBox.confirm(`确认删除选中的 ${multipleSelection.value.length} 个邮箱吗？`, '删除确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(() => {
        const selected = new Set(multipleSelection.value.map(item => item.email))
        mailList.value = mailList.value.filter(item => !selected.has(item.email))
        saveMailList()
        multipleTableRef.value?.clearSelection()
        if (nowPost.value.email && selected.has(nowPost.value.email)) {
            resetMailbox()
        }
        ElMessage.success('删除成功')
    }).catch(() => undefined)
}

const handleDeleteAll = () => {
    ElMessageBox.confirm('确认删除所有邮箱吗？', '删除确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(() => {
        mailList.value = []
        saveMailList()
        resetMailbox()
        multipleTableRef.value?.clearSelection()
        ElMessage.success('删除成功')
    }).catch(() => undefined)
}

const handleBatchExport = () => {
    if (multipleSelection.value.length === 0) {
        ElMessage.warning('请选择要导出的邮箱')
        return
    }
    exportMails(multipleSelection.value, 'selected_mails.txt')
}

const handleExportAll = () => {
    if (mailList.value.length === 0) {
        ElMessage.warning('请先添加邮箱')
        return
    }
    exportMails(mailList.value, 'all_mails.txt')
}

const exportMails = (rows: Email[], filename: string) => {
    const exportContent = rows.map(item => [
        item.email,
        item.password,
        item.client_id,
        item.refresh_token
    ].join(toolForm.value.splitSymbol)).join('\n')
    const blob = new Blob([exportContent], { type: 'text/plain;charset=utf-8' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    a.click()
    URL.revokeObjectURL(a.href)
    ElMessage.success('导出成功')
}

const handleEdit = (row: Email, index: number) => {
    editIndex.value = mailList.value.findIndex(item => item.email === row.email)
    editForm.value = JSON.parse(JSON.stringify(row))
    dialogEditVisible.value = true
}

const handleSave = () => {
    if (editIndex.value === -1) {
        ElMessage.error('编辑索引错误')
        return
    }

    mailList.value[editIndex.value] = editForm.value
    saveMailList()
    if (nowPost.value.email === editForm.value.email) {
        nowPost.value = editForm.value
    }
    dialogEditVisible.value = false
    ElMessage.success('保存成功')
}

const handleDelete = (row: Email, index: number) => {
    ElMessageBox.confirm(`确认删除 ${row.email} 吗？`, '删除确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(() => {
        const absoluteIndex = mailList.value.findIndex(item => item.email === row.email)
        if (absoluteIndex === -1) return
        mailList.value.splice(absoluteIndex, 1)
        saveMailList()
        if (nowPost.value.email === row.email) resetMailbox()
        ElMessage.success('删除成功')
    }).catch(() => undefined)
}

const handleAccountRowClick = (row: Email) => {
    handleInbox(row)
}

const handleInbox = (row: Email) => {
    boxType.value = 'INBOX'
    handlePost(row, true)
}

const handleTrash = (row: Email) => {
    boxType.value = 'Junk'
    handlePost(row, true)
}

const handleMailboxChange = () => {
    if (nowPost.value.email) {
        handlePost(nowPost.value, true)
    }
}

const handlePost = (row: Email, fetchNow = true) => {
    nowPost.value = row
    const cached = JSON.parse(localStorage.getItem(row.email + boxType.value) || '[]')
    postList.value = Array.isArray(cached) ? cached : []
    selectedPost.value = postList.value[0] || null
    lastFetchText.value = ''
    if (fetchNow) {
        getPosts(row.email, row.password, row.client_id, row.refresh_token, boxType.value, 'all')
    }
}

const handleReceive = () => {
    if (!nowPost.value.email) return
    const { email, password, client_id, refresh_token } = nowPost.value
    getPosts(email, password, client_id, refresh_token, boxType.value, 'all')
}

const handleReceiveNew = () => {
    if (!nowPost.value.email) return
    const { email, password, client_id, refresh_token } = nowPost.value
    getPosts(email, password, client_id, refresh_token, boxType.value, 'new')
}

const getPosts = async (email: string, password: string, client_id: string, refresh_token: string, mailbox: string, mode: 'all' | 'new') => {
    postLoading.value = true
    try {
        const response = await fetch(mode === 'new' ? '/api/mail_new' : '/api/mail_all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                password,
                client_id,
                refresh_token,
                mailbox
            })
        })
        const data = await response.json()

        if (data.code == 200) {
            const incoming = Array.isArray(data.data) ? data.data : []
            postList.value = mode === 'new' && incoming.length > 0 ? mergePosts(incoming, postList.value) : incoming
            selectedPost.value = postList.value[0] || null
            localStorage.setItem(nowPost.value.email + boxType.value, JSON.stringify(postList.value))
            updateRefreshToken(data.new_refresh_token)
            lastFetchText.value = `${formatDate(new Date().toISOString(), true)} 更新`
            ElMessage.success('收取成功')
        } else {
            ElMessage.error(data.message || '收取失败')
        }
    } catch (error) {
        ElMessage.error('收取失败')
    } finally {
        postLoading.value = false
    }
}

const updateRefreshToken = (newRefreshToken?: string) => {
    if (!newRefreshToken) return
    const idx = mailList.value.findIndex((m: Email) => m.email === nowPost.value.email)
    const entry = idx !== -1 ? mailList.value[idx] : undefined
    if (entry) {
        entry.refresh_token = newRefreshToken
        localStorage.setItem('localMailList', JSON.stringify(mailList.value))
    }
    nowPost.value.refresh_token = newRefreshToken
}

const mergePosts = (incoming: Post[], current: Post[]) => {
    const seen = new Set<string>()
    return incoming.concat(current).filter(item => {
        const key = messageKey(item)
        if (seen.has(key)) return false
        seen.add(key)
        return true
    })
}

const selectPost = (post: Post) => {
    selectedPost.value = post
}

const handleClear = () => {
    if (!nowPost.value.email) return
    ElMessageBox.confirm(`确认清空 ${nowPost.value.email} 的${boxType.value === 'INBOX' ? '收件箱' : '垃圾箱'}吗？`, '清空确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(() => {
        postList.value = []
        selectedPost.value = null
        localStorage.setItem(nowPost.value.email + boxType.value, JSON.stringify(postList.value))
        clearPosts(nowPost.value.email, nowPost.value.password, nowPost.value.client_id, nowPost.value.refresh_token, boxType.value)
        ElMessage.success('邮箱正在清空中')
    }).catch(() => undefined)
}

const clearPosts = (email: string, password: string, client_id: string, refresh_token: string, mailbox: string) => {
    fetch('/api/process-mailbox', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            email,
            password,
            client_id,
            refresh_token,
            mailbox
        })
    })
}

const resetMailbox = () => {
    nowPost.value = {
        email: '',
        password: '',
        client_id: '',
        refresh_token: ''
    }
    postList.value = []
    selectedPost.value = null
}

const maskClientId = (clientId: string) => {
    if (!clientId) return '未配置 client_id'
    return clientId.length > 12 ? `${clientId.slice(0, 8)}...${clientId.slice(-4)}` : clientId
}

const normalizeSender = (sender: string) => {
    return sender || '(未知发件人)'
}

const stripHtml = (html: string) => {
    if (!html) return ''
    return html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
}

const formatDate = (date: string, full = false) => {
    if (!date) return ''
    const parsed = new Date(date)
    if (Number.isNaN(parsed.getTime())) return date
    return parsed.toLocaleString('zh-CN', full
        ? { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }
        : { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const messageKey = (post: Post) => {
    return `${post.send}-${post.subject}-${post.date}`
}

onMounted(() => {
    nextTick(() => {
        const firstMail = mailList.value[0]
        if (firstMail) {
            handlePost(firstMail, false)
        }
    })
})
</script>

<style scoped>
.mail-workspace {
    display: grid;
    grid-template-columns: minmax(320px, 390px) minmax(420px, 1fr) minmax(330px, 430px);
    gap: 16px;
    min-height: calc(100vh - 64px);
    padding: 16px;
    background: #eef2f7;
}

.account-panel,
.mail-panel,
.preview-panel {
    min-width: 0;
    background: #ffffff;
    border: 1px solid #d9e1ec;
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(30, 41, 59, 0.08);
}

.account-panel,
.mail-panel {
    display: flex;
    flex-direction: column;
}

.panel-head,
.mail-toolbar,
.preview-head {
    padding: 18px 20px;
    border-bottom: 1px solid #e3e9f2;
}

.panel-head,
.mail-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.eyebrow {
    margin: 0 0 4px;
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0;
}

h1,
h2 {
    margin: 0;
    color: #172033;
    font-size: 20px;
    line-height: 1.3;
    font-weight: 700;
}

.account-tools {
    display: grid;
    gap: 10px;
    padding: 14px;
    border-bottom: 1px solid #e3e9f2;
}

.split-row {
    display: grid;
    grid-template-columns: minmax(74px, 1fr) 36px 36px 36px;
    gap: 8px;
    align-items: center;
}

.file-hint {
    color: #64748b;
    font-size: 12px;
}

.bulk-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    padding: 12px 14px;
    border-bottom: 1px solid #e3e9f2;
}

.bulk-actions :deep(.el-button) {
    margin: 0;
}

.account-table {
    flex: 1;
}

.account-cell {
    display: grid;
    gap: 4px;
    min-width: 0;
}

.account-email {
    overflow: hidden;
    color: #1e293b;
    font-weight: 650;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.account-client {
    color: #64748b;
    font-size: 12px;
}

.row-actions {
    display: inline-flex;
    gap: 6px;
}

.row-actions :deep(.el-button + .el-button) {
    margin-left: 0;
}

.pagination.compact {
    display: flex;
    justify-content: center;
    padding: 12px;
    border-top: 1px solid #e3e9f2;
}

.mail-toolbar {
    align-items: flex-start;
}

.mail-title {
    min-width: 0;
}

.mail-title h1 {
    overflow: hidden;
    max-width: 420px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.mail-actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 8px;
}

.mail-actions :deep(.el-button + .el-button) {
    margin-left: 0;
}

.mail-stats {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 44px;
    padding: 0 20px;
    color: #64748b;
    border-bottom: 1px solid #e3e9f2;
    font-size: 13px;
}

.message-list {
    display: grid;
    align-content: start;
    gap: 10px;
    overflow: auto;
    padding: 14px;
}

.message-card {
    display: grid;
    gap: 7px;
    width: 100%;
    min-height: 96px;
    padding: 14px;
    border: 1px solid #d9e1ec;
    border-radius: 8px;
    background: #ffffff;
    color: inherit;
    cursor: pointer;
    text-align: left;
    transition: border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
}

.message-card:hover,
.message-card.active {
    border-color: #2563eb;
    background: #f8fbff;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.12);
}

.message-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.sender,
.subject {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.sender {
    color: #334155;
    font-weight: 650;
}

.date {
    flex: 0 0 auto;
    color: #64748b;
    font-size: 12px;
}

.subject {
    color: #0f172a;
    font-size: 15px;
    font-weight: 700;
}

.preview {
    display: -webkit-box;
    overflow: hidden;
    color: #64748b;
    font-size: 13px;
    line-height: 1.45;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
}

.preview-panel {
    display: flex;
    min-height: 0;
    flex-direction: column;
}

.preview-head h2 {
    display: -webkit-box;
    overflow: hidden;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
}

.meta {
    display: grid;
    gap: 4px;
    margin-top: 10px;
    color: #64748b;
    font-size: 12px;
}

.preview-body {
    flex: 1;
    min-height: 0;
    padding: 14px;
}

.preview-body iframe {
    width: 100%;
    height: calc(100vh - 214px);
    border: 1px solid #e3e9f2;
    border-radius: 8px;
    background: #ffffff;
}

.preview-body pre {
    overflow: auto;
    height: calc(100vh - 214px);
    margin: 0;
    padding: 14px;
    border: 1px solid #e3e9f2;
    border-radius: 8px;
    color: #1e293b;
    font-family: inherit;
    white-space: pre-wrap;
}

.empty-pane,
.empty-preview,
.mail-skeleton {
    display: grid;
    place-items: center;
    align-content: center;
    gap: 12px;
    min-height: 360px;
    padding: 24px;
    color: #64748b;
}

.mail-skeleton {
    display: grid;
    grid-template-columns: 1fr;
    place-items: stretch;
    align-content: start;
}

.empty-pane :deep(.el-icon),
.empty-preview :deep(.el-icon) {
    color: #94a3b8;
    font-size: 34px;
}

.custom-upload :deep(.el-upload__tip),
.custom-upload :deep(.el-upload__list) {
    display: none;
}

@media (max-width: 1280px) {
    .mail-workspace {
        grid-template-columns: minmax(300px, 360px) minmax(420px, 1fr);
    }

    .preview-panel {
        grid-column: 1 / -1;
        min-height: 420px;
    }

    .preview-body iframe,
    .preview-body pre {
        height: 360px;
    }
}

@media (max-width: 860px) {
    .mail-workspace {
        grid-template-columns: 1fr;
        padding: 10px;
    }

    .mail-toolbar,
    .panel-head {
        align-items: stretch;
        flex-direction: column;
    }

    .mail-actions {
        justify-content: flex-start;
    }

    .mail-title h1 {
        max-width: 100%;
    }
}
</style>
