import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from fpdf import FPDF
import os

# --- 1. PDF 클래스 (에러 방지용 최적화) ---
class InventoryPDF(FPDF):
    def __init__(self, client_name, sales_rep):
        super().__init__()
        self.client_name = client_name
        self.sales_rep = sales_rep
        self.font_path = "NanumGothic.ttf"

    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        
        # 한글 폰트 로드 예외 처리
        if os.path.exists(self.font_path):
            self.add_font('Nanum', '', self.font_path)
            self.set_font('Nanum', '', 18)
        else:
            self.set_font('helvetica', 'B', 16)
        
        self.cell(0, 15, f'{self.client_name} 스트라우만 재고확인', ln=True, align='C')
        
        if os.path.exists(self.font_path): self.set_font('Nanum', '', 10)
        self.cell(0, 10, f"발행일: {date.today().strftime('%Y-%m-%d')} | 담당자: {self.sales_rep}", ln=True, align='R')
        self.ln(5)

# --- 2. 메인 UI 구성 ---
st.set_page_config(page_title="Straumann Stock", layout="wide")

# 제목 섹션
st.title("🦷 스트라우만 재고 및 유효기간 관리")
st.write("제품 정보를 입력한 후 우측 상단의 '발행' 버튼을 눌러주세요.")

# 데이터 입력 테이블 (에러 방지를 위해 설정 단순화)
if 'inventory_df' not in st.session_state:
    st.session_state.inventory_df = pd.DataFrame([
        {"대분류": "BLT", "표면처리": "Roxolid SLActive", "사이즈": "4.1", "유효기간": date.today() + timedelta(days=600)}
    ])

# [TypeError 방지] column_config를 가장 안정적인 형태로 작성
edited_df = st.data_editor(
    st.session_state.inventory_df,
    num_rows="dynamic",
    column_config={
        "대분류": st.column_config.SelectboxColumn("대분류", options=["BL", "BLT", "BLX", "TL", "TLX"]),
        "표면처리": st.column_config.SelectboxColumn("표면처리", options=["Ti-SLA", "Roxolid SLA", "Roxolid SLActive"]),
        "사이즈": st.column_config.TextColumn("사이즈"), # placeholder 제거로 에러 방지
        "유효기간": st.column_config.DateColumn("유효기간", format="YYYY-MM-DD")
    },
    use_container_width=True
)

# --- 3. 우측 하단 팝업 스타일 버튼 배치 ---
# 화면 하단에 고정된 느낌을 주기 위해 columns 활용
_, col_btn = st.columns([0.8, 0.2])

with col_btn:
    with st.popover("🚀 PDF 발행하기", use_container_width=True):
        st.markdown("### 발행 정보 입력")
        c_name = st.text_input("거래처명", placeholder="예: 서울치과")
        s_rep = st.text_input("담당자", placeholder="영업사원 성함")
        
        if st.button("PDF 생성 실행", use_container_width=True):
            if not c_name or not s_rep:
                st.warning("거래처명과 담당자를 입력해야 합니다.")
            else:
                try:
                    pdf = InventoryPDF(c_name, s_rep)
                    pdf.add_page()
                    
                    if os.path.exists("NanumGothic.ttf"):
                        pdf.add_font('Nanum', '', "NanumGothic.ttf")
                        pdf.set_font('Nanum', '', 11)
                    
                    # 헤더 출력
                    pdf.set_fill_color(240, 240, 240)
                    widths = [30, 60, 30, 70]
                    headers = ["대분류", "표면처리", "사이즈", "유효기간"]
                    for i, h in enumerate(headers):
                        pdf.cell(widths[i], 12, h, 1, 0, 'C', fill=True)
                    pdf.ln()

                    # 데이터 출력
                    limit_date = date.today() + timedelta(days=547)
                    for _, row in edited_df.iterrows():
                        if row['유효기간'] < limit_date:
                            pdf.set_text_color(220, 50, 50)
                        else:
                            pdf.set_text_color(0, 0, 0)
                        
                        pdf.cell(widths[0], 10, str(row['대분류']), 1, 0, 'C')
                        pdf.cell(widths[1], 10, str(row['표면처리']), 1, 0, 'C')
                        pdf.cell(widths[2], 10, str(row['사이즈']), 1, 0, 'C')
                        pdf.cell(widths[3], 10, str(row['유효기간']), 1, 1, 'C')

                    pdf.ln(10)
                    pdf.set_text_color(255, 0, 0)
                    pdf.cell(0, 10, "※ 유효기간 1년 미만 제품은 교환이 불가합니다.", ln=True)

                    # [AttributeError 해결] fpdf2 최신 방식 바이트 변환
                    pdf_output = pdf.output()
                    
                    st.success("준비 완료!")
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=bytes(pdf_output),
                        file_name=f"{c_name}_재고확인.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF 생성 에러: {e}")
