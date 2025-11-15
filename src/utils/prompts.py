"""
Prompt templates for various agents in the email assistant workflow.
These templates are used by LLM agents to generate structured outputs.
"""

from langchain.prompts import ChatPromptTemplate

# Input Parser Prompt (shared across InputParserAgent)
INPUT_PARSER_PROMPT = ChatPromptTemplate.from_template(
   """
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
   """
)

# Intent Detector Prompt (shared across IntentDetectorAgent)
INTENT_DETECTOR_PROMPT = ChatPromptTemplate.from_template(
   """
   You are an expert at classifying email intents.

   Based on the email purpose and context, classify the intent into ONE of these categories:
   {intents}

   Email Purpose: {email_purpose}
   Key Points: {key_points}
   Context: {context}

   Respond with ONLY the intent category name (e.g., "outreach", "follow_up", etc.).
   No explanation needed. Just the exact category name.
   """
)

# Draft Writer Prompts by Intent
OUTREACH_PROMPT = """Write a professional outreach email with this structure:

1. Personalized opening (reference recipient's work/company if known)
2. Brief self-introduction (generic if not provided)
3. Clear value proposition
4. Specific ask or next step
5. Professional closing

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

IMPORTANT: Do NOT use placeholder brackets like [Your Name], [Company Name], etc. If information is missing, write naturally without placeholders. Personalization occurs later.
TARGET LENGTH: Aim for approximately {target_length} words (do not exceed by >10%).
"""

FOLLOWUP_PROMPT = """Write a follow-up email that:

1. References previous interaction/email
2. Provides context reminder
3. Adds new value or information
4. Includes clear call-to-action
5. Shows respect for their time

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

TARGET LENGTH: About {target_length} words (concise, non-pushy).
"""

THANKYOU_PROMPT = """Write a genuine thank you email that:

1. Opens with sincere gratitude
2. Specifically mentions what you're thanking them for
3. Explains the impact or value
4. Offers reciprocity if appropriate
5. Warm closing

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

TARGET LENGTH: About {target_length} words (warm and authentic).
"""

MEETING_REQUEST_PROMPT = """Write a meeting request email that:

1. Clear subject line suggestion
2. Brief context for the meeting
3. Proposed agenda or topics
4. Specific time options or scheduling link
5. Expected duration

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

TARGET LENGTH: About {target_length} words (organized, respectful).
"""

APOLOGY_PROMPT = """Write a sincere apology email that:

1. Takes clear responsibility
2. Acknowledges the impact
3. Explains what happened (briefly, no excuses)
4. Describes corrective action
5. Asks for another chance

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: empathetic and professional

TARGET LENGTH: About {target_length} words (genuine and concise).
"""

INFORMATION_REQUEST_PROMPT = """Write an information request email that:

1. Polite opening
2. Context for your request
3. Specific questions or information needed
4. Why you're asking them specifically
5. Appreciation for their time

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

IMPORTANT: Do NOT use placeholder brackets. If information is not provided, write naturally.
TARGET LENGTH: About {target_length} words (clear and respectful).
"""

# Additional templates added to support all intents used by DraftWriterAgent
STATUS_UPDATE_PROMPT = """Write a professional status update email that:

1. Clear opening about the update
2. Current status/progress summary
3. Key accomplishments or milestones
4. Next steps or upcoming actions
5. Call to action if needed

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

TARGET LENGTH: About {target_length} words (concise and structured).
"""

INTRODUCTION_PROMPT = """Write a professional introduction email that:

1. Warm, personalized opening
2. Brief background about yourself
3. How you learned about or were referred to the recipient
4. Shared interests or mutual connections
5. Soft ask or invitation to connect

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

TARGET LENGTH: About {target_length} words (genuine and engaging).
"""

NETWORKING_PROMPT = """Write a professional networking email that:

1. Personalized compliment or reference
2. Why you admire their work
3. What you're doing and shared interests
4. Suggested ways to stay connected
5. Open invitation to coffee/call

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: {tone}

TARGET LENGTH: About {target_length} words (authentic and conversational).
"""

COMPLAINT_PROMPT = """Write a professional complaint email that:

1. Respectful, non-accusatory opening
2. Clear description of the issue
3. Impact or consequences
4. Specific resolution requested
5. Timeline and contact information

Recipient: {recipient}
Purpose: {purpose}
Key Points: {key_points}
Tone: assertive and professional

TARGET LENGTH: About {target_length} words (firm but constructive).
"""

# Tone Stylist Prompt (shared across ToneStylistAgent)
TONE_STYLIST_PROMPT = ChatPromptTemplate.from_template(
   """
   You are an expert at adjusting email tone while preserving the core message.

   Original Draft:
   {draft}

   Target Tone: {tone}
   Target Length: {target_length} words (stay within ±5%)

   Tone Guidelines:
   - Characteristics: {characteristics}
   - Vocabulary: {vocabulary}
   - Structure: {structure}
   - Greeting style: {greeting}
   - Closing style: {closing}

   Rewrite the email to match the target tone perfectly while:
   1. Keeping all key points and information
   2. Keeping total length near the target length (do not exceed by more than ~5%)
   3. Ensuring natural flow
   4. Matching the tone guidelines exactly
   5. Do NOT change the greeting line or the recipient name; preserve them exactly as in the original draft

   Return ONLY the rewritten email, no explanations.
   """
)

