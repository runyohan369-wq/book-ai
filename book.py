import streamlit as st
import requests
import json
import re
import random
import os

# -----------------------------------
# 페이지 설정
# -----------------------------------

st.set_page_config(
    page_title="AI 책 추천",
    page_icon="📚",
    layout="wide"
)

# -----------------------------------
# CSS
# -----------------------------------

st.markdown("""
<style>

.main {
    padding-top: 0.5rem;
}

.title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 3px;
}

.subtitle {
    color: gray;
    margin-bottom: 20px;
    font-size: 14px;
}

.book-card {
    background-color: white;
    padding: 18px;
    border-radius: 18px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    margin-bottom: 25px;
    transition: 0.2s;
}

.book-card:hover {
    transform: translateY(-4px);
}

.book-title {
    font-size: 20px;
    font-weight: bold;
    margin-top: 10px;
}

.book-author {
    color: gray;
    margin-bottom: 10px;
}

.ai-box {
    background-color: #f5f7ff;
    padding: 12px;
    border-radius: 12px;
    margin-top: 10px;
    font-size: 15px;
}

.sidebar-box {
    background-color: white;
    padding: 15px;
    border-radius: 15px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.05);
}

.stButton>button {
    width: 100%;
    border-radius: 12px;
    height: 48px;
    font-size: 17px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------
# 제목
# -----------------------------------

st.markdown(
    '<div class="title">📚 한국 책 AI 추천</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">AI가 당신에게 맞는 책을 추천해줍니다</div>',
    unsafe_allow_html=True
)

# -----------------------------------
# API 키
# -----------------------------------

# secrets.toml 우선 사용
# 없으면 환경변수 사용

try:

    NAVER_CLIENT_ID = st.secrets[
        "NAVER_CLIENT_ID"
    ]

    NAVER_CLIENT_SECRET = st.secrets[
        "NAVER_CLIENT_SECRET"
    ]

    OLLAMA_API_KEY = st.secrets[
        "OLLAMA_API_KEY"
    ]

except:

    NAVER_CLIENT_ID = os.getenv(
        "NAVER_CLIENT_ID"
    )

    NAVER_CLIENT_SECRET = os.getenv(
        "NAVER_CLIENT_SECRET"
    )

    OLLAMA_API_KEY = os.getenv(
        "OLLAMA_API_KEY"
    )

OLLAMA_URL = "https://ollama.com/api/chat"

# -----------------------------------
# API 키 체크
# -----------------------------------

if not NAVER_CLIENT_ID:

    st.error(
        """
NAVER_CLIENT_ID가 없습니다.

방법 1:
.streamlit/secrets.toml 생성

방법 2:
환경변수 사용
"""
    )

    st.stop()

# -----------------------------------
# 상단 입력
# -----------------------------------

top1, top2 = st.columns([3, 1])

with top1:

    with st.form("search_form"):

        search_title = st.text_input(
            "🔍 책 제목 검색",
            placeholder="예: 불편한 편의점"
        )

        search_submit = st.form_submit_button(
            "🔎 검색"
        )

with top2:

    age = st.number_input(
        "🎂 나이",
        min_value=5,
        max_value=100,
        step=1
    )

# -----------------------------------
# 연령대
# -----------------------------------

if 5 <= age <= 12:
    age_text = "어린이"

elif 13 <= age <= 17:
    age_text = "청소년"

elif 18 <= age <= 49:
    age_text = "성인"

else:
    age_text = "중장년"

# -----------------------------------
# 레이아웃
# -----------------------------------

left_col, right_col = st.columns([1, 3])

# -----------------------------------
# 왼쪽 메뉴
# -----------------------------------

with left_col:

    st.markdown(
        '<div class="sidebar-box">',
        unsafe_allow_html=True
    )

    st.subheader("📚 분야")

    category = st.radio(
        "",
        [
            "문학",
            "과학",
            "시",
            "역사",
            "경제",
            "사회",
            "법",
            "철학",
            "심리학",
            "판타지",
            "추리",
            "자기계발",
            "에세이"
        ]
    )

    recommend_button = st.button(
        "📖 추천 받기"
    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

# -----------------------------------
# HTML 제거
# -----------------------------------

def remove_html(text):

    if text is None:
        return ""

    clean = re.compile('<.*?>')

    return re.sub(clean, '', text)

# -----------------------------------
# 네이버 책 API
# -----------------------------------

@st.cache_data
def get_books(keyword):

    url = (
        "https://openapi.naver.com/"
        "v1/search/book.json"
    )

    headers = {
        "X-Naver-Client-Id":
        NAVER_CLIENT_ID.strip(),

        "X-Naver-Client-Secret":
        NAVER_CLIENT_SECRET.strip()
    }

    params = {
        "query": keyword,
        "display": 20,
        "sort": "sim"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code != 200:

            st.error(
                f"""
네이버 API 오류

코드:
{response.status_code}

내용:
{response.text}
"""
            )

            return []

        data = response.json()

        return data.get("items", [])

    except Exception as e:

        st.error(f"API 오류: {e}")

        return []

# -----------------------------------
# AI 추천
# -----------------------------------

def generate_ai_summary(title, description):

    headers = {
        "Authorization":
        f"Bearer {OLLAMA_API_KEY}",

        "Content-Type":
        "application/json"
    }

    payload = {
        "model": "gpt-oss:120b",

        "messages": [
            {
                "role": "system",

                "content":
                "너는 한국 책 추천 AI이다."
            },

            {
                "role": "user",

                "content": f"""
책 제목:
{title}

설명:
{description}

조건:
- 2줄 이내
- 짧고 자연스럽게
- 읽고 싶어지게
"""
            }
        ],

        "stream": False
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:

            return (
                f"AI 오류 코드: "
                f"{response.status_code}"
            )

        result = response.json()

        return result["message"]["content"]

    except Exception as e:

        return f"AI 오류: {e}"

# -----------------------------------
# 추천 / 검색
# -----------------------------------

with right_col:

    if search_submit or recommend_button:

        # 제목 검색 우선
        if search_title.strip() != "":

            keyword = search_title

        else:

            # 어린이 랜덤 추천
            if age_text == "어린이":

                child_keywords = [
                    "어린이 동화",
                    "초등 과학",
                    "어린이 판타지",
                    "어린이 모험",
                    "초등 학습만화",
                    "어린이 추리",
                    "초등 역사",
                    "어린이 창작동화"
                ]

                keyword = random.choice(
                    child_keywords
                )

            else:

                keyword = (
                    f"{age_text} "
                    f"{category} 추천 도서"
                )

        st.subheader("✨ 추천 도서")

        books = get_books(keyword)

        if len(books) == 0:

            st.warning(
                "책 정보를 불러오지 못했습니다."
            )

            st.stop()

        cols = st.columns(2)

        for idx, book in enumerate(books[:8]):

            title = remove_html(
                book.get("title", "제목 없음")
            )

            author = remove_html(
                book.get("author", "작가 없음")
            )

            description = remove_html(
                book.get(
                    "description",
                    "설명 없음"
                )
            )

            image = book.get(
                "image",
                "https://via.placeholder.com/300x450"
            )

            link = book.get(
                "link",
                "https://search.naver.com"
            )

            if len(description) < 10:

                description = (
                    "이 책에는 흥미로운 "
                    "이야기가 담겨 있습니다."
                )

            ai_summary = generate_ai_summary(
                title,
                description[:200]
            )

            with cols[idx % 2]:

                st.markdown(
                    '<div class="book-card">',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"""
<a href="{link}" target="_blank">
<img src="{image}"
width="220"
style="border-radius:14px;">
</a>
""",
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"""
<div class="book-title">
📘 {title}
</div>
""",
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"""
<div class="book-author">
✍️ {author}
</div>
""",
                    unsafe_allow_html=True
                )

                st.write(
                    description[:180] + "..."
                )

                st.markdown(
                    f"""
<div class="ai-box">
🤖 {ai_summary}
</div>
""",
                    unsafe_allow_html=True
                )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )