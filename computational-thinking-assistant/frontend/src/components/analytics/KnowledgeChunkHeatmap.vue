<template>
  <div class="chunk-heatmap">
    <div v-if="!data || !data.chunks || data.chunks.length === 0" class="empty-state">
      <div class="empty-icon">📚</div>
      <h3>暂无引用数据</h3>
      <p>知识库被引用后将显示热度统计</p>
    </div>
    <div v-else>
      <!-- 汇总信息 -->
      <div class="summary-bar">
        <span class="summary-item">
          <strong>{{ data.total_retrieved }}</strong> 次总引用
        </span>
        <span class="summary-item">
          <strong>{{ data.total_chunks }}</strong> 个知识块上榜
        </span>
      </div>
      <!-- 热度排行列表 -->
      <div class="chunk-list">
        <div
          v-for="(chunk, index) in data.chunks"
          :key="chunk.id"
          class="chunk-row"
        >
          <div class="rank-badge" :class="getRankClass(index)">{{ index + 1 }}</div>
          <div class="chunk-info">
            <div class="chunk-name">
              <span class="source-tag">{{ chunk.source }}</span>
              <span class="chapter-text">{{ chunk.chapter }}</span>
              <span v-if="chunk.section" class="section-text"> / {{ chunk.section }}</span>
              <span v-if="chunk.has_code" class="code-badge">含代码</span>
            </div>
            <div class="heat-bar-wrap">
              <div
                class="heat-bar"
                :style="{ width: chunk.heat_rate + '%' }"
                :title="`引用占比 ${chunk.heat_rate}%`"
              ></div>
            </div>
          </div>
          <div class="chunk-count">
            <span class="count-num">{{ chunk.retrieved_count }}</span>
            <span class="count-label">次</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: {
    type: Object,
    default: () => null,
  },
});

function getRankClass(index) {
  if (index === 0) return "gold";
  if (index === 1) return "silver";
  if (index === 2) return "bronze";
  return "";
}
</script>

<style scoped>
.chunk-heatmap { display: flex; flex-direction: column; gap: 12px; }
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; color: #999; padding: 40px 0; }
.empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.5; }
.summary-bar { display: flex; gap: 24px; padding: 12px 16px; background: #f5f7fa; border-radius: 8px; }
.summary-item { font-size: 14px; color: #555; }
.summary-item strong { color: #667eea; font-size: 18px; margin-right: 4px; }
.chunk-list { display: flex; flex-direction: column; gap: 8px; }
.chunk-row { display: flex; align-items: center; gap: 12px; padding: 10px 12px; background: #fafbfc; border-radius: 8px; border: 1px solid #f0f0f0; }
.rank-badge { width: 26px; height: 26px; border-radius: 50%; background: #667eea; color: white; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; flex-shrink: 0; }
.rank-badge.gold { background: #ffd700; color: #333; }
.rank-badge.silver { background: #c0c0c0; color: #333; }
.rank-badge.bronze { background: #cd7f32; color: white; }
.chunk-info { flex: 1; min-width: 0; }
.chunk-name { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; font-size: 13px; }
.source-tag { background: #e8f0fe; color: #667eea; padding: 2px 8px; border-radius: 10px; font-size: 11px; flex-shrink: 0; }
.chapter-text { font-weight: 600; color: #333; }
.section-text { color: #666; }
.code-badge { background: #e6f4ea; color: #34a853; padding: 2px 6px; border-radius: 10px; font-size: 11px; }
.heat-bar-wrap { height: 6px; background: #ebedf0; border-radius: 3px; overflow: hidden; }
.heat-bar { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 3px; transition: width 0.5s ease; min-width: 2px; }
.chunk-count { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }
.count-num { font-size: 18px; font-weight: bold; color: #667eea; line-height: 1; }
.count-label { font-size: 11px; color: #999; }
</style>
