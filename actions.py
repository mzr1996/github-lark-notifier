from datetime import datetime
from configparser import ConfigParser


CONFIG = ConfigParser()
CONFIG.read('./config.ini')
MAINTAINER = CONFIG['member'].pop('maintainer')
MEMBER_MAPPING = CONFIG['member']

ACTIONS = []
register = lambda c: ACTIONS.append(c())

@register
class OpenIssue:
    def condition(self, message: dict):
        action = message.get('action', None)
        return (action == 'opened' and 'issue' in message)

    def report(self, message: dict):
        issue = message['issue']
        title = issue.get('title', "")
        url = issue.get('html_url', "")
        return f"【Issue】{title}\n{url}\n"

@register
class CommentIssue:
    def condition(self, message: dict):
        action = message.get('action', None)
        return (action == 'created' and 'issue' in message
                and 'comment' in message)

    def report(self, message: dict):
        issue = message['issue']
        comment = message['comment']
        title = issue.get('title', "")
        url = comment.get('html_url', "")
        author = comment['user']['login']
        if author in MEMBER_MAPPING or author in "mm-assistant[bot]":
            # 成员的评论回复不用通知了
            return None

        return f"【Issue】{author} 评论了 {title}\n{url}\n"


@register
class OpenPR:
    def condition(self, message:dict):
        action = message.get('action', None)
        return (action == 'opened' and 'pull_request' in message)

    def report(self, message: dict):
        pr = message['pull_request']
        title = pr.get('title', "")
        url = pr.get('html_url', "")

        reviewers = [
            MEMBER_MAPPING.get(i['login'], i['login'])
            for i in pr.get('requested_reviewers', [])
        ]
        text = f'【PR】{title}\n{url}\n'
        if len(reviewers) > 0:
            text += f'请 {", ".join(reviewers)} 进行 review\n'

        return text

@register
class RequestReviewer:
    def condition(self, message:dict):
        action = message.get('action', None)
        return (action == 'review_requested' and 'pull_request' in message)

    def report(self, message: dict):
        pr = message['pull_request']
        title = pr.get('title', "")
        url = pr.get('html_url', "")

        number = pr.get('number')

        parse_time = lambda time: datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')

        create_time = parse_time(pr['created_at'])
        update_time = parse_time(pr['updated_at'])
        if create_time != update_time:
            # 滤除 open pr 同时分配 reviewer 的情况
            reviewer = message['requested_reviewer']['login']
            reviewer = MEMBER_MAPPING.get(reviewer, reviewer)
            text = f"【PR】请 {reviewer} review PR{number} - {title}\n{url}\n"
            return text

@register
class SubmitReview:
    def condition(self, message:dict):
        action = message.get('action', None)
        return (action == 'submitted' and 'pull_request' in message
                and 'review' in message)

    def report(self, message: dict):
        pr = message['pull_request']
        review = message['review']
        state = review['state']
        url = pr.get('html_url', "")
        number = pr.get('number')

        reviewer = review['user']['login']
        author = pr['user']['login']

        if state == "changes_requested" and author in MEMBER_MAPPING:
            author = MEMBER_MAPPING[author]
            return f"【PR】{reviewer} 请求 {author} 对 PR{number} 进行修改\n{url}\n"
        elif state == "approved" and reviewer != MAINTAINER:
            # maintainer approve 的 PR 就不用通知了
            maintainer = MEMBER_MAPPING[MAINTAINER]
            return f"【PR】{reviewer} 同意了 PR{number}. {maintainer}\n{url}\n"

        return None

@register
class CreateDiscussion:
    def condition(self, message:dict):
        action = message.get('action', None)
        return (action == 'created' and 'discussion' in message
                and 'comment' not in message)

    def report(self, message: dict):
        discussion = message['discussion']
        url = discussion.get('html_url', "")
        title = discussion.get('title')

        author = discussion['user']['login']

        return f'【讨论】{author} 创建了新的讨论：{title}\n{url}\n'

@register
class CommentDiscussion:
    def condition(self, message:dict):
        action = message.get('action', None)
        return (action == 'created' and 'discussion' in message
                and 'comment' in message)

    def report(self, message: dict):
        discussion = message['discussion']
        comment = message['comment']
        url = comment.get('html_url', "")
        title = discussion.get('title')

        author = comment['user']['login']
        if author in MEMBER_MAPPING:
            # 成员的评论回复不用通知了
            return None

        return f'【讨论】{author} 评论了 {title}\n{url}\n'
