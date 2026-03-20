# -*- coding: utf-8 -*-
"""
Mini DB Query - 管理平台前端更新脚本
用途: 为管理平台添加业务大类、模板权限等功能
"""

import re

ADMIN_FILE = '/root/projects/mini-db-query/backend/admin/index.html'

def read_file():
    with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(content):
    with open(ADMIN_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

def update_admin():
    content = read_file()
    
    # 1. 添加业务大类管理页面的数据和方法
    # 在 templates 相关变量后添加 categories 变量
    
    # 找到 const templates = ref([]); 后面添加 categories 相关变量
    categories_vars = '''
                // 业务大类
                const categories = ref([]);
                const categorySearch = reactive({ school_id: null });
                const categoryDialogVisible = ref(false);
                const categoryForm = reactive({
                    id: null,
                    school_id: null,
                    code: '',
                    name: '',
                    icon: '',
                    sort_order: 0,
                    description: ''
                });
                const categoryFormRef = ref(null);
'''
    
    if 'const categories = ref([]);' not in content:
        # 在 templates 变量后添加
        content = content.replace(
            'const templates = ref([]);',
            'const templates = ref([]);' + categories_vars
        )
    
    # 2. 添加筛选后的数据库和分类计算属性
    computed_props = '''
                // 筛选后的数据库列表（根据选择的学校）
                const filteredDatabases = computed(() => {
                    if (!templateForm.school_id) return databases.value;
                    return databases.value.filter(db => db.school_id === templateForm.school_id);
                });
                
                // 筛选后的业务大类列表（根据选择的学校）
                const filteredCategories = computed(() => {
                    if (!templateForm.school_id) return categories.value;
                    return categories.value.filter(cat => cat.school_id === templateForm.school_id);
                });
'''
    
    if 'filteredDatabases' not in content:
        # 在 currentMenuName 计算属性后添加
        content = content.replace(
            "return item ? item.name : '';",
            "return item ? item.name : '';" + computed_props
        )
    
    # 3. 添加业务大类管理方法
    category_methods = '''
                // 业务大类管理
                const loadCategories = async () => {
                    const params = new URLSearchParams();
                    if (categorySearch.school_id) params.append('school_id', categorySearch.school_id);
                    try {
                        const res = await request(`/categories?${params}`);
                        if (res.code === 200) {
                            categories.value = res.data || [];
                        }
                    } catch (e) {
                        console.error('加载业务大类失败:', e);
                    }
                };
                
                const showCategoryDialog = (category) => {
                    if (category) {
                        categoryForm.id = category.id;
                        categoryForm.school_id = category.school_id;
                        categoryForm.code = category.code;
                        categoryForm.name = category.name;
                        categoryForm.icon = category.icon || '';
                        categoryForm.sort_order = category.sort_order || 0;
                        categoryForm.description = category.description || '';
                    } else {
                        categoryForm.id = null;
                        categoryForm.school_id = null;
                        categoryForm.code = '';
                        categoryForm.name = '';
                        categoryForm.icon = '';
                        categoryForm.sort_order = 0;
                        categoryForm.description = '';
                    }
                    categoryDialogVisible.value = true;
                };
                
                const handleSaveCategory = async () => {
                    const url = categoryForm.id ? `/categories/${categoryForm.id}` : '/categories';
                    const method = categoryForm.id ? 'PUT' : 'POST';
                    try {
                        const res = await request(url, {
                            method,
                            body: JSON.stringify(categoryForm)
                        });
                        if (res.code === 200) {
                            ElMessage.success('保存成功');
                            categoryDialogVisible.value = false;
                            loadCategories();
                        } else {
                            ElMessage.error(res.message || '保存失败');
                        }
                    } catch (e) {
                        ElMessage.error('保存失败: ' + e.message);
                    }
                };
                
                const handleDeleteCategory = async (category) => {
                    try {
                        await ElMessageBox.confirm('确定删除该业务大类吗？', '确认删除', { type: 'warning' });
                        const res = await request(`/categories/${category.id}`, { method: 'DELETE' });
                        if (res.code === 200) {
                            ElMessage.success('删除成功');
                            loadCategories();
                        } else {
                            ElMessage.error(res.message || '删除失败');
                        }
                    } catch (e) {
                        if (e !== 'cancel') {
                            ElMessage.error('删除失败: ' + e.message);
                        }
                    }
                };
                
                // 模板学校变化时加载对应数据
                const onTemplateSchoolChange = () => {
                    templateForm.database_id = null;
                    templateForm.category_id = null;
                };
                
                // 分类变化时更新编码和名称（兼容）
                const onCategoryChange = (categoryId) => {
                    const cat = categories.value.find(c => c.id === categoryId);
                    if (cat) {
                        templateForm.category = cat.code;
                        templateForm.category_name = cat.name;
                        templateForm.category_icon = cat.icon;
                    }
                };
'''
    
    if 'const loadCategories = async' not in content:
        # 在 loadTemplates 方法前添加
        content = content.replace(
            'const loadTemplates = async',
            category_methods + '\n                const loadTemplates = async'
        )
    
    # 4. 更新 templateForm 添加新字段
    if 'templateForm.database_id' not in content:
        content = content.replace(
            '''const templateForm = reactive({
                    id: null,
                    school_id: null,
                    category: '',''',
            '''const templateForm = reactive({
                    id: null,
                    school_id: null,
                    database_id: null,
                    category_id: null,
                    version: 'v1.0.0',
                    category: '','''
        )
    
    # 5. 更新 showTemplateDialog 方法
    if 'templateForm.database_id = template.database_id' not in content:
        content = content.replace(
            '''templateForm.id = template.id;
                        templateForm.school_id = template.school_id;''',
            '''templateForm.id = template.id;
                        templateForm.school_id = template.school_id;
                        templateForm.database_id = template.database_id;
                        templateForm.category_id = template.category_id;
                        templateForm.version = template.version || 'v1.0.0';'''
        )
    
    # 6. 添加业务大类对话框 HTML
    category_dialog = '''
        <!-- 业务大类对话框 -->
        <el-dialog v-model="categoryDialogVisible" :title="categoryForm.id ? '✏️ 编辑业务大类' : '➕ 新增业务大类'" width="500px">
            <el-form :model="categoryForm" ref="categoryFormRef" label-width="100px">
                <el-form-item label="所属学校" required>
                    <el-select v-model="categoryForm.school_id" placeholder="选择学校" style="width: 100%">
                        <el-option 
                            v-for="school in schools" 
                            :key="school.id" 
                            :label="school.name" 
                            :value="school.id"
                        ></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item label="编码" required>
                    <el-input v-model="categoryForm.code" placeholder="如: consume"></el-input>
                </el-form-item>
                <el-form-item label="名称" required>
                    <el-input v-model="categoryForm.name" placeholder="如: 消费业务"></el-input>
                </el-form-item>
                <el-form-item label="图标">
                    <el-input v-model="categoryForm.icon" placeholder="如: 💰"></el-input>
                </el-form-item>
                <el-form-item label="排序">
                    <el-input-number v-model="categoryForm.sort_order" :min="0" style="width: 100%"></el-input-number>
                </el-form-item>
                <el-form-item label="描述">
                    <el-input v-model="categoryForm.description" type="textarea" :rows="2"></el-input>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="categoryDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSaveCategory">保存</el-button>
            </template>
        </el-dialog>

'''
    
    if '<!-- 业务大类对话框 -->' not in content:
        # 在模板对话框后添加
        content = content.replace(
            '</el-dialog>\n\n        <!-- 权限对话框 -->',
            '</el-dialog>' + category_dialog + '        <!-- 权限对话框 -->'
        )
    
    # 7. 更新模板列表显示数据库和版本
    if 'database_id' not in content or 'templateForm.database_id' not in content:
        # 添加数据库列显示
        content = content.replace(
            '<el-table-column prop="category_name" label="业务大类" width="120">',
            '''<el-table-column label="数据库" width="120">
                                <template #default="{ row }">
                                    <span v-if="row.database_id">{{ getDatabaseName(row.database_id) }}</span>
                                    <span v-else style="color: #999;">未配置</span>
                                </template>
                            </el-table-column>
                            <el-table-column prop="category_name" label="业务大类" width="120">'''
        )
    
    # 8. 添加导出
    if 'categories,' not in content:
        content = content.replace(
            'templates,',
            'templates,\n                    categories,'
        )
    
    if 'loadCategories,' not in content:
        content = content.replace(
            'loadTemplates,',
            'loadCategories,\n                    loadTemplates,'
        )
    
    if 'showCategoryDialog,' not in content:
        content = content.replace(
            'showTemplateDialog,',
            'showCategoryDialog,\n                    showTemplateDialog,'
        )
    
    if 'handleSaveCategory,' not in content:
        content = content.replace(
            'handleSaveTemplate,',
            'handleSaveCategory,\n                    handleSaveTemplate,'
        )
    
    if 'handleDeleteCategory,' not in content:
        content = content.replace(
            'handleDeleteTemplate,',
            'handleDeleteCategory,\n                    handleDeleteTemplate,'
        )
    
    if 'categoryDialogVisible,' not in content:
        content = content.replace(
            'templateDialogVisible,',
            'categoryDialogVisible,\n                    templateDialogVisible,'
        )
    
    if 'categoryForm,' not in content:
        content = content.replace(
            'templateForm,',
            'categoryForm,\n                    templateForm,'
        )
    
    if 'filteredDatabases,' not in content:
        content = content.replace(
            'templates,',
            'templates,\n                    filteredDatabases,\n                    filteredCategories,'
        )
    
    if 'onTemplateSchoolChange,' not in content:
        content = content.replace(
            'onTemplateSchoolChange,',
            'onTemplateSchoolChange,'
        )
    
    if 'onCategoryChange,' not in content:
        content = content.replace(
            'onCategoryChange,',
            'onCategoryChange,'
        )
    
    # 添加 categorySearch
    if 'categorySearch,' not in content:
        content = content.replace(
            'templateSearch,',
            'categorySearch,\n                    templateSearch,'
        )
    
    write_file(content)
    print("✅ 管理平台前端更新完成")


if __name__ == '__main__':
    update_admin()
