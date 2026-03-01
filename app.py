import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

Base = declarative_base()

STATIC_DIR = "/var/www/FitSurvey/assets/images"

def get_image_path(equipment, image_type="photo"):
    """이미지 경로 가져오기 - 서버 경로 강제 사용"""
    equipment_id = equipment['id']
    image_name = f"eq_{equipment_id}_{image_type}.png"
    
    # 서버 경로만 사용 (DB 경로 무시)
    image_path = os.path.join(STATIC_DIR, image_name)
    
    # 디버깅 정보 출력
    exists = os.path.exists(image_path)
    print(f"[이미지] ID: {equipment_id}, 타입: {image_type}")
    print(f"[이미지] 경로: {image_path}")
    print(f"[이미지] 존재: {exists}")
    
    return image_path

st.set_page_config(
    page_title="아파트 휘트니스 장비 교체 설문",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

VOTE_OPTIONS = {
    "교체 시급": "🚨 우선 교체 희망",
    "도입 반대": "❌ 장비 폐지 희망", 
    "현재 장비 유지": "✅ 현행 유지"
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
                policy_choice varchar(50) NULL,
                additional_requests text NULL,
                submitted_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
                CONSTRAINT user_policy_survey_pkey PRIMARY KEY (phone_suffix)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS individual_votes (
                id serial4 NOT NULL,
                phone_suffix bpchar(4) NULL,
                equipment_id int4 NULL,
                vote_type varchar(50) NULL,
                CONSTRAINT individual_votes_phone_suffix_equipment_id_key UNIQUE (phone_suffix, equipment_id),
                CONSTRAINT individual_votes_pkey PRIMARY KEY (id),
                CONSTRAINT individual_votes_equipment_id_fkey FOREIGN KEY (equipment_id) REFERENCES equipment_list(id) ON DELETE CASCADE,
                CONSTRAINT individual_votes_phone_suffix_fkey FOREIGN KEY (phone_suffix) REFERENCES user_policy_survey(phone_suffix) ON DELETE CASCADE
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


def upsert_user_survey(phone_suffix, policy_choice, additional_requests=""):
    session = get_db_session()
    try:
        query = text("""
            INSERT INTO user_policy_survey (phone_suffix, policy_choice, additional_requests, submitted_at)
            VALUES (:phone_suffix, :policy_choice, :additional_requests, CURRENT_TIMESTAMP)
            ON CONFLICT (phone_suffix) 
            DO UPDATE SET 
                policy_choice = EXCLUDED.policy_choice,
                additional_requests = EXCLUDED.additional_requests,
                submitted_at = CURRENT_TIMESTAMP
        """)
        session.execute(query, {
            "phone_suffix": phone_suffix,
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


def upsert_individual_vote(phone_suffix, equipment_id, vote_type):
    session = get_db_session()
    try:
        query = text("""
            INSERT INTO individual_votes (phone_suffix, equipment_id, vote_type)
            VALUES (:phone_suffix, :equipment_id, :vote_type)
            ON CONFLICT (phone_suffix, equipment_id) 
            DO UPDATE SET 
                vote_type = EXCLUDED.vote_type
        """)
        session.execute(query, {
            "phone_suffix": phone_suffix,
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


def get_user_votes(phone_suffix):
    session = get_db_session()
    try:
        query = text("SELECT equipment_id, vote_type FROM individual_votes WHERE phone_suffix = :phone_suffix")
        result = session.execute(query, {"phone_suffix": phone_suffix})
        return {row.equipment_id: row.vote_type for row in result}
    finally:
        session.close()


def render_equipment_page(equipment, current_vote):
    """장비 상세 페이지 렌더링"""
    
    # 상단 헤더 숨기기 CSS (강력한 버전)
    st.markdown("""
    <style>
        /* Streamlit 헤더 완전 숨김 */
        header {visibility: hidden; display: none;}
        .stApp > header {visibility: hidden; display: none;}
        /* Deploy 버튼과 메뉴 숨김 */
        .stDeployButton {display: none;}
        [data-testid="stToolbar"] {display: none;}
        /* Main menu (점 3개) 숨김 */
        [data-testid="stMainMenu"] {display: none;}
        /* 상단 여백 제거 */
        .main > div:first-child {padding-top: 0 !important;}
        .main > div {padding-top: 0 !important;}
        .block-container {padding-top: 0 !important; margin-top: 0 !important;}
        .stApp {padding-top: 0 !important;}
        /* 모든 상단 마진 제거 */
        * {margin-top: 0 !important;}
        h1, h2, h3, h4, h5, h6 {margin-top: 0 !important; padding-top: 0 !important;}
    </style>
    """, unsafe_allow_html=True)
    
    # 장비 정보 상단 표시
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: #1f77b4; font-size: 18px;">{equipment['item_name']}({equipment.get('model_name', '')}) 📍 {equipment.get('location', '정보 없음')}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 투표 버튼 (한 줄에 3개)
    st.markdown("""
    <style>
    .stButton > button {
        width: 100% !important;
        margin: 0 !important;
        padding: 6px 4px !important;
        font-size: 14px !important;
        min-width: 0 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    div[data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    cols = st.columns([1, 1, 1])
    for idx, (label, display) in enumerate(VOTE_OPTIONS.items()):
        with cols[idx]:
            is_selected = current_vote == label
            button_type = "primary" if is_selected else "secondary"
            
            if st.button(
                display,
                key=f"vote_{equipment['id']}_{label}",
                use_container_width=True,
                type=button_type
            ):
                if upsert_individual_vote(st.session_state.phone_suffix, equipment["id"], label):
                    st.session_state.votes[equipment["id"]] = label
                    
                    # 특정 선택지에 대한 코멘트 표시
                    if label == "도입 반대":
                        st.warning("💬 장비 폐지 희망: 현재 장비를 철거하고, 이런 종류의 장비는 아예 두지 않는 것을 희망합니다.")
                    elif label == "현재 장비 유지":
                        st.info("💬 현행 유지: 현재 장비도 충분하므로 굳이 새로운 장비를 도입하지 않는 것을 희망합니다.")
                    
                    st.rerun()
    
    st.divider()
    
    # 장비 정보 탭
    tab1, tab2 = st.tabs(["장비", "상세스펙"])
    
    # 확대 상태 확인
    show_photo_zoom = st.session_state.get(f"show_photo_zoom_{equipment['id']}", False)
    show_spec_zoom = st.session_state.get(f"show_spec_zoom_{equipment['id']}", False)
    
    with tab1:
        # 장비 이미지
        image_path = get_image_path(equipment, 'photo')
        if os.path.exists(image_path):
            if show_photo_zoom:
                # 확대된 이미지 표시
                st.markdown(f"### 🔍 {equipment['item_name']} - 장비 이미지 (확대)")
                st.image(image_path, width=800)
                if st.button("🔍 축소", key=f"zoom_out_photo_{equipment['id']}", use_container_width=True):
                    st.session_state[f"show_photo_zoom_{equipment['id']}"] = False
                    st.rerun()
            else:
                # 일반 이미지 표시
                st.image(image_path, use_container_width=True)
                
                # 이미지 하단에 작은 확대 버튼
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("🔍 확대", key=f"zoom_photo_{equipment['id']}", use_container_width=True):
                        st.session_state[f"show_photo_zoom_{equipment['id']}"] = True
                        st.rerun()
        else:
            st.info(f"📷 {equipment['item_name']} 사진")
    
    with tab2:
        # 상세 스펙 이미지 또는 텍스트
        spec_image_path = get_image_path(equipment, 'spec')
        if os.path.exists(spec_image_path):
            if show_spec_zoom:
                # 확대된 이미지 표시
                st.markdown(f"### 🔍 {equipment['item_name']} - 상세 스펙 (확대)")
                st.image(spec_image_path, width=800)
                if st.button("🔍 축소", key=f"zoom_out_spec_{equipment['id']}", use_container_width=True):
                    st.session_state[f"show_spec_zoom_{equipment['id']}"] = False
                    st.rerun()
            else:
                # 일반 이미지 표시
                st.image(spec_image_path, use_container_width=True)
                
                # 이미지 하단에 작은 확대 버튼
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("🔍 확대", key=f"zoom_spec_{equipment['id']}", use_container_width=True):
                        st.session_state[f"show_spec_zoom_{equipment['id']}"] = True
                        st.rerun()
        elif equipment["specs"]:
            st.markdown(equipment["specs"])
        else:
            st.info("스펙 정보가 없습니다.")
    
    st.divider()


def equipment_survey_page():
    if "phone_suffix" not in st.session_state:
        st.session_state.page = "policy_survey"
        st.rerun()
        return
    
    equipment_list = get_equipment_list()
    if not equipment_list:
        st.error("장비 정보가 없습니다. 먼저 장비 정보를 등록해주세요.")
        return
    
    if "votes" not in st.session_state:
        st.session_state.votes = get_user_votes(st.session_state.phone_suffix)
    
    if "current_equipment_index" not in st.session_state:
        st.session_state.current_equipment_index = 0
    
    # DB 순서와 인덱스 일치 확인
    current_equipment = equipment_list[st.session_state.current_equipment_index]
    current_vote = st.session_state.votes.get(current_equipment["id"])
    
    # 디버깅 정보 (임시)
    print(f"인덱스: {st.session_state.current_equipment_index}, ID: {current_equipment['id']}, 이름: {current_equipment['item_name']}")
    
    render_equipment_page(current_equipment, current_vote)
    
    # 페이지 네비게이션
    total_equipment = len(equipment_list)
    current_index = st.session_state.current_equipment_index
    
    cols = st.columns([1, 2, 1])
    
    with cols[0]:
        if current_index > 0:
            if st.button("⬅️ 이전 장비", key="prev_equipment", use_container_width=True):
                st.session_state.current_equipment_index = current_index - 1
                st.rerun()
    
    with cols[1]:
        st.markdown(f"<div style='text-align: center; padding: 10px;'>장비 {current_index + 1} / {total_equipment}</div>", unsafe_allow_html=True)
    
    with cols[2]:
        if current_index < total_equipment - 1:
            if st.button("다음 장비 ➡️", key="next_equipment", use_container_width=True):
                st.session_state.current_equipment_index = current_index + 1
                st.rerun()
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← 기본 정책 의견 수정", use_container_width=True):
            st.session_state.page = "policy_survey"
            st.rerun()
    with col2:
        if st.button("설문 완료", use_container_width=True, type="primary"):
            st.success("설문에 참여해 주셔서 감사합니다!")
            st.balloons()
            st.session_state.page = "thank_you"
            st.rerun()


def policy_survey_page():
    st.title("🏋️ 아파트 휘트니스 장비 교체 설문")
    
    st.markdown("""
    ### 안내
    
    19년 된 아파트 휘트니스 장비 교체를 검토하고 있습니다. 
    
    입주민 여러분의 소중한 의견을 수렴하여 최적의 시설 환경을 조성하고자 합니다.
    
    아래 설문에 참여해 주시면 감사하겠습니다.
    """)
    
    st.divider()
    
    st.subheader("📱 전화번호 뒷자리 4자리")
    phone_input = st.text_input(
        "전화번호 뒷자리 4자리를 입력하세요",
        max_chars=4,
        placeholder="예: 1234",
        label_visibility="collapsed"
    )
    
    st.subheader("📝 장비 교체 방식에 대한 의견")
    st.markdown("장비 교체 방식에 대한 의견은 무엇입니까?")
    
    policy_choice = st.radio(
        "선택지",
        options=list(POLICY_OPTIONS.values()),
        label_visibility="collapsed"
    )
    
    st.subheader("💬 추가 요청사항 (선택)")
    additional_requests = st.text_area(
        "추가로 요청하실 사항이 있다면 작성해주세요",
        placeholder="예: 특정 장비 추가 설치 희망 등",
        label_visibility="collapsed"
    )
    
    st.divider()
    
    if st.button("의견 제출 후 장비별 상세 투표하기", use_container_width=True, type="primary"):
        if len(phone_input) != 4 or not phone_input.isdigit():
            st.error("전화번호 뒷자리 4자리를 정확히 입력해주세요.")
            return
        
        if upsert_user_survey(phone_input, policy_choice, additional_requests):
            st.session_state.phone_suffix = phone_input
            st.session_state.page = "equipment_survey"
            st.session_state.votes = get_user_votes(phone_input)
            st.session_state.current_equipment_index = 0
            st.rerun()


def thank_you_page():
    st.title("🎉 설문 완료")
    st.markdown("""
    ## 감사합니다!
    
    소중한 의견을 제출해 주셔서 감사합니다.
    
    입주민 여러분의 의견을 바탕으로 더 나은 휘트니스 시설을 준비하겠습니다.
    """)
    
    if st.button("새로운 설문 시작", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.page = "policy_survey"
        st.rerun()


def main():
    init_database()
    
    if "page" not in st.session_state:
        st.session_state.page = "policy_survey"
    
    if st.session_state.page == "policy_survey":
        policy_survey_page()
    elif st.session_state.page == "equipment_survey":
        equipment_survey_page()
    elif st.session_state.page == "thank_you":
        thank_you_page()


if __name__ == "__main__":
    main()
