import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

Base = declarative_base()

# 환경 감지하여 경로 설정 (PC vs 서버)
if os.path.exists("/var/www/FitSurvey/assets/images"):
    # 서버 환경
    STATIC_DIR = "/var/www/FitSurvey/assets/images"
else:
    # PC/로컬 환경 - 스크립트 기준 상대 경로
    STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "images")

def get_image_path(equipment, image_type="photo"):
    """이미지 경로 가져오기 - 서버 경로 강제 사용"""
    equipment_id = equipment['id']
    image_name = f"eq_{equipment_id}_{image_type}.png"
    
    # 서버 경로만 사용 (DB 경로 무시)
    image_path = os.path.join(STATIC_DIR, image_name)
    
    return image_path

st.set_page_config(
    page_title="이문e편한세상휘트니스",
    page_icon="imune_log_t.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Open Graph 메타 태그 추가 (공유 시 미리보기 최적화)
st.markdown("""
<head>
    <meta property="og:title" content="이문e편한세상휘트니스">
    <meta property="og:description" content="입주민 여러분의 소중한 의견으로 더 나은 휘트니스를 만듭니다.">
    <meta property="og:image" content="imune_log_t.png">
    <meta property="og:type" content="website">
</head>
""", unsafe_allow_html=True)

# 초기 페이지 타이틀 설정 및 최상단 스크롤
components.html("""
    <script>
        document.title = "이문e편한세상휘트니스";
        window.parent.document.querySelector('.main').scrollTo(0,0);
        setTimeout(function() {
            window.parent.document.querySelector('.main').scrollTo(0,0);
        }, 100);
    </script>
""", height=0)

# 스크롤 최상단 이동 함수 - 페이지 전환 시 즉시 실행
def scroll_to_top():
    components.html("""
        <script>
            // 페이지 타이틀 변경
            document.title = "이문e편한세상휘트니스";
            
            // 즉시 스크롤
            window.parent.document.querySelector('.main').scrollTo(0,0);
            
            // 여러 지연 시간으로 반복 실행
            setTimeout(function() {
                window.parent.document.querySelector('.main').scrollTo(0,0);
                document.title = "이문e편한세상휘트니스";
            }, 50);
            setTimeout(function() {
                window.parent.document.querySelector('.main').scrollTo(0,0);
            }, 100);
            setTimeout(function() {
                window.parent.document.querySelector('.main').scrollTo(0,0);
            }, 200);
        </script>
    """, height=0)


def render_committee_signature():
    """운영 주체 문구 표시 - 가운데 정렬 (로고 제거)"""
    # 로고 메인 색상
    brand_color = "#1e40af"

    # 문구만 표시 (로고 제거)
    st.markdown(
        f'<div style="color:{brand_color}; font-size:13px; font-weight:700; text-align:center; margin-top:8px;">'
        '이문e편한세상휘트니스운영위원회'
        '</div>',
        unsafe_allow_html=True,
    )

# 전역 CSS 스타일 정의 - 통합 및 상단 여백 강제 제거
st.markdown("""
<style>
/* Streamlit 기본 상단 여백 완전 제거 */
[data-testid="stAppViewBlockContainer"] {
    padding-top: 0 !important;
    padding-bottom: 1rem !important;
}
header[data-testid="stHeader"], .stAppHeader {
    display: none !important;
    visibility: hidden !important;
}
.stApp > div:first-child {
    padding-top: 0 !important;
}
.stApp {
    padding-top: 0 !important;
}

/* 전역 상단 여백 제거 */
.stApp > div {
    padding-top: 0 !important;
}

.main .block-container {
    padding-top: 0 !important;
    padding-bottom: 1rem !important;
    max-width: 800px;
}

/* Streamlit 내부 요소 상단 여백 제거 */
.stApp > div > div > div {
    padding-top: 0 !important;
}
[data-testid="stVerticalBlock"] {
    padding-top: 0 !important;
}
[data-testid="stAppViewContainer"] .main,
[data-testid="stAppViewContainer"] .block-container,
[data-testid="stAppViewContainer"] [data-testid="stAppViewBlockContainer"] {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
[data-testid="stHeader"] {
    height: 0 !important;
    min-height: 0 !important;
}
[data-testid="stDecoration"] {
    display: none !important;
}
section.main,
section.main > div,
section.main > div > div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
[data-testid="stToolbar"] {
    display: none !important;
}

/* 최상단 여백 제거 - 가장 강력한 우선순위 */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* 모든 최상위 컨테이너 여백 제거 */
[data-testid="stAppViewContainer"] > div,
[data-testid="stAppViewContainer"] > section,
[data-testid="stAppViewBlockContainer"] > div {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* 첫 번째 블록 여백 제거 */
[data-testid="stVerticalBlock"] > div:first-child,
[data-testid="stVerticalBlock"] > div:first-child > div {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* 메인 콘텐츠 영역 최상단 정렬 */
.main .block-container > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* 헤더 완전 숨김 */
[data-testid="stHeader"],
.stAppHeader,
[data-testid="stDecoration"],
[data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* 텍스트 크기 계층 정상화 - 다크모드 대응 */
.page-title {
    font-size: 22px !important;
    font-weight: 800 !important;
    color: var(--text-color) !important;
    text-align: center !important;
    margin: 0 !important;
    padding: 0 !important;
    margin-bottom: 12px !important;
}

.section-header {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: var(--text-color) !important;
    margin: 16px 0 8px 0 !important;
}

/* 정보 박스 컴팩트화 */
.stAlert {
    padding: 0.75rem 1rem !important;
    font-size: 14px !important;
    line-height: 1.4 !important;
}

.stAlert > div {
    padding: 0 !important;
}

/* 버튼 최적화 */
.stButton > button {
    padding: 8px 16px !important;
    font-size: 14px !important;
    min-height: 36px !important;
    margin: 2px !important;
}

/* 투표 버튼 그리드 최적화 */
.vote-button {
    width: 100% !important;
    min-height: 32px !important;
    padding: 6px 12px !important;
    font-size: 13px !important;
    margin: 1px !important;
}

.vote-button.selected {
    background-color: #2563eb !important;
    color: white !important;
    border-color: #2563eb !important;
}

/* 리뷰 페이지 컴팩트화 - 다크모드 대응 */
.review-item {
    padding: 8px 12px !important;
    margin: 4px 0 !important;
    font-size: 14px !important;
    color: var(--text-color) !important;
    border-bottom: 1px solid var(--border-color) !important;
}

.review-item:last-child {
    border-bottom: none !important;
}

/* 입력 필드 최적화 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    font-size: 14px !important;
    padding: 8px !important;
}

/* 라디오 버튼 최적화 */
.stRadio > div {
    font-size: 14px !important;
}

/* 구분선 최적화 */
.stDivider {
    margin: 12px 0 !important;
}

/* 하단 버튼 최소화 - 2/3 크기로, 잘 보이지 않게 흐리게 */
/* 이 선택자는 반드시 전역 .stButton > button보다 구체적이어야 함 */
div[data-testid="stHorizontalBlock"]:nth-of-type(3) .stButton > button[data-testid="stBaseButton-secondary"],
div[data-testid="stHorizontalBlock"]:nth-of-type(3) .stButton > button[data-testid="stBaseButton-primary"],
button[key="back_to_policy"],
button[key="go_to_review"] {
    height: 18px !important;
    min-height: 18px !important;
    max-height: 18px !important;
    min-width: auto !important;
    width: auto !important;
    padding: 1px 4px !important;
    font-size: 8px !important;
    color: #9ca3af !important;
    background-color: #f3f4f6 !important;
    border: 1px solid #d1d5db !important;
    opacity: 0.5 !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"]:nth-of-type(3) .stButton > button:hover,
button[key="back_to_policy"]:hover,
button[key="go_to_review"]:hover {
    opacity: 0.7 !important;
    background-color: #e5e7eb !important;
}

/* 장비 투표 화면 스타일 - 다크모드 대응 */
.equipment-header {
    background-color: var(--secondary-background-color);
    padding: 10px 14px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}
.location-badge {
    display: inline-flex;
    align-items: center;
    background-color: var(--primary-color);
    color: var(--text-color);
    opacity: 0.9;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 600;
    border: 1px solid var(--border-color);
    flex-shrink: 0;
}
.equipment-title {
    font-size: 20px !important;
    font-weight: 700 !important;
    color: var(--text-color) !important;
    line-height: 1.3 !important;
    margin: 0 !important;
}

/* 투표 버튼 그리드 - 2x2 고정 및 크기 고정 */
.stHorizontalBlock {
    max-width: 520px;
    margin-left: auto !important;
    margin-right: auto !important;
    gap: 4px !important;
}
.stHorizontalBlock > div {
    flex: 0 0 calc(50% - 2px) !important;
    min-width: 0 !important;
    max-width: calc(50% - 2px) !important;
}
.stButton > button {
    width: 100% !important;
    height: 50px !important;
    min-height: 50px !important;
    max-height: 50px !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    white-space: normal !important;
    line-height: 1.2 !important;
}
.stButton > button:has(.vote-selected) {
    background-color: #2563eb !important;
    color: white !important;
    border-color: #2563eb !important;
}

/* 이미지 탭 - 다크모드 대응 */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--secondary-background-color);
    border-bottom: 1px solid var(--border-color);
    padding: 0 12px;
}
.stTabs [data-baseweb="tab"] {
    padding: 8px 12px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-color);
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: var(--primary-color);
}

/* 이미지 컨테이너 - 다크모드 대응 */
.image-container {
    background-color: var(--background-color);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 12px;
    margin: 12px 0;
    text-align: center;
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* 하단 내비게이션 - 4개 버튼 2x2 레이아웃 - 다크모드 대응 */
.nav-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: var(--background-color);
    border-top: 1px solid var(--border-color);
    padding: 8px 16px;
    z-index: 999;
}
.page-indicator {
    text-align: center;
    font-size: 12px;
    color: var(--text-color);
    opacity: 0.7;
    margin-bottom: 8px;
    font-weight: 500;
}
.nav-buttons {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
}
.nav-buttons button {
    flex: 1;
    height: 36px !important;
    min-height: 36px !important;
    max-height: 36px !important;
    padding: 6px 12px !important;
    font-size: 12px !important;
    margin: 0 !important;
}
.action-buttons {
    display: flex;
    gap: 8px;
}
.action-buttons button {
    flex: 1;
    height: 36px !important;
    min-height: 36px !important;
    max-height: 36px !important;
    padding: 6px 12px !important;
    font-size: 12px !important;
    margin: 0 !important;
}

/* 상단 여백 완전 제거 - 극단적 */
* {
    margin-top: 0 !important;
}

/* 최상단 요소들 여백 제거 */
[data-testid="stAppViewBlockContainer"] > div:first-child,
.block-container > div:first-child,
[data-testid="stVerticalBlock"] > div:first-child,
.main > div:first-child,
.stApp > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* 첫 번째 요소의 상단 마진 제거 */
[data-testid="stAppViewBlockContainer"] > div:first-of-type,
.block-container > div:first-of-type,
[data-testid="stVerticalBlock"] > div:first-of-type,
.main > div:first-of-type {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

VOTE_OPTIONS = {
    "새로 교체": "🎯 새 장비로 교체",
    "계속 사용": "📋 기존 기구 계속 사용", 
    "완전 철거": "🗑️ 불필요 (완전 철거)",
    "의견 없음": "🤷 잘 모름 (기권)"
}


POLICY_OPTIONS = {
    "전체 일괄 교체": "전체 일괄 교체",
    "고장난 장비만 선별 교체": "고장난 장비만 선별 교체"
}


def get_db_session():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        st.error("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        st.stop()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


def init_database():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        return
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS equipment_list (
                id serial4 NOT NULL,
                location varchar(50) NULL,
                category varchar(50) NULL,
                item_name varchar(100) NULL,
                model_name varchar(100) NULL,
                specs text NULL,
                photo_image_path varchar(255) NULL,
                spec_image_path varchar(255) NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
                CONSTRAINT equipment_list_pkey PRIMARY KEY (id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_policy_survey (
                phone_suffix bpchar(4) NOT NULL,
                unit_number bpchar(3) NOT NULL,
                policy_choice varchar(50) NULL,
                additional_requests text NULL,
                submitted_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
                CONSTRAINT user_policy_survey_pkey PRIMARY KEY (phone_suffix, unit_number)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS individual_votes (
                id serial4 NOT NULL,
                phone_suffix bpchar(4) NULL,
                unit_number bpchar(3) NULL,
                equipment_id int4 NULL,
                vote_type varchar(50) NULL,
                CONSTRAINT individual_votes_phone_suffix_equipment_id_key UNIQUE (phone_suffix, unit_number, equipment_id),
                CONSTRAINT individual_votes_pkey PRIMARY KEY (id),
                CONSTRAINT individual_votes_equipment_id_fkey FOREIGN KEY (equipment_id) REFERENCES equipment_list(id) ON DELETE CASCADE,
                CONSTRAINT individual_votes_phone_suffix_fkey FOREIGN KEY (phone_suffix, unit_number) REFERENCES user_policy_survey(phone_suffix, unit_number) ON DELETE CASCADE
            )
        """))
        conn.commit()


