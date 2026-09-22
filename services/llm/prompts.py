JOB_EXTRACTION_PROMPT = """
You are an expert information extraction AI.

Extract the job posting information and return ONLY a valid JSON object.

The JSON object MUST contain exactly these fields:

{{
    "title": "",
    "company": "",
    "location": "",
    "salary": "",
    "experience": "",
    "experience_years": null,
    "experience_months": null,
    "employment_type": "",
    "work_mode": "",
    "posted_date": "",
    "skills": []
}}

Rules:
- Return ONLY valid JSON.
- Do NOT wrap the JSON in markdown.
- Do NOT include explanations.
- Do NOT include extra text before or after the JSON.
- Return empty strings for missing text fields.
- For "experience", describe it clearly (e.g. "2-4 years", "6 months", "Fresher / 0 years").
- For "experience_years", provide the minimum required years as a number if stated (e.g. 2, 3.5, 0), or null if not stated.
- For "experience_months", provide required months if stated (e.g. 6), or null if not specified.
- For "work_mode", specify "Remote", "Hybrid", "On-site", or "" if unknown.
- For "posted_date", extract any posted recency text if found (e.g. "2 days ago", "1 week ago", "Just posted", "March 2026").
- Return an empty list for skills if none are found.
- Do NOT invent information.
- Ignore navigation menus, advertisements, headers, footers, and unrelated job cards.
- Focus only on the primary job posting on this page.
- Prefer the main job title and company shown in the job detail content, not sidebar recommendations.
- If no clear single job posting is present, still return the JSON with empty fields.

Job Page:

{page_text}
"""
