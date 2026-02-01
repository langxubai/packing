# 🧳 智能旅行打包助手 (Packing Assistant)

这是一个基于 **Streamlit** 开发的轻量级旅行打包清单工具。它支持自定义分类模板、自动保存进度，并提供直观的进度条显示，确保你的旅途万无一失。

## ✨ 主要功能

* **✅ 开始打包**：实时勾选物品，进度条动态更新，完成后有小惊喜。
* **🆕 新旅程生成**：从预设模板中灵活挑选本次旅行所需的物品，一键生成清单。
* **📝 模板管理**：动态编辑你的“装备库”，支持新增分类、修改物品及删除操作。
* **💾 自动持久化**：所有更改（勾选状态、模板修改）都会实时保存到本地 JSON 文件中。

## 🚀 快速开始

### 本地运行

1. **克隆仓库**：
```bash
git clone <your-repo-url>
cd packing

```


2. **安装依赖**：
```bash
pip install -r requirements.txt

```


3. **启动应用**：
```bash
streamlit run src/app.py

```



### Docker 运行

1. **构建镜像**：
```bash
docker build -t packing-app .

```


2. **运行容器**：
```bash
docker run -p 8501:8501 packing-app

```



## 🛠 技术栈

* **Python 3.9+**
* **Streamlit**: 前端框架
* **Pandas**: 数据处理
* **Docker**: 环境容器化