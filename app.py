import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet

# ---------- PAGE SETTINGS ----------
st.set_page_config(
    page_title="SalesFlow | Sales Analytics",
    page_icon="📊",
    layout="wide"
)

# ---------- PROFESSIONAL DESIGN ----------
st.markdown("""
<style>
.stApp {
    background: #f5f7fb;
}
.block-container {
    padding-top: 2rem;
    max-width: 1200px;
}
.hero {
    background: linear-gradient(120deg, #142850, #274690);
    padding: 30px;
    border-radius: 18px;
    color: white;
    margin-bottom: 25px;
}
.hero h1 {
    color: white;
    font-size: 38px;
    margin-bottom: 5px;
}
.hero p {
    color: #e0eaff;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>SalesFlow</h1>
    <p>Sales Data Automation & Analytics</p>
    <p>Turn sales spreadsheets into clear, actionable reports.</p>
</div>
""", unsafe_allow_html=True)

st.write(
    "Upload a CSV file to analyse sales, review data quality, "
    "visualise revenue, and download your reports."
)

st.caption(
    "Portfolio demo by an AI & ML diploma student. "
    "Use sample data or files you are authorised to process."
)

# ---------- FILE UPLOAD ----------
uploaded_file = st.file_uploader(
    "Upload your sales CSV",
    type=["csv"]
)

# ---------- PDF GENERATOR ----------
def make_pdf(report_rows, summary, total_revenue,
             original_count, duplicate_count, invalid_count):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("SalesFlow Sales Report", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Generated: " + datetime.now().strftime("%d %b %Y, %H:%M"),
        styles["Normal"]
    ))
    story.append(Spacer(1, 15))

    metrics = [
        ["Metric", "Value"],
        ["Original rows", str(original_count)],
        ["Duplicate rows detected", str(duplicate_count)],
        ["Rows needing review", str(invalid_count)],
        ["Rows included in analysis", str(len(report_rows))],
        ["Total revenue", f"Rs. {total_revenue:,.2f}"]
    ]

    table = Table(metrics, colWidths=[260, 180])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#142850")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke)
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Product-wise Revenue", styles["Heading2"]))
    product_data = [["Product", "Revenue"]]
    for _, row in summary.iterrows():
        product_data.append([
            str(row["product"]),
            f"Rs. {row['revenue']:,.2f}"
        ])

    product_table = Table(product_data, colWidths=[260, 180])
    product_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#274690")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))
    story.append(product_table)
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "Review excluded or invalid records before making business decisions.",
        styles["Normal"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ---------- PROCESS DATA ----------
if uploaded_file is not None:
    try:
        original = pd.read_csv(uploaded_file)
        original.columns = [
            str(col).strip().lower() for col in original.columns
        ]

        required = ["product", "quantity", "price"]
        missing = [col for col in required if col not in original.columns]

        if missing:
            st.error(
                "Missing required columns: " + ", ".join(missing)
            )
            st.stop()

        original_count = len(original)
        df = original.copy()

        df["product"] = df["product"].astype("string").str.strip()
        df["quantity"] = pd.to_numeric(
            df["quantity"], errors="coerce"
        )
        df["price"] = pd.to_numeric(
            df["price"], errors="coerce"
        )

        duplicate_count = int(df.duplicated().sum())
        df = df.drop_duplicates()

        invalid = (
            df["product"].isna()
            | df["product"].eq("")
            | df["quantity"].isna()
            | df["price"].isna()
            | (df["quantity"] < 0)
            | (df["price"] < 0)
        )
        invalid_count = int(invalid.sum())

        clean = df.loc[~invalid].copy()
        clean["revenue"] = clean["quantity"] * clean["price"]

        total_revenue = float(clean["revenue"].sum())
        summary = (
            clean.groupby("product", as_index=False)["revenue"]
            .sum()
            .sort_values("revenue", ascending=False)
        )

        st.success("Your sales report is ready!")

        # ---------- METRIC CARDS ----------
        a, b, c, d = st.columns(4)
        a.metric("Total Revenue", f"₹{total_revenue:,.2f}")
        b.metric("Valid Rows", len(clean))
        c.metric("Duplicates", duplicate_count)
        d.metric("Rows to Review", invalid_count)

        st.divider()

        # ---------- CHARTS ----------
        left, right = st.columns(2)

        with left:
            st.subheader("Revenue by Product")
            if not summary.empty:
                st.bar_chart(
                    summary.set_index("product")["revenue"]
                )
            else:
                st.info("No valid sales data to chart.")

        with right:
            st.subheader("Product Revenue Summary")
            st.dataframe(summary, use_container_width=True)

        # ---------- DATA TABLE ----------
        st.subheader("Cleaned Sales Data")
        st.dataframe(clean, use_container_width=True)

        # ---------- DOWNLOADS ----------
        st.subheader("Download Your Reports")

        csv_bytes = clean.to_csv(index=False).encode("utf-8")
        report_text = (
            "SALESFLOW SALES REPORT\n"
            "======================\n"
            f"Generated: {datetime.now():%d %b %Y %H:%M}\n"
            f"Original rows: {original_count}\n"
            f"Duplicate rows detected: {duplicate_count}\n"
            f"Rows needing review: {invalid_count}\n"
            f"Valid rows analysed: {len(clean)}\n"
            f"Total revenue: Rs. {total_revenue:,.2f}\n\n"
            "PRODUCT-WISE REVENUE\n"
            + summary.to_string(index=False)
        )

        pdf_bytes = make_pdf(
            clean, summary, total_revenue,
            original_count, duplicate_count, invalid_count
        )

        x, y, z = st.columns(3)
        x.download_button(
            "Download Cleaned CSV",
            data=csv_bytes,
            file_name="cleaned_sales.csv",
            mime="text/csv",
            use_container_width=True
        )
        y.download_button(
            "Download Text Report",
            data=report_text,
            file_name="sales_report.txt",
            mime="text/plain",
            use_container_width=True
        )
        z.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name="sales_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        with st.expander("View original uploaded data"):
            st.dataframe(original, use_container_width=True)

        st.caption(
            "SalesFlow portfolio demo. Check data quality and "
            "confirm business rules before relying on results."
        )

    except Exception as error:
        st.error(f"Unable to process this file: {error}")

else:
    st.info(
        "👆 Upload a CSV file to get started, or create a sample "
        "file with columns: product, quantity, price."
    )
    st.markdown("### How it works")
    a, b, c = st.columns(3)
    a.write("📂 **1. Upload**\n\nChoose a sales CSV file.")
    b.write("📊 **2. Analyse**\n\nReview revenue and data quality.")
    c.write("📄 **3. Export**\n\nDownload CSV, text, and PDF reports.")
