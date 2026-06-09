# Test Content for Peer Graders

This file gives you enough career material to run the full app without writing anything yourself.
The fictional candidate is **Alex Rivera**, a senior/lead data engineer with ~10 years of experience.

You will use this content in two ways:
1. **Resume** — paste into `clio seed` when it asks for source material (choose "existing letter/bio/resume")
2. **Cover letter paragraphs** — paste one or several at a time into `clio seed` as prose source material
3. **Job description** — paste into `clio build --jd` when prompted

You can lightly edit names, details, or phrasing to make it feel more like your own.

---

## FAKE RESUME — Alex Rivera

**Alex Rivera**
alex.rivera@email.com | github.com/alexrivera | Brooklyn, NY

**Senior Data Engineer** with 10 years of experience building production data infrastructure in Python and SQL. Specializes in subscription analytics, event-driven pipelines, and data models where the business rules are complex and the output has to be trusted. Proven track record owning end-to-end pipelines at companies ranging from seed-stage startups to mid-size media companies.

---

### Meridian Streaming — Senior Data Engineer (2020–present)

- Owned the subscriber analytics data model serving finance, product, and executive reporting
- Redesigned subscriber history as a Type 2 slowly changing dimension when recovery logic and premium tier launch made current-state tracking insufficient for reconciliation
- Built and maintained Airflow DAGs for nightly subscriber snapshot pipeline processing 4M+ records
- Defined churn, recovery, and reactivation business rules in dbt; these definitions were adopted org-wide
- Led data model review process for two junior engineers; introduced PR review standards for SQL
- Diagnosed and resolved a vendor-side double-count bug that was causing churn to be overcounted by 14%; fix required coordinating with the vendor's engineering team and reprocessing 8 months of history
- Built event ingestion pipeline for play/pause/seek/heartbeat events from three device platforms into Redshift; pipeline processes ~200M events per day

### CommonGround Institute — Data Engineer (2017–2020)

- First dedicated data engineer at a worker advocacy nonprofit with 60 staff and programs in 12 states
- Built the organization's first data warehouse from scratch in PostgreSQL on AWS RDS
- Modeled worker survey data, campaign contact history, and outcome tracking for program staff and funders
- Designed and maintained ETL pipelines integrating Salesforce, Qualtrics, and flat-file state agency exports
- Wrote the organization's first data dictionary and trained program staff in 4 regional offices on reporting tools
- Worked directly with the research director to define outcome metrics for a federal grant report; the definitions were later cited in the organization's policy brief

### Fieldwork Analytics — Junior Data Engineer (2015–2017)

- First data engineer hire at a seed-stage civic tech startup building a canvassing app for down-ballot campaigns
- Parsed, modeled, and served voter files, shapefiles, and GPS data so field organizers could use maps and routing in real time
- Built the data-serving layer for the live application almost entirely from scratch in Python and PostgreSQL
- If the data was wrong, the product was wrong: the voter universe, the turf boundaries, and the organizer's trust in the tool all depended on the accuracy of the underlying data
- Worked from a TypeScript backend codebase, wrote RFCs, and improved Python code quality under guidance from the engineering lead

---

## COVER LETTER PARAGRAPHS

Paste any of these into `clio seed`. They are written as prose paragraphs the way a cover letter or bio would read. Each one is long enough to extract 2-3 claims.

---

### Paragraph 1 — Subscriber analytics ownership (Meridian)

At Meridian Streaming I owned the subscriber analytics data model end to end. Every metric finance used for revenue forecasting, every number product reviewed in weekly standups, and every figure in the board deck came from models I built and maintained. When the product team launched a premium tier and introduced recovery logic, subscription status, plan type, recovery state, and effective dates all became more complex than the existing model could handle. The right fix was not to patch the current-state model but to redesign it as an effective-dated subscriber history, essentially a Type 2 slowly changing dimension, so that each version of a subscriber record was preserved with start and end dates. That made it possible to reconcile churn, recovery, and month-end subscriber counts against the exact customer state that was valid for each reporting period. The tradeoff was added complexity in the model and joins, because the reporting logic had to select the correct subscriber version for each date. The benefit was that discrepancies became explainable: I could trace every count back to the customer statuses, state changes, effective dates, and business rules that produced it. Before that redesign, unexplained discrepancies between finance and product numbers required hours of manual reconciliation. After it, the answer was always in the model.

---

### Paragraph 2 — Vendor bug and data integrity (Meridian)

The most consequential data integrity problem I solved at Meridian was a vendor-side double-count bug that was causing churn to be overcounted by 14 percent across all reporting. I caught it while doing a routine reconciliation check between our subscriber snapshot and a vendor export, noticed the discrepancy was consistent across multiple months, and traced it to a race condition in the vendor's event processing that was creating duplicate cancellation records. The fix required me to reproduce the issue in our data, write a detailed technical spec for the vendor's engineering team, coordinate the fix across two engineering orgs, and reprocess eight months of subscriber history once the vendor confirmed the root cause. Finance had been using the overcounted churn figures for quarterly planning. I documented the corrected numbers, walked the finance team through what had changed and why, and updated the data dictionary to note the corrected methodology. I take data integrity seriously enough to follow a discrepancy all the way to another company's codebase if that is what it takes.

---

### Paragraph 3 — First data engineer, CommonGround

