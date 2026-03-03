import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from fpdf import FPDF
import os

# --- 1. PDF 클래스 (에러 방지를 위한 폰트 예외 처리 강화) ---
class InventoryPDF(FPDF):
    def __init__(self, client_name, sales_rep):
        super().__init__()
        self.client_name = client_name
        self.sales_rep = sales_rep
        self.font_path = "NanumGothic.ttf"

    def header(self):
        # 로고 삽입
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        
        # 한글 폰트 로드 (에러 방지용 try-except)
        if os.path.exists(self.font_path):
            self.add_font('Nanum', '', self.font_path, uni=True)
            self.set_font('Nanum', '', 18)
        else:
            self.set_font('Arial', 'B', 16)
        
        self.cell(0, 15, f'{self.client_name} 스트라우만 재고확인', ln=True, align='C')
        
        if os.path.exists(self.font_path): self.set_font('Nanum', '', 10)
        self.cell(0, 10, f"발행일: {date.today().strftime('%Y-%m-%d')} | 담당자: {self.sales_rep}", ln=True, align='R')
        self.ln(5)

# --- 2. 메인 화면 레이아웃 ---
st.set_page_config(page_title="Straumann Manager", layout="wide")

st.title("🦷 스트라우만 재고 및 유효기간 관리")
st.markdown("---")

# [핵심] 우측 상단/하단 느낌을 주기 위한 컬럼 배치
col1, col2 = st.columns([0.8, 0.2])

with col1:
    st.subheader("📦 제품 리스트 작성")
    st.caption("아래 표에 제품 정보를 입력하세요. (날짜는 클릭하여 선택)")

with col2:
    # 사이드바 대신 '팝업(Popover)' 버튼을 우측에 배치
    with st.popover("📝 정보 입력 및 PDF 발행", use_container_width=True):
        st.write("발행에 필요한 정보를 입력하세요.")
        client_name = st.text_input("거래처명 (병원명)", placeholder="예: 서울치과")
        sales_rep = st.text_input("담당 영업사원", placeholder="이름 입력")
        generate_btn = st.button("🚀 PDF 생성하기", use_container_width=True)

# 데이터 입력 테이블 (표면처리 항목 포함)
if 'inventory_df' not in st.session_state:
    st.session_state.inventory_df = pd.DataFrame([
        {
            "대분류": "BLT", 
            "표면처리": "Roxolid SLActive", 
            "사이즈": "4.1", 
            "유효기간": date.today() + timedelta(days=600)
        }
    ])

edited_df = st.data_editor(
    st.session_state.inventory_df,
    num_rows="dynamic",
    column_config={
        "대분류": st.column_config.SelectboxColumn(
            "대분류", options=["BL", "BLT", "BLX", "TL", "TLX"], required=True
        ),
        "표면처리": st.column_config.SelectboxColumn(
            "표면처리", options=["Ti-SLA", "Roxolid SLA", "Roxolid SLActive"], required=True
        ),
        "사이즈": st.column_config.TextColumn("사이즈 (숫자)", placeholder="예: 4.1"),
        "유효기간": st.column_config.DateColumn(
            "유효기간 만료일", format="YYYY-MM-DD", required=True
        )
    },
    use_container_width=True
)

# --- 3. PDF 생성 및 다운로드 로직 ---
if generate_btn:
    if not client_name or not sales_rep:
        st.error("⚠️ 정보 입력 팝업에서 거래처명과 이름을 입력해주세요.")
    else:
        try:
            pdf = InventoryPDF(client_name, sales_rep)
            pdf.add_page()
            
            # 폰트 적용
            if os.path.exists("NanumGothic.ttf"):
                pdf.add_font('Nanum', '', "NanumGothic.ttf", uni=True)
                pdf.set_font('Nanum', '', 11)
            
            # 테이블 헤더
            pdf.set_fill_color(240, 240, 240)
            widths = [35, 55, 30, 65]
            cols = ["대분류", "표면처리", "사이즈", "유효기간"]
            for i, head in enumerate(cols):
                pdf.cell(widths[i], 12, head, 1, 0, 'C', fill=True)
            pdf.ln()

            # 데이터 행
            limit_date = date.today() + timedelta(days=547) # 1.5년
            
            for _, row in edited_df.iterrows():
                # 조건부 서식: 1년 6개월 미만 빨간색
                if row['유효기간'] < limit_date:
                    pdf.set_text_color(220, 50, 50)
                else:
                    pdf.set_text_color(0, 0, 0)
                
                pdf.cell(widths[0], 10, str(row['대분류']), 1, 0, 'C')
                pdf.cell(widths[1], 10, str(row['표면처리']), 1, 0, 'C')
                pdf.cell(widths[2], 10, str(row['사이즈']), 1, 0, 'C')
                pdf.cell(widths[3], 10, row['유효기간'].strftime('%Y-%m-%d'), 1, 1, 'C')
            
            # 하단 고정 문구
            pdf.ln(10)
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, "※ 유효기간 1년 미만 제품은 교환이 불가합니다.", ln=True)
            
            # [수정] PDF 바이트 생성 방식 최적화
            pdf_out = pdf.output()
            
            st.success("✅ PDF 생성이 완료되었습니다!")
            st.download_button(
                label="📥 PDF 다운로드 하기",
                data=bytes(pdf_out),
                file_name=f"{client_name}_재고확인.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
