from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


load_dotenv(encoding='utf-8')

class BaseRetriever:
    def __init__(self, llm, template, question, retriever):
        self.llm = llm
        self.prompt = template.base_template()
        self.question = question
        self.retriever = retriever.base()


    async def get_answer(self):
        try:
            chain = (
                    {"context": self.retriever, "question": RunnablePassthrough()}
                    | self.prompt
                    | self.llm
                    | StrOutputParser()
            )
            answer = await chain.ainvoke(self.question)
            return answer
        except Exception as e:
            print(f"API Error: {e}")  # 💡 如果是配額問題，這裡會寫 "Quota exceeded"
            raise e



