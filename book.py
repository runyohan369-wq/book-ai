import streamlit as st
import requests
import re
import random
import os

# ==================================================
# 페이지 설정
# ==================================================
st.set_page_config(
    page_title="book ai",
    page_icon="📚",
    layout="wide"
)

# ==================================================
# Session State 초기화
# ==================================================
if "mode" not in st.session_state:
    st.session_state.mode = "recommend"

if "keyword" not in st.session_state:
    st.session_state.keyword = ""

# 🎲 랜덤 추천의 실시간 변화를 주기 위한 시드(Seed) 값 상태 관리
if "random_seed" not in st.session_state:
    st.session_state.random_seed = 0

if "prev_category" not in st.session_state:
    st.session_state.prev_category = ""
if "prev_book_type" not in st.session_state:
    st.session_state.prev_book_type = ""
if "prev_target" not in st.session_state:
    st.session_state.prev_target = ""

# ==================================================
# CSS 스타일 정의
# ==================================================
st.markdown("""
<style>
.main {
    background:#f7f8fc;
}
.block-container {
    padding-top: 2.5rem !important;
}
.header-container {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 8px;
}
.title-link {
    text-decoration: none !important;
    color: #1E293B !important;
}
.title {
    font-size:36px;
    font-weight:800;
    display: inline-block;
}
.subtitle {
    color:#64748B;
    margin-bottom:30px;
    font-size:15px;
}
.click-notice {
    font-size: 14px;
    font-weight: 600;
    color: #EF4444;
    background-color: #FEF2F2;
    padding: 6px 12px;
    border-radius: 8px;
    border: 1px solid #FCA5A5;
    animation: blink 2s infinite;
}
@keyframes blink {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}
.search-box {
    background:white;
    padding:18px;
    border-radius:18px;
    box-shadow:0 3px 10px rgba(0,0,0,0.05);
    margin-bottom:20px;
}
.sidebar-box {
    background:white;
    padding:18px;
    border-radius:18px;
    box-shadow:0 3px 10px rgba(0,0,0,0.05);
}
.book-card {
    background:white;
    padding:18px;
    border-radius:18px;
    box-shadow:0 4px 12px rgba(0,0,0,0.07);
    margin-bottom:25px;
    transition:0.2s;
}
.book-card:hover {
    transform:translateY(-4px);
}
.book-title {
    font-size:18px;
    font-weight:bold;
    margin-top:10px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.4;
    height: 2.8em; 
}
.book-author {
    color:gray;
    margin-bottom:5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.book-pages {
    font-size:13px;
    color:#64748B;
    margin-bottom:5px;
}
.stButton>button {
    width:100%;
    border-radius:12px;
    height:45px;
    font-size:15px;
    font-weight:bold;
    background-color: #4F46E5 !important;
    color: white !important;
    border: none;
}
.info-message {
    background-color: #EFF6FF;
    color: #1E40AF;
    padding: 20px;
    border-radius: 14px;
    font-size: 16px;
    font-weight: 500;
    border-left: 5px solid #3B82F6;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# 상단 타이틀 레이아웃
st.markdown("""
<div class="header-container">
    <a href="./" target="_self" class="title-link"><div class="title">📚 book ai</div></a>
    <div class="click-notice">← 화면이 바뀌지 않는다면 클릭하세요</div>
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI가 당신과 책을 이어줍니다</div>', unsafe_allow_html=True)

# ==================================================
# API KEY 설정
# ==================================================
try:
    NAVER_CLIENT_ID = st.secrets["NAVER_CLIENT_ID"]
    NAVER_CLIENT_SECRET = st.secrets["NAVER_CLIENT_SECRET"]
except:
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

if not NAVER_CLIENT_ID:
    st.error("NAVER_CLIENT_ID를 설정해주세요.")
    st.stop()

def remove_html(text):
    if text is None: return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# ==================================================
# 상단 입력 UI
# ==================================================
st.markdown('<div class="search-box">', unsafe_allow_html=True)
top1, top2 = st.columns([2.5, 1.5])

with top1:
    with st.form("search_form"):
        search_title = st.text_input("🔍 책 검색", placeholder="원하는 책 제목을 입력하세요 (문제집은 필터링됩니다)")
        search_submit = st.form_submit_button("검색")
        if search_submit:
            st.session_state.mode = "search"
            st.session_state.keyword = search_title

with top2:
    user_target = st.segmented_control(
        "대상 분류",
        ["초등", "중등", "고등", "성인(대학/일반)"],
        default="성인(대학/일반)"
    )
    # 대상 분류 카테고리가 바뀌면 실시간 연동을 위한 제어 생성
    if user_target != st.session_state.prev_target:
        st.session_state.random_seed += 1
        if st.session_state.mode != "search":
            st.session_state.mode = "recommend"
st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# 왼쪽 레이아웃 & 카테고리 정의
# ==================================================
left_col, right_col = st.columns([1, 3])

with left_col:
    st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
    
    book_type = st.segmented_control(
        "선택",
        ["🔍 책 검색", "📝 문제집", "🎲 랜덤 추천"],
        default="🔍 책 검색"
    )
    
    category = ""
    
    if book_type == "🔍 책 검색":
        st.info("상단 검색창에 검색어를 입력하시면 가장 정확한 도서 정보가 나타납니다!")
        if book_type != st.session_state.prev_book_type:
            st.session_state.mode = "recommend"
            st.session_state.keyword = ""
            st.session_state.random_seed += 1
            
    elif book_type == "📝 문제집":
        if user_target == "성인(대학/일반)":
            categories = ["취업/상식", "영어/토익", "자격증", "공무원"]
        else:
            categories = ["국어", "영어", "수학", "과학", "사회", "한국사"]
            
        category = st.radio("과목/분야 선택", categories)
        
        if (category != st.session_state.prev_category) or (book_type != st.session_state.prev_book_type):
            st.session_state.mode = "recommend"
            st.session_state.keyword = ""
            st.session_state.random_seed += 1
            
    else:  # 🎲 랜덤 추천
        categories = ["문학", "과학", "역사", "철학", "판타지", "추리", "심리학", "에세이"]
        category = st.radio("카테고리 선택", categories)
        
        random_button = st.button("🎲 랜덤 도서 추천받기")
        if random_button or (category != st.session_state.prev_category):
            st.session_state.mode = "random_active"
            st.session_state.keyword = ""
            st.session_state.random_seed += 1 # 버튼을 누를 때마다 시드를 변경하여 완전 다른 도서 셔플 구현 🌟

    if book_type != st.session_state.prev_book_type and book_type == "🎲 랜덤 추천":
        st.session_state.mode = "random_idle"

    st.session_state.prev_category = category
    st.session_state.prev_book_type = book_type
    st.session_state.prev_target = user_target
    st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# 도서 검색 및 필터링 API 함수
# ==================================================
@st.cache_data(ttl=60)
def get_books(keyword, selected_category, current_mode, current_book_type):
    url = "https://openapi.naver.com/v1/search/book.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID.strip(),
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET.strip()
    }
    # 랜덤 셔플 및 풍부한 풀 확보를 위해 디스플레이 수집량을 최대로 할당
    params = {
        "query": keyword,
        "display": 100, 
        "sort": "sim"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code != 200: return []
        
        books = response.json().get("items", [])
        filtered_books = []
        seen_titles = set()
        
        for book in books:
            title = remove_html(book.get("title", ""))
            desc = remove_html(book.get("description", ""))
            publisher = remove_html(book.get("publisher", ""))
            
            # 세트/전집 도서 기본 차단
            if re.search(r'(세트|set|전권|전\-권|합본|특집호|개정판\s+전)', title, re.IGNORECASE):
                continue
            
            # 일반 도서 추천 시에만 문제집 계열 필터링 작동 🚫
            if current_book_type != "📝 문제집":
                workbook_pattern = (
                    r'(문제집|수험서|기출|토익|toeic|toefl|jlpt|hsk|만점왕|교재|특강|ebs|모의고사|'
                    r'학평|자격증|기능사|산업기사|기사시험|공무원|개념원리|우공비|체크체크|'
                    r'자습서|평가문제집|교과서|학습서|풀이|해설|정답|오답노트|수능\s*기출|내신|고사|'
                    r'디딤돌|쎈\s+|개념책|유형책|바이블|자이스토리|마더텅|블랙라벨|에듀윌|해커스|영인재)'
                )
                
                full_inspect_text = f"{title} {desc} {publisher}".lower()
                if re.search(workbook_pattern, full_inspect_text, re.IGNORECASE):
                    continue

            # 중복 방지 알고리즘
            title_stem = re.sub(r'\s+', '', title)[:5].lower()
            if title_stem in seen_titles:
                continue
                
            if current_book_type == "🔍 책 검색" or current_mode == "search" or current_book_type == "📝 문제집":
                filtered_books.append(book)
                seen_titles.add(title_stem)
            else:
                text = (title + " " + desc).lower()
                if selected_category.lower() in text or selected_category in title:
                    filtered_books.append(book)
                    seen_titles.add(title_stem)
                    
        return filtered_books
    except:
        return []

# ==================================================
# 추천 시스템 결과 노출 레이아웃
# ==================================================
with right_col:
    if book_type == "🎲 랜덤 추천" and st.session_state.mode == "random_idle":
        st.subheader("🎲 랜덤 도서 추천")
        st.markdown('<div class="info-message">🎲 왼쪽의 [🎲 랜덤 도서 추천받기] 버튼을 눌러 나에게 맞는 책을 추천받으세요!</div>', unsafe_allow_html=True)
    
    elif st.session_state.mode in ["search", "recommend", "random_active"]:
        if st.session_state.mode == "search":
            keyword = st.session_state.keyword
            header_title = f"🔍 '{keyword}' 검색 결과"
        else:
            if book_type == "🔍 책 검색":
                if user_target == "초등":
                    keyword = "초등 필독도서"
                    header_title = "✨ 초등 학생 베스트셀러"
                elif user_target == "중등":
                    keyword = "청소년 추천도서"
                    header_title = "✨ 중등 청소년 베스트셀러"
                elif user_target == "고등":
                    keyword = "고등 추천도서"
                    header_title = "✨ 고등 필독 베스트셀러"
                else:
                    keyword = "소설 베스트셀러"
                    header_title = "✨ 성인 종합 베스트셀러"
                    
            elif book_type == "📝 문제집":
                header_title = f"✨ {user_target} {category} 문제집 베스트"
                
                if category == "한국사":
                    if user_target == "초등": keyword = "초등 한국사"
                    elif user_target == "중등": keyword = "중학 역사"
                    elif user_target == "고등": keyword = "고등 한국사 기출"
                    else: keyword = "한능검 기출문제집"
                else:
                    if user_target == "초등":
                        keyword = "초등 영어 파닉스" if category == "영어" else (f"초등 {category} 만점왕" if category in ["국어", "수학", "사회", "과학"] else f"초등 {category} 우공비")
                    elif user_target == "중등":
                        keyword = f"중학 {category} 체크체크" if category != "영어" else "중학 영어 숨마쿰라우데"
                    elif user_target == "고등":
                        if category == "수학": keyword = "개념원리 수학"
                        elif category == "영어": keyword = "마더텅 영어 고등"
                        elif category == "국어": keyword = "매삼비 국어"
                        else: keyword = f"완자 고등 {category}"
                    else: 
                        # 🌟 [성인 문제집 매칭 실패 완전 수술] 🌟
                        # 포괄적인 단어 대신 서점 API에 다이렉트로 매칭되는 베스트셀러 핵심 수험서 명칭 매핑
                        if category == "영어/토익": 
                            keyword = "해커스 토익 기출"
                        elif category == "취업/상식": 
                            keyword = "시사상식 GSAT NCS"
                        elif category == "자격증": 
                            keyword = "에듀윌 공인중개사 기출"
                        elif category == "공무원": 
                            keyword = "공무원 기출문제집"
                    
            else:
                header_title = f"🎲 {user_target}을 위한 {category} 추천"
                if user_target in ["초등", "중등", "고등"]:
                    keyword = f"{user_target} 추천 {category}"
                else:
                    keyword = f"성인 베스트셀러 {category}"

        st.subheader(header_title)

        # 도서 검색 호출
        books = get_books(keyword, category, st.session_state.mode, book_type)

        if len(books) == 0:
            st.warning("조건에 일치하는 도서를 찾지 못했습니다. 다른 카테고리를 선택하거나 상단 검색창에 직접 도서명을 입력해 보세요.")
            st.stop()

        # 🎲 랜덤 추천 탭일 때 리스트를 시드값에 기반해 셔플(Shuffling) 처리 진행
        if book_type == "🎲 랜덤 추천":
            # 무작위성을 부여하되, 세션 시드가 바뀌지 않으면 고정되어 깜빡임을 방지함
            random.seed(st.session_state.random_seed)
            random.shuffle(books)

        cols = st.columns(2)

        # 최종 가공 완료된 8권의 책 바인딩 출력
        for idx, book in enumerate(books[:8]):
            title = remove_html(book.get("title", "제목 없음"))
            author = remove_html(book.get("author", "작가 없음"))
            image = book.get("image", "https://via.placeholder.com/300x450")
            link = book.get("link", "https://search.naver.com")
            
            pages = book.get("pages", "")
            pages_text = f"📖 {pages}쪽" if pages and pages != "0" else "📖 페이지 정보 없음"

            with cols[idx % 2]:
                st.markdown('<div class="book-card">', unsafe_allow_html=True)
                st.markdown(f'<a href="{link}" target="_blank"><img src="{image}" width="220" style="border-radius:14px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"></a>', unsafe_allow_html=True)
                st.markdown(f'<div class="book-title">📘 {title}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="book-author">✍️ {author}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="book-pages">{pages_text}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)