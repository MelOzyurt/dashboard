import streamlit as st

print("dashboard.py started")

# =========================
#  PAGE / NAVIGATION STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "hub"  # "hub", "feedback_app", "other_app", ...

def go_home():
    st.session_state.page = "hub"

def go_to(page_name: str):
    st.session_state.page = page_name


# =========================
#  APP 1: CLIENT FEEDBACK ANALYZER (NO LOGIN)
# =========================
def run_client_feedback_analyzer():
    print("client feedback app started")

    # Page title
    st.title("📊 Client Feedback Analyzer")

    # 🔙 Back to Home button
    if st.button("🏠 Back to Home"):
        go_home()
        st.stop()

    # ========== APP WITHOUT LOGIN ==========

    import pandas as pd
    import openai
    from utils import preprocess_reviews
    from fpdf import FPDF

    # OpenAI Client (using Streamlit secrets)
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # AI interpretation helper
    def ai_interpretation(prompt):
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful AI assistant that analyzes customer feedback and generates insights. "
                            "Don't use the customer names on your report, just analyse attributes, outcomes as given requirements by code. "
                            "Don't list the reviews like review 1, review 2, the user is trying to understand the similarities and common patterns. "
                            "The user should know what's wrong with the product or services, what the pain points are, and what the repeating problems are."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"**Error during AI interpretation:** {e}"

    # Simple word-based limiter
    def truncate_text_by_tokens(text, max_tokens=1500):
        words = text.split()
        truncated = []
        token_count = 0
        for word in words:
            token_count += 1
            if token_count > max_tokens:
                break
            truncated.append(word)
        return " ".join(truncated)

    # Data input section
    st.subheader("Upload a dataset or paste your customer reviews below")

    uploaded_file = st.file_uploader(
        "Upload your feedback dataset", type=["csv", "xlsx", "xls", "json", "xml"]
    )

    # Initialize reviews list in session_state for persistence
    if "reviews" not in st.session_state:
        st.session_state.reviews = []

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith(".json"):
                df = pd.read_json(uploaded_file)
            elif uploaded_file.name.endswith(".xml"):
                df = pd.read_xml(uploaded_file)
            else:
                st.error("Unsupported file format.")
                st.stop()

            st.write("### Data Preview")
            st.dataframe(df.head())

            possible_cols = [
                col
                for col in df.columns
                if any(
                    keyword in col.lower()
                    for keyword in ["review", "feedback", "comment", "text"]
                )
            ]
            if not possible_cols:
                st.warning("No suitable text column found. Please paste your reviews below.")
                st.session_state.reviews = []
            else:
                chosen_col = st.selectbox(
                    "Select the text column for analysis", possible_cols
                )
                st.session_state.reviews = (
                    df[chosen_col].dropna().astype(str).tolist()
                )

        except Exception as e:
            st.error(f"Failed to load file: {e}")
            st.session_state.reviews = []
            st.stop()

    # Manual input if no file
    if not st.session_state.reviews:
        st.info("Or paste your customer reviews (one per line) below:")
        raw_text = st.text_area("Paste reviews here", height=200, value="")
        if raw_text.strip():
            st.session_state.reviews = [
                line.strip() for line in raw_text.split("\n") if line.strip()
            ]

    if not st.session_state.reviews:
        st.warning("Please upload a dataset or paste some reviews to analyze.")
        st.stop()

    if st.button("Analyze It"):
        # Preprocess
        reviews_clean_full = preprocess_reviews(
            "\n".join(st.session_state.reviews[:50])
        )  # limit to 50 reviews
        reviews_clean = truncate_text_by_tokens(reviews_clean_full, max_tokens=1500)

        # Prompts
        sentiment_prompt = f"""
Analyze the sentiment of the following customer reviews. Provide an overall summary of positive, negative, and neutral sentiments, and highlight any patterns or anomalies.

Customer reviews:
\"\"\"{reviews_clean}\"\"\""""

        swot_prompt = f"""
Perform a SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) based on the following customer feedback dataset:

\"\"\"{reviews_clean}\"\"\""""

        insight_prompt = f"""
Analyze the following customer feedback and provide insights about key themes, patterns, anomalies, and recommendations for the product/service.

\"\"\"{reviews_clean}\"\"\""""

        # AI analyses
        with st.spinner("Analyzing customer feedback..."):
            sentiment_result = ai_interpretation(sentiment_prompt)
            swot_result = ai_interpretation(swot_prompt)
            insight_result = ai_interpretation(insight_prompt)

        # Show results
        st.markdown("## 📝 Sentiment Analysis")
        st.write(sentiment_result)

        st.markdown("## 🏋️ SWOT Analysis")
        st.write(swot_result)

        st.markdown("## 🔎 AI Insights on Patterns & Anomalies")
        st.write(insight_result)

        st.success("✅ All analyses completed successfully.")

        class PDF(FPDF):
            def header(self):
                self.set_font("DejaVu", "", 14)
                self.cell(0, 10, "Client Feedback Analyzer Report", 0, 1, "C")

        def create_pdf_report(sentiment, swot, insight):
            pdf = PDF()
            pdf.add_page()

            # Unicode font (adjust path if needed on your system)
            pdf.add_font(
                "DejaVu",
                "",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                uni=True,
            )
            pdf.set_font("DejaVu", "", 12)

            pdf.cell(0, 10, "📝 Sentiment Analysis:", ln=True)
            pdf.multi_cell(0, 10, sentiment)
            pdf.ln(5)

            pdf.cell(0, 10, "🏋️ SWOT Analysis:", ln=True)
            pdf.multi_cell(0, 10, swot)
            pdf.ln(5)

            pdf.cell(0, 10, "🔎 AI Insights on Patterns & Anomalies:", ln=True)
            pdf.multi_cell(0, 10, insight)
            pdf.ln(5)

            return pdf.output(dest="S").encode("latin1")

        pdf_report = create_pdf_report(
            sentiment_result, swot_result, insight_result
        )
        st.download_button(
            label="Download the report as PDF",
            data=pdf_report,
            file_name="client_feedback_report.pdf",
            mime="application/pdf",
        )


# =========================
#  OTHER APP (placeholder)
# =========================
def run_other_app():
    st.title("📦 Second App (Placeholder)")
    if st.button("🏠 Back to Home"):
        go_home()
        st.stop()
    st.write("This is just a placeholder for your second mini app.")


# =========================
#  HUB (MAIN DASHBOARD)
# =========================
def run_hub():
    st.title("🧭 Analytics Hub")

    st.write("From this hub, you can open different mini analytics apps:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Client Feedback Analyzer", use_container_width=True):
            go_to("feedback_app")

    with col2:
        if st.button("📦 Second App (coming soon)", use_container_width=True):
            go_to("other_app")

    with col3:
        st.button("➕ Add new app... (placeholder)", disabled=True, use_container_width=True)


# =========================
#  MAIN
# =========================
def main():
    st.set_page_config(page_title="Analytics Hub", layout="wide")

    # Sidebar nav
    st.sidebar.title("Navigation")
    if st.sidebar.button("🏠 Home"):
        go_home()

    # Decide which page to show
    page = st.session_state.page

    if page == "hub":
        run_hub()
    elif page == "feedback_app":
        run_client_feedback_analyzer()
    elif page == "other_app":
        run_other_app()
    else:
        run_hub()


if __name__ == "__main__":
    main()
