import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from fpdf import FPDF
import os

# --- 1. PDF 생성 클래스 ---
class InventoryPDF(FPDF):
    def __init__(self, client_name, sales_rep):
        super().__init__()
        self.client_name = client_name
        self.sales_rep = sales_rep

    def header(self):
        # 로고 삽입
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        
        # 한글 폰트 설정 (파일명 확인 필수)
        self.add_font('Nanum', '', 'NanumGothic.ttf', uni=True)
        self.set_font('Nanum', '', 20)
        
        # 제목 및 정보
        self.cell(0, 15, f'{self.client_name} 스트라우만 재고확인', ln=True, align='C')
        self.set_font('Nanum', '', 10)
        self.cell(0, 10, f"발행일: {date.today().strftime('%Y-%m-%d')} | 담당자: {self.sales_rep}", ln=True, align='R')
        self.ln(5)

    def footer(self):
        self.set_y(-30)
        self.set_font('Nanum', '', 9)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "본 보고서는 재고 관리 및 유효기간 확인 목적으로 생성되었습니다.", ln=True, align='C')
        self.set_font('Nanum', '', 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f"확인 (병원): _______________ (인)          확인 (영업): {self.sales_rep} (인)", ln=True, align='C')

# --- 2. Streamlit UI 구성 ---
st.set_page_config(page_title="Straumann PDF Generator", layout="wide")

st.title("📄 스트라우만 재고확인 PDF 생성기")
st.info("거래처명과 품목을 입력하고 PDF 버튼을 누르세요. 1년 6개월 미만 제품은 자동으로 빨간색 표시됩니다.")

# 사이드바 입력
with st.sidebar:
    st.header("📋 기본 정보")
    client_name = st.text_input("거래처명 (병원명)", placeholder="예: 서울치과")
    sales_rep = st.text_input("담당 영업사원", placeholder="이름 입력")
    st.divider()
    generate_btn = st.button("✨ PDF 보고서 생성", use_container_width=True)

# 메인 입력창
st.subheader("📦 품목 및 유효기간 입력")

# 초기 데이터 구조 (BL, BLT, BLX, TL, TLX 선택 가능)
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame([
        {"품목": "BLT", "사이즈": "4.1", "유효기간": date.today() + timedelta(days=500)}
    ])

edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    column_config={
        "품목": st.column_config.SelectboxColumn(
            "대분류", options=["BL", "BLT", "BLX", "TL", "TLX"], required=True
        ),
        "사이즈": st.column_config.TextColumn("사이즈 (숫자)", placeholder="예: 4.1"),
        "유효기간": st.column_config.DateColumn("유효기간 만료일", required=True)
    },
    use_container_width=True
)

# --- 3. PDF 생성 로직 ---
if generate_btn:
    if not client_name or not sales_rep:
        st.error("거래처명과 담당자 이름을 입력해주세요.")
    elif edited_df.empty:
        st.error("입력된 품목 데이터가 없습니다.")
    else:
        pdf = InventoryPDF(client_name, sales_rep)
        pdf.add_page()
        pdf.add_font('Nanum', '', 'NanumGothic.ttf', uni=True)
        
        # 표 헤더
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Nanum', '', 12)
        pdf.cell(50, 12, '품목(대분류)', 1, 0, 'C', fill=True)
        pdf.cell(50, 12, '사이즈', 1, 0, 'C', fill=True)
        pdf.cell(90, 12, '유효기간 만료일', 1, 1, 'C', fill=True)
        
        # 데이터 출력 (조건부 서식 적용)
        limit_date = date.today() + timedelta(days=547) # 1년 6개월 기준
        
        for _, row in edited_df.iterrows():
            # 유효기간 1년 6개월 미만 체크
            if row['유효기간'] < limit_date:
                pdf.set_text_color(255, 0, 0) # 빨간색
            else:
                pdf.set_text_color(0, 0, 0) # 검정색
                
            pdf.cell(50, 10, str(row['품목']), 1, 0, 'C')
            pdf.cell(50, 10, str(row['사이즈']), 1, 0, 'C')
            pdf.cell(90, 10, row['유효기간'].strftime('%Y-%m-%d'), 1, 1, 'C')
        
        # 하단 고정 문구
        pdf.ln(10)
        pdf.set_text_color(255, 0, 0)
        pdf.set_font('Nanum', '', 10)
        pdf.cell(0, 10, "※ 유효기간 1년 미만 제품은 교환불가 합니다.", ln=True) #
        
        # PDF 다운로드 버튼 활성화
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore')
        st.success(f"✅ {client_name} 보고서가 생성되었습니다.")
        st.download_button(
            label="📥 PDF 다운로드",
            data=pdf_bytes,
            file_name=f"{client_name}_스트라우만_재고확인.pdf",
            mime="application/pdf",
            use_container_width=True
        )