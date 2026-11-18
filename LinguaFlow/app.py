import re
import html
import time
import requests
import streamlit as st
from io import BytesIO
from deep_translator import GoogleTranslator
from gtts import gTTS

st.set_page_config(
    page_title="LinguaFlow | Smart Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

LANGUAGES = {
    "Auto detect": {"code": "auto", "memory": "autodetect", "speech": None},
    "English": {"code": "en", "memory": "en", "speech": "en"},
    "Tamil": {"code": "ta", "memory": "ta", "speech": "ta"},
    "Hindi": {"code": "hi", "memory": "hi", "speech": "hi"},
    "Telugu": {"code": "te", "memory": "te", "speech": "te"},
    "Malayalam": {"code": "ml", "memory": "ml", "speech": "ml"},
    "Kannada": {"code": "kn", "memory": "kn", "speech": "kn"},
    "Bengali": {"code": "bn", "memory": "bn", "speech": "bn"},
    "Marathi": {"code": "mr", "memory": "mr", "speech": "mr"},
    "Gujarati": {"code": "gu", "memory": "gu", "speech": "gu"},
    "Punjabi": {"code": "pa", "memory": "pa", "speech": "pa"},
    "Urdu": {"code": "ur", "memory": "ur", "speech": "ur"},
    "French": {"code": "fr", "memory": "fr", "speech": "fr"},
    "German": {"code": "de", "memory": "de", "speech": "de"},
    "Spanish": {"code": "es", "memory": "es", "speech": "es"},
    "Italian": {"code": "it", "memory": "it", "speech": "it"},
    "Portuguese": {"code": "pt", "memory": "pt", "speech": "pt"},
    "Japanese": {"code": "ja", "memory": "ja", "speech": "ja"},
    "Korean": {"code": "ko", "memory": "ko", "speech": "ko"},
    "Chinese (Simplified)": {"code": "zh", "memory": "zh", "speech": "zh-CN"},
    "Arabic": {"code": "ar", "memory": "ar", "speech": "ar"},
    "Russian": {"code": "ru", "memory": "ru", "speech": "ru"},
}

# Public LibreTranslate instances may change availability.
LIBRE_ENDPOINTS = [
    "https://translate.astian.org/translate",
    "https://libretranslate.de/translate",
]

MYMEMORY_URL = "https://api.mymemory.translated.net/get"
MAX_MYMEMORY_BYTES = 430
MAX_INPUT_CHARACTERS = 12000
REQUEST_TIMEOUT = 18

if "history" not in st.session_state:
    st.session_state.history = []
if "translation_result" not in st.session_state:
    st.session_state.translation_result = None
if "source_text" not in st.session_state:
    st.session_state.source_text = ""

def split_text(text, max_bytes=MAX_MYMEMORY_BYTES):
    """Split text without cutting a UTF-8 character or word."""
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    chunks = []
    current = ""

    # Keep paragraph and sentence boundaries where possible.
    pieces = re.split(r"(?<=[.!?。！？\n])\s*", text)

    for piece in pieces:
        if not piece:
            continue

        candidate = current + (" " if current else "") + piece

        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(piece.encode("utf-8")) <= max_bytes:
            current = piece
            continue

        words = re.findall(r"\S+\s*", piece)
        for word in words:
            candidate = current + word
            if len(candidate.encode("utf-8")) <= max_bytes:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = word

                # Extremely long individual tokens are split by characters.
                while len(current.encode("utf-8")) > max_bytes:
                    fragment = ""
                    for char in current:
                        if len((fragment + char).encode("utf-8")) > max_bytes:
                            break
                        fragment += char
                    chunks.append(fragment)
                    current = current[len(fragment):]

    if current:
        chunks.append(current)

    return chunks

def libre_translate(text, source, target):
    errors = []

    for endpoint in LIBRE_ENDPOINTS:
        try:
            response = requests.post(
                endpoint,
                json={
                    "q": text,
                    "source": source,
                    "target": target,
                    "format": "text"
                },
                headers={"Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            result = data.get("translatedText")

            if result and result.strip():
                return html.unescape(result.strip()), endpoint

            errors.append(f"{endpoint}: Empty response")
        except Exception as exc:
            errors.append(f"{endpoint}: {str(exc)[:180]}")

    raise RuntimeError("LibreTranslate unavailable: " + " | ".join(errors))

def mymemory_translate(text, source, target):
    if source == "auto":
        source = "autodetect"

    response = requests.get(
        MYMEMORY_URL,
        params={"q": text, "langpair": f"{source}|{target}"},
        timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    data = response.json()

    if data.get("responseStatus") != 200:
        raise RuntimeError(
            data.get("responseDetails") or "MyMemory rejected the request."
        )

    result = data.get("responseData", {}).get("translatedText", "")

    if not result or not result.strip():
        raise RuntimeError("MyMemory returned an empty translation.")

    result = html.unescape(result.strip())

    # MyMemory sometimes returns the original text when no usable
    # translation is available. Treat that as an unsuccessful result.
    if result.casefold() == text.strip().casefold() and source != target:
        raise RuntimeError("The service returned the original text.")

    return result

def translate_chunk(text, source, target, disabled):
    errors = []

    # Google Translate
    if "Google Translate" not in disabled:
        try:
            result = GoogleTranslator(
                source=source,
                target=target
            ).translate(text)

            if result and result.strip():
                return result.strip(), "Google Translate"

        except Exception as exc:
            errors.append("Google Translate: " + str(exc)[:180])
            disabled.add("Google Translate")

    # LibreTranslate public instances
    if "LibreTranslate" not in disabled:
        try:
            result, endpoint = libre_translate(text, source, target)
            return result, "LibreTranslate"
        except Exception as exc:
            errors.append(str(exc)[:250])
            disabled.add("LibreTranslate")

    # MyMemory has a small per-request limit, so chunks are used.
    if "MyMemory" not in disabled:
        try:
            result = mymemory_translate(text, source, target)
            return result, "MyMemory"
        except Exception as exc:
            errors.append("MyMemory: " + str(exc)[:180])

    raise RuntimeError(" | ".join(errors) or "No translation service succeeded.")

def translate_full_text(text, source, target):
    chunks = split_text(text)
    translated_chunks = []
    providers = []
    disabled = set()

    progress = st.progress(0)
    status = st.empty()

    for index, chunk in enumerate(chunks):
        status.write(f"Translating part {index + 1} of {len(chunks)}...")

        result, provider = translate_chunk(
            chunk, source, target, disabled
        )

        translated_chunks.append(result)
        providers.append(provider)
        progress.progress((index + 1) / len(chunks))

        # Small pause to reduce request bursts.
        time.sleep(0.15)

    progress.empty()
    status.empty()

    # Keep paragraphs readable.
    translated = " ".join(translated_chunks)

    return translated, list(dict.fromkeys(providers)), len(chunks)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

.stApp {
    background:
      radial-gradient(ellipse at 10% 0%,rgba(54,111,230,.17),transparent 38%),
      radial-gradient(ellipse at 90% 25%,rgba(113,75,214,.13),transparent 35%),
      #0b1020;
    color: #edf2ff;
    font-family: 'DM Sans',sans-serif;
}
.block-container {max-width:1120px;padding-top:2rem;padding-bottom:3rem}
header[data-testid="stHeader"] {background:transparent}
.hero {text-align:center;padding:2rem 0 1.8rem}
.eyebrow {
 display:inline-block;border:1px solid #344c79;background:#172746;
 color:#a9c5ff;padding:7px 14px;border-radius:30px;
 font-size:12px;font-weight:700;letter-spacing:1px
}
.hero h1 {font-size:clamp(42px,6vw,65px);font-weight:800;letter-spacing:-2px;margin:14px 0 5px;color:#f5f7ff}
.hero h1 span {color:#83aaff}
.hero p {color:#a5b3cf;font-size:16px}
.panel {
 background:rgba(20,30,52,.88);border:1px solid rgba(148,172,222,.17);
 border-radius:20px;padding:24px;margin-bottom:20px;
 box-shadow:0 15px 40px rgba(0,0,0,.16)
}
.section-title {font-size:12px;letter-spacing:1px;font-weight:800;color:#9bb8f4;margin-bottom:12px}
.result {
 background:#111e35;border:1px solid #405c90;border-radius:16px;
 padding:20px;color:#f3f6ff;font-size:17px;line-height:1.8;
 white-space:pre-wrap;overflow-wrap:anywhere
}
.feature {
 background:#14213a;border:1px solid #2c3e61;
 border-radius:15px;padding:17px;min-height:110px
}
.feature strong {color:#eaf0ff}
.feature p {color:#9caccb;font-size:13px}
.footer {text-align:center;color:#7183a5;padding:28px 0;font-size:13px}
.stButton button,.stDownloadButton button {
 min-height:46px;border-radius:11px;font-weight:700;
 border:1px solid #5278c0;background:linear-gradient(110deg,#3978e8,#6758d9);
 color:white
}
.stButton button:hover {color:white;border-color:#a1bcff}
div[data-testid="stTextArea"] textarea {
 background:#111a2e;color:#f3f6ff;border:1px solid #35496d;
 border-radius:12px;font-size:16px;line-height:1.6
}
div[data-testid="stSelectbox"] > div > div {
 background:#111a2e;border-color:#35496d;border-radius:10px
}
hr {border-color:#283957}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
 <div class="eyebrow">SMART MULTI-LANGUAGE TRANSLATION</div>
 <h1>🌐 Lingua<span>Flow</span></h1>
 <p>Understand more. Connect everywhere.</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="section-title">01 / SELECT LANGUAGES</div>', unsafe_allow_html=True)

left, middle, right = st.columns([5, 1, 5])

with left:
    source_name = st.selectbox(
        "Translate from",
        list(LANGUAGES.keys()),
        index=1,
        key="source_choice"
    )

with middle:
    st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
    if st.button("⇄", help="Swap languages", use_container_width=True):
        if st.session_state.get("source_choice") != "Auto detect":
            old = st.session_state.source_choice
            st.session_state.source_choice = st.session_state.target_choice
            st.session_state.target_choice = old
            st.session_state.translation_result = None
            st.rerun()

with right:
    target_options = [name for name in LANGUAGES if name != "Auto detect"]
    target_name = st.selectbox(
        "Translate to",
        target_options,
        index=1,
        key="target_choice"
    )

st.markdown('<div class="section-title">02 / YOUR TEXT</div>', unsafe_allow_html=True)

input_text = st.text_area(
    "Enter text",
    placeholder="Write or paste text here. You can translate sentences and paragraphs...",
    height=190,
    max_chars=MAX_INPUT_CHARACTERS,
    label_visibility="collapsed",
    key="translation_input"
)

st.caption(f"Characters: {len(input_text)} / {MAX_INPUT_CHARACTERS}")

translate_clicked = st.button(
    "✦  Translate now",
    type="primary",
    use_container_width=True
)
st.markdown('</div>', unsafe_allow_html=True)

if translate_clicked:
    st.session_state.translation_result = None

    source = LANGUAGES[source_name]["code"]
    target = LANGUAGES[target_name]["code"]

    if not input_text.strip():
        st.warning("Enter some text before translating.")
    elif source == target:
        st.warning("Choose two different languages.")
    else:
        try:
            with st.spinner("Preparing your translation..."):
                translated, providers, chunk_count = translate_full_text(
                    input_text.strip(), source, target
                )

            st.session_state.translation_result = {
                "text": translated,
                "source": source_name,
                "target": target_name,
                "providers": providers,
                "chunks": chunk_count,
                "original": input_text.strip()
            }

            st.session_state.history.insert(0, {
                "source": source_name,
                "target": target_name,
                "text": translated
            })
            st.success("Translation completed.")

        except Exception as exc:
            st.error("We couldn't translate this text right now.")
            with st.expander("Technical details"):
                st.code(str(exc))
            st.info(
                "All available free providers may be temporarily unavailable "
                "or may have reached their usage limits. Please try again later."
            )

result = st.session_state.translation_result

if result:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">03 / TRANSLATION RESULT</div>', unsafe_allow_html=True)
    st.markdown(
        f"**{result['source']}**  →  **{result['target']}**"
    )
    st.markdown(
        '<div class="result">' + html.escape(result["text"]) + '</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Provider(s): " + ", ".join(result["providers"])
        + f" · Text sections: {result['chunks']}"
    )

    a, b = st.columns(2)
    with a:
        st.download_button(
            "⬇ Download translation",
            data=result["text"],
            file_name="linguaflow_translation.txt",
            mime="text/plain",
            use_container_width=True
        )
    with b:
        st.button(
            "New translation",
            use_container_width=True,
            on_click=lambda: st.session_state.update(
                translation_result=None
            )
        )

    speech_code = LANGUAGES[result["target"]]["speech"]

    if speech_code:
        if st.button("🔊 Generate speech", use_container_width=True):
            try:
                audio = BytesIO()
                gTTS(text=result["text"], lang=speech_code).write_to_fp(audio)
                st.audio(audio.getvalue(), format="audio/mp3")
            except Exception as exc:
                st.warning("Speech generation is unavailable right now.")
                st.caption(str(exc))

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">BUILT FOR CLEAR COMMUNICATION</div>', unsafe_allow_html=True)

one, two, three = st.columns(3)

with one:
    st.markdown("""
    <div class="feature">
      <strong>🌍 21 languages</strong>
      <p>Translate across widely used world and Indian languages.</p>
    </div>
    """, unsafe_allow_html=True)

with two:
    st.markdown("""
    <div class="feature">
      <strong>🔄 Provider fallback</strong>
      <p>Try alternative services when a translation provider is unavailable.</p>
    </div>
    """, unsafe_allow_html=True)

with three:
    st.markdown("""
    <div class="feature">
      <strong>📄 Longer text support</strong>
      <p>Split longer input into smaller sections before sending requests.</p>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.history:
    with st.expander("🕘 Recent translations"):
        for item in st.session_state.history[:10]:
            st.markdown(f"**{item['source']} → {item['target']}**")
            st.write(item["text"])
            st.divider()

st.markdown("""
<div class="footer">
 LinguaFlow · CodeAlpha Language Translator<br>
 A multilingual translation project
</div>
""", unsafe_allow_html=True)
