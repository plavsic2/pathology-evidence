"""Blinded, research-only visual comparison of retrieved pathology tiles."""

import base64
import io
import json
import os
import urllib.request

from PIL import Image, ImageDraw


LUMEN_URL = "https://lumen.ncsa.illinois.edu/v1/chat/completions"
MODEL = "gemma-4-31b-it"

PROMPT = """
You are comparing three H&E-stained colorectal tissue tiles.

Image A is the query.
Images B and C are reference examples with hidden tissue classes.

For EACH reference (B and C), compare it directly with A.

Return ONLY a valid JSON object in this exact structure:

{
  "B": {
    "supporting": [
      "Specific visible similarity",
      "Specific visible similarity"
    ],
    "contrasting": [
      "Specific visible difference",
      "Specific visible difference"
    ]
  },
  "C": {
    "supporting": [
      "Specific visible similarity",
      "Specific visible similarity"
    ],
    "contrasting": [
      "Specific visible difference",
      "Specific visible difference"
    ]
  }
}

Rules:
- Provide 2 or 3 supporting points and 2 or 3 contrasting points per reference.
- Each bullet must be one concise sentence, ideally under 18 words.
- Focus on visible fiber architecture, nuclear shape, density,
  arrangement, and staining.
- Be specific to the actual images, not generic tissue descriptions.
- Only describe features that can reasonably be observed.
- Avoid unsupported interpretations and clinical diagnoses.
- Do not infer hidden class labels.
- Do not choose a winning reference.
- Do not include markdown formatting or explanatory text outside JSON.
"""


def explain_retrieval(analysis, api_key=None):
    """Generate a blinded comparison using the top two predicted classes."""
    predictions = analysis["predictions"][:2]
    if len(predictions) < 2:
        raise ValueError("At least two predicted classes are required")

    references = [prediction["references"][0] for prediction in predictions]

    paths = [
        analysis["query"]["image_path"],
        references[0]["image_path"],
        references[1]["image_path"],
    ]

    canvas = Image.new("RGB", (728, 270), "white")
    draw = ImageDraw.Draw(canvas)

    for i, path in enumerate(paths):
        with Image.open(path) as image:
            tile = image.convert("RGB")
            if tile.size != (224, 224):
                raise ValueError(f"Unexpected tile dimensions: {tile.size}")
            x = 8 + i * 240
            canvas.paste(tile, (x, 36))
            draw.text((x, 10), f"Image {'ABC'[i]}", fill="black")

    buffer = io.BytesIO()
    canvas.save(buffer, format="JPEG", quality=75)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64," + encoded
                    },
                },
            ],
        }],
        "max_tokens": 1200,
    }

    key = api_key or os.environ["LUMEN_API_KEY"]

    request = urllib.request.Request(
        LUMEN_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        output = json.load(response)

    return {
        "model": MODEL,
        "comparison": output["choices"][0]["message"]["content"],
        "image_mapping": {
            "A": {"role": "query", "image_id": analysis["query"]["image_id"]},
            "B": {
                "role": "reference",
                "class_id": references[0]["class_id"],
                "image_id": references[0]["image_id"],
            },
            "C": {
                "role": "reference",
                "class_id": references[1]["class_id"],
                "image_id": references[1]["image_id"],
            },
        },
    }


CANDIDATE_PROMPT = """
You are comparing H&E-stained colorectal tissue tiles.

Image A is the query.
Images B, C, and D are retrieved reference examples.
Their tissue class is intentionally hidden.

Compare the visible morphology of A against the references.

Return ONLY valid JSON:

{
  "supporting": [],
  "contrasting": []
}

Rules:
- Include 0 to 3 supporting similarities and 1 to 3 contrasting differences.
- Do not invent supporting evidence to fill the list.
- If only generic similarities exist, such as pink staining, leave
  supporting empty.
- Each bullet must be a complete, concise sentence under 20 words.
- Focus on observable fiber patterns, nuclear shapes, density,
  spatial arrangement, and tissue architecture.
- Compare the query directly with the references, not just describe
  the images independently.
- When a feature appears in only one reference, identify that image.
- Distinguish visible observations from uncertain interpretations.
- Do not infer tissue class names or clinical diagnoses.
- Avoid terms such as pleomorphic, atypical, malignant,
  hyperchromatic, or high nuclear-to-cytoplasmic ratio.
- Do not identify cell types unless directly distinguishable.
- Do not select a winning class.
- No markdown or text outside the JSON object.
"""


def explain_candidates(analysis, api_key=None, max_refs=3):
    """Generate blinded supporting and contrasting evidence per candidate."""

    key = api_key or os.environ["LUMEN_API_KEY"]
    query_path = analysis["query"]["image_path"]
    candidates = []

    for prediction in analysis["predictions"]:
        references = prediction["references"][:max_refs]

        if not references:
            continue

        paths = [query_path] + [
            ref["image_path"] for ref in references
        ]

        width = len(paths) * 240 + 8
        canvas = Image.new("RGB", (width, 270), "white")
        draw = ImageDraw.Draw(canvas)

        for i, path in enumerate(paths):
            with Image.open(path) as image:
                tile = image.convert("RGB")

            if tile.size != (224, 224):
                raise ValueError(
                    f"Unexpected tile dimensions: {tile.size}"
                )

            x = 8 + i * 240
            canvas.paste(tile, (x, 36))
            draw.text(
                (x, 10),
                f"Image {chr(ord('A') + i)}",
                fill="black",
            )

        buffer = io.BytesIO()
        canvas.save(buffer, format="JPEG", quality=75)

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode("ascii")

        payload = {
            "model": MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": CANDIDATE_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/jpeg;base64," + encoded
                        },
                    },
                ],
            }],
            "max_tokens": 700,
        }

        request = urllib.request.Request(
            LUMEN_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
        )

        explanation_unavailable = False
        try:
            with urllib.request.urlopen(
                request, timeout=45
            ) as response:
                output = json.load(response)

            raw = output["choices"][0]["message"]["content"].strip()

            # Handle JSON optionally enclosed in markdown fences.
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            evidence = json.loads(raw)

            if not all(
                isinstance(evidence.get(field), list)
                and all(isinstance(item, str) for item in evidence[field])
                for field in ("supporting", "contrasting")
            ):
                raise ValueError("Unexpected evidence response structure")

        except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            print(
                f"Evidence unavailable for {prediction['class_id']}: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )
            evidence = {'supporting': [], 'contrasting': []}
            explanation_unavailable = True

        candidates.append({
            "class_id": prediction["class_id"],
            "references": [
                {
                    "image_id": ref["image_id"],
                    "image_path": ref["image_path"],
                }
                for ref in references
            ],
            "supporting": evidence["supporting"],
            "contrasting": evidence["contrasting"],
            "explanation_unavailable": explanation_unavailable,
        })

    return {
        "query": analysis["query"],
        "candidates": candidates,
    }
