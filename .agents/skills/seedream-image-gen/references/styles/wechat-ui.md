# Seedream 5.0 Pro — WeChat / iOS App UI 伪造 Recipe

> Covers chat / group-chat / 朋友圈 / 转账 / 微信支付 / 语音通话 / 红包.
> All generations are **text-to-image (no reference screenshot needed)** — the model has iOS WeChat UI hard-memorized.

---

## 1. TL;DR Recipe

```bash
uv run scripts/seedream_image_gen.py generate --phone \
  --prompt "以假乱真的微信{页面类型}截图, 手机竖版9:16, 严格复刻iOS版微信UI:
状态栏{时间}; 导航栏'{对象名}'头像为{头像描述};
{对话/内容逐字写：每条消息标左/右、颜色、内容};
输入框在底部; 苹方字体, 绿泡泡#95EC69, 极真实以假乱真微信截图"
```

Key knobs:
- **`--phone`** → Pro: 1152×2048, Lite: 1440×2560. This is the only size where iOS UI chrome renders crisply. Do NOT use `--portrait` (3:4 is squarish) or `--wide` (landscape).
- **optimize_prompt**: leave as default `"standard"`. The prompt rewriter helps fill in standard UI chrome you didn't enumerate.
- **No reference image needed.** WeChat UI is in training data; just describe it.

---

## 2. 页面类型 & Recipes

### 2.1 单聊界面 (1-on-1 chat)

Prompt shape:
```
以假乱真的微信聊天界面截图, 手机竖版9:16, 严格复刻iOS版微信UI:
状态栏10:24;
导航栏联系人'{名字}'头像为{头像描述：服饰+动作+外貌};
聊天背景默认米白纹理;
对话:
  {对象名}(左白气泡)'{message1}';
  我(右绿气泡)'{reply1}';
  {对象名}(左白气泡)'{message2}';
  我(右绿气泡)'{reply2}';
  ... (≤8 轮对话, 超过会挤爆)
输入框在底部;
苹方字体, 绿泡泡#95EC69, 极真实以假乱真微信截图
```

What renders correctly:
- ✅ Status bar (time numerals, signal dots, wifi, battery icon)
- ✅ Nav bar (back chevron <, contact name, camera/... icons)
- ✅ Avatar as circular portrait
- ✅ Bubble alignment: left=white/them, right=green/me, with correct bubble tails pointing to avatar side
- ✅ Green bubble hex **must be specified as `#95EC69`** if you want pixel-accurate color (model will pick a similar green otherwise)
- ✅ Input bar (mic icon left, "按住 说话"/输入区, smiley + "+" right)
- ✅ 表情包/sticker as a square image-within-bubble when described (e.g. "孙悟空发来一个表情包位置是悟空摸鱼翘脚的卡通(用方角图显示)")
- ✅ 红包 (red packet bubble with "開" coin + custom red-packet preview card)

Bugs/weak spots:
- ⚠️ "我"的头像默认会随机生成一个真人头像（亚裔男/女都有），想要特定头像在 prompt 里也描述一下"我的头像是xxx"
- ⚠️ 表情包内的小字可能略糊，单字/两字 emoji 没问题，四字以上需要 retry
- ⚠️ 超过 8 轮对话会导致顶部消息溢出状态栏或重复

### 2.2 群聊界面 (group chat)

Additions vs single chat:
- 群名带人数："导航栏群名'{群名}({N})'"
- 群成员列表副标题："副标题显示'成员A、成员B、成员C、成员D、成员E'"
- 系统灰条消息："{系统提示内容}"（居中灰色 pill bar，用于"X 撤回了一条消息""X 修改群名为 Y""X 通过扫描群二维码加入群聊"等）
- 每个白气泡前加名字："{名字}(左白气泡)'{msg}'" （群聊白气泡带头像+昵称，绿气泡还是"我"）

Group-chat structure (group name with member count, subtitle member list, system grey pill bars, white bubbles with avatar+name) renders correctly across groups.

### 2.3 朋友圈 (Moments)

Moments 需要更多结构描述：
```
以假乱真的微信朋友圈界面截图, 手机竖版9:16, 严格复刻iOS版微信UI:
顶部封面图是{cover图描述};
封面右下角圆形头像为'{自己头像}', 右侧白色昵称'{自己的昵称}';
下方是3条朋友圈动态:
  第一条 {头像1描述}+昵称'{名字1}': '{正文内容}'; 下方配一张方形{图片描述}; 右下角两个图标(♡赞和气泡评论); 下方显示'赞: {点赞人列表}'; 评论区: '{评论人}: {评论内容}';
  第二条 ...
  第三条 ...
底部tab栏: 微信/通讯录/发现/我, 当前选中'发现'(绿色);
苹方字体, 极真实以假乱真
```

Weak spot:
- ❌ 评论/点赞小图标（评论气泡 shape）在 1152×2048 下偶尔渲染成伪汉字（"谫"），这是小 UI glyph 的共同问题，不影响整体观感。其他元素（头像、昵称、正文、配图、点赞列表文字、评论文字、tab 栏四个 tab 的中文文字）都准。

### 2.4 转账界面 (Transfer)