At CommonGround I was the first dedicated data engineer in the organization's history, which meant I had to figure out what the organization actually needed before I could build anything. There was no data warehouse, no ETL infrastructure, no documentation of where data lived or what it meant. Program staff were running campaigns across 12 states and tracking outcomes in Salesforce, Qualtrics, and a dozen state-specific flat-file exports, none of which talked to each other. I built the organization's first data warehouse in PostgreSQL on AWS RDS, designed the data model for worker survey data and campaign contact history, and wrote the first data dictionary the organization had ever had. I trained program staff in four regional offices on the reporting tools I built. When the research director needed to define outcome metrics for a federal grant report, I worked directly with her to make sure the definitions were precise enough to be cited in policy work. The metrics I defined with her were later included in a published policy brief. I did not go to CommonGround to maintain an existing system. I went because the work was not done yet.

---

### Paragraph 4 — Event pipeline at Meridian

The event ingestion pipeline I built at Meridian processes roughly 200 million play, pause, seek, and heartbeat events per day from three device platforms into Redshift. The engineering challenge was that each platform had a different event schema and a different delivery reliability profile: web events arrived in near real time, mobile events batched and sometimes arrived out of order, and connected TV events had a 6-to-12-hour delivery lag. I built a normalization layer that reconciled events across platforms into a single canonical schema, handled deduplication, and flagged late-arriving events for downstream consumers to handle appropriately. The content analytics team, the recommendation team, and the product team all built on top of that pipeline. When the recommendation team needed engagement signals broken down by content type and device class, I did not rebuild the pipeline; I extended the schema. Designing for extensibility from the start meant that adding a new signal was a schema change and a backfill, not a rewrite.

---

### Paragraph 5 — Defining business rules (Meridian)

Defining what churn means sounds like a business question, but at Meridian it was an engineering problem. When I joined, finance, product, and marketing each had a different definition of churn, each one implemented in a different place in the codebase, each one producing different numbers. I led a cross-functional working session to get finance, product, and the VP of analytics in the same room. I prepared a technical brief explaining where each definition differed and what the implications were for trend reporting. We agreed on a single set of definitions covering churn, reactivation, and recovery, and I implemented them in dbt as a single source of truth that all downstream reporting pulled from. After that, I owned those definitions. If a new business rule change had downstream reporting implications, the conversation came to me before the change went into production. I had never been given that kind of authority over a business definition before, and I treated it as an accountability, not a perk.

---

### Paragraph 6 — Fieldwork Analytics, first role

I am proud of the backend data work I shipped at Fieldwork Analytics because it was my first data engineering role, at a seed-stage startup, as the first data engineer. Fieldwork was building a data-driven canvassing app for down-ballot campaigns, and my work powered the live application used to run campaigns. I parsed, modeled, and served voter files, shapefiles, and GPS data so organizers could use maps and field workflows in real time. If that data was wrong, the product was wrong: the voter universe, the turf boundaries, the field workflow, and the organizer's trust in the tool. I worked from a TypeScript backend codebase, wrote RFCs, improved the quality of my Python code, and helped build the data-serving layer the product needed almost entirely from scratch. The app shipped and ran in real campaigns. That was my standard from the beginning: production means something is actually running.

---

### Paragraph 7 — Mentorship and code review (Meridian)

When two junior data engineers joined Meridian in 2022, I became the person they came to with questions, which meant I had to decide what kind of senior engineer I wanted to be. I introduced a PR review process for SQL and dbt model changes that had not existed before. I wrote the first internal style guide for data model naming conventions and documentation standards. I ran a weekly review of new dbt models where we would walk through the logic together before anything went to production. One of the junior engineers told me six months in that the review sessions had changed how she thought about writing SQL. I took that seriously. Technical mentorship works when the person you are mentoring starts making decisions differently, not just when they produce cleaner code.

---

### Paragraph 8 — Why this kind of work

I have spent my career building data infrastructure in places where the output of the data has real stakes. At Fieldwork the stakes were whether organizers could trust the turf they were walking. At CommonGround the stakes were whether program staff could report accurately on outcomes that affected federal funding. At Meridian the stakes were whether finance could build a revenue plan on numbers that were actually correct. I am not drawn to data engineering as a craft abstracted from what the data is for. I care about building infrastructure that makes it possible for the people who depend on it to make good decisions and trust the numbers they are looking at. That is what has kept me in this work.

---

## SAMPLE JOB DESCRIPTION

Paste this when `clio build --jd` asks for the job description.  
You are also welcome to find a jd online and copy it for this purpose.

---

**Senior Data Engineer — Greenfield Analytics**

Greenfield Analytics is building data infrastructure to help regional health systems understand population health trends and care gaps. We are a team of 30, Series B, and our data platform powers clinical dashboards used by care coordinators and administrators across 8 hospital systems.

**What you will do:**
- Own and extend our core data pipelines in Python and Airflow, including our patient census and encounter history models
- Design and maintain dbt models that serve clinical reporting and product analytics
- Define and document business rules for key clinical metrics in collaboration with clinical informatics staff
- Build event-driven pipelines for real-time care coordination signals
- Mentor 1-2 junior engineers on the data team

**What we are looking for:**
- 7+ years of data engineering experience
- Strong Python and SQL; experience with dbt, Airflow, and a cloud data warehouse (we use Snowflake)
- Experience owning data models in complex business-rule environments where precision matters
- Ability to work cross-functionally with non-technical stakeholders to define and implement data definitions
- Experience in healthcare, public sector, or another high-stakes domain is a plus but not required
- Someone who cares about what the data is actually used for, not just whether the pipeline runs

**Nice to have:**
- Experience with HL7/FHIR or claims data
- Experience with slowly changing dimensions or temporal data modeling
- Technical writing: data dictionaries, runbooks, style guides
