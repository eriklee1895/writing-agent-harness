# Notion Property 别名表

本文件记录 article-to-notion skill 在填充 Notion database properties 时使用的字段名启发式匹配规则。

匹配规则：
- 字段名比较时忽略大小写、忽略首尾空格
- 一个字段只能匹配一个语义；按表中顺序优先
- 匹配到就填，匹配不到就跳过，不报错

## 字段映射

### 标题
- `name`
- `title`
- `标题`
- `名称`
- `名字`

### 原文链接
- `url`
- `link`
- `links`
- `链接`
- `原文`
- `source`
- `source_url`

### 摘要/介绍
- `summary`
- `description`
- `intro`
- `introduction`
- `介绍`
- `摘要`
- `描述`
- `note`
- `notes`

### 标签/类型
- `tags`
- `type`
- `types`
- `类型`
- `标签`
- `tag`
- `category`
- `categories`

### 作者/来源
- `author`
- `account`
- `source`
- `来源`
- `作者`
- `公众号`
- `账号`
- `publisher`

### 发布日期
- `date`
- `published`
- `publish_date`
- `发布时间`
- `发布日期`
- `创建时间`
- `created_time`
