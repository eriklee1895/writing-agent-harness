# seed-audio-1.0 Prompt Guide

How to write effective `text_prompt` for Volcano Engine's Doubao Audio Generation 1.0 (`seed-audio-1.0`).

## Overview

seed-audio-1.0 is a **generative audio model** — you describe a scene in natural language, and it produces a mixed audio clip with voice, BGM, and sound effects. The prompt is your director's script: it controls who speaks, what they say, when they say it, what music plays, and what sound effects fire.

The model supports up to 120 seconds of audio per call, 20 languages, and multi-character dialogue.

## Timestamp Control

Precise timeline control with 100ms granularity. Use the format:

```
[<start_seconds>:<end_seconds>]"<dialogue>"
```

The time range specifies when the line should be spoken within the generated audio. Both `start` and `end` are in seconds, with up to 0.1s precision.

**Verified in production** (2026-08-26).

### Example

```
一位女声朗读：[1.0s:3.0s]"你好，这是时间戳测试。"[5.0s:7.0s]"第二句在五秒开始。"
```

This generates a 7.0s audio clip with two lines, placed at their specified time windows.

### Multi-character with timestamps

```
广告播音员语速慢地说道：[2.7s:5.7s]"美丽的旅程，值得一个璀璨的开始。"
广告播音员继续介绍：[6.6s:18.9s]"Pocara面霜，专为年轻肌肤定制的第一瓶高端养护..."
```

## Scene Element Structure

A complete prompt builds a scene from these layers, written in natural Chinese (or English):

1. **BGM description** — genre, mood, tempo, instruments
2. **Character definition** — gender, age, voice quality, speed, emotion
3. **Timestamped dialogue** — lines placed at specific times
4. **Sound effects** — position relative to dialogue (e.g. "句首伴随一声水声流过的特效音")

### Prompt Template

```
<BGM描述>。<角色1定义>：[<start>:<end>]"<台词>"<音效描述>。<角色2定义>：[<start>:<end>]"<台词>"<音效描述>。
```

You do not need all elements; a minimal prompt can be just a character + dialogue. The model fills in reasonable defaults.

### Layers Explained

**BGM**: Describe the music style, mood, and instruments. Be specific:
- Good: "轻柔的钢琴独奏" / "爵士三重奏，慵懒的萨克斯主旋律" / "史诗管弦乐，渐强"
- Avoid: "一些音乐" / "有BGM"

**Character definition**: Describe the speaker before their dialogue. Include:
- Gender: "一位女声" / "中年男性"
- Voice quality: "温柔" / "低沉沙哑" / "清澈明亮" / "雄浑有力"
- Speed: "语速缓慢" / "快速说道" / "不紧不慢地"
- Emotion: "深情地" / "激动地" / "平静地" / "俏皮地说"
- Age: "年轻女声" / "老人" / "少年"

**Dialogue**: The actual spoken text, wrapped in quotes. Place with timestamp brackets for precise control, or without for auto-placement.

**Sound effects**: Describe what happens and when:
- "句首伴随一声水声流过的特效音"
- "句尾有一声微弱的叹息"
- "背景有雨声"
- "然后传来一声清脆的玻璃碰撞声"

## Multi-Reference Audio (`@AudioN`)

When passing multiple reference audio files (via `references` array in the API, or sequentially via `--ref-audio-url`), reference them in the prompt by index:

```
@Audio1的声音朗读："这是第一段台词。"
@Audio2的声音随即回答："这是第二段台词。"
```

`@Audio1` maps to the first entry in the `references` array, `@Audio2` to the second, and so on. This is how you create multi-character dialogue with cloned voices.

## Voice Selection

### From the catalog (--speaker)

Use `--speaker <voice_type>` to select from the 444-voice catalog. See `references/speakers.md` for the full table with descriptions and trial audio URLs.

Quick picks:

| Scenario | Voice Type | Description |
|---|---|---|
| 通用旁白 | `zh_female_vv_uranus_bigtts` | Vivi 2.0 — warm, versatile female |
| 深沉男声 | `zh_male_dongfanghaoran_uranus_bigtts` | 东方浩然 2.0 — heroic, powerful male |
| 温柔妈妈 | `zh_female_wenroumama_uranus_bigtts` | 温柔妈妈 2.0 — warm, gentle |
| 悬疑解说 | `zh_male_xuanyijieshuo_uranus_bigtts` | 悬疑解说 2.0 — dramatic male |
| English female | `en_female_dacey_uranus_bigtts` | Dacey — natural American female |
| English male | `en_male_tim_uranus_bigtts` | Tim — natural American male |

The `_tob` (ICL) voices are pre-registered character voices ideal for audiobooks and radio dramas — they have distinct personalities (e.g. "恐怖小丑", "温柔知性的辅导员", "帅气少年感的青年教师").

### By cloning (--ref-audio / --ref-audio-url)

Provide a reference audio clip (max 30s, max 10MB) and the model clones the timbre. No additional charge.

```bash
uv run scripts/seed-audio-gen.py "用参考音色朗读：这是克隆后的声音。" --ref-audio ~/my-voice.wav
```

In the prompt, you can simply describe "用参考音色朗读" or "用提供的声音说" — the model understands the reference is the voice source.

### By character description (no reference)

If no `--speaker` or `--ref-audio` is provided, the model generates a voice from the character description in the prompt. This is the most flexible approach: just describe the voice you want ("一位声音沙哑的老船长", "一个活泼可爱的少女", "一位严肃的新闻播音员").

## Prompt Length

- **Hard limit**: 3000 characters (the CLI rejects longer prompts with an error).
- **Recommended**: For Chinese voice content, keep the spoken dialogue to **400 characters or fewer**. While the hard limit is 3000, the model's quality degrades when the voice content is too dense. Scene description, BGM, and sound effect instructions are part of the 3000 limit but do not count toward the 400-char voice recommendation.

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

## Tips

- **Be specific, not vague**: "轻柔的钢琴独奏" beats "有音乐". "声音沙哑的老人" beats "一个老年人".
- **Layer, don't list**: Describe the scene as a whole rather than a checklist. The model understands narrative flow.
- **Timestamp for precision, omit for flow**: Use timestamps when you need exact timing (ads, synced dialogue). Omit them when you want the model to pace naturally.
- **Use sound effects as punctuation**: "句首" / "句尾" / "伴随着" / "然后" — these position words help the model place effects relative to dialogue.
- **The model may paraphrase**: It's generative, not deterministic. If verbatim accuracy is critical, use `volcengine-tts` instead.
- **Test and iterate**: seed-audio rewards prompt experimentation. Start simple, listen, then add detail.