# Spike Notes 中文教程

[English](../README.md) | 简体中文

Spike Notes 是一个用 Python 和 PySide6 制作的桌面便签应用。把待办事项贴在桌面任意位置，完成后拖到右下角的金属钉座上，让小小的成果一张张积累起来。

无需注册账号，便签保存在本机。当前应用菜单为英文，本教程提供对应的中文说明。

![桌面上的独立便签](../preview.png)

## 安装与启动

需要 Python 3.10 或更新版本，以及支持 PySide6 的桌面系统。以下命令在项目根目录运行。

### macOS

打开 Terminal（终端），依次运行：

```bash
git clone https://github.com/NicoleJiaxinSun/SpikeTasks.git
cd SpikeTasks
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

如果已经下载 ZIP，解压后在终端输入 `cd `（末尾留一个空格），把解压后的项目文件夹拖进终端，再按回车。然后从上面的 `python3 -m venv .venv` 开始执行。

以后再次启动，在项目文件夹里运行：

```bash
source .venv/bin/activate
python main.py
```

运行期间保留终端窗口。请先从应用菜单退出，再关闭终端。

### Windows

打开命令提示符（cmd），运行：

```bat
git clone https://github.com/NicoleJiaxinSun/SpikeTasks.git
cd SpikeTasks
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python main.py
```

如果使用下载的 ZIP，先解压并进入项目文件夹，再从创建虚拟环境开始执行。上述激活命令用于 cmd。

## 新建便签

即使桌面上没有剩余便签，也可以新建：

1. 右键点击右下角的钉座或已完成的纸堆；也可以点击菜单栏／系统托盘中的 **S** 图标。
2. 选择 **＋ New note**（新建便签）。
3. 输入内容并选择颜色，点击 **Save**（保存）。

内容最多 280 个字符。短句更适合便签；较长内容可能无法在纸面上全部显示，可以双击打开编辑窗口查看全文。

## 移动、编辑与删除

- **移动**：按住便签拖动，可放到连接的屏幕上，位置会自动保存。
- **编辑**：双击便签，或右键选择 **Edit note**。
- **删除**：右键便签，选择 **Delete note**。
- **查看清晰颜色**：鼠标移入时便签完全显色，并出现编辑提示；移开后恢复半透明。

便签是独立的透明窗口，便签之间没有覆盖整个桌面的背景窗口。默认情况下，切换到其他应用可能会遮住便签。

## 完成任务与查看成果

1. 把便签的中心拖到金属钉尖附近。
2. 出现 **RELEASE TO COMPLETE**（松开以完成）后松开鼠标。
3. 纸张会播放穿刺、飘落和叠放动画，留在钉座上。

前十张纸会保留明显的层间距离，让完成数量看得出来。数量增多后，间距会逐渐压缩，所有完成记录仍可在列表中查看。

![已完成的便签叠放在钉座上](../completed-preview.png)

左键点击纸堆，或在菜单中选择 **Small wins**（已完成任务），打开完成列表：

- **Restore**：恢复为待办便签，重新出现在桌面上。
- **Delete**：删除这条完成记录。
- **Close**：关闭列表。

## 常用菜单

| 英文菜单 | 功能 |
|---|---|
| ＋ New note | 新建便签 |
| Small wins | 查看、恢复或删除已完成任务 |
| Show all notes | 显示便签并将其带到前面 |
| Keep above other windows | 勾选后让便签和钉座保持置顶 |
| Quit Spike Notes | 保存并退出应用 |

钉座固定在主屏幕可用区域的右下角。正在播放完成动画时，退出操作会等纸张落稳后继续。

## 六色便签

| 颜色 | 色值 |
|---|---|
| 桃粉 · Rose pink | `#F3BCC6` |
| 蜜桃橙 · Peach orange | `#F6C29A` |
| 奶油黄 · Cream yellow | `#F5E69F` |
| 嫩绿 · Fresh green | `#C8EFC1` |
| 雾蓝 · Mist blue | `#B8D8F5` |
| 淡紫 · Soft violet | `#D8C5EE` |

正文采用 17 号常规字重。旧版八色便签数据会自动对应到新配色。

## 数据保存

便签内容、颜色、位置和完成状态会自动保存到本机应用数据目录中的 `tasks.json`。应用不需要在线服务。

- macOS：在 `~/Library/Application Support/` 下的 `SpikeNotes/Spike Notes` 目录。
- Windows：在 `%APPDATA%` 下的 `SpikeNotes/Spike Notes` 目录。
- Linux：在 `~/.local/share/` 下的 `SpikeNotes/Spike Notes` 目录。

首次启动提供三张示例便签；删空后，下次启动会保持空白。如果文件损坏，应用会保留原文件并停止保存，需修复或移走该文件后重启。避免同时运行多个实例修改同一份数据。

## 常见问题

**找不到新建入口？** 右键钉座或纸堆，选择 **＋ New note**；也可使用顶部菜单栏或系统托盘的 **S** 图标。

**便签被其他窗口挡住了？** 在菜单里选择 **Show all notes**。需要一直显示时，勾选 **Keep above other windows**。

**修改代码后没有变化？** 先通过 **Quit Spike Notes** 退出，再重新启动；已经运行的程序不会自动加载代码修改。

**提示找不到 PySide6？** 在项目文件夹激活 `.venv`，再执行 `python -m pip install -r requirements.txt`。

## 验证与限制

在项目根目录运行自动检查：

```bash
python -m unittest discover -s tests -v
```

当前七项自动检查覆盖保存、编辑、拖动、完成与恢复、独立便签场景、右键菜单和叠放间距。自动检查采用离屏模式；本文图片为实际 macOS 桌面截图。不同系统的透明效果、窗口层级、点击区域和多屏行为仍需实机检查。
