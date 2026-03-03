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
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        
        # 한글 폰트 (파일이 반드시 폴더에 있어야 함)
        try:
            self.add_font('Nanum', '', 'NanumGothic.ttf', uni=True)
            self.set_font('Nanum', '', 20)
        except:
            self.set_font('Arial', '', 20) # 폰트 없을 경우 대비
        
        self.cell(0, 15, f'{self.client_name} 재고확인서', ln=True, align='C')
        self.set_font('Nanum', '', 10) if os.path.exists('NanumGothic.ttf') else self.set_font('Arial', '', 10)
        self.cell(0, 10, f"발행일: {date.today().strftime('%Y-%m-%d')} | 담당자: {self.sales_rep}", ln=True, align='R')
        self.ln(5)

# --- 2. 메인 화면 구성 ---
st.set_page_config(page_title="Inventory PDF", layout="wide")
st.title("🦷 스트라우만 재고확인 PDF 생성기")

with st.sidebar:
    st.header("📋 정보 입력")
    client_name = st.text_input("거래처명 (병원명)")
    sales_rep = st.text_input("담당 영업사원")
    generate_btn = st.button("✨ PDF 생성하기", use_container_width=True)

# 에러가 발생했던 data_editor 부분을 더 안전하게 수정
st.subheader("📦 품목 및 유효기간 입력")

if 'inventory_df' not in st.session_state:
    st.session_state.inventory_df = pd.DataFrame([
        {"품목": "BLT", "사이즈": "4.1", "유효기간": date.today() + timedelta(days=600)}
    ])

# 안정적인 column_config 설정
edited_df = st.data_editor(
    st.session_state.inventory_df,
    num_rows="dynamic",
    column_config={
        "품목": st.column_config.SelectboxColumn("대분류", options=["BL", "BLT", "BLX", "TL", "TLX"]),
        "사이즈": st.column_config.TextColumn("사이즈"),
        "유효기간": st.column_config.DateColumn("유효기간")
    },
    use_container_width=True
)

if generate_btn:
    if not client_name or not sales_rep:
        st.error("거래처명과 담당자명을 입력해주세요.")
    else:
        pdf = InventoryPDF(client_name, sales_rep)
        pdf.add_page()
        
        # 테이블 헤더
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(50, 12, 'Category', 1, 0, 'C', fill=True)
        pdf.cell(50, 12, 'Size', 1, 0, 'C', fill=True)
        pdf.cell(90, 12, 'Expiration Date', 1, 1, 'C', fill=True)
        
        limit_date = date.today() + timedelta(days=547)
        
        for _, row in edited_df.iterrows():
            if row['유효기간'] < limit_date:
                pdf.set_text_color(255, 0, 0)
            else:
                pdf.set_text_color(0, 0, 0)
            
            pdf.cell(50, 10, str(row['품목']), 1, 0, 'C')
            pdf.cell(50, 10, str(row['사이즈']), 1, 0, 'C')
            pdf.cell(90, 10, row['유효기간'].strftime('%Y-%m-%d'), 1, 1, 'C')
        
        pdf.ln(10)
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, "Notice: Items with less than 1 year left cannot be exchanged.", ln=True)
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore')
        st.download_button(
            label="📥 PDF 다운로드",
            data=pdf_bytes,
            file_name=f"{client_name}_Inventory.pdf",
            mime="application/pdf",
            use_container_width=True
        )
