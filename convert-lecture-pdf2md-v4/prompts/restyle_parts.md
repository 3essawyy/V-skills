You repair specific PARTs of a merc-styled lecture markdown that failed validation. FORMAT ONLY: never add explanations or facts, never drop content.

Styled file: `{OUT}` (edit in place with the Edit tool). Raw conversion (source of truth for wording): `{IN}`. Pattern reference: `{STYLE_GUIDE}` (read it first). Full styling rules: `{STYLE_PROMPT}` (read it; the same rules apply).

Failing PARTs: {PARTS}
Validator problems:
{PROBLEMS}

For each failing PART: compare its slides with the matching `## Slide N:` sections of the raw file and fix every listed problem (missing words → restore them verbatim from raw; anchors/headings; math, table, Mermaid or callout syntax per the style guide). You may also improve that PART's formatting under the same rules. Touch nothing outside the failing PARTs, except ToC lines that point into them.

Reply under 80 words: per PART what you fixed.
