# MatchPrism — AI-Proof Analysis

Which persona ideas survive the test: "Can't I just ask ChatGPT to do this?"

---

## The Test

For each persona, ask:
1. **Can an LLM do this already?** If someone can paste their resume + job description into ChatGPT and get the same result, it's not a product.
2. **Does it need proprietary data?** If the value requires data that LLMs don't have (real-time, private, structured, aggregated), there's a moat.
3. **Does it need a persistent system?** If the value comes from tracking state over time, comparing across many options simultaneously, or integrating with external systems, a chatbot can't replicate it.
4. **Is the UI/UX the value?** Some things need a visual interface, not a chat window. Comparison tables, scoring dashboards, swipeable cards.

---

## Verdict Per Persona

### KILLED BY AI (Don't build these)

| # | Persona | Why AI kills it |
|---|---------|----------------|
| 4 | Career Changer Tom | "I'm in marketing, want to move to PM, what skills do I need?" — ChatGPT answers this perfectly already |
| 6 | Online Learner David | "Recommend a Python course for intermediate level" — ChatGPT does this |
| 22 | Developer Dev | "Should I use Next.js or Remix for X?" — ChatGPT's bread and butter |
| 24 | No-Code Builder Omar | "Which no-code tool for a marketplace?" — ChatGPT handles this |
| 29 | Book Club Sophie | "Recommend books like X" — ChatGPT/Goodreads already excellent |
| 30 | Travel Planner Carlos | "Where should I travel in March on $2K budget?" — ChatGPT is great at this |
| 35 | Startup Rachel | "Which accelerator fits my fintech startup?" — ChatGPT can reason through this |
| 36 | Retiree Mark | "Volunteer opportunities for accountants near me" — Google + ChatGPT |
| 37 | Interior Designer Leila | "Mid-century modern furniture recommendations" — Pinterest + ChatGPT |

**Pattern:** Any persona whose problem is "recommend me something based on my description" is already solved by LLMs. The LLM IS the matching engine.

---

### PARTIALLY AI-PROOF (Need something extra to survive)

| # | Persona | What AI can do | What it CAN'T do (your moat) |
|---|---------|---------------|------------------------------|
| 1 | Job Seeker Priya | Analyze one resume vs one job | Scan 10,000 live jobs simultaneously, track application status, auto-apply |
| 5 | College Applicant Ananya | Discuss university fit generally | Access real admission rates, scholarship data, alumni outcome data by program |
| 7 | Parent Sarah | General learning advice | Integrate with school systems, track progress over time, connect to local tutors |
| 11 | Dating Aisha | Discuss compatibility concepts | Persistent profiles, mutual matching, real-time availability — needs a platform |
| 21 | Fitness Riya | Suggest workouts | Track progress, adapt over time, integrate with wearables |
| 25 | Content Creator Zara | Advise on brand fit | Access real brand budgets, campaign data, audience overlap metrics — proprietary data |
| 34 | Language Learner Yuki | Language practice | Real-time matching with available partners — needs a live marketplace |
| 38 | Gamer Diego | Squad advice | Real-time matchmaking across live player pool — needs infrastructure |

**Pattern:** These survive IF you add proprietary data or a live marketplace. The AI handles the matching logic, but it can't access your database or manage two-sided interactions.

---

### AI-PROOF (Build these — LLMs can't replicate)

