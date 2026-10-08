# Table of Contents — Template

This is the exact format to use for Tables of Contents in generated guides.

---

## Standard ToC Format

```markdown
## Table of Contents

1. [First Major Section Title](#part-1--first-major-section-title)
2. [Second Major Section Title](#part-2--second-major-section-title)
3. [Third Major Section Title](#part-3--third-major-section-title)
4. [Fourth Major Section Title](#part-4--fourth-major-section-title)
```

---

## Anchor Link Rules

1. Take the full H1 heading text: `# PART 1 — First Major Section Title`
2. Remove the `#` and leading space
3. Lowercase everything
4. Replace spaces with hyphens (`-`)
5. The em-dash `—` becomes `--`
6. Remove all other special characters (`&`, `?`, `!`, `:`, etc.)
7. Result: `#part-1--first-major-section-title`

---

## Real Example (from ISTQB Guide)

```markdown
## Table of Contents

1. [Test Design Techniques — Black-Box](#part-1--test-design-techniques-black-box)
2. [Test Design Techniques — White-Box](#part-2--test-design-techniques-white-box)
3. [Experience-Based Techniques](#part-3--experience-based-techniques)
4. [Test Process Activities](#part-4--test-process-istqb-activities)
5. [Defect Management](#part-5--defect-management)
6. [Static Testing](#part-6--static-testing)
7. [Test Management](#part-7--test-management)
8. [Verification vs. Validation](#part-8--verification-vs-validation)
```

---

## Rules

- Number every item (1, 2, 3...)
- Each item links to the corresponding PART H1 heading
- ToC appears immediately after the title block and `---` separator
- After the ToC, add another `---` before PART 1 begins
- If the guide is split into multiple files, the index file's ToC links to the separate files instead of anchors