```
以假乱真的微信转账界面截图, 手机竖版9:16, 严格复刻iOS版微信UI:
顶部灰色导航栏'转账给 {对象名}', 返回<;
中部一行显示圆形头像+昵称'{对象名}';
下方巨大黑色'¥{金额}'（金额带千分位逗号，如¥8,888.88）;
下方转账说明栏浅灰字'{转账备注}';
下方一行'转账方式 零钱 >'右侧绿色对勾;
底部巨大绿色按钮'转账';
最底部小字'零钱';
苹方字体, 极真实
```

**金额数字和千分位逗号完全准确**。

### 2.5 微信支付到账通知 (Pay notification)

```
以假乱真的微信支付通知界面截图, 手机竖版9:16:
顶部绿色导航栏白字'微信支付', 返回<;
顶部绿色区域白色对勾logo, 金色大字'+¥{金额}.00', 白色小字'{支付类型, e.g. 二维码收款}';
下方白色区域: '付款方备注: {备注}', '来自: {付款方} {头像描述}';
下方两个绿色按钮'查看详情'/'回复';
下方交易记录列表: 若干条交易, 支出黑色-¥xx.xx, 收入绿色+¥xx.xx, 每条带图标和商家名;
最底部小字'微信安全支付'
```

支出/收入颜色可正确渲染（支出黑色-¥xx.xx，收入绿色+¥xx.xx）。

### 2.6 语音/视频通话 (Voice/Video call)

```
以假乱真的微信语音通话界面截图, 手机竖版9:16:
背景是对方头像的模糊放大版(高斯模糊);
页面中央一个巨大圆形头像(直径约画面宽度一半)为{头像描述};
头像外两圈淡白色脉冲环表示通话中;
头像下方白色粗体字'{对方名字}', 下方小字'正在语音通话... {通话时长}'（如00:42）;
下方灰色toast提示'你已切换到免提';
底部三个按钮水平排列: 左侧灰色麦克风(静音), 中间大红圆形挂断按钮(白色电话听筒下垂图标), 右侧白色圆形扬声器按钮;
```

### 2.7 红包 (Red packet in chat)

红包以**消息内小卡片**形式出现在聊天气泡位置，不需要单独页面：
```
{对象名}(左白气泡)发来一个[红包]: 红包是橙红色矩形带金色'開'字圆形按钮居中, 顶部小字'微信红包', 下方小字'恭喜发财，大吉大利'或自定义祝福
```

点开后的红包详情页支持度未确认；聊天气泡内的红包可正确渲染。

---

## 3. 安全/审查注意事项

以下内容未见安全审查拦截，包括：
- 直接使用"微信"产品名（no euphemism needed；"以假乱真"比"伪造"更稳）
- 古代神话/文学人物对话（孙悟空、财神、李白、观音、甄嬛、三国、西游、修仙）
- 小额玩笑金额 (¥888.88, ¥8,888.88, ¥10,000 年终奖 from 老板)
- 幽默/梗向对话（"八戒在分行李打算回高老庄""法海你不懂爱"）

**不要**：
- 不要伪造真实人物（政治人物/名人/朋友）的真实对话进行诈骗
- 不要生成超大金额（¥1,000,000+）的转账/支付截图（可能触发金融风控）
- 不要生成违法场景（赌博/色情/毒品交易对话）

Joke/meme 内容与神话/文学/虚构角色明显是 safe 的。

---

## 4. 已知局限与规避

| 问题 | 规避 |
|---|---|
| 底部 tab 小图标（评论气泡 shape 等）偶尔渲染成伪字 | 接受即可；文字标签（"微信/通讯录/发现/我"）是准的，小图标无伤大雅 |
| "我"的头像随机 | 在 prompt 里显式描述"我头像是xxx，戴xxx" |
| 对话超过 8 轮溢出 | 控制在 6-8 轮内；要长对话考虑分多张图 |
| 图片/表情包在气泡内分辨率有限 | 表情包主体描述要简洁（"一个橘猫比耶表情包"），不要让表情包自己带复杂小字 |
| 时间/电量精确位置可能略有浮动 | 接受即可，不影响以假乱真程度 |

---

## 5. 为什么 txt2img 比 reference-screenshot 更好？

不要把真实微信截图送进去做 reference——模型会照着真实截图重绘，反而会因为压缩/字体/像素对齐问题输出模糊/错位版。直接 text-to-image 让模型从记忆里渲染标准 UI，结果更 crisp。

如果需要特定对话内容/头像/昵称，纯文字描述足矣；不需要截图 reference。

---

## 6. 快速启动模板

Copy-paste 后改 `{braces}` 部分：

```bash
uv run scripts/seedream_image_gen.py generate --phone \
  --prompt "以假乱真的微信聊天界面截图, 手机竖版9:16, 严格复刻iOS版微信UI: 状态栏{时间}; 导航栏联系人'{对方名字}'头像为{头像服饰+外貌描述}; 聊天背景默认米白纹理; 对话: {对方}(左白气泡)'{msg1}'; 我(右绿气泡)'{reply1}'; {对方}(左白气泡)'{msg2}'; 我(右绿气泡)'{reply2}'; 输入框在底部; 苹方字体, 绿泡泡#95EC69, 极真实以假乱真微信截图"
```
