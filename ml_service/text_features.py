import re
import language_tool_python

# ── Initialize LanguageTool once (expensive to reload) ────────
print("⏳ Loading LanguageTool grammar checker...")
try:
    _tool = language_tool_python.LanguageTool("en-US")
    print("✅ LanguageTool loaded successfully!")
except Exception as e:
    print(f"⚠️ LanguageTool failed to load: {e}")
    _tool = None

# ── Filler words ───────────────────────────────────────────────
FILLER_WORDS = [
    "um", "uh", "like", "you know", "basically", "literally",
    "actually", "so", "right", "okay", "hmm", "er", "ah",
]

# ── Sentiment word lists ───────────────────────────────────────
POSITIVE_WORDS = [
    "achieved", "built", "created", "designed", "developed", "excellent",
    "experienced", "improved", "led", "managed", "motivated", "passionate",
    "skilled", "strong", "successful", "accomplished", "delivered",
    "implemented", "optimized", "solved", "collaborated", "innovative",
    "responsible", "initiative", "leadership", "teamwork", "communication",
    "dedicated", "focused", "results", "impact", "growth",
]

NEGATIVE_WORDS = [
    "bad", "difficult", "failed", "issue", "mistake", "nervous",
    "problem", "struggled", "unable", "uncertain", "unsure", "weak",
    "confused", "worried", "hard", "challenging", "never", "nothing",
    "difficulty", "trouble", "stress", "pressure", "overwhelmed",
    "hesitant", "doubt", "doubtful", "fear", "anxious", "panic"

]

# ── Question keyword bank ──────────────────────────────────────
QUESTION_KEYWORDS = {
    "tell_me_about_yourself": [
        "experience", "background","skill", "skills", "education", "work",
        "passion", "career", "study", "project","projects", "developed", "built",
        "university", "degree", "internship", "professional",

        "introduction", "overview", "academic",
        "qualification", "expertise", "knowledge", "training",
        "learning", "practical", "hands-on", "exposure",
        "specialization", "interest", "domain", "field",
        "achievements", "accomplishments", "pursuing", "tech"
    ],

    "greatest_strength": [
        "strength", "good", "best", "skilled", "excel", "ability",
        "capable", "strong", "proud", "achieved", "leadership",
        "communication", "problem", "solving", "analytical",

        # added
        "expert", "proficient", "talent", "competency", "efficiency",
        "productivity", "adaptability", "flexibility", "creativity",
        "innovation", "critical thinking", "decision making",
        "confidence", "self-motivated", "hardworking", "dedicated",
        "organized", "reliable", "strengths"
    ],

    "greatest_weakness": [
        "weakness", "improve", "working on", "learning", "challenge",
        "overcome", "growth", "developing", "better", "feedback",
        "mistake", "area", "focus",

        # added
        "limitation", "drawback", "shortcoming", "flaw", "issue",
        "struggle", "difficulty", "gap", "enhance", "progress",
        "self-improvement", "refine", "upgrade", "build",
        "correct", "adapt", "change", "improving"
    ],

    "why_this_role": [
        "interested", "excited", "company", "role", "opportunity",
        "contribute", "grow", "align", "passion", "mission", "value",
        "experience", "skills", "match", "perfect",

        # added
        "fit", "suitable", "motivation", "inspired", "enthusiastic",
        "career goals", "objectives", "organization", "culture",
        "vision", "purpose", "interest in", "preference",
        "long-term", "commitment", "alignment", "aspiration"
    ],

    "where_five_years": [
        "future", "goal", "vision", "lead", "grow", "senior", "manager",
        "develop", "expertise", "contribute", "advance", "career",
        "responsibility", "impact", "aspire",

        # added
        "long-term", "plan", "ambition", "progress", "promotion",
        "leadership role", "specialist", "mastery", "improvement",
        "professional growth", "career path", "direction",
        "objective", "milestone", "achievement", "success"
    ],

    "challenging_situation": [
        "challenge", "problem", "difficult", "situation", "solved",
        "overcome", "team", "deadline", "pressure", "result", "learned",
        "approach", "action", "outcome", "success",

        # added
        "issue", "obstacle", "barrier", "complex", "tough",
        "critical", "crisis", "handling", "managed", "resolved",
        "strategy", "process", "effort", "achievement",
        "experience", "lesson", "failure", "improvement"
    ],

    "teamwork_example": [
        "team", "collaborated", "together", "group", "helped",
        "supported", "communicated", "role", "contributed", "achieved",
        "conflict", "resolved", "cooperated", "shared", "goal",

        # added
        "coordination", "partnership", "interaction", "discussion",
        "teamwork", "unity", "cooperation", "participation",
        "involvement", "engagement", "assist", "guidance",
        "lead", "managed", "relationship", "bond", "synergy"
    ],

    "why_should_hire": [
        "skills", "experience", "contribute", "value", "unique",
        "bring", "offer", "benefit", "qualified", "passionate",
        "dedicated", "results", "proven", "track", "record",

        # added
        "capabilities", "strengths", "expertise", "knowledge",
        "efficiency", "performance", "impact", "advantage",
        "fit", "suitability", "commitment", "reliability",
        "consistency", "achievement", "success", "potential",
        "growth", "contribution"
    ],
}

