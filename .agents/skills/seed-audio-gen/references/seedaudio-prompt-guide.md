# seed-audio-1.0 Prompt Guide

How to write effective `text_prompt` for Volcano Engine's Doubao Audio Generation 1.0 (`seed-audio-1.0`).

## Overview

seed-audio-1.0 is a **generative audio model** — you describe a scene in natural language, and it produces a mixed audio clip with voice, BGM, and sound effects. The prompt is your director's script: it controls who speaks, what they say, when they say it, what music plays, and what sound effects fire.

The model supports up to 120 seconds of audio per call, 18 languages (API doc 2026-08-20), and multi-character dialogue.

## Duration Control

Two independent mechanisms:

### Total duration declaration

Declare the target total length at the very start of the prompt:

```
音频总时长：18秒。<开场描述>…
```

Verified 2026-08-27: `音频总时长：15秒` produced output of exactly 15.0s. Use this when the clip must fit a fixed video slot. If the spoken content is too dense for the declared duration, the model speeds up speech to fit — so keep dialogue realistic for the time budget.

### Per-line timestamps

Precise timeline control with 100ms granularity. Use the format:

```
[<start_seconds>:<end_seconds>]"<dialogue>"
```

The time range specifies when the line should be spoken within the generated audio. Both `start` and `end` are in seconds, with up to 0.1s precision.

**Verified in production** (2026-08-26).

**Example**

```
一位女声朗读：[1.0s:3.0s]"你好，这是时间戳测试。"[5.0s:7.0s]"第二句在五秒开始。"
```

This generates a 7.0s audio clip with two lines, placed at their specified time windows.

**Multi-character with timestamps**

```
广告播音员语速慢地说道：[2.7s:5.7s]"美丽的旅程，值得一个璀璨的开始。"
广告播音员继续介绍：[6.6s:18.9s]"Pocara面霜，专为年轻肌肤定制的第一瓶高端养护..."
```

Combine both for video dubbing: declare `音频总时长：N秒` to match the video length, then pin key lines with timestamps.

## Scene Element Structure

A complete prompt builds a scene from these layers, written in natural Chinese (or English):

1. **BGM description** — genre, mood, tempo, instruments (put this first)
2. **Character list** — for multi-character scenes, define all characters up front: name, age, gender, voice quality, accent, genre tag
3. **Timestamped dialogue** — lines placed at specific times, with acting directions
4. **Sound effects** — position relative to dialogue (e.g. "句首伴随一声水声流过的特效音")

### Prompt Template

```
<配乐描述>。
角色列表：
<角色1>（<年龄性别>，<嗓音特质>，<口音/风格标签>）
<角色2>（…）
<角色1>（<语气/表演指导>）说："[<start>:<end>]<台词>"<音效描述>。
<角色2>（<表演指导>）回应："…"
```

You do not need all elements; a minimal prompt can be just a character + dialogue. The model fills in reasonable defaults.

### Layers Explained

**BGM**: Describe the music style, mood, and instruments. Be specific — name instrument groups and texture:
- Good: "轻柔的钢琴独奏" / "弦乐组演奏的舞曲，大提琴与低音提琴演奏低声部跳音，小提琴演奏主旋律，随后手风琴加入" / "马林巴为主奏，加入 pad 铺底、合成器 lead、电贝斯，整体紧张悬疑"
- Avoid: "一些音乐" / "有BGM"

**Character definition**: Describe the speaker before their dialogue. Include the dimensions that matter:
- Gender/age: "一位女声" / "中年男性" / "55岁左右的中年女性"
- Voice quality: "温柔" / "低沉沙哑" / "清澈明亮" / "雄浑有力" / "气泡音" / "略带沙哑"
- Accent: "台湾口音" / "东北口音" / "译制片口音"
- Genre tag (anchors acting style): "现代剧" / "古装剧" / "播客" / "译制片"
- Emotion & pacing: "深情地" / "激动地" / "平静地" / "语速略微偏快，吐字清晰"

**Dialogue**: The actual spoken text, wrapped in quotes. Place with timestamp brackets for precise control, or without for auto-placement. You can direct delivery mid-line: "'特地'两个字被加重说了出来"、"句末呈现气声"、"说到这里停顿了一段时间"。

