from langchain_core.prompts import ChatPromptTemplate


class Template:
    @staticmethod
    def base_template():
        template = [
            ("system", """請根據背景資料回答問題：
                        背景資料：{context}"""),
            ("human", "問題：{question}")
        ]
        prompt = ChatPromptTemplate.from_messages(template)
        return prompt

    @staticmethod
    def analyze_complexity_template():
        template = [
            ("system", """分析查询的复杂度，返回以下之一:
            - simple: 简单事实性问题
            - ambiguous: 表达模糊的问题
            - complex: 需要多步推理的复杂问题
            - technical: 技术性强的专业问题
            
            只返回类别，不要解释。"""),
            ("human", "{question}")
        ]
        prompt = ChatPromptTemplate.from_messages(template)
        return prompt

    @staticmethod
    def mutiple_query_template():
        template = [
            ("system", """你是一个AI助手，负责生成查询的多个变体。
                给定一个用户查询，生成3个不同角度的相关查询。
                每行一个查询，不要编号。"""),
            ("human", "{question}")
        ]
        prompt = ChatPromptTemplate.from_messages(template)
        return prompt