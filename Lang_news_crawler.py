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

# OpenAI API 키 설정
# .env 파일에 OPENAI_API_KEY="sk-..." 형태로 키가 저장되어 있어야 합니다.
# 참고: openai 라이브러리는 환경변수 OPENAI_API_KEY를 자동으로 읽어 사용합니다.
client = openai.OpenAI()
llm = ChatOpenAI(model ="gpt-3.5 turbo", temperature = 0)

prompt = ChatPromptTemplate.from_messages(
    [("system", "You are a Helpful assistant that summarizes news articles in three sentences in Korean"),
     ("user","다음 뉴스 기사를 세 문장으로 요약해줘:{article_text}")]
)

summarize_chain = prompt | llm | StrOutputParser()
'''
1. 기사 텍스트 가져오기
2. 텍스트 요약하기
'''

def get_article_text_with_loader(url):
    if not url:
        return""
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        if docs:
            return docs[0].page_content
        return ""
    except Exception as e:
        print(f"{url}의 텍스트를 가져오는 데 실패: Error: {e}")
        return ""
#Webbaseloader로 변환
'''
def get_article_text(url):
    """URL에서 웹페이지의 본문 텍스트를 추출합니다."""
    if not url:
        return ""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()  # HTTP 에러가 발생하면 예외를 발생시킴

        soup = BeautifulSoup(response.text, 'html.parser')

        # 일반적인 기사 본문 태그들을 시도합니다. (p, article, main 등)
        # 이 부분은 웹사이트 구조에 따라 맞춤 조정이 필요할 수 있습니다.
        article_body = soup.find('article') or soup.find('main') or soup.body
        
        if article_body:
            paragraphs = article_body.find_all('p')
            text = ' '.join([p.get_text() for p in paragraphs])
            return text
        return ""
    except requests.RequestException as e:
        print(f"URL 텍스트를 가져오는 중 에러 발생: {url}, error: {e}")
        return ""
'''
#Summerizationo Chain으로 변환
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
            temperature=0.5,
        )
        summary = response.choices[0].message.content
        return summary.strip()
    except Exception as e:
        print(f"OpenAI API 호출 중 에러 발생: {e}")
        return "AI 요약 중 에러가 발생했습니다."


def get_news_articles(topic, page_size=5):
    """
    이 함수는 NewsAPI를 사용하여 '뉴스 목록'을 가져온 후,
    각 기사의 본문을 가져와 AI로 요약하는 전체 과정을 담당합니다.
    """
    print(f"'{topic}'에 대한 뉴스를 검색하고 AI 요약을 시작합니다.")
    
    # 1. NewsAPI를 사용해 뉴스 목록 가져오기
    # ------------------------------------------------------------------
    # 여기에 기존에 작성하셨던 NewsAPI 호출 코드를 유지합니다.
    # ------------------------------------------------------------------
    base_url = "https://newsapi.org/v2/everything"
    api_key = os.getenv("NEWS_API_KEY") # .env에서 NewsAPI 키를 가져옵니다.
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
                summarize_chain.invoke({"article_text":full_text[:4000]})
            except Exception as e:
                print(f"Langchain 실행 중 에러 발생: Error: {e}")
                summary = "AI 실행 중 에러가 발생했습니다."
            
        article["summary"] = summary.strip()
        summarized_articles.append(article)
    return summarized_articles