**Sound effects**: Describe what happens and when:
- "句首伴随一声水声流过的特效音"
- "句尾有一声轻微的汽车刹车声，随后是两声高跟鞋走路脚步声"
- "背景有雨声" / "一阵连续的布鞋走路脚步声"
- **Voice processing / channel effects** work too: "通过电话回应，声音经过处理，显得有些遥远和失真"
- **Crowd voices**: "卫兵们错落有力的声音喊道：'抓住她！在这里…'"、"其他卫兵大声回应：'是！是！'"

**Non-verbal performance**: Laughter, sighs, gasps, swallowing, stammering, screams, crying, breathing — write them directly into the script where they happen:
"她轻笑一声"、"他发出一声轻微的吸气"、"有略微吞口水的声音"、"唐娜发出一声非常轻微的、无奈的叹息声"、"声音颤抖和磕巴"、"句首和弗兰克的笑声重叠"（cross-character overlap direction）。

**Podcast naturalism**: For talk-show realism, lean on fillers and backchannels: 附和声（"对""嗯""是"）、停顿、吞字、口语重复（"是一个…是一个终生的事情"）——模型会还原真人说话的毛边感。

## Multi-Reference Audio (`@音频N`)

Pass up to **3 reference audios** per call for multi-character voice cloning. Use `--ref-audio <path>` for local files or `--ref-audio-url <url>` for remote audio (repeat either; they can be mixed; each ≤30s, ≤10MB, wav/mp3/pcm/ogg_opus). Bind references in the prompt with `@音频N` — **numbering strictly follows the flags left-to-right in CLI order** (official API contract):

- 1st reference flag → `@音频1`
- 2nd reference flag → `@音频2`
- 3rd reference flag → `@音频3`

Place the token at the point where that voice speaks, or in the character definition:

```
@音频1的声音（中年男性，低沉）用沉稳的语气说："大家好，我是一号男主播。"
@音频2的声音（年轻女性，甜美）笑着回应："大家好，我是二号女主播。"
```

Verified 2026-08-27: 2 and 3 reference audios are accepted with clean output. A listening test confirmed both forms bind references in upload order (1st reference → first speaker, etc.) and produce identical results — `<<TGT_SPK1>>`/`<<TGT_SPK2>>` (e.g. "饰演者为 <<TGT_SPK1>>", seen in demo prompts) works equivalently to `@音频N`, but `@音频N` is the documented public syntax, so prefer it.

### Multi-reference patterns

- **多人多音色**: each reference is a different person — `@音频1` plays the male lead, `@音频2` the female lead.
- **组合参考**: different references supply different dimensions — one for timbre, another for emotion and pacing.
- **一声多角**: the model decouples timbre from performance — one reference voice can play multiple characters with differentiated expression.
- **音频延长 (long-form chaining)**: feed the previous segment's output back in as a reference for the next call; the model extends with consistent timbre across segments. For recurring series, register a fixed `_tob` speaker ID instead.

### Reference images (separate mode)

`--ref-image` (max 1 image, ≤10MB, jpeg/png/webp) generates audio matching a picture's atmosphere/character setup; with an image, `text_prompt` can be just the lines to speak. Images **cannot** be mixed with audio references or `speaker` (API error `45001001`; official doc: image_data/image_url 不能与 audio_data、audio_url 或 speaker 同时传入). The CLI pre-validates this.

## Languages

18 languages per the API doc (last updated 2026-08-20): Chinese, English, Japanese, Korean, Mexican Spanish, Spanish, German, French, Brazilian Portuguese, Thai, Vietnamese, Malay, Filipino, Italian, Russian, Dutch, Polish, Turkish. (Indonesian and Swedish have also been observed to work but are not in the current API doc list; test those two before relying on them.)

- Write the prompt (or at least the dialogue) in the target language — the generated audio follows it: `男性が優しく言う:「すべてうまくいくよ。」`
- Dialogue and voice description can use different languages — only the quotes need the target language: `A man says warmly: 「Todo estará bien.」`