def get_equipment_list():
    session = get_db_session()
    try:
        query = text("""
            SELECT id, location, category, item_name, model_name, specs, photo_image_path, spec_image_path
            FROM equipment_list 
            ORDER BY id
        """)
        result = session.execute(query)
        return [
            {
                "id": row.id,
                "location": row.location,
                "category": row.category,
                "item_name": row.item_name,
                "model_name": row.model_name,
                "specs": row.specs,
                "photo_image_path": row.photo_image_path,
                "spec_image_path": row.spec_image_path
            }
            for row in result
        ]
    finally:
        session.close()


def upsert_user_survey(phone_suffix, unit_number, policy_choice, additional_requests=""):
    session = get_db_session()
    try:
        query = text("""
            INSERT INTO user_policy_survey (phone_suffix, unit_number, policy_choice, additional_requests, submitted_at)
            VALUES (:phone_suffix, :unit_number, :policy_choice, :additional_requests, CURRENT_TIMESTAMP)
            ON CONFLICT (phone_suffix, unit_number) 
            DO UPDATE SET 
                policy_choice = EXCLUDED.policy_choice,
                additional_requests = EXCLUDED.additional_requests,
                submitted_at = CURRENT_TIMESTAMP
        """)
        session.execute(query, {
            "phone_suffix": phone_suffix,
            "unit_number": unit_number,
            "policy_choice": policy_choice,
            "additional_requests": additional_requests
        })
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"저장 중 오류 발생: {e}")
        return False
    finally:
        session.close()


