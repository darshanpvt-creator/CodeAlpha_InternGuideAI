const LANGUAGES = {
  en:"English", ta:"Tamil", hi:"Hindi", te:"Telugu", ml:"Malayalam",
  kn:"Kannada", bn:"Bengali", mr:"Marathi", gu:"Gujarati", pa:"Punjabi",
  ur:"Urdu", fr:"French", de:"German", es:"Spanish", it:"Italian",
  pt:"Portuguese", ja:"Japanese", ko:"Korean", zh:"Chinese",
  ar:"Arabic", ru:"Russian", nl:"Dutch"
};

function splitUtf8(text, maxBytes = 430) {
  const words = text.match(/\S+\s*/gu) || [text];
  const chunks = [];
  let current = "";

  for (const word of words) {
    if (new TextEncoder().encode(current + word).length <= maxBytes) {
      current += word;
    } else {
      if (current) chunks.push(current);
      current = "";

      if (new TextEncoder().encode(word).length <= maxBytes) {
        current = word;
      } else {
        for (const char of word) {
          if (new TextEncoder().encode(current + char).length > maxBytes) {
            if (current) chunks.push(current);
            current = "";
          }
          current += char;
        }
      }
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

async function google(text, source, target) {
  const url = new URL("https://translate.googleapis.com/translate_a/single");
  url.searchParams.set("client", "gtx");
  url.searchParams.set("sl", source);
  url.searchParams.set("tl", target);
  url.searchParams.set("dt", "t");
  url.searchParams.set("q", text);

  const response = await fetch(url, {
    signal: AbortSignal.timeout(15000)
  });
  if (!response.ok) throw new Error("Google translation returned HTTP " + response.status);

  const data = await response.json();
  const translated = (data[0] || []).map(row => row?.[0] || "").join("");
  if (!translated) throw new Error("Google returned an empty translation");

  return {
    text: translated,
    detected: data[2] || source,
    provider: "Google Translate"
  };
}

const LIBRE_SERVERS = [
  "https://translate.astian.org/translate",
  "https://libretranslate.de/translate"
];

async function libre(text, source, target) {
  const errors = [];
  for (const endpoint of LIBRE_SERVERS) {
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
          q: text, source, target, format: "text"
        }),
        signal: AbortSignal.timeout(12000)
      });

      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.json();
      if (!data.translatedText) throw new Error("Empty translation");

      return {
        text: data.translatedText,
        detected: source,
        provider: "LibreTranslate"
      };
    } catch (error) {
      errors.push(error.message);
    }
  }
  throw new Error(errors.join("; "));
}

async function myMemory(text, source, target) {
  if (source === "auto") {
    throw new Error("MyMemory fallback needs a selected source language.");
  }

  const url = new URL("https://api.mymemory.translated.net/get");
  url.searchParams.set("q", text);
  url.searchParams.set("langpair", source + "|" + target);

  const response = await fetch(url, {
    signal: AbortSignal.timeout(15000)
  });
  if (!response.ok) throw new Error("MyMemory HTTP " + response.status);

  const data = await response.json();
  if (Number(data.responseStatus) !== 200) {
    throw new Error(data.responseDetails || "MyMemory rejected the request");
  }

  const translated = data.responseData?.translatedText;
  if (!translated) throw new Error("MyMemory returned an empty translation");

  return {
    text: translated,
    detected: source,
    provider: "MyMemory"
  };
}

async function translateChunk(text, source, target) {
  const errors = [];

  try {
    return await google(text, source, target);
  } catch (error) {
    errors.push("Google: " + error.message);
  }

  try {
    return await libre(text, source, target);
  } catch (error) {
    errors.push("LibreTranslate: " + error.message);
  }

  try {
    return await myMemory(text, source, target);
  } catch (error) {
    errors.push("MyMemory: " + error.message);
  }

  throw new Error(errors.join(" | "));
}

exports.handler = async (event) => {
  const headers = {
    "Content-Type": "application/json",
    "Cache-Control": "no-store"
  };

  if (event.httpMethod !== "POST") {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({error:"Use POST for translation."})
    };
  }

  try {
    const body = JSON.parse(event.body || "{}");
    const text = String(body.text || "").trim();
    const source = String(body.source || "en").toLowerCase();
    const target = String(body.target || "ta").toLowerCase();

    if (!text) {
      return {statusCode:400, headers, body:JSON.stringify({error:"Enter text to translate."})};
    }

    if (text.length > 12000) {
      return {statusCode:400, headers, body:JSON.stringify({error:"Maximum input length is 12,000 characters."})};
    }

    if (!LANGUAGES[target] || (source !== "auto" && !LANGUAGES[source])) {
      return {statusCode:400, headers, body:JSON.stringify({error:"Unsupported language selection."})};
    }

    if (source === target) {
      return {statusCode:400, headers, body:JSON.stringify({error:"Choose two different languages."})};
    }

    const chunks = splitUtf8(text);
    const results = [];
    const providers = new Set();
    let detected = source;

    for (const chunk of chunks) {
      const result = await translateChunk(chunk, detected, target);
      results.push(result.text);
      providers.add(result.provider);
      if (detected === "auto" && result.detected) detected = result.detected;
    }

    return {
      statusCode:200,
      headers,
      body:JSON.stringify({
        translation:results.join(""),
        providers:[...providers],
        detectedLanguage:detected,
        parts:chunks.length
      })
    };

  } catch (error) {
    console.error("Translation error:", error);
    return {
      statusCode:502,
      headers,
      body:JSON.stringify({
        error:"All free translation services are currently unavailable or have reached their limits.",
        details:error.message
      })
    };
  }
};
