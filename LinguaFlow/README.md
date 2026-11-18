# LinguaFlow

A Streamlit language translator with multiple translation providers.

## Features
- 21 languages
- Automatic source-language detection
- Google Translate, LibreTranslate and MyMemory fallback
- Long-text chunking
- Translation history during the session
- Text download and speech generation

## Installation

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Limitations
This application uses public translation services. Availability, language coverage, request limits and daily quotas depend on those providers. There is no guarantee of unlimited free usage.
