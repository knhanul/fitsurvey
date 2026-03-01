import streamlit as st
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
    page_title="아파트 휘트니스 장비 교체 설문",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

VOTE_OPTIONS = {
    "새로 교체": "� 새 장비로 교체",
    "계속 사용": "✅ 기존 기구 계속 사용", 
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


def render_equipment_page(equipment, current_vote, total_equipment, current_index):
    """장비 상세 페이지 렌더링 - 모바일 최적화 디자인"""
    
    # CSS 스타일링
    st.markdown("""
    <style>
    /* Streamlit 헤더 숨김 */
    header {visibility: hidden; display: none;}
    .stApp > header {visibility: hidden; display: none;}
    .stDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stMainMenu"] {display: none;}
    
    /* 상단 여백 제거 */
    .main > div:first-child {padding-top: 0 !important;}
    .block-container {padding: 0 !important; margin: 0 !important;}
    
    /* 커스텀 헤더 스타일 */
    .equipment-header {
        background-color: #f3f4f6;
        padding: 8px 16px;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .location-badge {
        display: inline-flex;
        align-items: center;
        background-color: #eff6ff;
        color: #3b82f6;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 600;
        border: 1px solid #dbeafe;
        flex-shrink: 0;
    }
    .equipment-title {
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #111827 !important;
        line-height: 1.3 !important;
        margin: 0 !important;
    }
    
    /* 투표 버튼 그리드 - 반드시 2x2 유지 */
    .stHorizontalBlock {
        flex-wrap: nowrap !important;
    }
    .stHorizontalBlock > div {
        flex: 0 0 50% !important;
        min-width: 0 !important;
        max-width: 50% !important;
    }
    
    /* 투표 버튼 스타일 */
    .stButton > button {
        width: 100% !important;
        min-height: 36px !important;
        padding: 4px 8px !important;
        font-size: 10px !important;
        line-height: 1.1 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        white-space: normal !important;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #e5e7eb;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        color: #ef4444 !important;
        border-bottom: 2px solid #ef4444 !important;
    }
    
    /* 이미지 컨테이너 */
    .image-container {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px;
        margin: 0 16px 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 300px;
    }
    
    /* 네비게이션 푸터 */
    .nav-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 12px;
        border-top: 1px solid #e5e7eb;
        font-size: 12px;
    }
    .page-indicator {
        font-size: 12px;
        color: #6b7280;
    }
    .page-indicator span {
        color: #111827;
        font-weight: 700;
    }
    
    /* 하단 버튼 영역 */
    .bottom-actions {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        padding: 16px;
        background: white;
        border-top: 1px solid #e5e7eb;
        position: sticky;
        bottom: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
    
    # 페이지 네비게이션과 하단 버튼
    st.markdown(f"""
    <div class="nav-footer">
        <span class="page-indicator">장비 <span>{current_index + 1}</span> / {total_equipment}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 하단 액션 버튼 - 최소화
    col_prev, col_next, col_back, col_review = st.columns([1, 1, 1.5, 1.5])
    
    with col_prev:
        if current_index > 0:
            if st.button("⬅️", key="prev_equipment", width='stretch'):
                st.session_state.current_equipment_index = current_index - 1
                st.rerun()
    
    with col_next:
        if current_index < total_equipment - 1:
            if st.button("➡️", key="next_equipment", width='stretch'):
                st.session_state.current_equipment_index = current_index + 1
                st.rerun()
    
    with col_back:
        if st.button("← 정책", width='stretch'):
            st.session_state.page = "policy_survey"
            st.rerun()
    
    with col_review:
        if st.button("제출", width='stretch', type="primary"):
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
    
    # 장비 페이지 렌더링 (내비게이션과 하단 버튼 포함)
    render_equipment_page(current_equipment, current_vote, total_equipment, current_index)


def policy_survey_page():
    st.title("🏋️ 아파트 휘트니스 장비 교체 설문")
    
    st.markdown("""
    ### 안내
    
    19년 된 아파트 휘트니스 장비 교체를 검토하고 있습니다. 
    
    입주민 여러분의 소중한 의견을 수렴하여 최적의 시설 환경을 조성하고자 합니다.
    
    아래 설문에 참여해 주시면 감사하겠습니다.
    """)
    
    st.divider()
    
    # 기존 입력값이 있으면 자동으로 채우기
    default_phone = st.session_state.get("phone_suffix", "")
    default_unit = st.session_state.get("unit_number", "")
    default_policy = st.session_state.get("policy_choice", "")
    
    st.subheader("📱 전화번호 뒷자리 4자리")
    phone_input = st.text_input(
        "전화번호 뒷자리 4자리를 입력하세요",
        value=default_phone,
        max_chars=4,
        placeholder="예: 1234",
        label_visibility="collapsed"
    )
    
    st.subheader("🏠 아파트 동 번호 3자리")
    unit_input = st.text_input(
        "아파트 동 번호 3자리를 입력하세요",
        value=default_unit,
        max_chars=3,
        placeholder="예: 101, 102, 103...",
        label_visibility="collapsed"
    )
    
    st.subheader(" 장비 교체 방식에 대한 의견")
    st.markdown("장비 교체 방식에 대한 의견은 무엇입니까?")
    
    policy_choice = st.radio(
        "선택지",
        options=list(POLICY_OPTIONS.values()),
        index=list(POLICY_OPTIONS.values()).index(default_policy) if default_policy in POLICY_OPTIONS.values() else 0,
        label_visibility="collapsed"
    )
    
    st.subheader("💬 추가 요청사항 (선택)")
    additional_requests = st.text_area(
        "추가로 요청하실 사항이 있다면 작성해주세요",
        value=st.session_state.get("additional_requests", ""),
        placeholder="예: 특정 장비 추가 설치 희망, 기존 장비 위치 변경 등",
        label_visibility="collapsed"
    )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("장비별 투표하기", width='stretch'):
            if len(phone_input) != 4 or not phone_input.isdigit():
                st.error("전화번호 뒷자리 4자리를 정확히 입력해주세요.")
                return
            
            if len(unit_input) != 3 or not unit_input.isdigit():
                st.error("아파트 동 번호 3자리를 정확히 입력해주세요. (예: 101, 102, 103...)")
                return
            
            if upsert_user_survey(phone_input, unit_input, policy_choice, additional_requests):
                st.session_state.phone_suffix = phone_input
                st.session_state.unit_number = unit_input
                st.session_state.policy_choice = policy_choice
                st.session_state.additional_requests = additional_requests
                st.session_state.page = "equipment_survey"
                st.session_state.votes = get_user_votes(phone_input, unit_input)
                st.session_state.current_equipment_index = 0
                st.rerun()
    
    with col2:
        if st.button("설문 바로 제출", width='stretch', type="primary"):
            if len(phone_input) != 4 or not phone_input.isdigit():
                st.error("전화번호 뒷자리 4자리를 정확히 입력해주세요.")
                return
            
            if len(unit_input) != 3 or not unit_input.isdigit():
                st.error("아파트 동 번호 3자리를 정확히 입력해주세요. (예: 101, 102, 103...)")
                return
            
            if upsert_user_survey(phone_input, unit_input, policy_choice, additional_requests):
                st.session_state.phone_suffix = phone_input
                st.session_state.unit_number = unit_input
                st.session_state.policy_choice = policy_choice
                st.session_state.additional_requests = additional_requests
                st.session_state.page = "thank_you"
                st.rerun()


def thank_you_page():
    st.title("🎉 설문 완료")
    st.markdown("""
    ## 감사합니다!
    
    소중한 의견을 제출해 주셔서 감사합니다.
    
    입주민 여러분의 의견을 바탕으로 더 나은 휘트니스 시설을 준비하겠습니다.
    """)
    
    if st.button("새로운 설문 시작", width='stretch', type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "policy_survey"
        st.rerun()


def review_page():
    """장비별 선택 내역 검토 및 추가 의견 입력 페이지"""
    st.title("📝 선택 내역 검토")
    
    if "phone_suffix" not in st.session_state or "unit_number" not in st.session_state:
        st.session_state.page = "policy_survey"
        st.rerun()
        return
    
    phone_suffix = st.session_state.phone_suffix
    unit_number = st.session_state.unit_number
    
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 16px;">📱 전화번호: ****-{phone_suffix} | 🏠 동 번호: {unit_number}동</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 장비별 선택 내역 표시
    equipment_list = get_equipment_list()
    votes = st.session_state.get("votes", {})
    
    st.subheader("📋 장비별 선택 내역")
    
    if not votes:
        st.warning("아직 선택한 장비가 없습니다. 장비별 투표를 진행해주세요.")
        if st.button("← 장비별 투표하러 가기", width='stretch'):
            st.session_state.page = "equipment_survey"
            st.rerun()
        return
    
    # 선택 내역 테이블
    for equipment in equipment_list:
        eq_id = equipment["id"]
        if eq_id in votes:
            vote = votes[eq_id]
            display = VOTE_OPTIONS.get(vote, vote)
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid #eee;">
                <span>{equipment['item_name']}</span>
                <span style="font-weight: bold;">{display}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # 추가 요청사항 입력
    st.subheader("💬 추가 요청사항 (선택)")
    
    # 기존 값이 있으면 불러오기
    default_requests = st.session_state.get("additional_requests", "")
    additional_requests = st.text_area(
        "추가로 요청하실 사항이 있다면 작성해주세요",
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


def main():
    init_database()
    
    if "page" not in st.session_state:
        st.session_state.page = "policy_survey"
    
    if st.session_state.page == "policy_survey":
        policy_survey_page()
    elif st.session_state.page == "equipment_survey":
        equipment_survey_page()
    elif st.session_state.page == "review":
        review_page()
    elif st.session_state.page == "thank_you":
        thank_you_page()


if __name__ == "__main__":
    main()