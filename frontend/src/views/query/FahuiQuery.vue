<template>
  <div class="fahui-query">
    <el-card>
      <template #header>
        <span>法会记录查询</span>
      </template>
      
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="模糊查询">
          <el-input v-model="searchForm.keyword" placeholder="输入关键词查询所有字段" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="法会名称">
          <el-select v-model="searchForm.fahui_name" clearable placeholder="全部" style="width: 150px">
            <el-option v-for="item in fahuiList" :key="item.id" :label="item.法会名称" :value="item.法会名称" />
          </el-select>
        </el-form-item>
        <el-form-item label="施主姓名">
          <el-input v-model="searchForm.shizhu_name" placeholder="输入姓名" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="施主编号">
          <el-input v-model="searchForm.shizhu_code" placeholder="输入编号" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="searchForm.start_date"
            type="date"
            placeholder="开始日期"
            value-format="YYYY-MM-DD"
            style="width: 140px"
          />
          <span style="margin: 0 5px">-</span>
          <el-date-picker
            v-model="searchForm.end_date"
            type="date"
            placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 140px"
          />
        </el-form-item>
        <el-form-item label="牌位类型">
          <el-select v-model="searchForm.paiwei_type" clearable placeholder="全部" style="width: 120px">
            <el-option label="大牌" value="大牌" />
            <el-option label="中牌" value="中牌" />
            <el-option label="小牌" value="小牌" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.yanwang" clearable placeholder="全部" style="width: 120px">
            <el-option label="延生" value="0" />
            <el-option label="往生" value="1" />
          </el-select>
        </el-form-item>
        <el-form-item label="打印状态">
          <el-select v-model="searchForm.prt" clearable placeholder="全部" style="width: 120px">
            <el-option label="未打印" value="0" />
            <el-option label="已打印" value="1" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleExport">导出</el-button>
          <el-button type="warning" @click="handleBatchPrinted(1)" :disabled="selectedRows.length === 0">标记已打印</el-button>
          <el-button type="info" @click="handleBatchPrinted(0)" :disabled="selectedRows.length === 0">标记未打印</el-button>
        </el-form-item>
      </el-form>
      
      <el-table :data="tableData" v-loading="loading" stripe max-height="500" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="施主编号" label="施主编号" width="120" />
        <el-table-column prop="施主姓名" label="施主姓名" width="100" />
        <el-table-column prop="fahui_name" label="法会名称" width="120" />
        <el-table-column prop="paiwei_type" label="牌位类型" width="80" />
        <el-table-column prop="amount" label="金额" width="100">
          <template #default="{ row }">
            {{ row.amount?.toFixed(2) }} 元
          </template>
        </el-table-column>
        <el-table-column prop="yanwang" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.yanwang === 0 ? 'success' : 'danger'">
              {{ row.yanwang === 0 ? '延生' : '往生' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="djdate" label="登记日期" width="110" />
        <el-table-column prop="经办人" label="经办人" width="80">
          <template #default="{ row }">
            {{ row.经办人 || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="prt" label="打印状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.prt === 1 ? 'success' : 'info'">
              {{ row.prt === 1 ? '已打印' : '未打印' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="340" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleDetail(row)">详情</el-button>
            <el-button v-if="row.prt === 0" type="success" link @click="handlePrint(row)">打印</el-button>
            <el-button v-if="row.prt === 1" type="warning" link @click="handlePrint(row)">重新打印</el-button>
            <el-button type="warning" link @click="handleAdd(row)">新增登记</el-button>
            <el-button type="info" link @click="handleEdit(row)">修改</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
      
      <div class="statistics">
        <span>共 {{ total }} 条记录</span>
        <span style="margin-left: 20px">金额合计: {{ totalAmount.toFixed(2) }} 元</span>
      </div>
    </el-card>
    
    <el-dialog v-model="detailVisible" title="法会记录详情" width="500px">
      <el-form label-width="80px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="施主编号">{{ detailData.施主编号 }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="施主姓名">{{ detailData.施主姓名 }}</el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="法会名称">{{ detailData.fahui_name }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="牌位类型">{{ detailData.paiwei_type }}</el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="金额">{{ detailData.amount?.toFixed(2) }} 元</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型">{{ detailData.yanwang === 0 ? '延生' : '往生' }}</el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="登记日期">{{ detailData.djdate }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="经办人">{{ detailData.经办人 || '-' }}</el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="打印状态">{{ detailData.prt === 1 ? '已打印' : '未打印' }}</el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">姓名信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名1">{{ detailData.xm1 || '-' }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名2">{{ detailData.xm2 || '-' }}</el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名3">{{ detailData.xm3 || '-' }}</el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名4">{{ detailData.xm4 || '-' }}</el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="姓名5">{{ detailData.xm5 || '-' }}</el-form-item>
        <el-form-item label="备注">{{ detailData.remarks || '-' }}</el-form-item>
      </el-form>
    </el-dialog>
    
    <PrintPreviewDialog v-model:visible="printVisible" :record="printData" @printed="fetchData">
      <template #footer-extra>
        <el-button type="warning" @click="handleEditFromPrint">修改</el-button>
      </template>
    </PrintPreviewDialog>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑法会登记' : '新增法会登记'"
      width="700px"
      destroy-on-close
    >
      <div v-if="formData.fahui_name || formData.fahui_user_id" class="sticky-info">
        <span v-if="formData.fahui_name" class="info-tag">
          <el-tag type="primary" size="large">{{ formData.fahui_name }}</el-tag>
        </span>
        <span v-if="selectedShizhuName" class="info-tag">
          <el-tag type="success" size="large">{{ selectedShizhuName }}</el-tag>
        </span>
        <el-tag :type="formData.yanwang === '0' ? 'warning' : 'danger'" size="large">
          {{ formData.yanwang === '0' ? '延生' : '往生' }}
        </el-tag>
      </div>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="法会名称" prop="fahui_name">
              <div style="display: flex; gap: 8px;">
                <el-select v-model="formData.fahui_name" style="flex: 1" filterable @change="handleFahuiSelect">
                  <el-option v-for="item in fahuiList" :key="item.id" :label="item.法会名称" :value="item.法会名称" />
                </el-select>
                <el-button type="primary" @click="handleOpenAddFahui">新增</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型" prop="yanwang">
              <el-radio-group v-model="formData.yanwang" @change="handleYanwangChange">
                <el-radio value="0">延生</el-radio>
                <el-radio value="1">往生</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="施主" prop="fahui_user_id">
              <div style="display: flex; gap: 8px;">
                <el-select-v2
                  v-model="formData.fahui_user_id"
                  :options="shizhuOptions"
                  filterable
                  :loading="shizhuLoading"
                  placeholder="搜索选择施主"
                  style="flex: 1"
                  @change="handleShizhuSelect"
                />
                <el-button type="primary" @click="handleOpenAddShizhu">新增</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="牌位类型" prop="paiwei_type">
              <el-select v-model="formData.paiwei_type" style="width: 100%">
                <el-option label="大牌" value="大牌" />
                <el-option label="中牌" value="中牌" />
                <el-option label="小牌" value="小牌" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <template v-if="formData.yanwang === '0'">
          <el-divider content-position="left">佛光注照</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光注照1">
                <el-input v-model="formData.xm1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光注照2">
                <el-input v-model="formData.xm2" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光注照3">
                <el-input v-model="formData.xm3" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光注照4">
                <el-input v-model="formData.xm4" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="佛光注照5">
            <el-input v-model="formData.xm5" />
          </el-form-item>
        </template>

        <template v-else>
          <el-divider content-position="left">佛光接引</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光接引1">
                <el-input v-model="formData.xm1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光接引2">
                <el-input v-model="formData.xm2" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="佛光接引3">
                <el-input v-model="formData.xm3" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="佛光接引4">
                <el-input v-model="formData.xm4" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-divider content-position="left">阳上</el-divider>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="阳上1">
                <el-input v-model="formData.xm5" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="阳上2">
                <el-input v-model="formData.xm6" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="阳上3">
                <el-input v-model="formData.xm7" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="阳上4">
                <el-input v-model="formData.xm8" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="阳上5">
                <el-input v-model="formData.xm9" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="阳上6">
                <el-input v-model="formData.xm10" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        
        <el-divider content-position="left">登记信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="座次">
              <el-input v-model="formData.座次" disabled placeholder="保存后自动生成" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="金额" prop="amount">
              <el-input-number v-model="formData.amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="登记日期">
              <el-date-picker
                v-model="formData.djdate"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="备注">
          <el-input v-model="formData.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="addFahuiDialogVisible"
      title="新增法会"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="addFahuiFormRef"
        :model="addFahuiFormData"
        :rules="addFahuiFormRules"
        label-width="100px"
      >
        <el-form-item label="法会名称" prop="法会名称">
          <el-input v-model="addFahuiFormData.法会名称" placeholder="请输入法会名称" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="addFahuiFormData.开始日期"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="addFahuiFormData.截止日期"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="功德金大">
              <el-input v-model="addFahuiFormData.功德金大" placeholder="金额" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="功德金中">
              <el-input v-model="addFahuiFormData.功德金中" placeholder="金额" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="功德金小">
              <el-input v-model="addFahuiFormData.功德金小" placeholder="金额" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="addFahuiFormData.备注" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addFahuiDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitAddFahui" :loading="addFahuiLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="addShizhuDialogVisible"
      title="新增施主"
      width="700px"
      destroy-on-close
    >
      <el-form
        ref="addShizhuFormRef"
        :model="addShizhuFormData"
        :rules="addShizhuFormRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="施主编号" prop="施主编号">
              <el-input v-model="addShizhuFormData.施主编号" placeholder="自动生成" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="施主姓名" prop="施主姓名">
              <el-input v-model="addShizhuFormData.施主姓名" placeholder="请输入施主姓名" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="addShizhuFormData.电话" placeholder="请输入电话" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="地址">
          <el-input v-model="addShizhuFormData.地址" placeholder="请输入地址" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="功德主">
              <el-switch
                v-model="addShizhuFormData.功德主"
                :active-value="1"
                :inactive-value="0"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">佛光接引</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光接引一">
              <el-input v-model="addShizhuFormData.佛光接引一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光接引二">
              <el-input v-model="addShizhuFormData.佛光接引二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光接引三">
              <el-input v-model="addShizhuFormData.佛光接引三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光接引四">
              <el-input v-model="addShizhuFormData.佛光接引四" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">阳上</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上一">
              <el-input v-model="addShizhuFormData.阳上一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上二">
              <el-input v-model="addShizhuFormData.阳上二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上三">
              <el-input v-model="addShizhuFormData.阳上三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上四">
              <el-input v-model="addShizhuFormData.阳上四" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="阳上五">
              <el-input v-model="addShizhuFormData.阳上五" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阳上六">
              <el-input v-model="addShizhuFormData.阳上六" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">佛光注照</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光注照一">
              <el-input v-model="addShizhuFormData.佛光注照一" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光注照二">
              <el-input v-model="addShizhuFormData.佛光注照二" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="佛光注照三">
              <el-input v-model="addShizhuFormData.佛光注照三" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="佛光注照四">
              <el-input v-model="addShizhuFormData.佛光注照四" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="备注">
          <el-input v-model="addShizhuFormData.备注" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addShizhuDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitAddShizhu" :loading="addShizhuLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fahuiRecordApi } from '@/api/fahuiRecords'
import { fahuiInfoApi } from '@/api/fahuiInfo'
import { fahuiUserApi } from '@/api/fahuiUsers'
import PrintPreviewDialog from '@/components/PrintPreviewDialog.vue'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const fahuiList = ref([])
const shizhuList = ref([])
const shizhuLoading = ref(false)
const shizhuSearchKeyword = ref('')
const total = ref(0)
const totalAmount = ref(0)
const detailVisible = ref(false)
const detailData = ref({})
const printVisible = ref(false)
const printData = ref({})
const selectedRows = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const currentPage = ref(1)
const pageSize = ref(20)

const searchForm = reactive({
  keyword: '',
  fahui_name: '',
  shizhu_name: '',
  shizhu_code: '',
  start_date: '',
  end_date: '',
  paiwei_type: '',
  yanwang: null,
  prt: null
})

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.fahui_name) params.fahui_name = searchForm.fahui_name
    if (searchForm.shizhu_name) params.shizhu_name = searchForm.shizhu_name
    if (searchForm.shizhu_code) params.shizhu_code = searchForm.shizhu_code
    if (searchForm.start_date) params.start_date = searchForm.start_date
    if (searchForm.end_date) params.end_date = searchForm.end_date
    if (searchForm.paiwei_type) params.paiwei_type = searchForm.paiwei_type
    if (searchForm.yanwang !== null && searchForm.yanwang !== '') params.yanwang = searchForm.yanwang
    if (searchForm.prt !== null && searchForm.prt !== '') params.prt = searchForm.prt

    const res = await fahuiRecordApi.queryByFahui(params)
    tableData.value = res.records || []
    total.value = res.total || 0
    totalAmount.value = res.total_amount || 0
  } catch (error) {
    console.error('查询失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchFahuiList = async () => {
  try {
    const res = await fahuiInfoApi.getList()
    fahuiList.value = res
  } catch (error) {
    console.error('获取法会列表失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    fahui_name: '',
    shizhu_name: '',
    shizhu_code: '',
    start_date: '',
    end_date: '',
    paiwei_type: '',
    yanwang: null,
    prt: null
  })
  currentPage.value = 1
  fetchData()
}

const handleExport = async () => {
  if (total.value === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }

  try {
    const params = { skip: 0, limit: 100000 }
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.fahui_name) params.fahui_name = searchForm.fahui_name
    if (searchForm.shizhu_name) params.shizhu_name = searchForm.shizhu_name
    if (searchForm.shizhu_code) params.shizhu_code = searchForm.shizhu_code
    if (searchForm.start_date) params.start_date = searchForm.start_date
    if (searchForm.end_date) params.end_date = searchForm.end_date
    if (searchForm.paiwei_type) params.paiwei_type = searchForm.paiwei_type
    if (searchForm.yanwang !== null && searchForm.yanwang !== '') params.yanwang = searchForm.yanwang
    if (searchForm.prt !== null && searchForm.prt !== '') params.prt = searchForm.prt

    const res = await fahuiRecordApi.queryByFahui(params)
    const exportData = res.records || []

    if (exportData.length === 0) {
      ElMessage.warning('没有数据可导出')
      return
    }

    const headers = ['施主编号', '施主姓名', '法会名称', '牌位类型', '金额', '类型', '登记日期', '经办人', '打印状态', '姓名1', '姓名2', '姓名3', '姓名4', '姓名5', '备注']
    const rows = exportData.map(item => [
      item.施主编号 || '',
      item.施主姓名 || '',
      item.fahui_name || '',
      item.paiwei_type || '',
      item.amount || 0,
      item.yanwang === 0 ? '延生' : '往生',
      item.djdate || '',
      item.经办人 || '',
      item.prt === 1 ? '已打印' : '未打印',
      item.xm1 || '',
      item.xm2 || '',
      item.xm3 || '',
      item.xm4 || '',
      item.xm5 || '',
      item.remarks || ''
    ])

    let csvContent = '\uFEFF' + headers.join(',') + '\n'
    rows.forEach(row => {
      csvContent += row.map(cell => `"${cell}"`).join(',') + '\n'
    })

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `法会记录查询_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}

const handleEditFromPrint = () => {
  printVisible.value = false
  handleEdit(printData.value)
}

const handleEdit = async (row) => {
  resetForm()
  isEdit.value = true
  if (fahuiList.value.length === 0) {
    await fetchFahuiList()
  }
  await fetchShizhuList()
  const fahui = fahuiList.value.find(item => item.法会名称 === row.fahui_name)
  Object.assign(formData, {
    id: row.id,
    fahui_id: fahui ? fahui.id : (row.fahui_id || ''),
    fahui_name: row.fahui_name || '',
    fahui_user_id: row.fahui_user_id || null,
    xm1: row.xm1 || '',
    xm2: row.xm2 || '',
    xm3: row.xm3 || '',
    xm4: row.xm4 || '',
    xm5: row.xm5 || '',
    xm6: row.xm6 || '',
    xm7: row.xm7 || '',
    xm8: row.xm8 || '',
    xm9: row.xm9 || '',
    xm10: row.xm10 || '',
    paiwei_type: row.paiwei_type || '中牌',
    yanwang: row.yanwang !== undefined ? String(row.yanwang) : '0',
    amount: row.amount || 0,
    djdate: row.djdate || '',
    remarks: row.remarks || ''
  })
  if (row.fahui_user_id && !shizhuList.value.find(item => item.id === row.fahui_user_id)) {
    shizhuList.value.unshift({
      id: row.fahui_user_id,
      施主编号: row.施主编号 || '',
      施主姓名: row.施主姓名 || ''
    })
  }
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该法会登记记录吗？', '提示', {
      type: 'warning'
    })
    await fahuiRecordApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleDetail = (row) => {
  detailData.value = row
  detailVisible.value = true
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const handleBatchPrinted = async (prtStatus) => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要操作的记录')
    return
  }

  const statusText = prtStatus === 1 ? '已打印' : '未打印'
  try {
    await ElMessageBox.confirm(`确定要将选中的 ${selectedRows.value.length} 条记录标记为${statusText}吗？`, '提示', {
      type: 'warning'
    })

    let successCount = 0
    let failCount = 0

    for (const row of selectedRows.value) {
      try {
        await fahuiRecordApi.update(row.id, { prt: prtStatus })
        successCount++
      } catch (error) {
        failCount++
        console.error(`更新记录 ${row.id} 失败:`, error)
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功标记 ${successCount} 条记录为${statusText}`)
      fetchData()
    }
    if (failCount > 0) {
      ElMessage.warning(`${failCount} 条记录标记失败`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量操作失败:', error)
    }
  }
}

const handlePrint = (row) => {
  printData.value = row
  printVisible.value = true
}

const formData = reactive({
  id: null,
  fahui_id: '',
  fahui_name: '',
  fahui_user_id: null,
  座次: '',
  xm1: '',
  xm2: '',
  xm3: '',
  xm4: '',
  xm5: '',
  xm6: '',
  xm7: '',
  xm8: '',
  xm9: '',
  xm10: '',
  paiwei_type: '中牌',
  yanwang: '0',
  amount: 0,
  djdate: '',
  prt: '0',
  remarks: ''
})

const formRules = {
  fahui_name: [{ required: true, message: '请选择法会', trigger: 'change' }],
  fahui_user_id: [{ required: true, message: '请选择施主', trigger: 'change' }],
  paiwei_type: [{ required: true, message: '请选择牌位类型', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }]
}

const selectedShizhuName = computed(() => {
  if (!formData.fahui_user_id) return ''
  const shizhu = shizhuList.value.find(item => item.id === formData.fahui_user_id)
  return shizhu ? `${shizhu.施主姓名} (${shizhu.施主编号})` : ''
})

const shizhuOptions = computed(() =>
  shizhuList.value.map(item => ({
    value: item.id,
    label: `${item.施主姓名} (${item.施主编号})`
  }))
)

const fetchShizhuList = async (keyword = '') => {
  shizhuLoading.value = true
  try {
    const res = await fahuiUserApi.getList(keyword || undefined, 10000)
    shizhuList.value = res
  } catch (error) {
    console.error('获取施主列表失败:', error)
  } finally {
    shizhuLoading.value = false
  }
}

const handleShizhuSearch = (query) => {
  shizhuSearchKeyword.value = query
  fetchShizhuList(query)
}

const resetForm = () => {
  const today = new Date().toISOString().split('T')[0]
  Object.assign(formData, {
    id: null,
    fahui_id: '',
    fahui_name: '',
    fahui_user_id: null,
    座次: '',
    xm1: '',
    xm2: '',
    xm3: '',
    xm4: '',
    xm5: '',
    xm6: '',
    xm7: '',
    xm8: '',
    xm9: '',
    xm10: '',
    paiwei_type: '中牌',
    yanwang: '0',
    amount: 0,
    djdate: today,
    prt: '0',
    remarks: ''
  })
}

const handleAdd = async (row) => {
  resetForm()
  isEdit.value = false
  if (fahuiList.value.length === 0) {
    await fetchFahuiList()
  }
  await fetchShizhuList()
  if (row) {
    const fahui = fahuiList.value.find(item => item.法会名称 === row.fahui_name)
    Object.assign(formData, {
      fahui_id: fahui ? fahui.id : (row.fahui_id || ''),
      fahui_name: row.fahui_name || '',
      fahui_user_id: row.fahui_user_id || null,
      xm1: row.xm1 || '',
      xm2: row.xm2 || '',
      xm3: row.xm3 || '',
      xm4: row.xm4 || '',
      xm5: row.xm5 || '',
      xm6: row.xm6 || '',
      xm7: row.xm7 || '',
      xm8: row.xm8 || '',
      xm9: row.xm9 || '',
      xm10: row.xm10 || '',
      paiwei_type: row.paiwei_type || '中牌',
      yanwang: row.yanwang !== undefined ? String(row.yanwang) : '0',
      amount: row.amount || 0
    })
    if (row.fahui_user_id && !shizhuList.value.find(item => item.id === row.fahui_user_id)) {
      shizhuList.value.unshift({
        id: row.fahui_user_id,
        施主编号: row.施主编号 || '',
        施主姓名: row.施主姓名 || ''
      })
    }
  }
  dialogVisible.value = true
}

const handleFahuiSelect = (val) => {
  const fahui = fahuiList.value.find(item => item.法会名称 === val)
  if (fahui) {
    formData.fahui_id = fahui.id
  }
}

const handleShizhuSelect = (val) => {
  if (!val) {
    formData.xm1 = ''
    formData.xm2 = ''
    formData.xm3 = ''
    formData.xm4 = ''
    formData.xm5 = ''
    formData.xm6 = ''
    formData.xm7 = ''
    formData.xm8 = ''
    formData.xm9 = ''
    formData.xm10 = ''
    return
  }
  const shizhu = shizhuList.value.find(item => item.id === val)
  if (shizhu) {
    fillNamesFromShizhu(shizhu)
  }
}

const handleYanwangChange = () => {
  formData.xm1 = ''
  formData.xm2 = ''
  formData.xm3 = ''
  formData.xm4 = ''
  formData.xm5 = ''
  formData.xm6 = ''
  formData.xm7 = ''
  formData.xm8 = ''
  formData.xm9 = ''
  formData.xm10 = ''
  if (formData.fahui_user_id) {
    const shizhu = shizhuList.value.find(item => item.id === formData.fahui_user_id)
    if (shizhu) {
      fillNamesFromShizhu(shizhu)
    }
  }
}

const fillNamesFromShizhu = (shizhu) => {
  if (formData.yanwang === '0') {
    formData.xm1 = shizhu.佛光注照一 || ''
    formData.xm2 = shizhu.佛光注照二 || ''
    formData.xm3 = shizhu.佛光注照三 || ''
    formData.xm4 = shizhu.佛光注照四 || ''
    formData.xm5 = ''
    formData.xm6 = ''
    formData.xm7 = ''
    formData.xm8 = ''
    formData.xm9 = ''
    formData.xm10 = ''
  } else {
    formData.xm1 = shizhu.佛光接引一 || ''
    formData.xm2 = shizhu.佛光接引二 || ''
    formData.xm3 = shizhu.佛光接引三 || ''
    formData.xm4 = shizhu.佛光接引四 || ''
    formData.xm5 = shizhu.阳上一 || ''
    formData.xm6 = shizhu.阳上二 || ''
    formData.xm7 = shizhu.阳上三 || ''
    formData.xm8 = shizhu.阳上四 || ''
    formData.xm9 = shizhu.阳上五 || ''
    formData.xm10 = shizhu.阳上六 || ''
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const submitData = {
          fahui_user_id: formData.fahui_user_id,
          fahui_id: formData.fahui_id || null,
          fahui_name: formData.fahui_name || null,
          xm1: formData.xm1 || null,
          xm2: formData.xm2 || null,
          xm3: formData.xm3 || null,
          xm4: formData.xm4 || null,
          xm5: formData.xm5 || null,
          xm6: formData.xm6 || null,
          xm7: formData.xm7 || null,
          xm8: formData.xm8 || null,
          xm9: formData.xm9 || null,
          xm10: formData.xm10 || null,
          xm: formData.yanwang === '0' ? '佛光注照' : '佛光接引',
          paiwei_type: formData.paiwei_type || null,
          yanwang: parseInt(formData.yanwang),
          amount: parseFloat(formData.amount) || 0,
          djdate: formData.djdate || null,
          prt: parseInt(formData.prt),
          remarks: formData.remarks || null
        }
        if (isEdit.value) {
          await fahuiRecordApi.update(formData.id, submitData)
          ElMessage.success('更新成功')
        } else {
          await fahuiRecordApi.create(submitData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchData()
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error('操作失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const addFahuiDialogVisible = ref(false)
const addFahuiLoading = ref(false)
const addFahuiFormRef = ref(null)
const addFahuiFormData = reactive({
  法会名称: '',
  开始日期: '',
  截止日期: '',
  功德金大: '',
  功德金中: '',
  功德金小: '',
  备注: ''
})

const addFahuiFormRules = {
  法会名称: [{ required: true, message: '请输入法会名称', trigger: 'blur' }]
}

const handleOpenAddFahui = () => {
  Object.assign(addFahuiFormData, {
    法会名称: '',
    开始日期: '',
    截止日期: '',
    功德金大: '',
    功德金中: '',
    功德金小: '',
    备注: ''
  })
  addFahuiDialogVisible.value = true
}

const handleSubmitAddFahui = async () => {
  if (!addFahuiFormRef.value) return

  await addFahuiFormRef.value.validate(async (valid) => {
    if (valid) {
      addFahuiLoading.value = true
      try {
        await fahuiInfoApi.create(addFahuiFormData)
        ElMessage.success('法会创建成功')
        addFahuiDialogVisible.value = false
        await fetchFahuiList()
        formData.fahui_name = addFahuiFormData.法会名称
        const fahui = fahuiList.value.find(item => item.法会名称 === addFahuiFormData.法会名称)
        if (fahui) {
          formData.fahui_id = fahui.id
        }
      } catch (error) {
        console.error('创建法会失败:', error)
        ElMessage.error('创建法会失败')
      } finally {
        addFahuiLoading.value = false
      }
    }
  })
}

const addShizhuDialogVisible = ref(false)
const addShizhuLoading = ref(false)
const addShizhuFormRef = ref(null)
const addShizhuFormData = reactive({
  施主编号: '',
  施主姓名: '',
  电话: '',
  地址: '',
  功德主: 1,
  佛光接引一: '',
  佛光接引二: '',
  佛光接引三: '',
  佛光接引四: '',
  阳上一: '',
  阳上二: '',
  阳上三: '',
  阳上四: '',
  阳上五: '',
  阳上六: '',
  佛光注照一: '',
  佛光注照二: '',
  佛光注照三: '',
  佛光注照四: '',
  备注: ''
})

const addShizhuFormRules = {
  施主姓名: [{ required: true, message: '请输入施主姓名', trigger: 'blur' }]
}

const handleOpenAddShizhu = async () => {
  Object.assign(addShizhuFormData, {
    施主编号: '',
    施主姓名: '',
    电话: '',
    地址: '',
    功德主: 1,
    佛光接引一: '',
    佛光接引二: '',
    佛光接引三: '',
    佛光接引四: '',
    阳上一: '',
    阳上二: '',
    阳上三: '',
    阳上四: '',
    阳上五: '',
    阳上六: '',
    佛光注照一: '',
    佛光注照二: '',
    佛光注照三: '',
    佛光注照四: '',
    备注: ''
  })
  try {
    const res = await fahuiUserApi.generateCode()
    addShizhuFormData.施主编号 = res.code
  } catch (error) {
    console.error('生成编号失败:', error)
  }
  addShizhuDialogVisible.value = true
}

const handleSubmitAddShizhu = async () => {
  if (!addShizhuFormRef.value) return

  await addShizhuFormRef.value.validate(async (valid) => {
    if (valid) {
      addShizhuLoading.value = true
      try {
        await fahuiUserApi.create(addShizhuFormData)
        ElMessage.success('施主创建成功')
        addShizhuDialogVisible.value = false
        await fetchShizhuList(shizhuSearchKeyword.value)
        const newShizhu = shizhuList.value.find(item => item.施主编号 === addShizhuFormData.施主编号)
        if (newShizhu) {
          formData.fahui_user_id = newShizhu.id
          fillNamesFromShizhu(newShizhu)
        }
      } catch (error) {
        console.error('创建施主失败:', error)
        ElMessage.error('创建施主失败')
      } finally {
        addShizhuLoading.value = false
      }
    }
  })
}

onMounted(() => {
  fetchFahuiList()
  fetchShizhuList()
  fetchData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.statistics {
  margin-top: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
}

.print-preview {
  padding: 20px;
  border: 1px solid #ddd;
  background: #fff;
}

.print-header {
  text-align: center;
  margin-bottom: 20px;
}

.print-header h2 {
  margin: 0;
  font-size: 24px;
}

.print-header h3 {
  margin: 10px 0 0;
  font-size: 18px;
  color: #666;
}

.print-body {
  font-size: 16px;
}

.print-row {
  margin: 10px 0;
}

.print-row .label {
  font-weight: bold;
}

.print-names {
  margin: 20px 0;
  padding: 15px;
  border: 1px solid #ddd;
  text-align: center;
}

.names-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
}

.names-list {
  font-size: 20px;
}

.names-list span {
  margin: 0 10px;
}

.sticky-info {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #fff;
  padding: 10px 16px;
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-tag {
  display: inline-flex;
}
</style>
