"""
Prompt templates for various agents in the email assistant workflow.
These templates are used by LLM agents to generate structured outputs.
"""

from langchain.prompts import ChatPromptTemplate

# Input Parser Prompt
INPUT_PARSER_PROMPT = ChatPromptTemplate.from_template("""
You are an expert at understanding email composition requests.

Extract the following information from the user's request:
1. Recipient name or title
2. Email purpose/intent
3. Key points that must be included
4. Tone preference (if mentioned): formal, casual, assertive, empathetic
5. Any constraints (length, specific requirements)
6. Additional context

User Request: {user_input}

Return your analysis as a JSON object with these fields:
- recipient_name
- recipient_email (if provided)
- email_purpose
- key_points (array)
- tone_preference (default: "formal")
- constraints (object with any limits)
- context (any background info)

Be thorough but concise. If information isn't provided, use reasonable defaults.
""")

# Intent Detector Prompt
INTENT_DETECTOR_PROMPT = ChatPromptTemplate.from_template("""
You are an expert at classifying email intents.

Based on the email purpose and context, classify the intent into ONE of these categories:
{intents}

Email Purpose: {email_purpose}
Key Points: {key_points}
Context: {context}

Respond with ONLY the intent category name (e.g., "outreach", "follow_up", etc.).
No explanation needed.
""")

# Draft Writer Prompts by Intent
OUTREACH_PROMPT = """
Write a professional outreach email with this structure:

1. Personalized opening (reference recipient's work/company)
2. Brief self-introduction
3. Clear value proposition
4. Specific ask or next step
5. Professional closing

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

Make it concise (150-200 words), engaging, and action-oriented.
"""

FOLLOWUP_PROMPT = """
Write a follow-up email that:

1. References previous interaction/email
2. Provides context reminder
3. Adds new value or information
4. Includes clear call-to-action
5. Shows respect for their time

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

Keep it brief (100-150 words) and non-pushy.
"""

THANKYOU_PROMPT = """
Write a genuine thank you email that:

1. Opens with sincere gratitude
2. Specifically mentions what you're thanking them for
3. Explains the impact or value
4. Offers reciprocity if appropriate
5. Warm closing

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

Make it warm and authentic (100-150 words).
"""

MEETING_REQUEST_PROMPT = """
Write a meeting request email that:

1. Clear subject line suggestion
2. Brief context for the meeting
3. Proposed agenda or topics
4. Specific time options or scheduling link
5. Expected duration

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

Be respectful and organized (150-200 words).
"""

APOLOGY_PROMPT = """
Write a sincere apology email that:

1. Takes clear responsibility
2. Acknowledges the impact
3. Explains what happened (briefly, no excuses)
4. Describes corrective action
5. Asks for another chance

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: empathetic and professional

Be genuine and concise (150-200 words).
"""

INFORMATION_REQUEST_PROMPT = """
Write an information request email that:

1. Polite opening
2. Context for your request
3. Specific questions or information needed
4. Why you're asking them specifically
5. Appreciation for their time

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

Be clear and respectful (150-200 words).
"""

# Tone Stylist Prompt
TONE_STYLIST_PROMPT = ChatPromptTemplate.from_template("""
You are an expert at adjusting email tone while preserving the core message.

Original Draft:
{draft}

Target Tone: {tone}

Tone Guidelines:
- Characteristics: {characteristics}
- Vocabulary: {vocabulary}
- Structure: {structure}
- Greeting style: {greeting}
- Closing style: {closing}

Rewrite the email to match the target tone perfectly while:
1. Keeping all key points and information
2. Maintaining appropriate length
3. Ensuring natural flow
4. Matching the tone guidelines exactly

Return ONLY the rewritten email, no explanations.
""")

# Review Agent Prompt
REVIEW_AGENT_PROMPT = ChatPromptTemplate.from_template("""
You are an expert email reviewer. Analyze this email draft and improve it.

Email Draft:
{draft}

Expected Tone: {tone}
Expected Intent: {intent}

Review Criteria:
1. Tone Alignment: Does it match the expected tone?
2. Clarity: Is the message clear and well-structured?
3. Grammar: Are there any grammatical errors?
4. Completeness: Does it cover all necessary points?
5. Professional Quality: Is it polished and professional?

If the email needs improvement, provide an improved version.
If it's already excellent, return it as-is.

Return ONLY the final email draft (improved or original), no explanations.
""")

# Personalization Agent Prompt
PERSONALIZATION_PROMPT = ChatPromptTemplate.from_template("""
You are personalizing an email draft with user-specific information.

Original Draft:
{draft}

User Profile:
- Name: {user_name}
- Title: {user_title}
- Company: {user_company}
- Signature: {signature}
- Writing Style Notes: {style_notes}

CRITICAL INSTRUCTIONS for personalization:
1. Add the signature at the end
2. ONLY use profile fields that have actual values (not empty strings)
3. If Name is provided and not empty, use it in the signature and body where appropriate
4. If Title is provided and not empty, use it where relevant (e.g., "I am [Title]")
5. If Company is provided and not empty, use it where relevant (e.g., "at [Company]")
6. NEVER generate placeholder text like "[Your Name]", "[Your Title]", "[Your Company]", or similar brackets
7. If a field is empty, simply omit that information - do not create placeholders
8. Match the user's preferred writing style
9. Keep the core message intact

Return ONLY the personalized email with NO placeholder brackets.
""")

# Refinement Agent Prompt
REFINEMENT_AGENT_PROMPT = ChatPromptTemplate.from_template("""
You are an expert email refinement specialist. Your task is to polish the final email draft by addressing these specific issues:

Email Draft to Refine:
{draft}

REFINEMENT TASKS:

1. REMOVE DUPLICATE SIGNATURES
   - Check if the signature appears more than once (e.g., "Best regards" or "Sincerely" repeated)
   - Keep ONLY ONE signature block at the end of the email
   - If multiple signatures exist, consolidate into a single closing
   
   Example BEFORE:
   "...looking forward to hearing from you.
   
   Best regards,
   John Doe
   
   Best regards,
   John Doe"
   
   Example AFTER:
   "...looking forward to hearing from you.
   
   Best regards,
   John Doe"

2. FIX GRAMMAR AND SPELLING MISTAKES
   - Correct any grammatical errors (subject-verb agreement, tense consistency, etc.)
   - Fix spelling mistakes
   - Ensure proper capitalization
   - Fix punctuation errors
   
   Example BEFORE:
   "I would like too discuss about the oportunity. Their very interested in you're proposal."
   
   Example AFTER:
   "I would like to discuss the opportunity. They're very interested in your proposal."

3. REMOVE REPETITIVE SENTENCES
   - Identify sentences that convey the same meaning or information
   - Keep the clearest, most concise version
   - Eliminate redundant phrases or ideas
   
   Example BEFORE:
   "I am writing to follow up on my previous email. I wanted to follow up regarding the message I sent earlier. I'm reaching out again about my earlier communication."
   
   Example AFTER:
   "I am writing to follow up on my previous email."

IMPORTANT GUIDELINES:
- Preserve the original tone and intent of the email
- Do NOT change the greeting or recipient name
- Do NOT alter key content, dates, or important details
- Do NOT add new information that wasn't in the original draft
- Only fix the three specific issues listed above
- If no issues are found, return the draft unchanged

Return ONLY the refined email draft, with no explanations, comments, or markdown formatting.
""")

# Fallback Draft Template
FALLBACK_DRAFT_TEMPLATE = """Dear {recipient},

I hope this email finds you well.

{purpose}

{key_points}

I look forward to hearing from you.

Best regards"""
