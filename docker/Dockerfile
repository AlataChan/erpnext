# ============================================
# ERPNext 自定义Docker镜像
# 德川/裕霖业务管理系统
# ============================================
# 直接使用本地 ERPNext v16 代码构建
# 不依赖官方远程仓库
# ============================================

# ==================== 构建参数 ====================
ARG FRAPPE_VERSION=version-16

# ==================== 构建阶段 ====================
FROM frappe/bench:latest AS builder

# 设置环境变量
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER frappe
WORKDIR /home/frappe

# ==================== 初始化 Bench（只安装 Frappe，不安装 ERPNext）====================
ARG FRAPPE_VERSION
RUN bench init \
    --skip-redis-config-generation \
    --frappe-branch ${FRAPPE_VERSION} \
    frappe-bench

WORKDIR /home/frappe/frappe-bench

# ==================== 复制本地 ERPNext 代码 ====================
# 先创建目录结构
RUN mkdir -p apps/erpnext

# 复制所有必要文件（保持完整的项目结构）
# 注意：pyproject.toml 引用了 README.md，必须同时复制
COPY --chown=frappe:frappe ./pyproject.toml ./apps/erpnext/
COPY --chown=frappe:frappe ./package.json ./apps/erpnext/
COPY --chown=frappe:frappe ./yarn.lock ./apps/erpnext/
COPY --chown=frappe:frappe ./README.md ./apps/erpnext/
COPY --chown=frappe:frappe ./erpnext ./apps/erpnext/erpnext

# ==================== 安装 ERPNext 到 Bench ====================
# 注册应用到 apps.txt（确保在新行添加，避免与 frappe 连在一起）
RUN printf '\nerpnext\n' >> sites/apps.txt && \
    cat sites/apps.txt && \
    echo "--- apps.txt 内容确认 ---"

# 安装 Python 依赖
RUN ./env/bin/pip install -e apps/erpnext

# 安装前端依赖
WORKDIR /home/frappe/frappe-bench/apps/erpnext
RUN yarn install --frozen-lockfile || yarn install

WORKDIR /home/frappe/frappe-bench

# ==================== 安装 AI Agent 额外依赖 ====================
RUN ./env/bin/pip install --no-cache-dir \
    openai>=1.0.0 \
    langchain>=0.1.0 \
    langchain-openai>=0.0.5 \
    httpx>=0.25.0 \
    wechatpy>=1.8.0 \
    pdfplumber>=0.10.0 \
    openpyxl>=3.1.0

# ==================== 构建前端资源 ====================
RUN bench build --production

# ==================== 生产镜像 ====================
FROM frappe/bench:latest AS production

# 安装必要工具
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd curl \
    && rm -rf /var/lib/apt/lists/*

# 设置环境变量
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER frappe
WORKDIR /home/frappe

# 从构建阶段复制完整的 frappe-bench
COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

# 复制入口脚本
COPY --chown=frappe:frappe ./docker/scripts/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# 确保目录存在
RUN mkdir -p sites logs

# ==================== 容器配置 ====================
EXPOSE 8000 9000

# 健康检查（延长启动等待时间）
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=5 \
    CMD curl -f http://localhost:8000/api/method/ping || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["bench", "start"]
