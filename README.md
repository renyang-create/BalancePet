# Balance Pet · DeepSeek 余额桌宠

> 一只趴在桌面上的小宠物，帮你盯着 DeepSeek API 账户还剩多少钱。

![预览](docs/preview.gif)

> **个人学习项目**：本项目为个人学习练手所作，主要用于熟悉 Python 桌面 GUI 开发、Windows 窗口行为与第三方 API 调用，属于非商业项目，不保证长期维护。图片素材的来源说明见文末。

---

## 项目简介

**Balance Pet** 是一个独立的桌面宠物应用，用来查询并显示 **DeepSeek API 账户余额**。

它把自己做成一只**全局置顶、可拖拽、点一下会动**的桌宠，把余额直接显示在头顶的气泡里——写代码的时候瞄一眼就知道还能烧多久，不用再专门打开网页去查。

### 它和插件市场里大多数桌宠的区别

|  | 常见的桌宠 | Balance Pet |
|---|---|---|
| 运行形态 | 依附在编辑器 / 插件宿主里 | **独立桌面应用**，不依赖任何宿主 |
| 需要额外服务端吗 | 部分需要 | **不需要**，直连 DeepSeek 官方接口 |
| 能看余额吗 | 基本不能 | **能**，这是它的主要功能 |
| 前提条件 | 要装对应插件环境 | **只要有一个用过额度的 DeepSeek API Key** |

只要你的 Key 对应的账户**产生过消费**（在任意接入了 DeepSeek API 的工作台、插件、脚本里用过都算），就能直接查到余额——不需要额外的客户端、不需要插件、也不需要自己搭服务端。

---

## 功能说明

- **全局置顶悬浮**：无边框窗口 + 抠掉背景，只留宠物浮在桌面上
- **可拖拽**：按住宠物拖到任意位置
- **点击互动**：点击宠物会显示互动台词，并播放一段自然的"呼吸 / 浮沉"微动
- **余额展示**，气泡两行显示：
  - 第一行：`余额 ¥110.00 CNY`（总余额 + 货币类型）
  - 第二行：`可用 · 赠金 ¥10.00 · 充值 ¥100.00`（是否可用 + 赠金余额 + 充值余额）
- **定时刷新**：默认 60 秒一次，可在 `.env` 里改
- **右键菜单**：立即刷新余额 / 设置 API Key / 关于 / 退出
- **错误兜底**：Key 无效、网络异常、接口异常都会显示成可读的提示，不会崩

---

## 技术栈

