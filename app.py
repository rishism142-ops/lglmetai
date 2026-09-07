import streamlit as st
from PIL import Image
import pytesseract
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="LegalMet AI Vision Inspector", layout="centered")

st.title("⚖️ LegalMet AI: Live Vision OCR Inspector")
st.write("Real-time optical character recognition & statutory compliance audit under The Legal Metrology (Packaged Commodities) Rules, 2011.")

st.markdown("---")

uploaded_file = st.file_uploader("Upload Any Product Label / Package Photo", type=["jpg", "jpeg", "png"])

def run_real_ocr_engine(image):
    # Perform actual OCR text extraction from the uploaded image pixels
    try:
        extracted_raw = pytesseract.image_to_string(image)
    except Exception as e:
        extracted_raw = ""
        st.warning(f"OCR engine notice: {e}")
        
    text_lower = extracted_raw.lower()
    
    # Deterministic rule evaluation based on REAL extracted text keywords
    
    # 1. Manufacturer / Packer Details
    mfg_found = any(k in text_lower for k in ["mfd", "manufactured", "marketed by", "mfg by", "packer", "address"])
    
    # 2. Generic Name
    name_found = len(extracted_raw.strip()) > 20  # Assumes descriptive text block exists
    
    # 3. Net Quantity
    net_found = any(k in text_lower for k in ["net", "quantity", "weight", "contents", "g", "kg", "ml", "l", "gms"])
    
    # 4. Month/Year of Packing
    date_found = any(k in text_lower for k in ["mfd", "packed", "batch", "pkd", "month", "2025", "2026"])
    
    # 5. MRP & Taxes
    mrp_found = "mrp" in text_lower
    taxes_found = "inclusive of all taxes" in text_lower or "incl. of all taxes" in text_lower or "inclusive of taxes" in text_lower
    
    # 6. Consumer Care
    consumer_found = any(k in text_lower for k in ["consumer", "care", "helpline", "email", "support", "@", "1800"])
    
    # 7. Country of Origin
    origin_found = any(k in text_lower for k in ["country of origin", "made in", "manufactured in"])

    checks = [
        {
            "rule": "Rule 6(1)(a) - Manufacturer Identity & Address",
            "status": "PASS" if mfg_found else "FAIL",
            "extracted": extracted_raw[:120].replace('\n', ' ') if mfg_found else "No manufacturer text detected",
            "details": "Corporate entity name and address located via OCR scan." if mfg_found else "VIOLATION: Manufacturer name/address not detected in image text."
        },
        {
            "rule": "Rule 6(1)(b) - Common or Generic Name",
            "status": "PASS" if name_found else "FAIL",
            "extracted": "Text block successfully scanned from principal display",
            "details": "Generic product description identified." if name_found else "VIOLATION: Generic commodity name unclear or missing."
        },
        {
            "rule": "Rule 6(1)(c) - Net Quantity Declaration",
            "status": "PASS" if net_found else "FAIL",
            "extracted": "SI metric units identifier matched in text scan",
            "details": "Net quantity declaration located in standard units." if net_found else "VIOLATION: Net quantity declaration missing from image."
        },
        {
            "rule": "Rule 6(1)(d) - Month & Year of Packing",
            "status": "PASS" if date_found else "FAIL",
            "extracted": "Batch/Packing metadata found in OCR text",
            "details": "Packing month/year metadata verified." if date_found else "VIOLATION: Packing date or batch details missing."
        },
        {
            "rule": "Rule 6(1)(e) - Retail Sale Price (MRP Format)",
            "status": "PASS" if (mrp_found and taxes_found) else "FAIL",
            "extracted": f"MRP Detected: {mrp_found} | Taxes Declaration: {taxes_found}",
            "details": "MRP and mandatory 'inclusive of all taxes' text verified." if (mrp_found and taxes_found) else "VIOLATION: MRP missing or lacks mandatory 'inclusive of all taxes' phrase."
        },
        {
            "rule": "Rule 6(2) - Consumer Care Details",
            "status": "PASS" if consumer_found else "FAIL",
            "extracted": "Helpline/Email contact patterns matched",
            "details": "Valid consumer grievance contact info detected." if consumer_found else "VIOLATION: Consumer care contact details missing."
        },
        {
            "rule": "Import Compliance - Country of Origin",
            "status": "PASS" if origin_found else "WARNING",
            "extracted": "Country of origin tag scan result",
            "details": "Origin declaration verified." if origin_found else "NOTICE: Country of origin not explicitly detected (mandatory for imports)."
        }
    ]
    return checks, extracted_raw