# ── Grammar categories to ignore (not relevant for speech) ────
IGNORE_RULES = {
    "WHITESPACE_RULE",
    "COMMA_PARENTHESIS_WHITESPACE",
    "EN_QUOTES",
    "UPPERCASE_SENTENCE_START",  # speech often lacks capitals
    "DASH_RULE",
}

def check_grammar(transcript: str) -> dict:
    """
    Use LanguageTool to check grammar.
    Returns score 0-100 and list of specific issues found.
    """
    if not _tool or not transcript.strip():
        return {
            "grammar_score":        80,
            "grammar_issues":       [],
            "grammar_issue_count":  0,
            "repeated_words":       {},
            "incomplete_sentences": 0,
        }

    try:
        # ── Run LanguageTool ───────────────────────────────────
        matches = _tool.check(transcript)

        # Filter out rules irrelevant to spoken speech
        relevant_matches = [
            m for m in matches
            if m.ruleId not in IGNORE_RULES
        ]

        # Build list of human-readable issues
        issues = []
        seen   = set()
        for m in relevant_matches:
            # Deduplicate same rule appearing multiple times
            if m.ruleId not in seen:
                seen.add(m.ruleId)
                # Get the actual text that has an issue
                bad_text = transcript[m.offset: m.offset + m.errorLength]
                suggestion = m.replacements[0] if m.replacements else "no suggestion"
                issues.append({
                    "message":    m.message,
                    "bad_text":   bad_text,
                    "suggestion": suggestion,
                    "rule_id":    m.ruleId,
                    "category":   m.category,
                })

        # ── Repeated words ─────────────────────────────────────
        words     = transcript.lower().split()
        word_freq = {}
        for w in words:
            if len(w) > 4:
                word_freq[w] = word_freq.get(w, 0) + 1
        repeated = {w: c for w, c in word_freq.items() if c > 3}

        # ── Incomplete sentences ───────────────────────────────
        sentences  = [s.strip() for s in re.split(r"[.!?]+", transcript) if s.strip()]
        incomplete = sum(1 for s in sentences if len(s.split()) < 3)

        # ── Calculate grammar score ────────────────────────────
        # Start at 100, deduct based on issues found
        total_issues  = len(relevant_matches)
        word_count    = max(len(words), 1)

        # Normalize by length — more words = more chances for errors
        error_rate    = total_issues / (word_count / 10)
        grammar_score = max(0, min(100,
            100
            - (error_rate   * 15)    # deduct per error per 10 words
            - (incomplete   *  5)    # deduct per incomplete sentence
            - (len(repeated)*  3)    # deduct per overused word
        ))

        print(f"   LanguageTool found {total_issues} issues "
              f"({len(relevant_matches)} relevant) → score: {grammar_score:.1f}")

        return {
            "grammar_score":        round(grammar_score, 1),
            "grammar_issues":       issues[:8],   # top 8 issues max
            "grammar_issue_count":  total_issues,
            "repeated_words":       repeated,
            "incomplete_sentences": incomplete,
        }

    except Exception as e:
        print(f"⚠️ LanguageTool check failed: {e}")
        return {
            "grammar_score":        75,
            "grammar_issues":       [],
            "grammar_issue_count":  0,
            "repeated_words":       {},
            "incomplete_sentences": 0,
        }


