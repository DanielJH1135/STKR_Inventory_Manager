import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from fpdf import FPDF
import os

# --- 1. PDF 생성 클래스 (디자인 최적화) ---
class InventoryPDF(FPDF):
    def __init__(self, client_name, sales_rep):
        super().__init__()
        self.client_name = client_name
        self.sales_rep = sales_rep
        self.font_path = "NanumGothic.ttf"

    def header(self):
        # 1. 로고 중앙 상단 배치
        logo_w = 40 
        if os.path.exists("logo.png"):
            # 중앙 정렬 계산: (페이지 너비 - 로고 너비) / 2
            self.image("logo.png", x=(self.w - logo_w) / 2, y=10, w=logo_w)
        
        # 한글 폰트 설정
        if os.path.exists(self.font_path):
            self.add_font('Nanum', '', self.font_path)
            self.set_font('Nanum', '', 18)
        else:
            self.set_font('helvetica', 'B', 16)
        
        # 로고 아래로 여백 이동 (로고 위치에 따라 조정 가능)
        self.set_y(35)
        
        # 2. 제목 중앙 정렬 및 텍스트 수정
        self.cell(0, 15, f'"{self.client_name}" 스트라우만 재고확인서', ln=True, align='C')
        
        # 발행일 및 담당자 정보
        if os.path.exists(self.font_path): self.set_font('Nanum', '', 10)
        self.cell(0, 10, f"발행일: {date.today().strftime('%Y-%m-%d')} | 담당자: {self.sales_rep}", ln=True, align='R')
        self.ln(5)

# --- 2. 메인 UI 구성 ---
st.set_page_config(page_title="Straumann Stock Manager", layout="wide")

st.title("🦷 스트라우만 재고 및 유효기간 관리")
st.write("제품 정보를 입력한 후 우측 하단의 '발행' 버튼을 눌러주세요.")

# 데이터 세션 상태 관리
if 'inventory_df' not in st.session_state:
    st.session_state.inventory_df = pd.DataFrame([
        {
            "대분류": "BLT", 
            "표면처리": "Roxolid SLActive", 
            "사이즈": "4.1", 
            "유효기간": date.today() + timedelta(days=600)
        }
    ])

# 연도 4자리 고정 (min/max_value 제한)
edited_df = st.data_editor(
    st.session_state.inventory_df,
    num_rows="dynamic",
    column_config={
        "대분류": st.column_config.SelectboxColumn("대분류", options=["BL", "BLT", "BLX", "TL", "TLX"], required=True),
        "표면처리": st.column_config.SelectboxColumn("표면처리", options=["Ti-SLA", "Roxolid SLA", "Roxolid SLActive"], required=True),
        "사이즈": st.column_config.TextColumn("사이즈"),
        "유효기간": st.column_config.DateColumn(
            "유효기간", 
            format="YYYY-MM-DD",
            min_value=date(2020, 1, 1),
            max_value=date(2040, 12, 31)
        )
    },
    use_container_width=True
)

# --- 3. 우측 하단 팝업(Popover) 발행 섹션 ---
_, col_btn = st.columns([0.8, 0.2])

with col_btn:
    with st.popover("🚀 PDF 발행하기", use_container_width=True):
        st.markdown("### 발행 정보 확인")
        c_name = st.text_input("거래처명 (병원명)", placeholder="예: 서울치과")
        s_rep = st.text_input("담당 영업사원", placeholder="이름 입력")
        
        if st.button("PDF 생성 실행", use_container_width=True):
            if not c_name or not s_rep:
                st.warning("거래처명과 담당자명을 모두 입력해주세요.")
            else:
                try:
                    pdf = InventoryPDF(c_name, s_rep)
                    pdf.add_page()
                    
                    if os.path.exists("NanumGothic.ttf"):
                        pdf.add_font('Nanum', '', "NanumGothic.ttf")
                        pdf.set_font('Nanum', '', 11)
                    
                    # 테이블 헤더
                    pdf.set_fill_color(240, 240, 240)
                    w = [30, 60, 30, 65]
                    headers = ["대분류", "표면처리", "사이즈", "유효기간"]
                    for i, h in enumerate(headers):
                        pdf.cell(w[i], 12, h, 1, 0, 'C', fill=True)
                    pdf.ln()

                    # 데이터 출력 (1년 6개월 미만 빨간색 강조)
                    limit_date = date.today() + timedelta(days=547)
                    for _, row in edited_df.iterrows():
                        if row['유효기간'] < limit_date:
                            pdf.set_text_color(220, 50, 50)
                        else:
                            pdf.set_text_color(0, 0, 0)
                        
                        pdf.cell(w[0], 10, str(row['대분류']), 1, 0, 'C')
                        pdf.cell(w[1], 10, str(row['표면처리']), 1, 0, 'C')
                        pdf.cell(w[2], 10, str(row['사이즈']), 1, 0, 'C')
                        pdf.cell(w[3], 10, row['유효기간'].strftime('%Y-%m-%d'), 1, 1, 'C')

                    # 3. 하단 문구 수정 (색상 블랙, 문구 추가)
                    pdf.ln(10)
                    pdf.set_text_color(0, 0, 0) # 텍스트 색상 검정
                    if os.path.exists("NanumGothic.ttf"):
                        pdf.set_font('Nanum', '', 10)
                    
                    pdf.cell(0, 8, "※ 유효기간 1년 미만 제품은 교환이 불가합니다.", ln=True)
                    pdf.cell(0, 8, "※ 표에서 붉은색으로 표기된 제품은 유효기간 1년 6개월 미만 제품입니다.", ln=True)

                    # PDF 다운로드
                    pdf_output = pdf.output()
                    st.success("PDF 생성이 완료되었습니다!")
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=bytes(pdf_output),
                        file_name=f"{c_name}_재고확인.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF 생성 중 오류 발생: {e}")
