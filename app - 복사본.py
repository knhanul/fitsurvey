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
    page_icon="🏘️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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
        padding: 12px 16px;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 14px;
    }
    .location-badge {
        display: inline-flex;
        align-items: center;
        background-color: #eff6ff;
        color: #3b82f6;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 16px;
        font-weight: 600;
        border: 1px solid #dbeafe;
        flex-shrink: 0;
    }
    .equipment-title {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #111827 !important;
        line-height: 1.3 !important;
        margin: 0 !important;
    }

    /* 투표/하단 버튼: 스마트폰 최적화 폭으로 고정 + 가운데 정렬 */
    .stHorizontalBlock {
        max-width: 520px;
        margin-left: auto !important;
        margin-right: auto !important;
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
        min-height: 32px !important;
        padding: 3px 8px !important;
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
        <span class="page-indicator">장비 <span>{current_index + 1}</span> / {total_equipment} &nbsp;|&nbsp; 현재: {equipment.get('item_name','')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 하단 액션 버튼 - 최소화 (이전/다음 장비명 포함)
    col_prev, col_next = st.columns(2)
    with col_prev:
        if current_index > 0:
            if st.button(f"⬅️ {prev_equipment_name}", key="prev_equipment", width='stretch'):
                st.session_state.current_equipment_index = current_index - 1
                st.rerun()
    
    with col_next:
        if current_index < total_equipment - 1:
            if st.button(f"{next_equipment_name} ➡️", key="next_equipment", width='stretch'):
                st.session_state.current_equipment_index = current_index + 1
                st.rerun()
    
    col_back, col_review = st.columns(2)
    with col_back:
        if st.button("← 정책 페이지", width='stretch'):
            st.session_state.page = "policy_survey"
            st.rerun()
    
    with col_review:
        if st.button("최종(리뷰) 페이지 →", width='stretch', type="primary"):
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

    prev_name = equipment_list[current_index - 1]["item_name"] if current_index > 0 else ""
    next_name = equipment_list[current_index + 1]["item_name"] if current_index < total_equipment - 1 else ""
    
    # 장비 페이지 렌더링 (내비게이션과 하단 버튼 포함)
    render_equipment_page(current_equipment, current_vote, total_equipment, current_index, prev_equipment_name=prev_name, next_equipment_name=next_name)


def policy_survey_page():
    st.markdown("""
    <style>
    .policy-title {
        font-size: 18px;
        font-weight: 700;
        color: #333333;
        text-align: center;
        margin: 0;
        padding: 0;
    }
    </style>
    <div class="policy-title">🏘️ 장비 교체 정책 투표</div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💡 교체 범위 및 예산 계획 안내")
    st.info("""
    * **교체 범위**: '전체 일괄 교체' 방식은 노후화가 심한 **근력 운동 기구에만 적용**됩니다. (비교적 상태가 양호한 러닝머신, 일립티컬, 실내 사이클 등 유산소 기구는 교체 제외)
    * **도입 브랜드 (개선스포츠 선정 이유)**: 국내 헬스장 및 아파트 전문 브랜드인 **'개선스포츠'**로 도입할 예정입니다. 수입산 기구와 달리 **부품 수급이 매우 빠르고 유지보수(A/S) 비용이 저렴**하며, 한국인 체형에 맞는 설계와 뛰어난 내구성으로 전국 수많은 상업용 헬스장에서 가장 널리 검증된 합리적인 브랜드이기 때문입니다.
    * **예산 현황**: 현재 휘트니스 적립금은 **약 4,000만 원**입니다.
    * **예상 비용**: 헬스장 바닥 전면 교체 및 근력 기구 전면 교체 시 **약 4,500만 원**이 소요될 것으로 예상됩니다.
    * **운영 계획**: 모자란 예산을 한 번에 무리해서 지출하지 않고, **약 1,000만 원 규모는 렌탈 방식**을 활용할 예정입니다. 이 경우 **월 렌탈비는 약 25만 원** 수준으로 휘트니스 운영 수익 내에서 충분히 감당 가능한 금액입니다.
    """)
    
    st.divider()
    
    # 부드러운 넛지(Nudge) 방식의 기본 정보 입력 섹션
    st.subheader("📝 참여자 기본 정보")
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
    
    st.divider()
    
    st.subheader("📝 장비 교체 정책 의견")
    st.markdown("위 안내를 참고하시어, 선호하시는 장비 교체 방식을 선택해 주세요.")
    policy_choice = st.radio(
        "선택지",
        options=list(POLICY_OPTIONS.values()),
        label_visibility="collapsed"
    )
    
    # 추가 요청사항 섹션
    st.subheader("💬 추가 요청사항 (선택)")
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
    
    st.divider()
    
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
    st.title("🎉 설문 완료")
    st.markdown("""
    ## 감사합니다!
    
    소중한 의견을 제출해 주셔서 감사합니다.
    
    입주민 여러분의 의견을 바탕으로 더 나은 휘트니스 시설을 준비하겠습니다.
    """)
    
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <p style="color: #6b7280; font-size: 14px; margin-bottom: 10px;">
            이 창을 닫으려면 아래 버튼을 누르거나 브라우저의 닫기 버튼을 이용해주세요.
        </p>
        <button onclick="window.close();" style="
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
    st.markdown("""
    <style>
    .intro-container {
        padding: 0;
        margin: 0;
    }
    .intro-title {
        font-size: 18px;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 4px;
    }
    .intro-subtitle {
        font-size: 16px;
        font-weight: 600;
        color: #333333;
        text-align: center;
        margin-top: 0;
        margin-bottom: 16px;
    }
    </style>
    <div class="intro-container">
        <div class="intro-title">🏘️ 우리 아파트 휘트니스,</div>
        <div class="intro-subtitle">안전하고 쾌적하게 바꿀 때입니다!</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 부드러운 안내 메시지 (파란색 박스)
    st.info("안녕하세요. 입주민 및 휘트니스 회원 여러분.\n\n단지 내 휘트니스 센터의 노후 환경을 개선하고, 안전한 운동 공간을 조성하기 위해 여러분의 소중한 의견을 수렴하고자 합니다.")
    
    st.divider()
    
    # 배경 설명
    st.markdown("### 📅 왜 지금 교체를 추진하나요?")
    st.markdown("""
    2008년 개장 후 17년이 지나 기구들의 평균 내구연한(7~12년)을 훌쩍 넘겼습니다. 잦은 와이어 단선과 부품 수급 불가로 안전사고 위험마저 커지고 있습니다. 
    
    이에 입주자대표회의에서는 노후 바닥 교체의 시급성에 공감하며, 장비 교체 방식은 효율성을 위해 주민 의견을 모아 신중히 결정하기로 의결했습니다.
    """)
    
    # 예산 설명 (초록색 강조 박스)
    st.markdown("### 💰 4,000만 원, 투명하게 씁니다!")
    st.success("""
    그동안 **회원님들이 납부하신 이용 요금으로 약 4,000만 원의 적립금**이 마련되었습니다. 
    
    이 예산으로 '바닥 재시공 및 노후 근력 장비 신형 교체'를 제안하였으며, 소중한 예산인 만큼 **실제 이용하시는 회원님들과 입주민 여러분의 의견을 종합적으로 수렴**하여 최종 진행 방식을 결정할 예정입니다.
    """)
    
    # 설문 방법 안내
    st.markdown("### 🔍 설문 안내 (단 2단계!)")
    st.markdown("""
    * **1단계 (교체 방식):** 예산 내 전체 일괄 교체 vs 고장 장비 선별 교체
    * **2단계 (개별 장비 투표):** 각 장비 사진을 보고 '새로 교체 / 계속 사용 / 완전 철거 / 잘 모름' 선택
    
    여러분의 소중한 1표가 명품 휘트니스를 만듭니다. 지금 바로 아래 버튼을 눌러 설문을 시작해 주세요!
    """)
    
    st.divider()
    
    # 다음 페이지 이동 버튼
    if st.button("👉 설문 시작하기", use_container_width=True, type="primary"):
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
        st.warning("아직 선택한 장비가 없습니다. 장비별 투표는 건너뛰고 추가 의견만 제출할 수 있습니다.")
        if st.button("← 장비별 투표하러 가기", width='stretch'):
            st.session_state.page = "equipment_survey"
            st.rerun()
    
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