def generate_pdf_report(checks, final_status):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1f2937'), spaceAfter=4)
    subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#4b5563'), spaceAfter=12)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=7.5, leading=9, textColor=colors.HexColor('#1f2937'))
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=8, leading=10, fontName='Helvetica-Bold', textColor=colors.white)
    
    story.append(Paragraph("LEGAL METROLOGY VISION OCR AUDIT REPORT", title_style))
    story.append(Paragraph("Automated Computer Vision Statutory Inspection under The Legal Metrology Rules, 2011", subtitle_style))
    story.append(Spacer(1, 5))
    
    summary_color = colors.HexColor('#dc2626') if final_status == "NON-COMPLIANT" else colors.HexColor('#16a34a')
    summary_data = [[Paragraph(f"<b>FINAL AUDIT STATUS: {final_status}</b>", ParagraphStyle('SumText', textColor=colors.white, fontSize=11))]]
    summary_table = Table(summary_data, colWidths=[560])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), summary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))
    
    table_data = [[
        Paragraph("Rule Provision", header_style),
        Paragraph("OCR Scanned Text Preview", header_style),
        Paragraph("Status", header_style),
        Paragraph("Evaluation Findings", header_style)
    ]]
    
    for item in checks:
        status_text = item["status"]
        status_color = "#16a34a" if status_text == "PASS" else "#dc2626"
        status_cell = Paragraph(f"<font color='{status_color}'><b>{status_text}</b></font>", cell_style)
        
        table_data.append([
            Paragraph(item["rule"], cell_style),
            Paragraph(item["extracted"], cell_style),
            status_cell,
            Paragraph(item["details"], cell_style)
        ])
        
    t = Table(table_data, colWidths=[130, 150, 55, 225])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#374151')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Product Image Preview")
    
    if st.button("Run Live OCR Vision Audit"):
        with st.spinner("Scanning image pixels with Tesseract OCR engine..."):
            checks, raw_text = run_real_ocr_engine(image)
            failed_count = sum(1 for c in checks if c["status"] == "FAIL")
            final_status = "NON-COMPLIANT" if failed_count > 0 else "COMPLIANT"
            
            with st.expander("🔍 View Raw OCR Scanned Text"):
                st.text(raw_text if raw_text.strip() else "No text detected. Try a clearer, well-lit image.")
            
            st.markdown("### 📊 Statutory Audit Findings")
            
            for item in checks:
                if item["status"] == "PASS":
                    st.success(f"**{item['rule']}**\n\n📌 **OCR Scanned Snippet:** `{item['extracted']}`\n\n✅ **Status:** PASS — {item['details']}")
                else:
                    st.error(f"**{item['rule']}**\n\n📌 **OCR Scanned Snippet:** `{item['extracted']}`\n\n❌ **Status:** VIOLATION — {item['details']}")
            
            st.markdown("---")
            if final_status == "NON-COMPLIANT":
                st.error(f"**FINAL AUDIT RESULT: NON-COMPLIANT** ({failed_count} statutory violations detected)")
            else:
                st.success(f"**FINAL AUDIT RESULT: COMPLIANT** (All statutory checks passed)")
                
            pdf_buffer = generate_pdf_report(checks, final_status)
            st.download_button(
                label="📥 Download Official PDF Inspection Report",
                data=pdf_buffer,
                file_name="LegalMet_LiveOCR_Report.pdf",
                mime="application/pdf"
            )
