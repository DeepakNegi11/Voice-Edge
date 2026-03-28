def calculate_scores(
    confidence_class: int,
    confidence_score: float,
    audio_features:   dict,
    text_features:    dict,
) -> dict:

    # ── Clarity Score ──────────────────────────────────────────
    ideal_sent_len = 14
    length_penalty = abs(text_features["avg_sent_length"] - ideal_sent_len) * 2.5
    filler_penalty = text_features["filler_ratio"] * 80
    vocab_bonus    = text_features["unique_word_ratio"] * 20
    clarity = max(0, min(100,
        75 - length_penalty - filler_penalty + vocab_bonus
    ))

    # ── Fluency Score ──────────────────────────────────────────
    wpm = audio_features["speaking_rate"]
    if   wpm < 80:   pace_score = 40
    elif wpm < 120:  pace_score = 65
    elif wpm < 165:  pace_score = 100
    elif wpm < 200:  pace_score = 75
    else:            pace_score = 50

    fluency = max(0, min(100,
        pace_score * 0.55
        + (1 - audio_features["pause_ratio"]) * 35
        + (1 - text_features["filler_ratio"]) * 10
    ))

    # ── Delivery Score (precise) ───────────────────────────────

    # ── A. Voice Expressiveness (0-45 pts) ────────────────────
    # Uses pitch range, movement, dynamism, inflection rate

    # Pitch range: ideal 40-120 Hz spread between p10 and p90
    pitch_range = audio_features.get("pitch_range", 0)
    if   pitch_range < 10:   range_score = 5    # nearly monotone
    elif pitch_range < 30:   range_score = 15   # flat delivery
    elif pitch_range < 60:   range_score = 30   # decent variation
    elif pitch_range < 100:  range_score = 40   # expressive
    else:                    range_score = 30   # slightly over-dramatic

    # Pitch movement: average Hz change between segments
    # Ideal: 8-25 Hz between consecutive segments
    pitch_movement = audio_features.get("pitch_movement", 0)
    if   pitch_movement < 3:   move_score = 5
    elif pitch_movement < 8:   move_score = 10
    elif pitch_movement < 20:  move_score = 20
    elif pitch_movement < 35:  move_score = 15
    else:                      move_score = 8

    # Pitch dynamism: how often pitch changes direction (0-1)
    # Natural speech: 0.4-0.7
    pitch_dynamism = audio_features.get("pitch_dynamism", 0)
    if   pitch_dynamism < 0.2:  dyn_score = 5
    elif pitch_dynamism < 0.4:  dyn_score = 10
    elif pitch_dynamism < 0.7:  dyn_score = 20
    else:                       dyn_score = 15

    # Inflection rate: fraction of frames with noticeable pitch change
    # Ideal: 0.15-0.40
    inflection_rate = audio_features.get("inflection_rate", 0)
    if   inflection_rate < 0.05:  infl_score = 5
    elif inflection_rate < 0.15:  infl_score = 10
    elif inflection_rate < 0.40:  infl_score = 20
    elif inflection_rate < 0.60:  infl_score = 15
    else:                         infl_score = 8

    # Combine — cap at 45
    expressiveness = min(45,
        range_score * 0.35 +
        move_score  * 0.25 +
        dyn_score   * 0.25 +
        infl_score  * 0.15
    )

    # ── B. Energy Dynamics (0-40 pts) ─────────────────────────
    # Uses dynamic range, energy CV, emphasis ratio, entropy

    # Dynamic range: ratio of loudest to quietest segment
    # Ideal: 2.0-5.0x variation
    dynamic_range = audio_features.get("dynamic_range", 1.0)
    if   dynamic_range < 1.2:  dr_score = 5    # completely flat
    elif dynamic_range < 2.0:  dr_score = 15   # low variation
    elif dynamic_range < 4.0:  dr_score = 30   # good variation
    elif dynamic_range < 7.0:  dr_score = 20   # high variation
    else:                      dr_score = 10   # too erratic

    # Energy coefficient of variation: std/mean of segments
    # Ideal: 0.15-0.40
    energy_cv = audio_features.get("energy_cv", 0)
    if   energy_cv < 0.08:   cv_score = 5
    elif energy_cv < 0.15:   cv_score = 15
    elif energy_cv < 0.35:   cv_score = 25
    elif energy_cv < 0.55:   cv_score = 18
    else:                    cv_score = 8

    # Emphasis ratio: fraction of frames above 1.5x mean energy
    # Ideal: 0.10-0.25 (purposeful emphasis moments)
    emphasis_ratio = audio_features.get("emphasis_ratio", 0)
    if   emphasis_ratio < 0.05:   emp_score = 5
    elif emphasis_ratio < 0.10:   emp_score = 15
    elif emphasis_ratio < 0.25:   emp_score = 25
    elif emphasis_ratio < 0.40:   emp_score = 18
    else:                         emp_score = 10

    # Energy entropy: naturalness/unpredictability of energy flow
    # Ideal: 0.85-0.95 (high but not maximum)
    energy_entropy_n = audio_features.get("energy_entropy_n", 0)
    if   energy_entropy_n < 0.60:  ent_score = 8
    elif energy_entropy_n < 0.80:  ent_score = 15
    elif energy_entropy_n < 0.95:  ent_score = 20
    else:                          ent_score = 12

    # Combine — cap at 40
    energy_dynamics = min(40,
        dr_score  * 0.35 +
        cv_score  * 0.25 +
        emp_score * 0.25 +
        ent_score * 0.15
    )

    # ── C. Tone bonus (0-15 pts) ───────────────────────────────
    sentiment  = text_features.get("sentiment", 0)
    tone_score = max(0, min(15, int((sentiment + 1) / 2 * 15)))

    # ── Final Delivery Score ───────────────────────────────────
    delivery = max(0, min(100,
        expressiveness + energy_dynamics + tone_score
    ))

    print(f"   Delivery breakdown → "
          f"expressiveness={expressiveness:.1f} "
          f"energy_dynamics={energy_dynamics:.1f} "
          f"tone={tone_score:.1f} "
          f"total={delivery:.1f}")

    # ── Grammar Score (from text features) ────────────────────
    grammar = text_features.get("grammar_score", 80)

    # ── Relevance Score (from text features) ──────────────────
    relevance = text_features.get("relevance_score", 50)

    # ── Overall Score — now includes grammar + relevance ──────
    overall = round(
        relevance        * 0.22 +
        confidence_score * 0.17 +
        clarity          * 0.20 +
        fluency          * 0.15 +
        delivery          * 0.11 +
        grammar         * 0.15,
        1
    )

    return {
        "confidence":        round(confidence_score, 1),
        "clarity":           round(clarity,           1),
        "fluency":           round(fluency,           1),
        "delivery":          round(delivery,          1),
        "grammar":           round(grammar,           1),
        "relevance":         round(relevance,         1),
        "overall":           overall,
        "confidence_label":  ["Low", "Medium", "High"][confidence_class],
        "wpm":               round(wpm,               1),
    }


