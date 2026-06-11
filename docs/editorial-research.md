# Editorial research: making generated articles and pages not feel AI-ish

Research summary (2026-06-11) behind the rules baked into
`.claude/skills/worldcup-article/SKILL.md` and `.claude/skills/article-editor/SKILL.md`.

## Prose rules (evidence-backed)

- Lede ≤ 30 words, one sentence, decisive moment first; nut graf by para 2–3;
  inverted pyramid (CCC Media News & Reporting; Sports Field Guide).
- Unequal paragraph lengths and aggressive sentence-length variance — uniformity
  is a documented AI tell (Gary Provost "write music"; toolsforwriting.com).
- Never end on a summary; end forward-looking (Poynter on endings; Wikipedia:
  Signs of AI writing).
- Vocabulary banlist from peer-reviewed LLM frequency spikes: delve (~67x in
  2024 abstracts), meticulous (34.7x), intricate (11.2x), commendable (9.8x),
  plus showcase, boast, underscore, garner, realm, pivotal, tapestry, testament,
  landscape, foster, elevate, harness, seamless, robust, notably, nestled
  (Juzek & Ward arxiv 2412.11385; Kobak et al. Science Advances; Liang et al.
  ICML 2024).
- No exactly-three-item lists (the most-cited structural tell), ≤1 em dash per
  300 words, no sentence-final "-ing" profundity clauses, no vague attribution
  ("experts say") (Wikipedia Signs of AI writing; Beutler Ink; ContentBeta).
- Sports: every number gets a comparator in-sentence, max 2 stats per point,
  anchor sections in named concrete moments, cliché banlist ("110%", "hopes
  to/looks to" ledes) (Fiveable sports-reporting guides; Sports Field Guide;
  CJR; Rick Reilly's rules).
- Caveat: tells drift by model generation — refresh the banlist quarterly.
  Prompting reduces but does not eliminate tells; the editor pass is required.

## Page-design rules

- Header block: kicker → headline → dek → byline → date → reading time
  (Trust Project indicators; reading-time stat directional only).
- Real identity, no fake personas (NewsGuard's #1 content-farm tell); disclose
  AI assistance (Google helpful-content "How" test). → We use "MatchPrism
  Intelligence Desk · model-written, editor-reviewed" + methodology footnote.
- Body: serif 16–21px, line-height 1.4–1.6, 50–75 char measure (Butterick;
  PMC4612630). Drop cap and pull quotes sparingly, longform only.
- Charts at the exact paragraph discussing them, takeaway titles, one rigid
  theme with "MatchPrism · Source: ..." footer (FiveThirtyEight practice).
- Break template sameness: vary article lengths, featured-lead index layout,
  no stock/AI imagery — own data graphics as art (NewsGuard; AI-slop tells).
- Site trust scaffolding: about/contact/corrections/methodology visible from
  every article (Trust Project; NN/g trustworthiness).

## Automated editor-pass checks (implemented in the article-editor skill)

Hard fails: AI leakage strings ("as an AI", "knowledge cutoff", "oaicite",
stray `**`), banlist hits, "In conclusion/Ultimately" in last two paragraphs,
vague attribution. Metrics: sentence-length stddev < ~6 words → too uniform;
>2 tricolons/1,000 words; >1 em dash/300 words; >1 hedge/250 words; lede and
ending shape checks; every number must exist in source data (kills
hallucinated stats); cross-article cadence (word counts clustering ±10%,
duplicate headline structures).

Full citation list: see the linked sources inline above; primary anchors are
Wikipedia "Signs of AI writing", Juzek & Ward (2024), Kobak et al. (2024),
NewsGuard Newsbots report, Trust Project indicators, NN/g byline and
trustworthiness articles, Poynter, and the FiveThirtyEight visualization
write-ups.