## Voice Selection

### From the catalog (--speaker)

Use `--speaker <voice_type>` to select from the 444-voice catalog. For the default picks by scenario (general narration, suspense, audiobook, children, English, etc.), see the **Common-scene quick picks** table in `SKILL.md`; for a curated shortlist with trial links, read `references/speakers.md` (Top 5 per scene).

Browse or filter the full catalog without loading it into context:

```bash
uv run scripts/seed-audio-gen.py --list-speakers --filter scene=角色扮演 --sort heat
uv run scripts/seed-audio-gen.py --list-speakers --filter lang=ja
```

Do **not** read `references/speakers.json` directly — it is ~220KB; query it with `--list-speakers`.

The `_tob` (ICL) voices are pre-registered character voices ideal for audiobooks and radio dramas — they have distinct personalities (e.g. "恐怖小丑", "温柔知性的辅导员", "帅气少年感的青年教师").

### By cloning (--ref-audio / --ref-audio-url)

Provide reference audio clips (each max 30s, max 10MB; up to 3 per call) and the model clones the timbre(s). No additional charge. Use `--ref-audio` for local files, `--ref-audio-url` for remote URLs.

```bash
# Single local reference
uv run scripts/seed-audio-gen.py "用参考音色说：这是克隆后的声音。" --ref-audio ~/my-voice.wav

# Single remote reference
uv run scripts/seed-audio-gen.py "用参考音色说：远程克隆。" --ref-audio-url https://example.com/my-voice.wav

# Multiple references for multi-character cloning (up to 3, bound by CLI order; flags may mix)
uv run scripts/seed-audio-gen.py '@音频1的声音（男主，低沉）说："…"@音频2的声音（女主，甜美）回应："…"' \
  --ref-audio ~/male.wav --ref-audio-url https://example.com/female.wav
```

With one reference you can simply write "用参考音色朗读" / "用提供的声音说". With multiple references, bind each character with `@音频N` (see the Multi-Reference Audio section).

### By character description (no reference)

If no `--speaker` / `--ref-audio` / `--ref-audio-url` is provided, the model generates a voice from the character description in the prompt. This is the most flexible approach: just describe the voice you want ("一位声音沙哑的老船长", "一个活泼可爱的少女", "一位严肃的新闻播音员").

## Prompt Length

- **Hard limit**: 3000 characters (the CLI rejects longer prompts with an error).
- **Recommended**: For Chinese voice content, keep the spoken dialogue to **400 characters or fewer**. While the hard limit is 3000, the model's quality degrades when the voice content is too dense. Scene description, BGM, and sound effect instructions are part of the 3000 limit but do not count toward the 400-char voice recommendation.
- Official confirmation of the mechanism: when text is too long for the time budget, **the model speeds up speech to fit** — dense dialogue comes out rushed. Keep dialogue realistic for the duration (and the `音频总时长` declaration if used).

## Complete Examples

### Example 1: Skincare Ad

```
轻柔的钢琴背景音乐缓缓响起。广告播音员用温暖而专业的语气、语速慢地说道：[2.7s:5.7s]"美丽的旅程，值得一个璀璨的开始。"广告播音员继续介绍：[6.6s:18.9s]"Pocara面霜，专为年轻肌肤定制的第一瓶高端养护，蕴含三重玻尿酸与马齿苋精华，28天见证肌肤焕变。"句首伴随一声水声流过的特效音。广告播音员最后说道：[20.0s:25.0s]"Pocara，你的第一瓶高端面霜。"结尾钢琴渐弱，伴随一声轻柔的水滴声。
```

What this prompt does:
- Sets a piano BGM
- Defines a warm, professional female announcer
- Timestamps three lines at precise positions
- Adds a water sound effect before the second line
- Adds a water droplet sound effect at the end
- Piano fades out at the end

### Example 2: Rainy Night Farewell

```
雨声淅沥的夜晚，远处偶尔传来闷雷。一位年轻女声，声音略带哽咽，语速缓慢地说道：[2.0s:8.0s]"你走吧。我不会等你的。"她停顿片刻，深吸一口气，声音颤抖着继续说：[9.0s:16.0s]"可是，如果你回头，我可能还在原地。"雨声渐大，淹没最后一句尾音。
```