| # | Persona | Why AI can't kill it | Moat type |
|---|---------|---------------------|-----------|
| **2** | **Hiring Manager Raj** | Needs to score 300 real resumes against a real job spec simultaneously, rank them, track through pipeline. ChatGPT can't access his ATS, can't batch-process, can't persist state. | **Proprietary data + system integration** |
| **9** | **CTO Lisa (team matching)** | Needs to map actual employee skills to actual open roles inside her company. Requires HR system integration, org chart data, performance data LLMs don't have. | **Private enterprise data** |
| **10** | **VC James** | Needs to score 500 real pitch decks against a real investment thesis. Requires deal flow data, portfolio overlap detection, market sizing data. Can't be done in a chat window. | **Proprietary deal flow data + batch processing** |
| **13** | **Apartment Hunter Chen** | Needs real-time listing data (price, availability, location), combined with commute calculations, neighborhood stats, noise data. ChatGPT doesn't have live listings. | **Real-time external data** |
| **16** | **PM Nina (feature-user matching)** | Needs to connect to her product's analytics (Mixpanel/Amplitude), correlate feature usage with retention cohorts. Completely proprietary data. | **Customer's private analytics data** |
| **17** | **Sales Rep Alex** | Needs live CRM data (Salesforce), enrichment data (Clearbit), and company fit scoring against ICP. ChatGPT can't access his pipeline. | **CRM integration + live data** |
| **19** | **Patient Jorge** | Needs real doctor availability, insurance network data, specialty match, patient reviews aggregated. Medical matching needs verified, structured data. | **Regulated data + real-time availability** |
| **20** | **Therapist Dr. Kim** | Needs a structured clinical assessment tool with validated frameworks, client progress tracking, HIPAA-compliant storage. | **Clinical framework + compliance** |
| **23** | **CTO Maria (vendor eval)** | Needs to compare 50 real SaaS vendors against 100 specific requirements, with pricing data, integration compatibility, security compliance scores. | **Structured vendor database + live pricing** |
| **27** | **Pet Adopter Grace** | Needs real-time shelter data: which dogs are actually available right now, their temperament assessments, medical status. | **Real-time shelter integration** |
| **28** | **Matchmaker Raj Sr.** | Needs a two-sided platform with real profiles, verified information, family involvement, and cultural matching dimensions. | **Two-sided marketplace** |
| **33** | **Immigrant Ahmad** | Needs official credential recognition databases, regulatory body requirements by province, real course equivalency data. | **Government/regulatory data** |
| **39** | **Nonprofit Director Ava** | Needs real donor data (giving history, capacity scores, affinity indicators) integrated with CRM. | **Donor CRM integration** |
| **40** | **Car Buyer Tariq** | Needs real-time inventory (what's actually available at dealers near me), real pricing, real insurance estimates, real depreciation curves. | **Live market data** |

---

## The AI-Proof Ranking

Sorted by: (moat strength) × (market size) × (willingness to pay)

| Rank | Persona | Idea | Revenue | AI-Proof Score |
|------|---------|------|---------|----------------|
| **1** | **Raj (#2)** | Candidate-job fit scoring for recruiters | $99-500/seat/mo | 9/10 — needs ATS data |
| **2** | **Maria (#23)** | SaaS vendor evaluation scoring | $500/mo enterprise | 9/10 — needs vendor DB |
| **3** | **Alex (#17)** | Lead-ICP fit scoring for sales | $150/seat/mo | 9/10 — needs CRM data |
| **4** | **Nina (#16)** | Feature-user segment matching | $199/mo | 8/10 — needs analytics data |
| **5** | **James (#10)** | Startup-thesis matching for VCs | $500/mo | 8/10 — needs deal flow |
| **6** | **Tariq (#40)** | Car purchase decision engine | $10/report, high volume | 8/10 — needs live inventory |
| **7** | **Chen (#13)** | Neighborhood-lifestyle matching | $10/search | 8/10 — needs live listings |
| **8** | **Jorge (#19)** | Doctor-patient matching | $20/match | 8/10 — needs medical data |
| **9** | **Lisa (#9)** | Internal team-role optimization | $200/mo | 8/10 — needs HR data |
| **10** | **Ahmad (#33)** | Credential recognition matching | $30/report | 7/10 — needs gov data |

---

## The Insight

**The AI-proof moat is always one of:**
1. **Proprietary/live data** the LLM doesn't have (listings, inventory, CRM, ATS)
2. **System integration** the LLM can't do (connect to Salesforce, ATS, analytics)
3. **Two-sided marketplace** that needs real users on both sides
4. **Batch processing** across hundreds of options simultaneously (not one-at-a-time chat)
5. **Persistent state** that tracks changes over time (pipeline, progress, history)

If your matching logic can be described in a prompt and the data is public, ChatGPT already won. Build where the data is private, live, or needs infrastructure.

---

## Top 3 Recommendations for matchprism.com

### Option A: Recruiter Fit Scoring (Persona #2)
- **What:** Upload a job description → paste/upload resumes → get ranked fit scores with dimensional breakdown
- **Why AI-proof:** Batch processing 300 resumes simultaneously, scoring visualization, ATS integration
- **Revenue:** $99-500/seat/month, proven market
- **Risk:** Crowded space (but most tools are keyword-matching garbage, not real fit scoring)

### Option B: SaaS Vendor Evaluation (Persona #23)
- **What:** Define your requirements → get scored matches against a vendor database
- **Why AI-proof:** Needs structured vendor data (pricing, features, integrations, compliance) that LLMs don't have updated
- **Revenue:** $500/month enterprise
- **Risk:** Hard to build the vendor database initially

### Option C: Car/Product Purchase Decision Engine (Persona #40)
- **What:** Answer 10 questions about your needs → see every option scored and ranked with clear tradeoffs
- **Why AI-proof:** Needs live inventory, real pricing, insurance estimates, depreciation data
- **Revenue:** $10/report (but massive volume potential — everyone buys cars/laptops/phones)
- **Risk:** Data partnerships needed
