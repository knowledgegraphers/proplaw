# Propra API Contract — v0.3

## Base URL
`http://localhost:8000` (development)

---

## POST /query

Main endpoint. The user submits a legal question along with structured context from the guided input fields. The backend returns an explanation with citations.

### Request

```json
{
  "question": "Wie hoch darf mein Zaun sein?",
  "jurisdiction": "BE",
  "language": "de",
  "property_type": "single_family_house",
  "floors": 2
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `question` | string | yes | User question (German or English) |
| `jurisdiction` | string | yes | 2-letter German state code |
| `language` | enum | yes | `"de"` or `"en"` — follows the UI language toggle |
| `property_type` | enum | yes | Property category selected by the user |
| `floors` | integer | yes | Number of floors of the building |

### Allowed jurisdiction values

```
BE, BW, BY, BB, HB, HH, HE, MV,
NI, NW, RP, SL, SN, ST, SH, TH
```

The backend should accept both uppercase and lowercase. The frontend will normalize values to uppercase.

### Property type values (MVP)

```
single_family_house
semi_detached_house
multi_family_house
apartment_building
commercial_building
```

These are English slugs used as API values. The frontend maps them to German or English display labels depending on the UI language toggle. The backend maps them to the corresponding German KG node names.

---

### Response (200)

```json
{
  "answer": "In Berlin darf ein Zaun an der Grundstücksgrenze bis zu 1,20 m hoch sein.",
  "citations": [
    {
      "id": "BauOBln_6_7",
      "paragraph": "§ 6 Abs. 7",
      "regulation": "BauOBln",
      "jurisdiction": "BE",
      "url": "https://gesetze.berlin.de/..."
    }
  ],
  "confidence": "medium",
  "next_action": "Sprechen Sie mit Ihrem Bezirksamt, bevor Sie mit dem Bau beginnen.",
  "language": "de"
}
```

| Field | Type | Notes |
|---|---|---|
| `answer` | string | Plain-language explanation for the user |
| `citations` | array (1..n) | At least one citation is required |
| `confidence` | enum | `"low"`, `"medium"`, `"high"` |
| `next_action` | string | Concrete next step for the user |
| `language` | string | Echoes the request language — all response content must be in this language |

### Citation object

| Field | Type | Notes |
|---|---|---|
| `id` | string (optional) | Unique citation identifier |
| `paragraph` | string | Legal paragraph reference |
| `regulation` | string | Regulation name (e.g. BauOBln) |
| `jurisdiction` | string | State code |
| `url` | string (optional) | Link to the legal text |

---

### Error response (422 / 500)

```json
{
  "detail": "Field 'jurisdiction' must be a valid German state code.",
  "user_message": "Ihre Anfrage konnte nicht verarbeitet werden. Bitte versuchen Sie es erneut."
}
```

| Field | Purpose |
|---|---|
| `detail` | Developer-facing error message (English) |
| `user_message` | User-facing message — must be in the language matching the request `language` field |

---

## GET /health

```json
{ "status": "ok" }
```

Used for infrastructure monitoring.

---

## Backend rules (from CLAUDE.md)

- `confidence: "high"` must never be returned when B-Plan data is absent
- All outputs must be validated using Pydantic
- Every response must include at least one citation
- All user-facing content in the response (including `user_message` in errors) must match the `language` field in the request

---

## Notes for backend team

- The `property_type` and `floors` slugs in this contract are a starting point for MVP. Backend should update them to reflect whichever property categories are most useful given the most important nodes in the Knowledge Graph.
- The backend is responsible for mapping `property_type` slugs to the corresponding German KG node names.
- The frontend will normalize jurisdiction values to uppercase before sending requests.
