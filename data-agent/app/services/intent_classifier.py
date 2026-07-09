from enum import StrEnum


class QueryIntent(StrEnum):
    DATA_QUERY = "data_query"
    GREETING = "greeting"
    HELP = "help"
    THANKS = "thanks"
    CASUAL = "casual"


DATA_QUERY_KEYWORDS = (
    "销售额",
    "销量",
    "订单",
    "成交",
    "收入",
    "金额",
    "gmv",
    "aov",
    "平均",
    "总和",
    "合计",
    "统计",
    "查询",
    "多少",
    "排名",
    "趋势",
    "同比",
    "环比",
    "省",
    "地区",
    "大区",
    "商品",
    "品类",
    "品牌",
    "客户",
    "会员",
    "性别",
    "季度",
    "月份",
)

GREETING_WORDS = {
    "你好",
    "您好",
    "hi",
    "hello",
    "嗨",
    "在吗",
    "早上好",
    "下午好",
    "晚上好",
}

THANKS_WORDS = {
    "谢谢",
    "感谢",
    "多谢",
    "thanks",
    "thank you",
}

HELP_WORDS = {
    "帮助",
    "help",
    "你能做什么",
    "怎么用",
    "如何使用",
    "可以问什么",
    "示例问题",
}


def classify_query_intent(query: str) -> QueryIntent:
    text = query.strip().lower()
    compact_text = "".join(text.split())

    if not compact_text:
        return QueryIntent.CASUAL

    if any(keyword in compact_text for keyword in DATA_QUERY_KEYWORDS):
        return QueryIntent.DATA_QUERY

    if compact_text in GREETING_WORDS:
        return QueryIntent.GREETING

    if compact_text in THANKS_WORDS:
        return QueryIntent.THANKS

    if any(word in compact_text for word in HELP_WORDS):
        return QueryIntent.HELP

    return QueryIntent.CASUAL


def get_intent_reply(intent: QueryIntent) -> str:
    if intent == QueryIntent.GREETING:
        return "你好，我是智能问数助手。你可以直接问我类似“各省销售额是多少？”这样的问题。"

    if intent == QueryIntent.THANKS:
        return "不客气。你可以继续问我订单、销售额、销量、地区、商品品类等数据问题。"

    if intent == QueryIntent.HELP:
        return (
            "我可以帮你查询订单分析 Demo 数据，例如：各省销售额是多少、不同商品品类的销量是多少、"
            "华东地区的 GMV 是多少、各会员等级的订单金额是多少。"
        )

    return "我主要负责业务数据查询。你可以问我：各省销售额是多少？或不同商品品类的销量是多少？"
