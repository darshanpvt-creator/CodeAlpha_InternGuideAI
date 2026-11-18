import requests

API_ENDPOINTS = [
    "https://translate.flossboxin.org.in/translate",
    "https://libretranslate.de/translate",
    "https://translate.argosopentech.com/translate"
]


def translate_text(text, source_language, target_language):
    if not text or not text.strip():
        raise ValueError("Please enter text to translate.")

    if source_language == target_language:
        return text

    payload = {
        "q": text,
        "source": source_language,
        "target": target_language,
        "format": "text"
    }

    errors = []

    for endpoint in API_ENDPOINTS:
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20
            )

            response.raise_for_status()
            data = response.json()

            translated = data.get("translatedText")

            if translated and translated.strip():
                return translated

            errors.append(f"{endpoint}: Empty translation")

        except (requests.RequestException, ValueError) as error:
            errors.append(f"{endpoint}: {error}")

    raise RuntimeError(
        "All translation servers are currently unavailable. "
        "Please try again later. Details: " + " | ".join(errors)
    )
