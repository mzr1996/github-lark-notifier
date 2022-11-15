# github-lark-notifier
github - 飞书自定义消息提醒

# Feature
1. issue 创建，评论 issue，PR 创建，请求 PR review，提交 review 意见（Request Changes / Approve），创建 Discussion 讨论，评论 Discussion 讨论时，给飞书发提醒
2. 仅周一至周五且 10~19 点才工作（可在 `config.ini` 中配置）
3. 非工作期间的消息，都记入 `history.txt`，到达工作时间时一起发。

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

# 如何配置自定义的通知类型
1. 可以在 `config.ini` 中设置 `save_receive` 为 yes，这样会以 json 格式保存所有 GitHub 发送给你的信息。
2. 触发一次你想配置的通知行为，然后从所有保存的 json 信息中找到该行为对应的 json 文件。
3. 在 `actions.py` 中添加一个类，并用 `@register` 注册。这个类需要实现两个方法：
   - `condition` 方法接受字典类型的 `message` 参数，也就是 GitHub 给你发的各种 json 信息，这个方法需要根据 json 的特征判断是否是你想触发通知的消息类型，并返回布尔值。
   - `report` 方法同样接受 `message` 参数，并根据 `message` 参数返回你想给飞书发送的消息文本，返回 None 则不发消息。

**注意**：如果你在配置 GitHub hook 的时候没有勾选相应的行为，则无法触发相应的 GitHub 通知。


# 致谢
* Modified from https://github.com/tpoisonooo/cpp-syntactic-sugar/tree/master/github-lark-notifier

# License
[license](LICENSE)