def upsert_individual_vote(phone_suffix, unit_number, equipment_id, vote_type):
    session = get_db_session()
    try:
        query = text("""
            INSERT INTO individual_votes (phone_suffix, unit_number, equipment_id, vote_type)
            VALUES (:phone_suffix, :unit_number, :equipment_id, :vote_type)
            ON CONFLICT (phone_suffix, unit_number, equipment_id) 
            DO UPDATE SET 
                vote_type = EXCLUDED.vote_type
        """)
        session.execute(query, {
            "phone_suffix": phone_suffix,
            "unit_number": unit_number,
            "equipment_id": equipment_id,
            "vote_type": vote_type
        })
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"투표 저장 중 오류 발생: {e}")
        return False
    finally:
        session.close()


def get_user_votes(phone_suffix, unit_number):
    session = get_db_session()
    try:
        query = text("SELECT equipment_id, vote_type FROM individual_votes WHERE phone_suffix = :phone_suffix AND unit_number = :unit_number")
        result = session.execute(query, {"phone_suffix": phone_suffix, "unit_number": unit_number})
        return {row.equipment_id: row.vote_type for row in result}
    finally:
        session.close()


def render_equipment_page(equipment, current_vote, total_equipment, current_index, prev_equipment_name="", next_equipment_name=""):
    """장비 상세 페이지 렌더링 - 모바일 최적화 디자인"""
    
    # 헤더 섹션 - 한 줄로 구성
    location = equipment.get('location', '정보 없음')
    item_name = equipment['item_name']
    model_name = equipment.get('model_name', '')
    
    # 장비명과 모델명 합치기
    full_name = f"{item_name} ({model_name})" if model_name else item_name
    
    st.markdown(f"""
    <div class="equipment-header">
        <div class="location-badge">📍 {location}</div>
        <div class="equipment-title">{full_name}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 투표 버튼 (2x2 그리드) - 아이콘과 컬러 변경
    vote_icons = {
        "새로 교체": "🎯",
        "계속 사용": "📋",
        "완전 철거": "🗑️",
        "의견 없음": "🤷"
    }
    
    vote_labels = {
        "새로 교체": "새 장비로<br>교체",
        "계속 사용": "기존 기구<br>계속 사용",
        "완전 철거": "불필요<br>(완전 철거)",
        "의견 없음": "잘 모름<br>(기권)"
    }
    
    col1, col2 = st.columns(2)
    vote_items = list(VOTE_OPTIONS.items())
    
    # 첫 번째 행
    with col1:
        label1, display1 = vote_items[0]
        icon1 = vote_icons[label1]
        is_selected1 = current_vote == label1
        
        if is_selected1:
            st.markdown(f"""
            <div style="background: #dbeafe; border: 2px solid #3b82f6; border-radius: 12px; padding: 10px 12px;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <div style="font-size: 18px;">{icon1}</div>
                    <div style="font-size: 11px; font-weight: 700; color: #1e40af;">새 장비로 교체</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(f"{icon1} 새 장비로 교체", key=f"vote_{equipment['id']}_{label1}", width='stretch'):
                handle_vote(equipment, label1, current_index, total_equipment)
    
    with col2:
        label2, display2 = vote_items[1]
        icon2 = vote_icons[label2]
        is_selected2 = current_vote == label2
        
        if is_selected2:
            st.markdown(f"""
            <div style="background: #f9fafb; border: 1px solid #d1d5db; border-radius: 12px; padding: 10px 12px;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <div style="font-size: 18px;">{icon2}</div>
                    <div style="font-size: 11px; font-weight: 500; color: #6b7280;">기존 기구 계속 사용</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(f"{icon2} 기존 기구 계속 사용", key=f"vote_{equipment['id']}_{label2}", width='stretch'):
                handle_vote(equipment, label2, current_index, total_equipment)
    
    # 두 번째 행
    col3, col4 = st.columns(2)
    with col3:
        label3, display3 = vote_items[2]
        icon3 = vote_icons[label3]
        is_selected3 = current_vote == label3
        
        if is_selected3:
            st.markdown(f"""
            <div style="background: #fee2e2; border: 2px solid #ef4444; border-radius: 12px; padding: 10px 12px;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <div style="font-size: 18px;">{icon3}</div>
                    <div style="font-size: 11px; font-weight: 700; color: #991b1b;">불필요 (완전 철거)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(f"{icon3} 불필요 (완전 철거)", key=f"vote_{equipment['id']}_{label3}", width='stretch'):
                handle_vote(equipment, label3, current_index, total_equipment)
    
    with col4:
        label4, display4 = vote_items[3]
        icon4 = vote_icons[label4]
        is_selected4 = current_vote == label4
        
        if is_selected4:
            st.markdown(f"""
            <div style="background: #f3f4f6; border: 2px solid #9ca3af; border-radius: 12px; padding: 10px 12px;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <div style="font-size: 18px;">{icon4}</div>
                    <div style="font-size: 11px; font-weight: 600; color: #4b5563;">잘 모름 (기권)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(f"{icon4} 잘 모름 (기권)", key=f"vote_{equipment['id']}_{label4}", width='stretch'):
                handle_vote(equipment, label4, current_index, total_equipment)
    
    # 탭 네비게이션 (장비 / 상세스펙)
    tab1, tab2 = st.tabs(["장비", "상세스펙"])
    
    with tab1:
        # 장비 이미지
        image_path = get_image_path(equipment, 'photo')
        if os.path.exists(image_path):
            st.image(image_path, width='stretch')
        else:
            st.info(f"📷 {equipment['item_name']} 사진")
    
    with tab2:
        # 상세 스펙 이미지
        spec_image_path = get_image_path(equipment, 'spec')
        if os.path.exists(spec_image_path):
            st.image(spec_image_path, width='stretch')
        elif equipment["specs"]:
            st.markdown(equipment["specs"])
        else:
            st.info("스펙 정보가 없습니다.")
    
    # 하단 버튼 2줄 레이아웃
    col_prev, col_next = st.columns(2)
    with col_prev:
        if current_index > 0:
            if st.button(f"⬅️ {prev_equipment_name}", key="prev_equipment", width='stretch'):
                st.session_state.current_equipment_index = current_index - 1
                st.rerun()
        else:
            st.button("⬅️ 이전 장비", key="prev_equipment_disabled", width='stretch', disabled=True)

    with col_next:
        if current_index < total_equipment - 1:
            if st.button(f"{next_equipment_name} ➡️", key="next_equipment", width='stretch'):
                st.session_state.current_equipment_index = current_index + 1
                st.rerun()
        else:
            st.button("다음 장비 ➡️", key="next_equipment_disabled", width='stretch', disabled=True)

    st.markdown(
        f'<div style="text-align:center; font-size:14px; font-weight:700; color:#1f2937; margin:2px 0 3px;">'
        f'<span style="color:#6b7280;">현재 장비:</span> {equipment.get("item_name", "")} &nbsp;|&nbsp; '
        f'<span style="color:#2563eb; font-size:15px; font-weight:800;">{current_index + 1}</span>'
        f'<span style="color:#9ca3af;">/{total_equipment}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_policy, col_review = st.columns(2)
    with col_policy:
        if st.button("← 1단계(정책 투표) 수정하기", key="back_to_policy", width='stretch'):
            st.session_state.page = "policy_survey"
            st.rerun()

    with col_review:
        if st.button("내 투표 확인하고 최종 제출 →", key="go_to_review", width='stretch'):
            st.session_state.page = "review"
            st.rerun()


def handle_vote(equipment, label, current_index, total_equipment):
    """투표 처리 함수"""
    phone_suffix = st.session_state.phone_suffix
    unit_number = st.session_state.unit_number
    
    if upsert_individual_vote(phone_suffix, unit_number, equipment["id"], label):
        st.session_state.votes[equipment["id"]] = label
        
        # 마지막 장비가 아니면 다음 장비로 자동 이동
        if current_index < total_equipment - 1:
            st.session_state.current_equipment_index = current_index + 1
        else:
            # 마지막 장비면 검토 페이지로
            st.session_state.page = "review"
        
        st.rerun()


def equipment_survey_page():
    scroll_to_top()
    if "phone_suffix" not in st.session_state or "unit_number" not in st.session_state:
        st.session_state.page = "policy_survey"
        st.rerun()
        return
    
    equipment_list = get_equipment_list()
    if not equipment_list:
        st.error("장비 정보가 없습니다. 먼저 장비 정보를 등록해주세요.")
        return
    
    phone_suffix = st.session_state.phone_suffix
    unit_number = st.session_state.unit_number
    
    if "votes" not in st.session_state:
        st.session_state.votes = get_user_votes(phone_suffix, unit_number)
    
    if "current_equipment_index" not in st.session_state:
        st.session_state.current_equipment_index = 0
    
    # DB 순서와 인덱스 일치 확인
    current_equipment = equipment_list[st.session_state.current_equipment_index]
    current_vote = st.session_state.votes.get(current_equipment["id"])
    
    total_equipment = len(equipment_list)
    current_index = st.session_state.current_equipment_index

    prev_name = equipment_list[current_index - 1]["item_name"] if current_index > 0 else ""
    next_name = equipment_list[current_index + 1]["item_name"] if current_index < total_equipment - 1 else ""
    
    # 장비 페이지 렌더링 (내비게이션과 하단 버튼 포함)
    render_equipment_page(current_equipment, current_vote, total_equipment, current_index, prev_equipment_name=prev_name, next_equipment_name=next_name)


def policy_survey_page():
    scroll_to_top()
    st.markdown('<div class="page-title">🏘️ 장비 교체 정책 투표</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">💡 교체 범위 및 예산 계획 안내</div>', unsafe_allow_html=True)
    st.info("""
    * **교체 범위**: '전체 일괄 교체' 방식은 노후화가 심한 **근력 운동 기구에만 적용**됩니다. (비교적 상태가 양호한 러닝머신, 일립티컬, 실내 사이클 등 유산소 기구는 교체 제외)
    * **도입 브랜드 (개선스포츠 선정 이유)**: 국내 헬스장 및 아파트 전문 브랜드인 **'개선스포츠'**로 도입할 예정입니다. 수입산 기구와 달리 **부품 수급이 매우 빠르고 유지보수(A/S) 비용이 저렴**하며, 한국인 체형에 맞는 설계와 뛰어난 내구성으로 전국 수많은 상업용 헬스장에서 가장 널리 검증된 합리적인 브랜드이기 때문입니다.
    * **예산 현황**: 현재 휘트니스 적립금은 **약 4,000만 원**입니다.
    * **예상 비용**: 헬스장 바닥 전면 교체 및 근력 기구 전면 교체 시 **약 4,500만 원**이 소요될 것으로 예상됩니다.
    * **운영 계획**: 모자란 예산을 한 번에 무리해서 지출하지 않고, **약 1,000만 원 규모는 렌탈 방식**을 활용할 예정입니다. 이 경우 **월 렌탈비는 약 25만 원** 수준으로 휘트니스 운영 수익 내에서 충분히 감당 가능한 금액입니다.
    """)
    
    # 부드러운 넛지(Nudge) 방식의 기본 정보 입력 섹션
    st.markdown('<div class="section-header">📝 참여자 기본 정보</div>', unsafe_allow_html=True)
    st.markdown("<span style='font-size: 14px; color: #666;'>단지 내 다양한 세대의 의견을 고르게 수렴하기 위해 거주하시는 <b>동</b>과 <b>전화번호 뒷자리</b>를 입력해 주세요.</span>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        unit_number = st.text_input(
            "거주 동",
            max_chars=3,
            placeholder="예: 101",
            help="숫자만 입력해 주세요."
        )
    with col2:
        phone_input = st.text_input(
            "전화번호 뒷자리",
            max_chars=4,
            placeholder="예: 1234"
        )
    
    st.markdown('<div class="section-header">📝 장비 교체 정책 의견</div>', unsafe_allow_html=True)
    st.markdown("위 안내를 참고하시어, 선호하시는 장비 교체 방식을 선택해 주세요.")
    policy_choice = st.radio(
        "선택지",
        options=list(POLICY_OPTIONS.values()),
        label_visibility="collapsed"
    )
    
    # 추가 요청사항 섹션
    st.markdown('<div class="section-header">💬 추가 요청사항 (선택)</div>', unsafe_allow_html=True)
    st.markdown("""
    <span style="font-size: 14px; color: #4b5563;">
    추가로 희망하시는 장비가 있다면, 가급적 포털 사이트에서 <b>'개선스포츠'</b> 브랜드를 검색해 보신 후 
    원하시는 모델명이나 장비명을 적어주시면 예산 검토에 큰 도움이 됩니다.
    </span>
    """, unsafe_allow_html=True)
    
    additional_requests = st.text_area(
        "요청사항",
        value=st.session_state.get("additional_requests", ""),
        placeholder="예: 개선스포츠 암컬 머신(UT101) 추가 설치 희망, 기존 장비 위치 변경 등",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👉 의견 제출 후 장비별 상세 투표하기", use_container_width=True, type="primary"):
            # 입력값 검증 로직
            if not unit_number or not unit_number.isdigit():
                st.error("원활한 통계를 위해 거주하시는 '동'을 숫자로 정확히 입력해 주세요. (예: 101)")
                return
            if len(phone_input) != 4 or not phone_input.isdigit():
                st.error("전화번호 뒷자리 4자리를 정확히 입력해 주세요.")
                return
            
            # 백엔드 데이터 저장
            if upsert_user_survey(phone_input, unit_number, policy_choice, additional_requests):
                st.session_state.phone_suffix = phone_input
                st.session_state.unit_number = unit_number
                st.session_state.additional_requests = additional_requests
                st.session_state.page = "equipment_survey"
                st.session_state.votes = get_user_votes(phone_input, unit_number) 
                st.session_state.current_equipment_index = 0
                st.rerun()
    
    with col2:
        if st.button("✅ 정책 의견만 제출하고 마치기", use_container_width=True):
            # 입력값 검증 로직
            if not unit_number or not unit_number.isdigit():
                st.error("원활한 통계를 위해 거주하시는 '동'을 숫자로 정확히 입력해 주세요. (예: 101)")
                return
            if len(phone_input) != 4 or not phone_input.isdigit():
                st.error("전화번호 뒷자리 4자리를 정확히 입력해 주세요.")
                return
            
            # 백엔드 데이터 저장
            if upsert_user_survey(phone_input, unit_number, policy_choice, additional_requests):
                st.session_state.phone_suffix = phone_input
                st.session_state.unit_number = unit_number
                st.session_state.additional_requests = additional_requests
                st.session_state.page = "thank_you"
                st.rerun()


def thank_you_page():
    scroll_to_top()
    st.markdown('<div class="page-title">🎉 설문 완료</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; padding: 16px 0;">
        <div style="font-size: 16px; font-weight: 600; color: var(--text-color); margin-bottom: 8px;">감사합니다!</div>
        <div style="font-size: 14px; color: var(--text-color); opacity: 0.8; line-height: 1.5;">
            소중한 의견을 제출해 주셔서 감사합니다.<br>
            입주민 여러분의 의견을 바탕으로 더 나은 휘트니스 시설을 준비하겠습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    render_committee_signature(logo_width=24)
    
    # 모바일 대응 닫기 버튼 - history.back() 사용
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <p style="color: var(--text-color); opacity: 0.7; font-size: 14px; margin-bottom: 10px;">
            이 창을 닫으려면 아래 버튼을 눌러주세요.
        </p>
        <button onclick="
            if (window.history.length > 1) {
                window.history.back();
            } else {
                window.close();
            }
            if (navigator.userAgent.match(/Android|iPhone|iPad|iPod/i)) {
                setTimeout(function() {
                    window.location.href = 'about:blank';
                }, 100);
            }
        " style="
            background-color: #ef4444;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        ">닫기</button>
    </div>
    """, unsafe_allow_html=True)


def intro_page():
    scroll_to_top()
    st.markdown('<div class="page-title">🏘️ 우리 아파트 휘트니스, 안전하고 쾌적하게 바꿀 때입니다!</div>', unsafe_allow_html=True)
    
    # 부드러운 안내 메시지 (파란색 박스)
    st.info("안녕하세요. 입주민 및 휘트니스 회원 여러분.\n\n단지 내 휘트니스 센터의 노후 환경을 개선하고, 안전한 운동 공간을 조성하기 위해 여러분의 소중한 의견을 수렴하고자 합니다.")
    
    # 배경 설명
    st.markdown('<div class="section-header">📅 왜 지금 교체를 추진하나요?</div>', unsafe_allow_html=True)
    st.markdown("""
    2008년 개장 후 17년이 지나 기구들의 평균 내구연한(7~12년)을 훌쩍 넘겼습니다. 잦은 와이어 단선과 부품 수급 불가로 안전사고 위험마저 커지고 있습니다. 
    
    이에 입주자대표회의에서는 노후 바닥 교체의 시급성에 공감하며, 장비 교체 방식은 효율성을 위해 주민 의견을 모아 신중히 결정하기로 의결했습니다.
    """)
    
    # 예산 설명 (초록색 강조 박스)
    st.markdown('<div class="section-header">💰 4,000만 원, 투명하게 씁니다!</div>', unsafe_allow_html=True)
    st.success("""
    그동안 **회원님들이 납부하신 이용 요금으로 약 4,000만 원의 적립금**이 마련되었습니다. 
    
    이 예산으로 '바닥 재시공 및 노후 근력 장비 신형 교체'를 제안하였으며, 소중한 예산인 만큼 **실제 이용하시는 회원님들과 입주민 여러분의 의견을 종합적으로 수렴**하여 최종 진행 방식을 결정할 예정입니다.
    """)
    
    # 설문 방법 안내
    st.markdown('<div class="section-header">🔍 설문 안내 (단 2단계!)</div>', unsafe_allow_html=True)
    st.markdown("""
    * **1단계 (교체 방식):** 예산 내 전체 일괄 교체 vs 고장 장비 선별 교체
    * **2단계 (개별 장비 투표):** 각 장비 사진을 보고 '새로 교체 / 계속 사용 / 완전 철거 / 잘 모름' 선택
    
    여러분의 소중한 1표가 명품 휘트니스를 만듭니다. 지금 바로 아래 버튼을 눌러 설문을 시작해 주세요!
    """)

    render_committee_signature()
    
    # 다음 페이지 이동 버튼
    if st.button("👉 설문 시작하기", use_container_width=True, type="primary"):
        st.session_state.page = "policy_survey"
        st.rerun()


def review_page():
    """장비별 선택 내역 검토 및 추가 의견 입력 페이지 - 컴팩트한 디자인"""
    scroll_to_top()
    st.markdown('<div class="page-title">📝 선택 내역 검토</div>', unsafe_allow_html=True)
    
    if "phone_suffix" not in st.session_state or "unit_number" not in st.session_state:
        st.session_state.page = "policy_survey"
        st.rerun()
        return
    
    phone_suffix = st.session_state.phone_suffix
    unit_number = st.session_state.unit_number
    
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 8px; margin-bottom: 16px; font-size: 14px;">
        📱 ****-{phone_suffix} | 🏠 {unit_number}동
    </div>
    """, unsafe_allow_html=True)
    
    # 장비별 선택 내역 표시
    equipment_list = get_equipment_list()
    votes = st.session_state.get("votes", {})
    
    st.markdown('<div class="section-header">📋 장비별 선택 내역</div>', unsafe_allow_html=True)
    
    if not votes:
        st.warning("아직 선택한 장비가 없습니다. 장비별 투표는 건너뛰고 추가 의견만 제출할 수 있습니다.")
        if st.button("← 장비별 투표하러 가기", width='stretch'):
            st.session_state.page = "equipment_survey"
            st.rerun()
    else:
        # 컴팩트한 리스트 형태로 표시
        for equipment in equipment_list:
            equipment_id = equipment["id"]
            if equipment_id in votes:
                vote = votes[equipment_id]
                vote_display = VOTE_OPTIONS.get(vote, vote)
                
                st.markdown(f"""
                <div class="review-item">
                    <strong>{equipment['item_name']}</strong>: {vote_display}
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()
    
    # 추가 요청사항 섹션
    st.markdown('<div class="section-header">💬 추가 요청사항 (선택)</div>', unsafe_allow_html=True)
    
    # 기존 값이 있으면 불러오기
    default_requests = st.session_state.get("additional_requests", "")
    additional_requests = st.text_area(
        "요청사항",
        value=default_requests,
        placeholder="예: 특정 장비 추가 설치 희망, 기존 장비 위치 변경 등",
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # 버튼 영역
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← 장비별 투표 수정", width='stretch'):
            # 추가 의견 임시 저장
            st.session_state.additional_requests = additional_requests
            st.session_state.page = "equipment_survey"
            st.rerun()
    
    with col2:
        if st.button("설문 제출 완료", width='stretch', type="primary"):
            # 추가 의견 저장
            policy_choice = st.session_state.get("policy_choice", "")
            if upsert_user_survey(phone_suffix, unit_number, policy_choice, additional_requests):
                st.session_state.page = "thank_you"
                st.rerun()


def render_header():
    """사이트 상단 로고 및 타이틀 표시"""
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imune_log_t.png")
    
    # 가운데 정렬된 헤더 컨테이너
    st.markdown("<div style='text-align: center; margin-bottom: 10px;'>", unsafe_allow_html=True)
    
    # 로고 표시
    if os.path.exists(logo_path):
        st.image(logo_path, width=60)
    
    # 사이트 타이틀 표시 (로고 메인 색상)
    st.markdown(
        '<div style="color:#1e40af; font-size:18px; font-weight:800; text-align:center; margin-top:4px;">'
        '이문e편한세상휘트니스'
        '</div>',
        unsafe_allow_html=True,
    )
    
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    init_database()
    
    # 헤더 제거됨
    
    if "page" not in st.session_state:
        st.session_state.page = "intro"
    
    if st.session_state.page == "intro":
        intro_page()
    elif st.session_state.page == "policy_survey":
        policy_survey_page()
    elif st.session_state.page == "equipment_survey":
        equipment_survey_page()
    elif st.session_state.page == "review":
        review_page()
    elif st.session_state.page == "thank_you":
        thank_you_page()


if __name__ == "__main__":
    main()