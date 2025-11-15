from dotenv import load_dotenv
import os
import openai
import requests
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import WebBaseLoader

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()
# .env 파일에 OPENAI_API_KEY="sk-..." 형태로 키가 저장되어 있어야 합니다.
# 참고: openai 라이브러리는 환경변수 OPENAI_API_KEY를 자동으로 읽어 사용합니다.

llm = ChatOpenAI(model ="gpt-3.5 turbo", temperature = 0)

prompt = ChatPromptTemplate.from_messages(
    [("system", "You are a Helpful assistant that summarizes news articles in three sentences in Korean"),
     ("user","다음 뉴스 기사를 세 문장으로 요약해줘:{article_text}")]
)

#prompt: 사용자에게 받은 article text를 system, user 메시지에 맞춰 llm이 이해할 수 있는 프롬프트로 변환.
#llm: 프롬프트를 gpt에게 전달하고, 모델로부터 요약된 기사를 포함한 응답을 받음.
#stroutputparser: 전달받은 요약 응답에서 텍스트만 추출함
summarize_chain = prompt | llm | StrOutputParser()

'''
1. 기사 텍스트 가져오기
2. 텍스트 요약하기
'''
#Webbaseloader: 웹페이지 텍스트 추출 및 정제. AI가 처리할 텍스트를 만드는 역할
#WebBaseLoader가 가져온 기사의 텍스트 추출
def get_article_text_with_loader(url):
    if not url:
        return""
    try:
        #HTML에서 document들의 텍스트를 다 가져옴
        loader = WebBaseLoader(url)
        #그것들을 추출하는 역할
        docs = loader.load()
        if docs:
            return docs[0].page_content
        return ""
    except Exception as e:
        print(f"{url}의 텍스트를 가져오는 데 실패: Error: {e}")
        return ""
'''
#Summerizationo Chain으로 기사 요약
def summarize_with_openai(text):
    """OpenAI API를 사용해 텍스트를 요약합니다."""
    if not text or len(text.strip()) < 100: # 너무 짧은 텍스트는 요약하지 않음
        return "요약할 내용이 충분하지 않습니다."

    try:
        # GPT-3.5-turbo 모델을 사용해 요약을 요청합니다.
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news articles in three sentences in Korean."},
                {"role": "user", "content": f"다음 뉴스 기사를 세 문장으로 요약해줘: {text[:4000]}"} # 토큰 제한을 위해 텍스트 일부만 사용
            ],
            temperature=0,
        )
        summary = response.choices[0].message.content
        return summary.strip()
    except Exception as e:
        print(f"OpenAI API 호출 중 에러 발생: {e}")
        return "AI 요약 중 에러가 발생했습니다."
'''

#메인 함수
def get_news_articles(topic, page_size=5):
    """
    이 함수는 NewsAPI를 사용하여 '뉴스 목록'을 가져온 후,
    각 기사의 본문을 가져와 AI로 요약하는 전체 과정을 담당합니다.
    """
    print(f"'{topic}'에 대한 뉴스를 검색하고 AI 요약을 시작합니다.")
    
    # 1. NewsAPI를 사용해 뉴스 목록 가져오기
    base_url = "https://newsapi.org/v2/everything"
    api_key = os.getenv("NEWS_API_KEY") # .env에서 NewsAPI 키를 가져옵니다.
    #params는 newsapi 서버와 이미 합의된 형식들
    params = {
        "q": topic,
        "language": "ko",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": api_key
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["status"] != "ok":
            print(f"NewsAPI 오류: {data.get('message', '알 수 없는 오류')}")
            return []
        
        initial_articles = data.get("articles", [])
        
    except requests.exceptions.RequestException as e:
        print(f"네트워크 또는 API 요청 오류 발생: {e}")
        return []
    # ------------------------------------------------------------------

    # 2. 뉴스 목록을 순회하며 각 기사의 본문을 가져오고 요약합니다.
    summarized_articles = []
    for article in initial_articles:
        print(f"기사 요약 중: {article.get('title')}")
        
        # 기사 본문 텍스트 가져오기
        full_text = get_article_text_with_loader(article.get('url'))
        
        if not full_text or len(full_text)< 100:
            summary = "요약할 내용이 충분하지 않습니다."
        else:
            try:
                #가져온 기사 텍스트 요약하기
                summarize_chain.invoke({"article_text":full_text[:4000]})
            except Exception as e:
                print(f"Langchain 실행 중 에러 발생: Error: {e}")
                summary = "AI 실행 중 에러가 발생했습니다."
            
        article["summary"] = summary.strip()
        summarized_articles.append(article)
    return summarized_articles