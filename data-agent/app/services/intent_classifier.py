from enum import StrEnum


class QueryIntent(StrEnum):
    DATA_QUERY = "data_query"
    CHAT = "chat"
    UNCLEAR = "unclear"


DATA_QUERY_KEYWORDS = (
    "销售额",
    "销量",
    "销售量",
    "订单量",
    "订单数",
    "客单价",
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
    "排行",
    "趋势",
    "同比",
    "环比",
    "占比",
    "省",
    "省份",
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

CHAT_KEYWORDS = (
    "你好",
    "您好",
    "hi",
    "hello",
    "嗨",
    "在吗",
    "早上好",
    "下午好",
    "晚上好",
    "谢谢",
    "感谢",
    "多谢",
    "thanks",
    "thankyou",
    "帮助",
    "help",
    "你能做什么",
    "怎么用",
    "如何使用",
    "可以问什么",
    "示例问题",
)

AMBIGUOUS_TIME_WORDS = (
    "今天",
    "昨天",
    "本周",
    "上周",
    "本月",
    "上月",
    "今年",
    "去年",
    "最近",
)

AMBIGUOUS_ACTION_WORDS = (
    "怎么样",
    "如何",
    "看看",
    "看下",
    "看一下",
    "分析一下",
    "情况",
    "表现",
)


def classify_query_intent(query: str) -> QueryIntent:
    text = query.strip().lower()
    compact_text = "".join(text.split())

    if not compact_text:
        return QueryIntent.CHAT

    if any(keyword in compact_text for keyword in DATA_QUERY_KEYWORDS):
        return QueryIntent.DATA_QUERY

    if any(keyword in compact_text for keyword in CHAT_KEYWORDS):
        return QueryIntent.CHAT

    has_time_word = any(word in compact_text for word in AMBIGUOUS_TIME_WORDS)
    has_action_word = any(word in compact_text for word in AMBIGUOUS_ACTION_WORDS)
    if has_time_word or has_action_word:
        return QueryIntent.UNCLEAR

    return QueryIntent.CHAT
