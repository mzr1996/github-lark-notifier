# github-lark-notifier
github - 飞书自定义消息提醒

# Feature
1. issue 创建，PR 创建，请求 PR review，提交 review 意见（Request Changes / Approve）时，给飞书发提醒
2. 仅周一至周五且 10~19 点才工作
3. 非工作期间的消息，都记入 `history.txt`，随下一条工作消息一起发

# 基本用法
1. 复制 `config.ini.template` 至 `config.ini`
2. 打开飞书 APP，“添加机器人”、创建自定义消息机器人，得到 `lark_webhook`
3. `lark_webhook` 填入 `config.ini` 的 `webhook` 中，并配置其他配置项
4. 执行 `python3 main.py`，监听 50000 端口
5. 保证 ip+端口在公网能够访问，例如使用 `ngrok http 50000` 转发为 `robot_webhook`
6. 打开 github settings, add webhook。把 `robot_webook` 填进去、消息类型选 `application/json`

# 如何配置用户 OPENID

`config.ini` 的 member 字段允许建立 GitHub 用户名和飞书 openid 的映射，实现发送消息时 at 的功能。

获取 openid 的方式较为繁琐，请查阅飞书官方文档。

# 致谢
* Modified from https://github.com/tpoisonooo/cpp-syntactic-sugar/tree/master/github-lark-notifier

# License
[license](LICENSE)
