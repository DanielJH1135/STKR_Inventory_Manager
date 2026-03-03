import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from fpdf import FPDF
import os

# --- 1. PDF 생성 클래스 (오류 방지 설계) ---
class InventoryPDF(FPDF):
    def __init__(self, client_name, sales_rep):
        super().__init__()
        self.client_name = client_name
        self.sales_rep = sales_rep
        # 폰트 파일이 있는지 미리 체크
        self.font_path = "NanumGothic.ttf"
        self.has_font = os.path.exists(self.font_path)

    def header(self):
        # 로고 삽입
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        
        # 한글 폰트 설정
        if self.has_font:
            self.add_font('Nanum', '', self.font_path, uni=True)
            self.set_font('Nanum', '', 18)
        else:
            self.set_font('Arial', 'B', 16)
        
        # 제목
        self.cell(0, 15, f'{self.client_name} 재고확인서', ln=True, align='C')
        
        # 상단 정보 (발행일, 담당자)
        if self.has_font: self.set_font('Nanum', '', 10)
        self.cell(0, 10, f"발행일: {date.today().strftime('%Y-%m-%d')} | 담당 영업사원: {self.sales_rep}", ln=True, align='R')
        self.ln(5)

    def footer(self):
        self.set_y(-30)
        if self.has_font: self.set_font('Nanum', '', 9)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "본 보고서는 Straumann 제품 재고 관리용으로 작성되었습니다.", ln=True, align='C')
        
        self.ln(2)
        if self.has_font: self.set_font('Nanum', '', 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f"확인 (병원): _______________ (인)          확인 (영업): {self.sales_rep} (인)", ln=True, align='C')

# --- 2. Streamlit UI 구성 ---
st.set_page_config(page_title="Straumann Stock Manager", layout="wide")

st.title("🦷 스트라우만 재고 및 유효기간 관리")
st.markdown("---")

# 사이드바: 정보 입력
with st.sidebar:
    st.header("📋 기본 정보")
    client_name = st.text_input("거래처명 (병원/기공소)", placeholder="예: 서울치과")
    sales_rep = st.text_input("담당 영업사원", placeholder="이름 입력")
    st.divider()
    generate_btn = st.button("📄 PDF 보고서 생성하기", use_container_width=True)
    if not os.path.exists("NanumGothic.ttf"):
        st.warning("⚠️ NanumGothic.ttf 폰트 파일이 없습니다. PDF 한글이 깨질 수 있습니다.")

# 메인 화면: 데이터 입력
st.subheader("📦 제품 리스트 작성")
st.caption("아래 표에 직접 입력하세요. 행 추가는 표 아래의 '+' 버튼을 누르시면 됩니다.")

# 초기 샘플 데이터 세팅
if 'inventory_df' not in st.session_state:
    st.session_state.inventory_df = pd.DataFrame([
        {
            "대분류": "BLT", 
            "표면처리": "Roxolid SLActive", 
            "사이즈": "4.1", 
            "유효기간": date.today() + timedelta(days=600)
        }
    ])

# 데이터 에디터 (입력 편의성 극대화)
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
        "사이즈": st.column_config.TextColumn("사이즈 (숫자)", placeholder="예: 4.1 / 10"),
        "유효기간": st.column_config.DateColumn(
            "유효기간 만료일", 
            min_value=date(2020, 1, 1),
            max_value=date(2040, 12, 31),
            format="YYYY-MM-DD",
            required=True
        )
    },
    use_container_width=True
)

# --- 3. 실행 로직 ---
if generate_btn:
    if not client_name or not sales_rep:
        st.error("⚠️ 거래처명과 담당 영업사원을 입력해주세요.")
    elif edited_df.empty:
        st.error("⚠️ 입력된 제품 데이터가 없습니다.")
    else:
        try:
            pdf = InventoryPDF(client_name, sales_rep)
            pdf.add_page()
            
            # 테이블 헤더 설정
            pdf.set_fill_color(240, 240, 240)
            if pdf.has_font: pdf.set_font('Nanum', '', 11)
            
            # 헤더 너비 설정
            c1, c2, c3, c4 = 35, 60, 30, 60
            pdf.cell(c1, 12, '대분류', 1, 0, 'C', fill=True)
            pdf.cell(c2, 12, '표면처리', 1, 0, 'C', fill=True)
            pdf.cell(c3, 12, '사이즈', 1, 0, 'C', fill=True)
            pdf.cell(c4, 12, '유효기간', 1, 1, 'C', fill=True)
            
            # 데이터 채우기
            limit_date = date.today() + timedelta(days=547) # 1.5년 기준
            
            for _, row in edited_df.iterrows():
                # 유효기간 체크 (1년 6개월 미만 빨간색)
                if row['유효기간'] < limit_date:
                    pdf.set_text_color(220, 50, 50)
                else:
                    pdf.set_text_color(0, 0, 0)
                
                pdf.cell(c1, 10, str(row['대분류']), 1, 0, 'C')
                pdf.cell(c2, 10, str(row['표면처리']), 1, 0, 'C')
                pdf.cell(c3, 10, str(row['사이즈']), 1, 0, 'C')
                pdf.cell(c4, 10, row['유효기간'].strftime('%Y-%m-%d'), 1, 1, 'C')
            
            # 하단 주의문구
            pdf.ln(10)
            pdf.set_text_color(255, 0, 0)
            if pdf.has_font: pdf.set_font('Nanum', '', 10)
            pdf.cell(0, 10, "※ 유효기간 1년 미만 제품은 교환이 불가합니다.", ln=True)
            
            # PDF 출력 및 다운로드 버튼 생성
            # fpdf2 최신 버전에서는 latin-1 인코딩 없이도 동작할 수 있도록 구성
            pdf_bytes = pdf.output()
            
            st.success(f"✅ {client_name} 재고확인서가 생성되었습니다.")
            st.download_button(
                label="📥 PDF 파일 다운로드",
                data=bytes(pdf_bytes),
                file_name=f"{client_name}_스트라우만_재고확인.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ PDF 생성 중 오류가 발생했습니다: {e}")