def generate_feedback(scores: dict, audio: dict, text: dict) -> list:
    tips = []

    # ── Confidence ─────────────────────────────────────────────
    if scores["confidence"] < 50:
        tips.append("💪 Confidence is low — use stronger words like 'I achieved', 'I built', 'I led'.")
    elif scores["confidence"] < 80:
        tips.append("📈 Good confidence! Reduce hesitation pauses to push your score higher.")
    else:
        tips.append("✅ Strong confidence detected — great assertive tone!")

    # ── Filler words ───────────────────────────────────────────
    if text["filler_count"] > 0:
        found = ", ".join([f"'{w}' ×{c}" for w, c in text["filler_words_found"].items()])
        tips.append(f"🗣️ Filler words detected: {found}. Pause silently instead of using fillers.")

    # ── Speaking pace ──────────────────────────────────────────
    wpm = scores["wpm"]
    if wpm < 90:
        tips.append(f"🚀 You spoke at {wpm} wpm — too slow. Aim for 90-120 wpm.")
    elif wpm > 130:
        tips.append(f"⏱️ You spoke at {wpm} wpm — too fast. Slow down for clarity.")
    else:
        tips.append(f"✅ Great speaking pace at {wpm} wpm — right in the ideal range!")

    # ── Grammar ────────────────────────────────────────────────
    if scores["grammar"] < 60:
        issues = text.get("grammar_issues", [])
        if issues:
            tips.append(f"📝 Grammar issues found: {', '.join(issues[:3])}. Review your sentence structure.")
        else:
            tips.append("📝 Work on your grammar — use complete, well-structured sentences.")
    elif scores["grammar"] < 80:
        tips.append("📝 Grammar is decent — avoid repeating the same words too often.")
    else:
        tips.append("✅ Good grammar and sentence structure throughout your answer!")

    # ── Relevance ──────────────────────────────────────────────
    if scores["relevance"] < 40:
        missing = text.get("missing_keywords", [])
        tips.append(
            f"🎯 Your answer is not very relevant to the question. "
            f"Try to include topics like: {', '.join(missing[:4])}."
        )
    elif scores["relevance"] < 65:
        missing = text.get("missing_keywords", [])
        tips.append(
            f"🎯 Moderate relevance — strengthen your answer by mentioning: "
            f"{', '.join(missing[:3])}."
        )
    else:
        matched = text.get("matched_keywords", [])
        tips.append(
            f"✅ Great relevance! You covered key topics: {', '.join(matched[:4])}."
        )

    # ── Clarity ────────────────────────────────────────────────
    if text["avg_sent_length"] > 25:
        tips.append("✂️ Your sentences are too long — break them into shorter ones.")
    elif text["avg_sent_length"] < 6 and text["word_count"] > 10:
        tips.append("📝 Answers are too brief — add more detail and real examples.")

    # ── Delivery ───────────────────────────────────────────────
    if audio.get("pitch_std", 0) < 10:
        tips.append("🎵 Your voice sounds monotone — vary your pitch to sound more engaging.")

    # ── Pauses ─────────────────────────────────────────────────
    if audio["pause_ratio"] > 0.45:
        tips.append("🤫 Too many pauses — practice your answer to speak more smoothly.")

    # ── Duration ───────────────────────────────────────────────
    if audio["duration"] < 20:
        tips.append("⏳ Answer was under 20 seconds — aim for 60–120 seconds.")
    elif audio["duration"] > 180:
        tips.append("⌛ Answer was over 3 minutes — practice being more concise.")

    # ── Vocabulary ─────────────────────────────────────────────
    if text["unique_word_ratio"] < 0.5:
        tips.append("📚 You repeated many words — try to use more varied vocabulary.")

    # ── Repeated words ─────────────────────────────────────────
    repeated = text.get("repeated_words", {})
    if repeated:
        words_str = ", ".join([f"'{w}' ×{c}" for w, c in list(repeated.items())[:3]])
        tips.append(f"🔁 Overused words: {words_str}. Try using synonyms instead.")

    # ── Overall ────────────────────────────────────────────────
    if scores["overall"] >= 75:
        tips.append("🌟 Excellent overall performance — you're well prepared!")
    elif scores["overall"] >= 60:
        tips.append("👍 Solid performance — work on the tips above to improve further.")
    else:
        tips.append("📚 Keep practicing — focus on relevance, grammar, and confidence.")

    return tips