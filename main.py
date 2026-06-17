import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import openai

# .env 파일 로드
load_dotenv()

app = FastAPI()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- 프롬프트 생성 로직 ---
def generate_behavior_note(api_key, user_input):
    client = openai.OpenAI(api_key=api_key)
    
    system_prompt = """
    당신은 고등학교 생활기록부 '행동특성 및 종합의견'을 작성하는 베테랑 교사입니다.
    입력된 키워드를 바탕으로 격조 있고 풍성한 문장을 작성하십시오.

    [핵심 작성 규칙]
    1. 주어 삭제: '해당 학생은', '이 학생은', '본인은' 등의 단어를 절대 사용하지 마십시오.
    2. **관찰 단어 금지**: '관찰됨', '확인됨', '보여짐', '분석됨', '나타남' 등의 단어를 문장 끝이나 중간에 절대 쓰지 마십시오.
    3. **직접 서술**: '원만함이 관찰됨' 대신 '원만함', '우수함이 관찰됨' 대신 '우수함' 또는 '우수성을 발휘함'과 같이 사실과 상태를 직접 기술하십시오.
    4. 분량 최적화: 공백 포함 900~1000바이트(한글 기준 약 300자 내외)로 내용을 풍성하게 구성하십시오.
    5. 내용 구성: 키워드를 바탕으로 구체적인 상황과 긍정적인 파생 효과를 포함하여 전문적으로 서술하십시오.
    6. 어미 처리: 반드시 명사형 어미(~함, ~임, ~됨)로 종결하십시오.
    """

    user_prompt = f"학생 키워드: {user_input}\n\n위 키워드를 바탕으로 나이스 행발용(1000바이트 내외)으로 전문적인 문장을 작성해줘. '관찰됨' 같은 표현은 절대 쓰지 마."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7, 
        max_tokens=800
    )
    return response.choices[0].message.content

# --- 나이스 기준 바이트 계산 함수 ---
def count_neis_bytes(text):
    count = 0
    for char in text:
        if ord(char) <= 127: # ASCII (영문, 숫자, 기호)
            count += 1
        else: # 한글 및 특수문자
            count += 3
    return count

# --- HTML 템플릿 ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI 행발 생성기 (직접 서술형)</title>
    <style>
        body {{ font-family: 'Malgun Gothic', apple-system, sans-serif; background-color: #f4f7f9; color: #333; line-height: 1.6; padding: 40px 20px; }}
        .container {{ max-width: 850px; margin: 0 auto; background: #fff; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
        h1 {{ color: #1a73e8; font-size: 24px; border-bottom: 2px solid #e8f0fe; padding-bottom: 15px; }}
        p {{ color: #666; font-size: 14px; }}
        textarea {{ width: 100%; height: 120px; padding: 15px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 16px; margin: 20px 0; resize: none; }}
        textarea:focus {{ border-color: #1a73e8; outline: none; }}
        button {{ background: #1a73e8; color: white; padding: 13px 28px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; font-weight: bold; transition: 0.3s; }}
        button:hover {{ background: #1557b0; }}
        .result-box {{ background: #fdfdfd; padding: 25px; margin-top: 30px; border: 1px solid #eee; border-radius: 12px; font-size: 17px; white-space: pre-wrap; line-height: 1.9; border-left: 5px solid #1a73e8; }}
        .stats {{ margin-top: 15px; font-weight: bold; font-size: 15px; }}
        .copy-btn {{ background: #34a853; margin-top: 15px; }}
        .copy-btn:hover {{ background: #2d8e47; }}
        .footer {{ margin-top: 30px; text-align: center; color: #999; font-size: 12px; }}
    </style>
    <script>
        function copyText() {{
            const text = document.getElementById("resultArea").innerText;
            navigator.clipboard.writeText(text).then(() => alert("복사되었습니다!"));
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>📑 정제된 행발 직접 서술 생성기</h1>
        <p>"해당 학생은" 및 "관찰됨" 표현 없이 <b>직접적인 상태 서술</b>로 1,000바이트 분량을 채워줍니다.</p>
        
        {content}
        
        <div class="footer">OpenAI GPT-4o-mini를 활용하여 최적화된 문장을 생성합니다.</div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    form_html = """
    <form action="/generate" method="post">
        <textarea name="keywords" placeholder="사례 예시: 수학적 추론 능력 우수, 학급 청소 시간에 성실함, 친구 관계 원만함" required></textarea>
        <button type="submit">행발 문구 생성</button>
    </form>
    """
    return HTML_LAYOUT.format(content=form_html)

@app.post("/generate", response_class=HTMLResponse)
async def handle_generate(keywords: str = Form(...)):
    if not OPENAI_API_KEY:
        return "오류: .env 파일에 OPENAI_API_KEY를 설정해주세요."

    result_text = generate_behavior_note(OPENAI_API_KEY, keywords)
    byte_size = count_neis_bytes(result_text)
    byte_color = "#1a73e8" if byte_size <= 1000 else "#d93025"

    result_html = f"""
    <div class="result-box" id="resultArea">{result_text}</div>
    <div class="stats" style="color: {byte_color};">
        현재 크기: {byte_size} / 1000 Bytes (나이스 기준)
    </div>
    <button class="copy-btn" onclick="copyText()">클립보드로 복사</button>
    <br><br>
    <a href="/" style="text-decoration: none; color: #1a73e8;">← 다시 입력하기</a>
    """
    return HTML_LAYOUT.format(content=result_html)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
