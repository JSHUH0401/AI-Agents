from flask import Flask, render_template, request
from Lang_news_crawler import get_news_articles

# Flask 앱을 생성합니다.
app = Flask(__name__)

# 기본 URL 경로('/')에 대한 처리를 정의합니다.
# GET 방식은 페이지를 처음 로드할 때, POST 방식은 폼을 제출(검색 버튼 클릭)할 때 사용됩니다.
@app.route('/', methods=['GET','POST'])
#index함수는 기본 홈페이지로 돌아갈 때 알아서 실행될 수 있는 함수를 작성
def index():
    #뒤의 render_template를 위해서 미리 만들어 두는 것.
    articles = []
    topic = ""
    if request.method == 'POST':
        # 사용자가 입력한 주제를 폼에서 가져옵니다.
        topic = request.form['topic']
        # news_crawler.py의 get_news 함수를 호출해 뉴스 데이터를 가져옵니다.
        articles = get_news_articles(topic)

    # index.html 템플릿을 렌더링합니다.
    # articles와 topic 변수를 템플릿으로 전달하여 화면에 표시할 수 있게 합니다.
    #클라 인 웹 브라우저는 그냥 다 합쳐진 index.html만 받아서 출력함.
    return render_template('index.html', articles=articles, topic=topic)

# 이 스크립트가 직접 실행될 때만 Flask 서버를 실행합니다.
if __name__ == '__main__':
    # debug=True 모드는 코드가 변경될 때마다 서버를 자동으로 재시작해줘서 개발 시 편리합니다.
    app.run(debug=True)
    #배포할 때에는 False로 만들고 올려라. 무조오오오오오건