# Review Agent Prompt (shared across ReviewAgent)
REVIEW_AGENT_PROMPT = ChatPromptTemplate.from_template(
   """
   You are an expert email reviewer and editor. Analyze this email draft and improve it if needed.

   Email Draft:
   {draft}

   Expected Tone: {tone}
   Expected Intent: {intent}
   Target Length: {target_length} words (stay within ±5%)

   Review Criteria:
   1. Tone Alignment: Does it match the expected tone?
   2. Clarity: Is the message clear and well-structured?
   3. Grammar: Are there any grammatical errors?
   4. Completeness: Does it cover all necessary points?
   5. Professional Quality: Is it polished and professional?
   6. Length: Keep total words near the target length; trim/condense if too long.
   7. Recipient Safety: Do NOT change the greeting line or recipient name.

   If the email needs improvement, provide an improved version within the target length budget.
   If it's already excellent, return it as-is.

   Return ONLY the final email draft (improved or original), no explanations.
   """
)

# Personalization Agent Prompt (shared across PersonalizationAgent)
PERSONALIZATION_PROMPT = ChatPromptTemplate.from_template(
   """
   You are personalizing an email draft with user-specific information.

   Original Draft:
   {draft}

   User Profile:
   - Name: {user_name}
   - Title: {user_title}
   - Company: {user_company}
   - Signature: {signature}
   - Writing Style Notes: {style_notes}

   Target Length: {target_length} words (stay within ±5%)

   CRITICAL INSTRUCTIONS for personalization:
   1. Add the signature at the end
   2. ONLY use profile fields that have actual values (not empty strings)
   3. Use provided Name naturally in the body and signature
   4. Use Title and Company only if non-empty
   5. NEVER generate placeholder text like "[Your Name]" or bracketed tokens
   6. Omit empty fields entirely
   7. Match the user's preferred writing style
   8. Keep the core message intact
   9. Maintain the target length by condensing if necessary; do not significantly exceed it.
   10. Do NOT alter the greeting line or the recipient name; preserve them exactly as in the original draft. Never substitute the recipient with the sender's name.

   Return ONLY the personalized email with NO placeholder brackets.
   """
)

# Refinement Agent Prompt
REFINEMENT_AGENT_PROMPT = ChatPromptTemplate.from_template("""
You are an expert email refinement specialist. Refine the draft strictly according to the ordered tasks below. Do NOT invent new facts.

Email Draft (to refine as needed):
{draft}

ORDERED REFINEMENT TASKS (perform in sequence; skip a task if not needed):

1. DEDUPLICATE CLOSINGS & SIGNATURES
   - Keep only ONE closing/signature block at end (e.g., choose a single final block among: "Best regards", "Regards", "Sincerely", "Thank you", "Warm regards").
   - If multiple appear, retain the first complete one with name/title; remove others.

2. DEDUPLICATE GREETINGS
   - If greeting lines repeat ("Hello Maria," / "Dear Team," etc.), keep the first valid greeting and remove subsequent duplicates.
   - Do NOT alter the recipient name or greeting wording aside from removing duplicates.

3. STRIP PLACEHOLDERS & TEMPLATE TOKENS
   - Remove bracketed or angle/curly placeholder tokens like: [Your Name], [Company], {{Company Name}}, <Insert Value>, (Your Title), {{{{anything}}}}, <<anything>>.
   - Remove obvious ALL-CAPS placeholder phrases of pattern: "YOUR ... HERE" or "INSERT ...".
   - After removal, ensure surrounding punctuation and spacing are clean.

4. UNWRAP NESTED / REDUNDANT BRACKETS
   - Convert [[[text]]], ((text)), {{{{text}}}}, <<text>>, [ [ text ] ], etc. to plain: text.
   - Remove empty bracket pairs entirely ([], {{}}, (), <> alone).

5. CLEAN ORPHANED BRACKETS & EXTRANEOUS PUNCTUATION/SPACES
   - Remove leftover solitary [, ], (, ), {{, }}, <, > that do not enclose content.
   - Collapse multiple consecutive spaces to one.
   - Replace sequences of more than three periods with an ellipsis "…" (single Unicode ellipsis) unless part of a quoted excerpt.

6. MERGE REPETITIVE SENTENCES/CLAIMS
   - If the same idea is repeated, keep the strongest, clearest version; remove the rest.
   - Do NOT remove unique details (dates, metrics, commitments).

7. LIGHT GRAMMAR & SPELLING CORRECTION
   - Fix spelling, agreement, punctuation, capitalization.
   - Preserve tone and intent; do NOT expand content.

8. LENGTH & SAFETY GUARDS
   - Aim to keep overall length within ±5% of original unless placeholder/bracket removal forces greater reduction.
   - Never shorten more than necessary; never lengthen beyond minor grammar adjustments.
   - Do NOT change greeting line or recipient name.
   - Do NOT introduce new facts, promises, dates, links, or attachments.

GENERAL RULES:
- Preserve core meaning and professional tone.
- Maintain any existing scheduling details, numbers, or commitments verbatim.
- If no changes are required, return the draft exactly unchanged.

OUTPUT:
Return ONLY the refined email text. No explanations, no commentary, no markdown.
""")

# Fallback Draft Template
FALLBACK_DRAFT_TEMPLATE = """Dear {recipient},

I hope this email finds you well.

{purpose}

{key_points}

I look forward to hearing from you.

Best regards"""
