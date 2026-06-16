# astrbot_plugin_sky_o_height_decoder

AstrBot 光遇扫码身高解析插件。用户发送 `https://sky.thatg.co/o=...` 扫码链接后，插件会离线解码链接中的身高和装扮信息，并返回文字结果。

注意：本项目不是一个可以单独运行的聊天机器人。它是 AstrBot 的插件，需要先安装并运行 AstrBot，再把本插件放进 AstrBot 插件目录。用户在 AstrBot 已接入的平台聊天窗口里发送链接，例如 QQ 群、QQ 私聊或其他 AstrBot 支持的平台，AstrBot 会调用本插件并自动回复。

## 小白先看

如果你只是想知道这个插件怎么用，按这几步走：

1. 打开《光遇》。
2. 点击右上角齿轮，进入设置。
3. 点击 `更多`。
4. 往下拉，找到 `线下活动外观二维码`。
5. 用手机扫码。
6. 手机会得到一个 `https://sky.thatg.co/o=...` 开头的链接。
7. 把这个链接发送到已经安装本插件的 AstrBot 聊天窗口。
8. AstrBot 会自动回复身高参数和装扮 ID。

如果你是插件作者，想把这个插件上传到 GitHub，第一步是先创建 GitHub 账号，然后新建一个空仓库，仓库名建议使用：

```text
astrbot_plugin_sky_o_height_decoder
```

## 功能

- 支持识别 `https://sky.thatg.co/o=...` 链接
- 支持识别消息中的裸 `o=...` 数据
- 离线解码：`Base64 -> LZ4 block -> JSON`
- 返回体型值、身高值、当前身高、最高身高、最矮身高、查询时间
- 返回装扮 ID：裤子、斗篷、发型、面具、项链、鞋子、角饰、脸饰、背饰、头饰
- 不请求第三方接口，不消费好友码

## 安装

将本仓库目录放入 AstrBot 的插件目录，例如：

```text
AstrBot/data/plugins/astrbot_plugin_sky_o_height_decoder
```

重启 AstrBot，或在 AstrBot 插件管理中重载插件。

## 使用

### 获取扫码链接

在游戏里按这个路径获取链接：

```text
打开光遇 -> 右上角齿轮设置 -> 更多 -> 往下拉 -> 线下活动外观二维码 -> 手机扫码 -> 复制链接
```

复制到的链接一般长这样：

```text
https://sky.thatg.co/o=8RZ7...
```

把这个链接直接发送到已经安装本插件的 AstrBot 聊天窗口即可。

也可以发送帮助命令：

```text
扫码身高帮助
o身高帮助
光遇扫码身高帮助
```

## 返回示例

```text
光遇扫码身高解析成功
==================
体型值：0.056000002
身高值：1.9332844
当前身高：1.335346783
最高身高：1.135199983
最矮身高：13.135199983
查询时间：2026-06-15 15:37:06
==================
装扮信息
裤子：ID 1840544846
斗篷：ID 2496216296
发型：ID 1557042466
面具：ID 3995763436
项链：ID 3800884691
鞋子：ID 423244060
角饰：ID 3886634356
脸饰：ID 4037336099
背饰：ID 4248068234
头饰：ID 460877065
==================
```

## 配置

插件提供 `_conf_schema.json`，可在 AstrBot 插件配置中调整：

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `formula_base` | `7.6` | 身高公式常量 |
| `scale_coefficient` | `8.3` | 体型值 `S` 系数 |
| `height_coefficient` | `3.0` | 身高值 `H` 系数 |
| `tallest_height_value` | `2.0` | 最高身高对应的 `H` 值 |
| `shortest_height_value` | `-2.0` | 最矮身高对应的 `H` 值 |
| `timezone_offset` | `8` | 查询时间时区偏移 |

默认身高计算公式：

```text
当前身高 = 7.6 - 8.3 * scale - 3 * height
最高身高 = 7.6 - 8.3 * scale - 3 * 2
最矮身高 = 7.6 - 8.3 * scale - 3 * -2
```

公式参考：[身高 - 光遇wiki_bwiki_哔哩哔哩](https://wiki.biligame.com/sky/%E8%BA%AB%E9%AB%98)

## 文件结构

```text
astrbot_plugin_sky_o_height_decoder/
├── .github/workflows/check.yml
├── .gitignore
├── main.py
├── metadata.yaml
├── _conf_schema.json
├── README.md
├── LICENSE
├── CHANGELOG.md
├── 上传GitHub教程.md
└── 使用说明.md
```

## 说明

本插件只解析用户主动发送的扫码链接内容。链接中的数据不是服务端接口返回 JSON，而是 `o=` 参数内嵌的压缩数据。
