# seed-audio-1.0 音色速查（精选）

> 本表为**精选速查**：每场景按热度列 Top 5，带试听链接。全量 444 个音色（244 bigtts + 200 ICL，截至 2026-08-27）在 `speakers.json`，请勿把 speakers.json 读进上下文（约 220KB）；用下列命令查询。

```bash
uv run scripts/seed-audio-gen.py --list-speakers                          # 全量
uv run scripts/seed-audio-gen.py --list-speakers --filter scene=视频配音   # 按场景
uv run scripts/seed-audio-gen.py --list-speakers --filter lang=ja --sort heat
```

需要某个场景的全量音色（如全部 156 个角色扮演音）时，跑 `--list-speakers --filter scene=<场景>`。

## 通用场景（本场景共 133 个，列 Top 5；全量用 `--list-speakers --filter scene=通用场景`）

| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |
|---|---|---|---|---|---|
| 💐 Vivi 2.0 | `zh_female_vv_uranus_bigtts` | 女 | 语调平稳、咬字柔和、自带治愈安抚力的女声音色 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_vv_uranus_bigtts.wav) | 100 |
| 甜美小源 2.0 | `zh_female_tianmeixiaoyuan_uranus_bigtts` | 女 | 声线明亮甜美的专业客服，亲切耐心，服务细致周到 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_tianmeixiaoyuan_uranus_bigtts.mp3) | 12 |
| 爽快思思 2.0 | `zh_female_shuangkuaisisi_uranus_bigtts` | 女 | 温暖直爽的邻家小妹，阳光热情，相处轻松自在 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_shuangkuaisisi_uranus_bigtts.mp3) | 10 |
| 小何 2.0 | `zh_female_xiaohe_uranus_bigtts` | 女 | 声线甜美有活力的妹妹，活泼开朗，笑容明媚。 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_xiaohe_uranus_bigtts.mp3) | 9 |
| 开朗姐姐  2.0 | `zh_female_kailangjiejie_uranus_bigtts` | 女 | 语调明快、声线爽朗，阳光开朗的大姐姐音 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_kailangjiejie_uranus_bigtts.mp3) | 7 |

## 角色扮演（本场景共 156 个，列 Top 5；全量用 `--list-speakers --filter scene=角色扮演`）

| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |
|---|---|---|---|---|---|
| 熊二 2.0 | `zh_male_xionger_uranus_bigtts` | 男 | 声线憨厚软糯、语气呆萌，自带东北口音的可爱男声 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_male_xionger_uranus_bigtts.mp3) | 1 |
| 撒娇学妹 2.0 | `zh_female_sajiaoxuemei_uranus_bigtts` | 女 | 嗲甜软萌的可爱妹妹，灵动娇气，活泼讨喜 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_sajiaoxuemei_uranus_bigtts.mp3) | 1 |
| 知性灿灿 2.0 | `zh_female_cancan_uranus_bigtts` | 女 | 语气温柔舒缓，软糯但有善解人意的治愈系少女音 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_cancan_uranus_bigtts.mp3) | 1 |
| 调皮公主 2.0 | `ICL_uranus_zh_female_tiaopigongzhu_tob` | 女 | 娇俏公主，古灵精怪，偶尔娇气带点小自大 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ICL_uranus_zh_female_tiaopigongzhu_tob.wav) | 1 |
| 顾姐 2.0 | `zh_female_gujie_uranus_bigtts` | 女 | 声线干练、气场强大，飒爽独立的大女主音 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_gujie_uranus_bigtts.mp3) | 0 |

## 视频配音（本场景共 42 个，列 Top 5；全量用 `--list-speakers --filter scene=视频配音`）

| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |
|---|---|---|---|---|---|
| 黑猫侦探社咪仔 2.0 | `zh_female_mizai_uranus_bigtts` | 女 | 声线稳重优雅的知心姐姐，温暖亲和，善于陪伴 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_mizai_uranus_bigtts.mp3) | 7 |
| 佩奇猪 2.0 | `zh_female_peiqi_uranus_bigtts` | 女 | 活泼童趣，天真烂漫，可爱治愈 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_peiqi_uranus_bigtts.mp3) | 4 |
| 流畅女声 2.0 | `zh_female_liuchangnv_uranus_bigtts` | 女 | 温暖爽朗的小妹，阳光热情，性格直爽好相处 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_liuchangnv_uranus_bigtts.mp3) | 3 |
| 鸡汤女 2.0 | `zh_female_jitangnv_uranus_bigtts` | 女 | 声音治愈的知心姐姐，温柔体贴，擅长倾听与理解 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_jitangnv_uranus_bigtts.mp3) | 3 |
| 大壹 2.0 | `zh_male_dayi_uranus_bigtts` | 男 | 历经世事的沉稳大叔，果敢可靠，让人安心信赖 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_male_dayi_uranus_bigtts.mp3) | 3 |

## 有声阅读（本场景共 29 个，列 Top 5；全量用 `--list-speakers --filter scene=有声阅读`）

| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |
|---|---|---|---|---|---|
| 儿童绘本 2.0 | `zh_female_xiaoxue_uranus_bigtts` | 女 | 清甜讲述者，充满童趣与耐心，为孩子编织美好梦境 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_xiaoxue_uranus_bigtts.mp3) | 3 |
| 深夜播客 2.0 | `zh_male_shenyeboke_uranus_bigtts` | 男 | 语调舒缓、情感细腻，适配深夜陪伴的多情感男声，氛围感拉满 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_male_shenyeboke_uranus_bigtts.mp3) | 0 |
| 霸气青叔 2.0 | `zh_male_baqiqingshu_uranus_bigtts` | 男 | 声线浑厚成熟、气场强大，阅历感十足的叔音 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_male_baqiqingshu_uranus_bigtts.mp3) | 0 |
| 擎苍 2.0 | `zh_male_qingcang_uranus_bigtts` | 男 | 声线雄浑厚重、气势磅礴，充满力量感的霸气男声 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_male_qingcang_uranus_bigtts.mp3) | 0 |
| 儒雅青年 2.0 | `zh_male_ruyaqingnian_uranus_bigtts` | 男 | 语调温润、咬字文雅，书卷气十足的知性男声 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_male_ruyaqingnian_uranus_bigtts.mp3) | 0 |

## 趣味口音（本场景共 15 个，列 Top 5；全量用 `--list-speakers --filter scene=趣味口音`）

| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |
|---|---|---|---|---|---|
| Orion | `en_male_deep-voice_uranus_bigtts` | 男 | 嗓音沉实有质感，语速舒缓，戏剧表现力拉满。 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/en_male_deep-voice_uranus_bigtts.wav) | 0 |
| Silas | `ru_male_vlad_uranus_bigtts` | 男 | 轻柔低语的男生，性情温和内敛，沉静平和。 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ru_male_vlad_uranus_bigtts.wav) | 0 |
| Lily | `ja_female_bv523_uranus_bigtts` | 女 | 天真烂漫的女童，语调灵动，满是童真童趣。 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ja_female_bv523_uranus_bigtts.wav) | 0 |
| Aoi | `ja_female_bv521_uranus_bigtts` | 女 | 甜美灵动的女生，日系少女声线，表演感染力强。 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ja_female_bv521_uranus_bigtts.wav) | 0 |
| Sharron | `en_female_sharron_uranus_bigtts` | 女 | 声线轻柔带哑，语气悠然闲适的大小姐 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/en_female_sharron_uranus_bigtts.wav) | 0 |

## 多语种（本场景共 19 个，列 Top 5；全量用 `--list-speakers --filter scene=多语种`）

| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |
|---|---|---|---|---|---|
| Big Boogie 2.0 | `ICL_uranus_en_male_big_boogie_tob` | 男 | 声音沙哑浑厚的爷爷，从容有气度，擅长英语 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ICL_uranus_en_male_big_boogie_tob.wav) | 0 |
| Michael 2.0 | `ICL_uranus_en_male_michael_tob` | 男 | 平易近人的学长，温暖亲切，待人真诚，擅长英语 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ICL_uranus_en_male_michael_tob.wav) | 0 |
| Kevin McCallister 2.0 | `ICL_uranus_en_male_kevin_mccallister_tob` | 男 | 可爱乖巧的萌娃，说话干净软糯，擅长英语 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ICL_uranus_en_male_kevin_mccallister_tob.wav) | 0 |
| The Grinch 2.0 | `ICL_uranus_en_male_the_grinch_tob` | 男 | 声音磁性的成熟大叔，沉稳直率，擅长英语 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ICL_uranus_en_male_the_grinch_tob.wav) | 0 |
| Frosty Man 2.0 | `ICL_uranus_en_male_frosty_man_tob` | 男 | 低沉浑厚的儒雅大叔，温柔亲切，擅长英语 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ICL_uranus_en_male_frosty_man_tob.wav) | 0 |

## 教学场景（本场景共 21 个，列 Top 5；全量用 `--list-speakers --filter scene=教学场景`）

| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |
|---|---|---|---|---|---|
| Tina老师 2.0 | `zh_female_yingyujiaoxue_uranus_bigtts` | 女 | 磁性知性的青年讲师，温柔耐心，专业靠谱 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_yingyujiaoxue_uranus_bigtts.mp3) | 21 |
| Charlotte | `en_female_authoritative-british_uranus_bigtts` | 女 | 清亮利落，张力十足的姐姐 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/en_female_authoritative-british_uranus_bigtts.wav) | 1 |
| Arthur | `pt_male_bv531_uranus_bigtts` | 男 | 理智客观的中年男声，行事稳重可靠。 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/pt_male_bv531_uranus_bigtts.wav) | 0 |
| Irene | `mx_female_bv065_uranus_bigtts` | 女 | 冷静客观的干练女生，做事干练且条理分明。 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/mx_female_bv065_uranus_bigtts.wav) | 0 |
| Zendaya | `en_female_zendaya_p1_uranus_bigtts` | 女 | 随性亲切的姐姐，松弛不拘谨又有活力。 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/en_female_zendaya_p1_uranus_bigtts.wav) | 0 |

## 客服场景（本场景共 28 个，列 Top 5；全量用 `--list-speakers --filter scene=客服场景`）

| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |
|---|---|---|---|---|---|
| 暖阳女声 2.0 | `zh_female_kefunvsheng_uranus_bigtts` | 女 | 开朗温柔的客服，阳光热情，服务贴心细致 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_female_kefunvsheng_uranus_bigtts.mp3) | 2 |
| 客服婉君 2.0 | `ICL_uranus_zh_female_kefuwanjun_tob` | 女 | 语气亲切，善用温和语气词，回复条理清晰的客服女生 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/ICL_uranus_zh_female_kefuwanjun_tob.mp3) | 0 |
| 营销小楠 2.0 | `ICL_uranus_zh_female_yingxiaokefu_v2_tob` | 女 | 偏低沉的暖女中音，气息稳、质感厚，讲起营销策略自带一种 "她说的都对" 的说服力。
 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/ICL_uranus_zh_female_yingxiaokefu_v2_tob.mp3) | 0 |
| Scarlet | `en_female_scarlet_p1_uranus_bigtts` | 女 | 柔婉深情的姐姐，眼里永远盛着光 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/en_female_scarlet_p1_uranus_bigtts.wav) | 0 |
| Ivy | `en_female_lana_del_rey_parky_s_p1_uranus_bigtts` | 女 | 温婉柔和女声，语调亲切自然，听感温润怡人 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/audio/en_female_lana_del_rey_parky_s_p1_uranus_bigtts.wav) | 0 |

## 其他（本场景共 1 个，列 Top 1；全量用 `--list-speakers --filter scene=其他`）

| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |
|---|---|---|---|---|---|
| 东方浩然 2.0 | `zh_male_dongfanghaoran_uranus_bigtts` | 男 | 声线雄浑、气场强大，正气凛然的成熟男声 | [试听](https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/zh_male_dongfanghaoran_uranus_bigtts.mp3) | 1 |
