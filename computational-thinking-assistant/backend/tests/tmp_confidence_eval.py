# -*- coding: utf-8 -*-
import json
import logging
import os
from statistics import mean

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# 尽量降低第三方噪音日志
for name in [
    "httpx",
    "urllib3",
    "sentence_transformers",
    "chromadb",
    "sqlalchemy.engine",
    "services.vector_service",
]:
    logging.getLogger(name).setLevel(logging.ERROR)

from config import Config
from utils.question_classifier import classify_question
from services.vector_service import get_vector_service

questions = [
    ("高", "什么是一维数组？在内存中如何存储？"),
    ("高", "C 语言中数组下标为什么从 0 开始？越界会有什么后果？"),
    ("高", "二维数组在 C 语言中是按行优先还是按列优先存储？"),
    ("高", "数组作为函数参数时，传递的是数组本身还是首地址？"),
    ("高", "指针变量如何声明和初始化？空指针为什么危险？"),
    ("高", "arr[i] 与 *(arr+i) 为什么等价？"),
    ("高", "malloc、calloc、realloc、free 的作用分别是什么？"),
    ("高", "fopen 常见模式 r、w、a、r+ 的区别是什么？"),
    ("高", "fread/fwrite 和 fscanf/fprintf 分别适合什么场景？"),
    ("高", "常见段错误（Segmentation Fault）的排查步骤是什么？"),

    ("中", "C23 的 typeof_unqual 与 GCC 的 typeof 在教学中如何兼容讲解？"),
    ("中", "const int *p、int *const p、const int *const p 的差异是什么？"),
    ("中", "qsort 的比较函数该如何写，才能避免比较器错误？"),
    ("中", "为什么数组传参后 sizeof 结果会变？应如何正确获取长度？"),
    ("中", "结构体内存对齐和填充会如何影响 sizeof 与二进制文件读写？"),
    ("中", "二分查找里 mid=(l+r)/2 有什么潜在风险？如何改写更稳妥？"),
    ("中", "函数指针在回调场景中的教学示例可以怎么设计？"),
    ("中", "多级指针在动态二维数组分配中如何避免内存泄漏？"),
    ("中", "AddressSanitizer 和 Valgrind 在课堂演示中如何分工使用？"),
    ("中", "文本文件与二进制文件在跨平台场景下的差异如何解释给学生？"),

    ("低", "Vue3 响应式系统的核心原理是什么？"),
    ("低", "Spring 事务传播行为有哪几种，如何选择？"),
    ("低", "Redis Cluster 的槽位迁移机制是怎样的？"),
    ("低", "TensorFlow 里反向传播自动求导是如何实现的？"),
    ("低", "Kubernetes 的 Service Mesh 为什么会引入额外延迟？"),
    ("低", "Rust 所有权和借用检查器的核心设计哲学是什么？"),
    ("低", "Solidity 合约如何防范重入攻击？"),
    ("低", "CUDA 中 warp divergence 为什么会降低性能？"),
    ("低", "Spark Shuffle 的代价主要来自哪里？"),
    ("低", "量子纠错码与经典纠错码的本质差异是什么？"),
]

vector = get_vector_service()

results = []

for i, (group, q) in enumerate(questions, start=1):
    c = classify_question(q)
    needs_rag = bool(c.get("needs_rag", True))
    qtype = c.get("category", "general")
    suggested_threshold = c.get("threshold")

    rag_mode = "none"
    mode = "ordinary"
    max_score = 0.0
    raw_count = 0
    used_count = 0
    top_ids = []

    if needs_rag:
        top_k = c.get("top_k", 5)
        raw = vector.search(query=q, top_k=top_k, threshold=suggested_threshold)
        raw_count = len(raw)
        top_ids = [str((d.get("chunk_id") or "")) for d in raw[:3]]

        if raw_count > 0:
            max_score = max(float(d.get("score", 0.0)) for d in raw)
            if max_score >= 0.80:
                rag_mode = "high"
                used = [d for d in raw if float(d.get("score", 0.0)) >= 0.60]
            elif max_score >= float(suggested_threshold or 0.60):
                rag_mode = "medium"
                used = [d for d in raw if float(d.get("score", 0.0)) >= float(suggested_threshold or 0.60)]
            else:
                rag_mode = "low"
                used = []
            used_count = len(used)
        else:
            rag_mode = "none"

        mode = "rag" if rag_mode in ("high", "medium") else "ordinary"
        confidence_mode = rag_mode if rag_mode in ("high", "medium", "low") else "none"
    else:
        confidence_mode = "none"

    results.append({
        "idx": i,
        "group": group,
        "question": q,
        "question_type": qtype,
        "needs_rag": needs_rag,
        "mode": mode,
        "confidence_mode": confidence_mode,
        "max_score": round(max_score, 4),
        "raw_result_count": raw_count,
        "used_result_count": used_count,
        "suggested_threshold": suggested_threshold,
        "effective_search_threshold": Config.SIMILARITY_THRESHOLD,
        "top_chunk_ids": top_ids,
    })

# 打印可读表
print("\n=== EVAL_TABLE_BEGIN ===")
print("idx\t组别\t是否RAG\t置信度\tmax_score\traw\tused\tquestion")
for r in results:
    print(f"{r['idx']}\t{r['group']}\t{r['mode']}\t{r['confidence_mode']}\t{r['max_score']}\t{r['raw_result_count']}\t{r['used_result_count']}\t{r['question']}")
print("=== EVAL_TABLE_END ===\n")

# 分组统计
for g in ["高", "中", "低"]:
    sub = [x for x in results if x["group"] == g]
    rag_n = sum(1 for x in sub if x["mode"] == "rag")
    high_n = sum(1 for x in sub if x["confidence_mode"] == "high")
    med_n = sum(1 for x in sub if x["confidence_mode"] == "medium")
    low_n = sum(1 for x in sub if x["confidence_mode"] == "low")
    avg_score = round(mean([x["max_score"] for x in sub]), 4)
    print(f"组别[{g}] => rag={rag_n}/{len(sub)}, high={high_n}, medium={med_n}, low={low_n}, avg_max_score={avg_score}")

print("\n=== EVAL_JSON_BEGIN ===")
print(json.dumps(results, ensure_ascii=False, indent=2))
print("=== EVAL_JSON_END ===")