def check_relevance(transcript: str, question_id: str) -> dict:
    """Check how relevant the answer is to the specific question."""
    if not transcript or question_id not in QUESTION_KEYWORDS:
        return {
            "relevance_score":  0,
            "matched_keywords": [],
            "missing_keywords": [],
            "keyword_coverage": 0.0,
        }

    expected = QUESTION_KEYWORDS[question_id]
    text_low = transcript.lower()
    matched  = [kw for kw in expected if kw in text_low]
    missing  = [kw for kw in expected if kw not in text_low]
    coverage = len(matched) / 12

    words        = transcript.split()
    length_bonus = min(len(words) / 100, 1.0) * 15
    relevance    = min(100, coverage * 85 + length_bonus)

    return {
        "relevance_score":  round(relevance,  1),
        "matched_keywords": matched,
        "missing_keywords": missing[:5],
        "keyword_coverage": round(coverage,   3),
    }


def analyze_text(transcript: str,
                 question_id: str = "tell_me_about_yourself") -> dict:

    if not transcript or not transcript.strip():
        return {
            "word_count":           0,
            "sentence_count":       0,
            "filler_count":         0,
            "filler_ratio":         0.0,
            "avg_sent_length":      0.0,
            "sentiment":            0.0,
            "pos_word_count":       0,
            "neg_word_count":       0,
            "unique_word_ratio":    0.0,
            "filler_words_found":   {},
            "grammar_score":        0,
            "grammar_issues":       [],
            "grammar_issue_count":  0,
            "repeated_words":       {},
            "incomplete_sentences": 0,
            "relevance_score":      0,
            "matched_keywords":     [],
            "missing_keywords":     [],
            "keyword_coverage":     0.0,
        }

    # ── Basic text features ────────────────────────────────────
    words           = transcript.lower().split()
    word_count      = len(words)
    sentences       = [s.strip() for s in re.split(r"[.!?]+", transcript) if s.strip()]
    sent_count      = max(len(sentences), 1)
    avg_sent_length = word_count / sent_count

    # ── Filler words ───────────────────────────────────────────
    filler_count  = 0
    found_fillers = {}
    for fw in FILLER_WORDS:
        matches = re.findall(r"\b" + re.escape(fw) + r"\b", transcript.lower())
        if matches:
            filler_count     += len(matches)
            found_fillers[fw] = len(matches)
    filler_ratio = filler_count / max(word_count, 1)

    # ── Sentiment ──────────────────────────────────────────────
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    total     = pos_count + neg_count
    sentiment = (pos_count - neg_count) / total if total > 0 else 0.0

    # ── Vocabulary richness ────────────────────────────────────
    unique_word_ratio = len(set(words)) / max(word_count, 1)

    # ── Grammar (LanguageTool) ─────────────────────────────────
    print("📖 Running LanguageTool grammar check...")
    grammar = check_grammar(transcript)

    # ── Relevance ──────────────────────────────────────────────
    print(f"🎯 Checking relevance for question: {question_id}")
    relevance = check_relevance(transcript, question_id)

    return {
        "word_count":           word_count,
        "sentence_count":       sent_count,
        "filler_count":         filler_count,
        "filler_ratio":         round(filler_ratio,      3),
        "avg_sent_length":      round(avg_sent_length,   1),
        "sentiment":            round(sentiment,          3),
        "pos_word_count":       pos_count,
        "neg_word_count":       neg_count,
        "unique_word_ratio":    round(unique_word_ratio, 3),
        "filler_words_found":   found_fillers,
        "grammar_score":        grammar["grammar_score"],
        "grammar_issues":       grammar["grammar_issues"],
        "grammar_issue_count":  grammar["grammar_issue_count"],
        "repeated_words":       grammar["repeated_words"],
        "incomplete_sentences": grammar["incomplete_sentences"],
        "relevance_score":      relevance["relevance_score"],
        "matched_keywords":     relevance["matched_keywords"],
        "missing_keywords":     relevance["missing_keywords"],
        "keyword_coverage":     relevance["keyword_coverage"],
    }