What this prompt does:
- Sets a rainy night atmosphere with thunder
- Defines a young female voice with specific emotion (choking up, trembling)
- Timestamps two lines with a pause between them
- Uses rain as a narrative device (growing louder to drown the ending)

### Example 3: Game Character Voice

```
史诗管弦乐低音部持续铺底，伴随战鼓节奏。一位声音雄浑的中年男性将军，用威严的语气命令道：[2.0s:6.0s]"将士们，今日一战，非生即死！"音效：拔剑出鞘的金属声。将军提高音量：[7.0s:12.0s]"为了我们的家园，冲锋！"战鼓骤然加速，号角齐鸣，人声呐喊渐强。
```

What this prompt does:
- Orchestral BGM with drums
- Defines a heroic male general voice
- Sword-draw sound effect positioned between lines
- Dynamic music change (drums accelerate) at the climax
- Battle cries and horns build up at the end

### Example 4: Audiobook Scene (Multi-character)

```
深夜的密林，背景有虫鸣和猫头鹰叫声。一位声音沙哑的老人，语速缓慢地低声说：[2.0s:5.0s]"你听到了吗？"一位年轻男孩，声音颤抖，小声回答：[5.5s:8.0s]"听...听到了。在那边。"老人突然厉声：[8.5s:11.0s]"别动！"一阵急促的脚步声，树叶沙沙作响，然后一切归于寂静。
```

### Example 5: Podcast Chat (character list + naturalism)

```
背景音乐极其微弱，播客录制环境。
角色列表：
主播1（成年男性，嗓音低沉，略带沙哑，吐字清晰，语速略微偏快，播客）
主播2（年轻女性，嗓音偏御，略哑，播客）
主播1语调平缓地说："我是觉得亏欠这种事情，不是一次两次可以补偿得了的，对吧？"说到这里稍微停顿，略微加重语气："这一次去迪士尼，我主要想的就是这两个原因，就去了。"主播2简短附和："是。"主播1语气略微提高，带点惊讶的腔调："我跟你讲，去了之后其实我有点惊讶。"主播2笑了一声。主播1继续说，期间有略微吞口水的声音："我们特地挑了今年入冬以来最冷的一天，最低气温零下三度。""特地"两个字被加重说了出来。主播2笑着肯定道："是。"
```

What this prompt does:
- Opens with a character list defining both voices up front, each tagged `播客` (genre tag anchors the acting style)
- Uses backchannel fillers ("是。"), short reactions, and laughter for podcast realism
- Directs non-verbal performance: 吞口水声、停顿、加重词、笑声
- Keeps BGM minimal, matching real podcast production

## Tips

- **Be specific, not vague**: "轻柔的钢琴独奏" beats "有音乐". "声音沙哑的老人" beats "一个老年人".
- **Layer, don't list**: Describe the scene as a whole rather than a checklist. The model understands narrative flow.
- **For multi-character scenes, open with a character list**: define every voice up front (name, age, timbre, accent, genre tag like 现代剧/古装剧/播客), then write the scene. This keeps voices consistent across long dialogues.
- **Timestamp for precision, omit for flow**: Use timestamps when you need exact timing (ads, synced dialogue). Omit them when you want the model to pace naturally. Declare `音频总时长：N秒` when the clip must fit a fixed video slot.
- **Use sound effects as punctuation**: "句首" / "句尾" / "伴随着" / "然后" — these position words help the model place effects relative to dialogue. Non-verbal acting directions (气声、笑声、叹息、吞口水、磕巴) and processing directions (电话失真、遥远) are understood literally.
- **Direct acting, not just content**: "句末呈现气声"、"音调略微提高"、"语速加快"、"句首和对方的笑声重叠" — the model follows performance directions at this granularity.
- **The model may paraphrase**: It's generative, not deterministic. If verbatim accuracy is critical, add "请逐字朗读，不要增删改" or use `volcengine-tts`.
- **Test and iterate**: seed-audio rewards prompt experimentation. Start simple, listen, then add detail.