| 用途 | 依赖 |
|---|---|
| 界面 / 无边框悬浮窗 | [customtkinter](https://github.com/TomSchimansky/CustomTkinter)（基于 Tkinter） |
| 接口请求 | [requests](https://requests.readthedocs.io/) |
| 图片处理 | [Pillow](https://python-pillow.org/) |
| 配置 | 原生 `.env` 解析 + 系统环境变量（无需 python-dotenv） |
| 动画 | 用 Pillow 预生成帧，运行时逐帧切换（整图刚体变换） |

- Python **3.9+**
- 系统：**Windows**（`-transparentcolor` 抠背景是 Windows 专有特性；macOS / Linux 上会退化成一块深色底）

---

## 文件结构

```
BalancePet/
├── main.py                    # 桌宠主程序（入口）
├── requirements.txt           # 依赖清单
├── .env.example               # 配置模板（复制成 .env 后填 Key）
├── .gitignore
├── LICENSE
├── README.md
├── assets/                    # 素材（可替换成你自己的宠物）
│   ├── pet.png                # 静态素材（透明 PNG）
│   ├── pet_idle_static.png    # 静止图（= 动画第 0 帧）
│   ├── pet_frames/            # 22 帧微动动画
│   │   ├── f00.png
│   │   └── ...
│   └── pet.ico                # 快捷方式图标（由 tools 生成）
├── docs/
│   └── preview.gif            # README 里的预览图
└── tools/                     # 可选工具，不影响主程序运行
    ├── make_idle_frames.py    # 重新生成动画帧
    └── make_shortcut.py       # 生成桌面快捷方式（Windows）
```

---

## 安装方法

### 1. 克隆仓库

```bash
git clone https://github.com/<你的用户名>/BalancePet.git
cd BalancePet
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 生成配置文件

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

### 4. 填入你的 API Key

打开 `.env`，把这一行填上你自己的 Key：

```ini
DEEPSEEK_API_KEY=sk-你的密钥
```

> Key 在 <https://platform.deepseek.com/api_keys> 创建。

### 5. 启动

```bash
python main.py
```

第一次启动如果发现 `.env` 不存在，程序会**自动生成一份模板**，填好 Key 再启动即可。

---

## 使用方法

| 操作 | 效果 |
|---|---|
| **左键点击**宠物 | 显示互动台词 + 播放一段微动动画 |
| **左键拖拽**宠物 | 移动到任意位置 |
| **右键点击**宠物 | 弹出菜单 |
| └ 立即刷新余额 | 不用等定时器，立刻拉一次 |
| └ 设置 API Key… | 弹窗粘贴 Key，自动写入 `.env` 并立刻刷新 |
| └ 关于 | 查看当前 Key（打码）、刷新间隔、接口地址 |
| └ 退出 | 关闭桌宠 |

### 开机自启（可选，Windows）

1. 先执行一次：`python tools/make_shortcut.py`（会在桌面生成 `Balance Pet.lnk`，用 `pythonw.exe` 启动，**不会弹黑窗口**）
2. 按 `Win + R`，输入 `shell:startup`，回车
3. 把桌面上的 `Balance Pet.lnk` 复制/拖进打开的启动文件夹

### 换成你自己的宠物形象

1. 准备一张**背景透明**的 PNG，命名成 `assets/pet.png` 覆盖原文件
2. 执行 `python tools/make_idle_frames.py` 重新生成动画帧和静止图
3. 重启桌宠

> 动画是"整图刚体变换"（等比缩放 + 平移），所以**不会出现破面、断脖子、多出五官**这类问题——不管换成什么形象都安全。

---

## API Key 配置说明

### 读取优先级

```
.env 文件  →  系统环境变量 DEEPSEEK_API_KEY
```

两个都配了的话，**以 `.env` 为准**。

### 三种配置方式

**方式一：编辑 `.env`（推荐）**

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
REFRESH_INTERVAL=60
```

**方式二：程序内设置**

右键桌宠 → `设置 API Key…` → 粘贴 → 确定。
程序会自动把 Key 写进 `.env` 并立刻刷新余额。

**方式三：系统环境变量**

```powershell
# Windows PowerShell（临时，仅当前窗口）
$env:DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxx"
python main.py
```

### 安全说明

- **代码里没有任何密钥**，也不存在硬编码的默认 Key
- `.env` 已经在 `.gitignore` 里，**不会被提交**，不会随仓库泄露
- 想确认自己没手滑提交密钥：

  ```bash
  git check-ignore -v .env     # 有输出 = 已被忽略，安全
  git log --all -S "sk-" --oneline   # 应该没有输出
  ```

- 万一 Key 泄露了，去 <https://platform.deepseek.com/api_keys> 立刻删除并重建

---

## 注意事项

1. **接口用量**：程序只调用 `GET /user/balance` 这一个只读接口，**不会产生任何模型调用费用**。
2. **刷新间隔**：建议不要小于 15 秒，太频繁可能被限流（程序内部已经做了最小值保护）。
3. **余额口径**：接口返回的是**账户总额度**，不是实时消耗明细。想看按次的 token 消耗和"思考 token"，只能去 DeepSeek 官方控制台的用量页面。
4. **平台支持**：抠背景用的是 Windows 专有的 `-transparentcolor`，所以在 macOS / Linux 上宠物会带一块深色方底，观感会有折扣（功能正常）。
5. **无控制台启动**：用 `pythonw.exe` 或桌面快捷方式启动时不会弹黑窗口；如果程序出错，异常会写进同目录的 `pet_error.log`。
6. **素材版权**：`assets/` 里的宠物形象请确认你有权使用，开源仓库里建议一并说明来源。

---

## 常见问题

**Q：气泡一直显示"还没设置 API Key"？**
A：`.env` 没建或没填。右键 → `设置 API Key…` 最快。

**Q：显示"API Key 无效或已过期"？**
A：Key 复制错了（多了空格 / 少了字符），或者这个 Key 已被删除。重新去控制台复制一次。

**Q：显示"网络异常，稍后重试"？**
A：本机连不上 `api.deepseek.com`。检查代理 / 防火墙，或者把代理设成系统代理后重试。

**Q：宠物不见了？**
A：它默认停在屏幕右下角；如果拖到了屏幕外面，删掉进程重开即可。也可以用右键 → 退出。

**Q：不想让它一直置顶？**
A：编辑 `main.py`，把 `self.attributes("-topmost", True)` 删掉。

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源。

- ✅ 可以自由使用、修改、分发、商用
- ✅ 保留版权声明即可
- ⚠️ 二次分发时请保留 `LICENSE` 中的版权声明
- ⚠️ 软件按"原样"提供，作者不对使用后果负责

---

## 素材与实现说明

### 图像素材

本项目中的宠物形象（`assets/pet.png`）及全部动画帧（`assets/pet_frames/`）均由 **AI 工具生成**，仅用于本项目的功能演示与个人学习，**不包含任何官方素材，也不用于任何商业用途**。

> 想换成你自己的形象：直接替换 `assets/pet.png`，再跑一次 `python tools/make_idle_frames.py` 即可，详见 [换成你自己的宠物形象](#换成你自己的宠物形象)。

### 实现与测试

需求设计、代码实现、参数调优与多轮实测验证均由作者完成，其中重点处理了 Windows 平台下 Tk / CustomTkinter 的几个经典坑位：

- 子线程直接操作控件会抛 `RuntimeError: main thread is not in main loop` —— 改为「子线程入队 + 主线程消费」
- `-alpha` 与 `-transparentcolor` 在 Windows 上相互冲突，一旦设置 alpha，抠背景立刻失效 —— 去掉 alpha
- `<Button-1>` 是 `<ButtonPress-1>` 的别名，同一控件重复绑定会让「拖拽」被误判成「点击」—— 点击判定挪到 `ButtonRelease` 并加位移阈值
- 拖拽若以「按下点」为基准，位移会逐帧累加、窗口越拖越飞 —— 改用根坐标反算窗口位置

本项目已在 **Windows + Python 3.14** 上完整验证；其他环境下的表现未做完整测试，遇到问题欢迎提 Issue / PR。

---

## 致谢

- 界面基于 [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- 余额接口来自 [DeepSeek 开放平台](https://platform.deepseek.com/)
