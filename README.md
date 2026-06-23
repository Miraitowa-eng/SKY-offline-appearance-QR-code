# 光遇扫码身高解析 AstrBot 插件

离线解析 `sky.thatg.co/o=` 扫码链接中的光遇身高数据，并返回体型值、身高值、当前身高编号、最高/最矮身高编号以及可选装扮信息。

本插件不请求第三方接口，不会消费好友码，适合直接放入 AstrBot 作为群聊或私聊工具使用。

## 功能特性

- 自动识别消息中的 `sky.thatg.co/o=` 链接。
- 支持直接发送 `o=` 后面的原始数据。
- 离线完成 `Base64 -> LZ4 block -> JSON` 解码。
- 按常见光遇身高编号公式计算当前、最高、最矮身高编号。
- 可展示扫码数据中包含的发型、斗篷、面具、背饰等装扮 ID。
- 提供 AstrBot WebUI 配置项，可调整公式参数、时区和装扮信息显示开关。

## 依赖

无需额外安装依赖。

插件只使用 Python 标准库和 AstrBot 插件 API。

## 安装与配置

### 通过 AstrBot 插件市场安装

在 AstrBot WebUI 的插件市场中搜索本插件并安装，安装完成后重载插件即可使用。

### 手动安装

将本仓库下载或克隆到 AstrBot 的插件目录：

```text
AstrBot/data/plugins/astrbot_plugin_sky_o_height_decoder
```

目录结构应保持为：

```text
astrbot_plugin_sky_o_height_decoder/
├── main.py
├── metadata.yaml
├── _conf_schema.json
└── README.md
```

放入后在 AstrBot WebUI 中重载插件，或重启 AstrBot。

## 使用方法

发送扫码链接：

```text
https://sky.thatg.co/o=8RZ7...
```

也可以只发送 `o=` 数据：

```text
o=8RZ7...
```

查看帮助：

```text
扫码身高帮助
o身高帮助
光遇身高帮助
身高帮助
```

## 返回示例

```text
光遇扫码身高解析成功
==================
体型值：0.123456
身高值：-0.654321
当前身高编号：8.5
最高身高编号：0.5
最矮身高编号：12.5
查询时间：2026-06-23 20:30:00
==================
装扮信息
发型：ID 123
斗篷：ID 456
==================
```

这里的“身高编号”采用常见光遇身高编号口径，数值越小越高。

## 配置项

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `formula_base` | `7.6` | 身高公式常量 |
| `scale_coefficient` | `8.3` | 体型值 `scale` 的系数 |
| `height_coefficient` | `3.0` | 身高值 `height` 的系数 |
| `tallest_height_value` | `2.0` | 计算最高身高编号时使用的 `height` 值 |
| `shortest_height_value` | `-2.0` | 计算最矮身高编号时使用的 `height` 值 |
| `show_outfit` | `true` | 是否显示装扮信息 |
| `timezone_offset` | `8` | 查询时间的时区偏移，中国时间填 `8` |

默认计算公式：

```text
当前身高编号 = 7.6 - 8.3 * scale - 3 * height
最高身高编号 = 7.6 - 8.3 * scale - 3 * 2
最矮身高编号 = 7.6 - 8.3 * scale - 3 * -2
```

公式参考：<https://wiki.biligame.com/sky/%E8%BA%AB%E9%AB%98>

## 隐私说明

本插件只在本地解析用户发送的扫码数据，不上传、不保存扫码链接，也不会调用任何第三方查询接口。
