# Extraction Review — 2026-05-31
Model: claude-haiku-4-5-20251001
Judge alignment: 92%
114 paragraph(s)

Open the Streamlit app to review and insert:
  uv run streamlit run coverletter/label_evals.py

---

## General / Opening
*hash: f13ae3ddabfa...*  

**Paragraph:**
> I have worked across disparate datasets in multiple domains, each with its own rules,
> stakeholders, and regulatory environment.

### Claim 1  [REJECTED] ❌ (Pure capability statement with no specific evidence — asserts breadth of experience but names no employers, domains, or concrete work that could substantiate it.)
> I have worked across disparate datasets in multiple domains, each with its own rules, stakeholders, and regulatory environment


---

## General / Through-Line
*hash: deca170c8105...*  

**Paragraph:**
> Across every domain I have worked in -- labor organizing, streaming media, electoral data,
> civic tech -- the same pattern has appeared: organizations are making decisions with worse
> data than they could have, and the gap between what they are seeing and what they could see
> is almost always an engineering problem. I know metrics. I know how they break down, where
> the business rules are hidden in the logic, and what it takes to produce a number someone
> can act on without second-guessing it. I think in workflows, systems, and interfaces, and
> the work I find most satisfying is translating a fuzzy stakeholder need into a data model
> that answers it cleanly, then building the infrastructure that keeps answering it correctly
> for as long as someone depends on it.

### Claim 1  [PENDING] ✅
> I am most excited by work where the gap between what an organization sees and what it could see is an engineering problem — translating a fuzzy stakeholder need into a data model that answers it cleanly, then building infrastructure that keeps answering it correctly

- Across labor organizing, streaming media, electoral data, and civic tech, organizations are making decisions with worse data than they could have
- I know metrics — how they break down, where the business rules are hidden in the logic, and what it takes to produce a number someone can act on without second-guessing it

### Claim 2  [PENDING] ✅
> I think in workflows, systems, and interfaces — translating fuzzy needs into clean data models is how I approach the work

- The work I find most satisfying is taking a stakeholder need and building the infrastructure that keeps answering it correctly for as long as someone depends on it

**Conclusion:** This is someone who sees data engineering as a tool for organizational accountability — not as a technical exercise, but as a way to close the gap between what people know and what they could know. The pattern across domains suggests this person has learned to recognize when a business problem is actually a data problem, and has developed a method for solving it.

---

## General / Through-Line
*hash: f46696fb75df...*  

**Paragraph:**
> One thing that distinguishes me as an engineer is that I am both deeply thoughtful about
> non-technical users and stakeholders, and serious about building solid, well-typed, tested
> Python. I spent many years caring for data on the frontlines of large campaigns, where data
> had to have precision and certainty, and I did extremely well with what would be considered
> an overwhelming amount of accountability for the numbers I delivered; this intensive experience of
> responsibility around data integrity is especially rare for data and backend engineers and it has 
> informed my abilities and focus in data governance.

### Claim 1  [PENDING] ✅
> I build solid, well-typed, tested Python while staying thoughtful about non-technical stakeholders

- consistent approach to engineering that balances technical rigor with stakeholder communication

### Claim 2  [PENDING] ✅
> I spent years caring for data on the frontlines of large campaigns, where data had to have precision and certainty

- worked in high-stakes environments where data accuracy was non-negotiable

### Claim 3  [PENDING] ✅
> I had accountability for data integrity at a level that is rare for data and backend engineers

- carried an overwhelming amount of accountability for the numbers I delivered
  - this intensive experience of responsibility around data integrity is especially rare for data and backend engineers

### Claim 4  [PENDING] ✅
> My experience with high-stakes data responsibility has shaped how I approach data governance

- intensive experience of responsibility around data integrity has informed my abilities and focus in data governance

**Conclusion:** Years of accountability for data precision in high-stakes campaign work created a rare combination for a data engineer: both the technical discipline to build well-tested systems and the stakeholder awareness to make governance meaningful to non-technical users.

---

## General / Through-Line
*hash: 64e4db848df3...*  

**Paragraph:**
> For the last fourteen years, I have often worked in environments where I was one of very
> few people, and sometimes the only person, responsible for my job function. I have had to
> work through ambiguity, limited direction, and high expectations without waiting for someone
> else to define the path. I have always been a problem solver, an enthusiastic project
> manager, and a self-starter. My best abilities come from curiosity and creativity around
> systems design, workflow efficiency, and intricate but well-structured data models.

### Claim 1  [PENDING] ✅
> For fourteen years, I have often been the only person responsible for my job function, working through ambiguity and high expectations without waiting for someone else to define the path

- Worked in environments with very few or no peers in the same role
  - Had to work through ambiguity and limited direction
  - Operated under high expectations without external definition of the path

### Claim 2  [PENDING] ✅
> I work as a problem solver and self-starter who figures things out without waiting for direction

- Consistent pattern across fourteen years of solo or near-solo responsibility

### Claim 3  [PENDING] ✅
> My best abilities come from curiosity and creativity around systems design, workflow efficiency, and intricate but well-structured data models

- Core strengths in systems thinking and data architecture
  - Drawn to systems design problems
  - Focused on workflow efficiency
  - Skilled at building intricate but well-structured data models

### Claim 4  [REJECTED] ❌ (Pure self-description with no specific evidence; asserts a quality without describing what was actually owned, decided, or how the person consistently worked)
> I am an enthusiastic project manager

- Self-identified as enthusiastic about project management work

---

## General / Through-Line
*hash: dfd1f15adac2...*  

**Paragraph:**
> Working backwards from what someone needs to understand into the data model that produces
> it is the hardest part of this work and the part most often skipped. At UNITE HERE,
> gathering requirements from local staff who had been doing their jobs for decades meant
> understanding their processes well enough to translate them into data structures before
> writing a line of code. At BritBox, the watch-duration work started with no specification:
> I had to determine what "watch duration" meant at the subscriber grain, what constituted a
> valid session, and how cross-midnight plays should be handled -- before the engineering
> could begin. In both cases the technical decisions were downstream of the requirements
> decisions. The pipelines that have caused the most downstream trust problems, at every
> place I have worked, were the ones where the requirements phase was skipped. Across all of them, I have been consistently
> surprised by how much room there is for data quality to be substantially better. Building
> systems that produce trustworthy, well-governed data at the right level of detail requires
> sustained, careful engineering work that organizations routinely underinvest in. I think in
> workflows, systems, and interfaces -- what the data needs to do, who needs to use it, what
> they need to see, and what stands between the raw source and a number someone can act on.
> The work I find most satisfying is closing that gap: figuring out what the data should say,
> building the infrastructure that makes it say that reliably, and making sure the people who
> depend on it can actually trust it.

### Claim 1  [PENDING] ✅
> I work backwards from what someone needs to understand into the data model that produces it

- At UNITE HERE, gathering requirements from local staff who had been doing their jobs for decades meant understanding their processes well enough to translate them into data structures before writing a line of code
- At BritBox, the watch-duration work started with no specification: I had to determine what 'watch duration' meant at the subscriber grain, what constituted a valid session, and how cross-midnight plays should be handled -- before the engineering could begin
  - In both cases the technical decisions were downstream of the requirements decisions

### Claim 2  [PENDING] ✅
> The pipelines that have caused the most downstream trust problems, at every place I have worked, were the ones where the requirements phase was skipped

- Across all of them, I have been consistently surprised by how much room there is for data quality to be substantially better

### Claim 3  [PENDING] ✅
> I think in workflows, systems, and interfaces -- what the data needs to do, who needs to use it, what they need to see, and what stands between the raw source and a number someone can act on

- Building systems that produce trustworthy, well-governed data at the right level of detail requires sustained, careful engineering work that organizations routinely underinvest in

### Claim 4  [PENDING] ✅
> The work I find most satisfying is closing that gap: figuring out what the data should say, building the infrastructure that makes it say that reliably, and making sure the people who depend on it can actually trust it

- Working backwards from what someone needs to understand into the data model that produces it is the hardest part of this work and the part most often skipped

**Conclusion:** This is data where the requirements phase determines whether downstream systems can be trusted — getting to trustworthy output requires understanding what the source actually records and what the consumer actually needs before any engineering begins.

---

## General / Through-Line
*hash: deeba64ba38b...*  

**Paragraph:**
> Across every domain I have worked in — labor organizing, streaming media, electoral data,
> civic tech — I have been released into ambiguous contexts and expected to find the
> problems, define them, and build end-to-end solutions while keeping stakeholders oriented
> to what I am doing and why. The same underlying conditions keep appearing: bad data,
> poorly structured tooling, and organizations that have been sold on what technology can do
> without being told what it requires. My first real boss taught me that honesty and
> directness build trust and cut through wasted effort, and I applied that to technical work
> in a way most of my technical peers did not. When I surface a constraint or a failure mode
> before anyone asked, I am doing two things at once: giving visibility to a decision point
> that exists whether or not anyone names it, and creating shared ownership of the more
> precise problem space. What happens next depends on the risk — sometimes more time is
> afforded to work around it, sometimes a plan is built to address it before it becomes
> inevitable, sometimes the stakeholder accepts it. All three of those are better outcomes
> than an emergency no one saw coming, and across every environment I have worked in, the
> people depending on the work have known they would get that clarity from me before they
> had to ask for it.

### Claim 1  [PENDING] ✅
> Across labor organizing, streaming media, electoral data, and civic tech, I have been released into ambiguous contexts and expected to find the problems, define them, and build end-to-end solutions while keeping stakeholders oriented to what I am doing and why

- Pattern of working across multiple domains with poorly structured initial conditions
  - labor organizing, streaming media, electoral data, civic tech
  - ambiguous contexts requiring problem definition before solution building
  - end-to-end ownership across technical and stakeholder communication
- Recurring structural problems across all these environments
  - bad data
  - poorly structured tooling
  - organizations sold on what technology can do without being told what it requires

### Claim 2  [PENDING] ✅
> I surface constraints and failure modes proactively, giving visibility to decision points that exist whether or not anyone names them, and creating shared ownership of the more precise problem space

- Approach to constraint visibility creates three better outcomes than emergency discovery
  - sometimes more time is afforded to work around it
  - sometimes a plan is built to address it before it becomes inevitable
  - sometimes the stakeholder accepts it
  - all three are better outcomes than an emergency no one saw coming
- Stakeholders across every environment have known they would get clarity before having to ask for it
  - this clarity is expected and relied upon, not a surprise

### Claim 3  [PENDING] ✅
> I apply honesty and directness to technical work in a way most of my technical peers do not

- First real boss taught that honesty and directness build trust and cut through wasted effort
  - this principle was applied to technical work specifically
  - distinguishes approach from how most technical peers work

### Claim 4  [PENDING] ✅
> When I surface a constraint or failure mode, I am doing two things at once: giving visibility to a decision point and creating shared ownership of the more precise problem space

- Proactive constraint surfacing reframes problem definition as collaborative
  - decision points exist whether or not anyone names them
  - naming them creates shared ownership rather than individual accountability
  - shifts from 'you missed something' to 'here is what we are actually deciding'

**Conclusion:** This is data where instrumentation is imperfect and the schema is controlled by a third party — getting to trustworthy output requires understanding what the source is actually recording before you model anything. Across every environment, the underlying work is the same: find the real problem, make the constraints visible, and build solutions that stakeholders understand and trust because they were part of naming what needed to be solved.

---

## General / Through-Line
*hash: 4033c9ecf387...*  

**Paragraph:**
> Every environment I have worked in has handed me the same problem in a different form:
> something complicated, something stuck, something where the path is not obvious and
> someone has to stay with it. The domains changed — digital arts, teaching, nonprofit
> consulting, labor data, production engineering — and the orientation did not. What people
> have consistently brought me into is the conversation before the build: the one where you
> work out what the problem is, what the data can and cannot do, and what the solution
> requires. In that conversation I am listening, asking follow-up questions that follow the
> shape of the thing I am already building in my head, pulling in the right people — a
> vendor, a data owner, a stakeholder whose requirements no one else has collected yet — and
> sorting out what is baseline from what is nice-to-have when the people asking have not
> necessarily talked to each other. I have been doing that since I was walking students
> through project conception to production and presentation end to end, and since I was
> getting multi-faceted art projects off the ground by holding the whole thing in my head at
> once. When the SSRS queries were too complex, when the joins across decades of membership
> data did not map cleanly to calculations that had to be exact, I got handed whatever
> stopped the person next to me, and I did not put it down until it worked.

### Claim 1  [PENDING] ✅
> I get brought into conversations before the build — where you work out what the problem is, what the data can and cannot do, and what the solution requires

- In that conversation I am listening, asking follow-up questions that follow the shape of the thing I am already building in my head, pulling in the right people — a vendor, a data owner, a stakeholder whose requirements no one else has collected yet
- I sort out what is baseline from what is nice-to-have when the people asking have not necessarily talked to each other

### Claim 2  [PENDING] ✅
> I have been doing this work — holding the whole thing in my head at once, staying with complicated problems until they work — across every domain I have worked in

*Contexts: employer: digital arts, employer: teaching, employer: nonprofit consulting, employer: labor data, employer: production engineering*

- Since I was walking students through project conception to production and presentation end to end
- Since I was getting multi-faceted art projects off the ground by holding the whole thing in my head at once

### Claim 3  [PENDING] ✅
> When the technical problem is hard — when SSRS queries are too complex, when joins across decades of membership data do not map cleanly to calculations that have to be exact — I get handed whatever stopped the person next to me, and I do not put it down until it worked

- SSRS queries that were too complex
- Joins across decades of membership data that did not map cleanly to calculations that had to be exact

### Claim 4  [PENDING] ✅
> My orientation is to stay with complicated, stuck problems where the path is not obvious — the domains changed but the orientation did not

- Every environment I have worked in has handed me the same problem in a different form: something complicated, something stuck, something where the path is not obvious and someone has to stay with it
  - The domains changed — digital arts, teaching, nonprofit consulting, labor data, production engineering — and the orientation did not

**Conclusion:** This is someone who is brought in to clarify what is actually being asked before anyone builds anything — who can hold a complex problem in their head, pull in the right people and information, and stay with it until it works, regardless of domain.

---

## Data Engineer / BritBox Subscriber Reporting
*hash: c89544e7b9b6...*  

**Paragraph:**
> The monthly subscriber reporting at BritBox went directly to the CTO and CEO

### Claim 1  [REJECTED] ❌ (Describes what a system did, not what the person owned, decided, or is characterized by — this is a support item, not a claim about the person.)
> At BritBox, the monthly subscriber reporting went directly to the CTO and CEO

*Contexts: employer: BritBox*

- monthly subscriber reporting was a direct executive deliverable

---

## Data Engineer / BritBox Subscriber Reporting
*hash: bb1f6ae37d2c...*  

**Paragraph:**
> Subscriber reporting at BritBox didn't come with a stable data model -- it came with
> failures that had to be found, diagnosed, and fixed each time they appeared. The Evergent
> system served only current-state data, which made accurate churn and subscriber counts
> dependent on monthly snapshots and vendor-side processing I couldn't fully inspect. When
> new billing recovery logic caused Evergent to double-count churn, I identified the pattern,
> documented the root cause for the vendor, and validated the fix before the numbers went back
> up. When new subscription tiers broke the model again -- subscription ID lineages where
> inactive records were current and active records were future, no anomaly detection built in
> -- I rebuilt the logic overnight with the Finance lead to hit the monthly close. The CFO,
> CTO, and CEO read those numbers the next morning. for meetings
> about the direction of the business. Getting those numbers wrong was not an option. The
> underlying problem was structural: Evergent served only current-state data to our warehouse,
> meaning subscriber records reflected the latest state rather than their history, which made
> accurate churn and subscriber count calculations dependent on monthly snapshots and
> vendor-side logic we could not fully control or validate. Two product-level decisions made
> this harder in sequence. First, new recovery logic in billing caused the Evergent system to
> count churn more than once for the same records, so our churn numbers were massively
> overcounted and subscriber counts were no longer reconciling against billing. I had to
> analyze the problem, make a recommendation to the vendor, get it fixed, and do QA to confirm
> it was resolved. Then when BritBox introduced new subscription tiers, the logic broke again
> -- the data model allowed long lineages of subscription IDs under a single customer ID, with
> subscriptions marked inactive that were actually current and future subscriptions marked
> active, and none of the new anomalies had been worked out ahead of time. I worked closely
> with the US reporting lead in Finance each month to ensure the numbers were correct before
> they went up, and sometimes that meant working until midnight to get new logic validated in
> time. Those numbers went to the CFO, CTO, and CEO and shaped how the company understood its
> own health and trajectory.

### Claim 1  [PENDING] ✅
> At BritBox, I owned subscriber reporting where the data model was unstable and failures had to be found, diagnosed, and fixed each time they appeared

*Contexts: employer: BritBox*

- Subscriber reporting came with no stable data model — it came with failures that had to be found, diagnosed, and fixed each time they appeared
- The Evergent system served only current-state data, which made accurate churn and subscriber counts dependent on monthly snapshots and vendor-side processing I couldn't fully inspect
  - Evergent served only current-state data to our warehouse, meaning subscriber records reflected the latest state rather than their history
  - This made accurate churn and subscriber count calculations dependent on monthly snapshots and vendor-side logic we could not fully control or validate

### Claim 2  [PENDING] ✅
> At BritBox, I identified and validated the fix when new billing recovery logic caused Evergent to double-count churn

*Contexts: employer: BritBox*

- When new recovery logic in billing caused the Evergent system to count churn more than once for the same records, I identified the pattern, documented the root cause for the vendor, and validated the fix
  - New recovery logic in billing caused Evergent to count churn more than once for the same records
  - This made our churn numbers massively overcounted and subscriber counts were no longer reconciling against billing
  - I had to analyze the problem, make a recommendation to the vendor, get it fixed, and do QA to confirm it was resolved

### Claim 3  [PENDING] ✅
> At BritBox, I rebuilt subscriber reporting logic overnight with the Finance lead when new subscription tiers broke the model, to hit the monthly close before the CFO, CTO, and CEO read those numbers

*Contexts: employer: BritBox*

- When BritBox introduced new subscription tiers, the logic broke again — subscription ID lineages where inactive records were current and active records were future, with no anomaly detection built in
  - The data model allowed long lineages of subscription IDs under a single customer ID
  - Subscriptions were marked inactive that were actually current and future subscriptions marked active
  - None of the new anomalies had been worked out ahead of time
- I worked closely with the US reporting lead in Finance each month to ensure the numbers were correct before they went up, and sometimes that meant working until midnight to get new logic validated in time
- Those numbers went to the CFO, CTO, and CEO and shaped how the company understood its own health and trajectory
  - Getting those numbers wrong was not an option

### Claim 4  [PENDING] ✅
> I had accountability for subscriber data accuracy at a level where the numbers I produced directly informed executive decisions about business direction

*Contexts: employer: BritBox*

- The CFO, CTO, and CEO read those numbers the next morning for meetings about the direction of the business
  - Getting those numbers wrong was not an option

**Conclusion:** This is data where the source system is controlled by a vendor and serves only current state, not history — getting to trustworthy output requires understanding what the system is actually recording, catching failures as they emerge, and validating fixes before numbers go to executives who depend on them to understand the business.

---

## Data Engineer / BritBox Watch-Duration Pipeline
*hash: 509694985734...*  

**Paragraph:**
> At BritBox, where I was the sole dedicated data engineer for nearly two years, I owned the
> company's most consequential data asset: a daily Spark pipeline processing over a billion
> playback events to produce the subscriber-level watch metrics that the business ran on. The
> project came to me as a four-month-old stub -- a column selection with no session logic, no
> enrichments, and no stitching -- handed off from a data scientist who had been told only to
> "work on it." I had four months and one hard deadline.

### Claim 1  [PENDING] ✅
> At BritBox, I owned the company's most consequential data asset: a daily Spark pipeline processing over a billion playback events to produce the subscriber-level watch metrics that the business ran on

*Contexts: employer: BritBox*

- sole dedicated data engineer for nearly two years
- pipeline processed over a billion playback events daily
- produced subscriber-level watch metrics that the business ran on

### Claim 2  [PENDING] ✅
> At BritBox, I inherited a four-month-old stub with no session logic, no enrichments, and no stitching, and had to rebuild it to production standard in four months against a hard deadline

*Contexts: employer: BritBox*

- project came as a column selection with no session logic, no enrichments, and no stitching
  - handed off from a data scientist who had been told only to 'work on it'
- had four months and one hard deadline to deliver

---

## Data Engineer / BritBox Watch-Duration Pipeline
*hash: 07288609b83f...*  

**Paragraph:**
> At BritBox I was the only dedicated data engineer for nearly two years, which meant full
> ownership wasn't a title -- it was the operating reality. The clearest example: I delivered
> the company's subscriber-level watch-duration pipeline, processing over a billion daily playback
> events, in four months from a cold start. The handoff I received was a partial column selection
> with no session logic and no enrichments. Correctness was mine to define: I designed the
> subscriber-level metric grain, built the cross-midnight session-stitching logic, created a
> cross-grain reconciliation framework to validate against the old customer-level output, and
> self-directed the Spark optimization for billion-row scale. The vendor it replaced failed
> regularly. Mine hasn't gone down once.

### Claim 1  [PENDING] ✅
> At BritBox, I owned the subscriber-level watch-duration pipeline end-to-end — from metric definition through production reliability at billion-event scale

*Contexts: employer: BritBox*

- Delivered the pipeline in four months from a cold start, processing over a billion daily playback events
  - Handoff was a partial column selection with no session logic and no enrichments
- Designed the subscriber-level metric grain and determined what correctness meant before building
- Built cross-midnight session-stitching logic to stitch sessions across day boundaries
- Created a cross-grain reconciliation framework to validate the new pipeline against the old customer-level output
- Self-directed Spark optimization for billion-row scale
- Pipeline has never gone down in production; the vendor it replaced failed regularly

### Claim 2  [PENDING] ✅
> As the only dedicated data engineer for nearly two years, I had full ownership not as a title but as the operating reality

*Contexts: employer: BritBox*

- Sole data engineer responsible for all data infrastructure and pipeline decisions

**Conclusion:** This is data where the schema is controlled by a third party (playback events), instrumentation is imperfect, and sessions cross system boundaries — getting to trustworthy output requires understanding what the source is actually recording, designing the right grain, and building validation that proves correctness before you can trust the metric.

---

## Data Engineer / BritBox Watch-Duration Pipeline
*hash: 121881f3562e...*  

**Paragraph:**
> What made it genuinely difficult wasn't the scale, though the scale was real. It was that
> correctness was undefined when I started. The prior vendor solution ran as a black box on their
> infrastructure, failed regularly, and modeled at the customer level. I was building at subscriber
> grain -- a different metric definition entirely -- which meant I couldn't just diff my output
> against theirs. I had to reconstruct a customer-level view from my subscriber-level output,
> join it back to the subscribers table, and tie out across a metric set I had defined myself.
> I also had to engineer the midnight session-boundary stitching from first principles: session
> IDs reset at midnight, so events had to be joined across date partitions to calculate watch
> duration correctly. And I had to teach myself the Spark optimization -- partitioning strategy,
> multi-CTE joins at billion-row scale -- while building under deadline.

### Claim 1  [PENDING] ✅
> I had to define correctness from first principles when the prior vendor solution was a black box that failed regularly and modeled at a different grain than what I was building

- The prior vendor solution ran as a black box on their infrastructure, failed regularly, and modeled at the customer level
- I was building at subscriber grain — a different metric definition entirely — which meant I couldn't just diff my output against theirs
- I had to reconstruct a customer-level view from my subscriber-level output, join it back to the subscribers table, and tie out across a metric set I had defined myself
  - This was the validation mechanism when direct comparison to the prior system was impossible

### Claim 2  [PENDING] ✅
> I engineered midnight session-boundary stitching from first principles to handle the fact that session IDs reset at midnight

- Session IDs reset at midnight, so events had to be joined across date partitions to calculate watch duration correctly
  - This required joining events across date partition boundaries, not within a single partition

### Claim 3  [PENDING] ✅
> I taught myself Spark optimization — partitioning strategy and multi-CTE joins at billion-row scale — while building under deadline

- Had to optimize for billion-row scale using partitioning strategy and multi-CTE joins
  - Learning and implementation happened concurrently with deadline pressure

### Claim 4  [PENDING] ✅
> What made the work genuinely difficult wasn't the scale itself, but that correctness was undefined when I started

- Scale was real but secondary to the problem of undefined correctness
  - The constraint was not computational but definitional — no ground truth existed to validate against

**Conclusion:** This is data where the prior system's failure and different grain meant I couldn't rely on existing output as validation — I had to build the entire correctness framework myself, including metric definition, cross-grain reconciliation, and handling of infrastructure constraints like session-boundary resets across partitions.

---

## Data Engineer / BritBox Watch-Duration Pipeline
*hash: cfb9261c361c...*  

**Paragraph:**
> The replacement has been 100% stable since go-live. The vendor's version failed regularly.
> That delta is the work.

### Claim 1  [PENDING] ✅
> I built a replacement that has been 100% stable since go-live, where the vendor's version failed regularly

- The replacement has been 100% stable since go-live
- The vendor's version failed regularly

**Conclusion:** The stability delta between the replacement and the vendor solution is the measure of the work.

---

## Data Engineer / BritBox Watch-Duration Pipeline
*hash: c984d6554666...*  

**Paragraph:**
> The watch-duration metrics I built at BritBox were what the company used to understand
> subscriber behavior -- which content was holding viewers, how engagement broke down by
> subscription tier, what watch patterns looked like across the catalog. A billion playback
> events came in daily, and the subscriber-level output drove decisions about content spend
> and catalog direction. The vendor pipeline I replaced failed regularly and modeled at the
> customer level, a coarser signal that also could not be trusted. My replacement built at
> subscriber grain, with proper session stitching and cross-grain reconciliation validation,
> has had no failures since go-live. For the first time, the viewership numbers were granular
> enough to be actionable and reliable enough to be trusted.

### Claim 1  [PENDING] ✅
> At BritBox, I owned the watch-duration metrics that the company used to understand subscriber behavior and make content spend and catalog decisions

*Contexts: employer: BritBox*

- The metrics showed which content was holding viewers, how engagement broke down by subscription tier, and what watch patterns looked like across the catalog
- A billion playback events came in daily, and the subscriber-level output drove decisions about content spend and catalog direction

### Claim 2  [PENDING] ✅
> At BritBox, I replaced a vendor pipeline that failed regularly and modeled at the customer level with a pipeline built at subscriber grain

*Contexts: employer: BritBox*

- The vendor pipeline failed regularly and modeled at the customer level, a coarser signal that could not be trusted
- My replacement built at subscriber grain with proper session stitching and cross-grain reconciliation validation
  - The new pipeline has had no failures since go-live

### Claim 3  [PENDING] ✅
> I built viewership metrics granular enough to be actionable and reliable enough to be trusted

*Contexts: employer: BritBox*

- For the first time, the viewership numbers were granular enough to be actionable and reliable enough to be trusted

**Conclusion:** This is data where the grain of aggregation and the reliability of the pipeline directly determine whether the output can drive real business decisions — getting both right required understanding what the source events actually represented and building validation that proved the output was trustworthy.

---

## Data Engineer / BritBox Watch-Duration Pipeline
*hash: 3bb78ee358b7...*  

**Paragraph:**
> The watch-duration work at BritBox required me to reconstruct the scope before I could build
> anything. The handoff was a partial column selection with no session logic, no enrichment
> specification, and no definition of what "watch duration" meant at the subscriber level -- just
> an instruction to "work on it." I did the requirements work myself: what grain should the
> metrics be calculated at, what constitutes a valid session boundary, how cross-midnight plays
> should be handled, and what the reconciliation target should be since no gold standard existed
> to validate against. I built the specification as I built the system -- architectural decisions
> and business logic decisions made simultaneously, alone, in four months. The final pipeline
> reconciles cleanly against the customer-level output the business had been using, which
> required me to define a customer-level rollup from my subscriber-grain output as the validation
> layer. I translated an ill-defined ask into a data model, a technical architecture, and a
> working pipeline.

### Claim 1  [PENDING] ✅
> At BritBox, I owned the watch-duration pipeline end-to-end and determined what 'watch duration' meant at the subscriber level before any engineering began

*Contexts: employer: BritBox*

- The handoff was a partial column selection with no session logic, no enrichment specification, and no definition of what 'watch duration' meant at the subscriber level
- I did the requirements work myself: what grain should the metrics be calculated at, what constitutes a valid session boundary, how cross-midnight plays should be handled, and what the reconciliation target should be since no gold standard existed to validate against
  - no gold standard existed to validate against — I had to define the reconciliation target myself
- I built the specification as I built the system — architectural decisions and business logic decisions made simultaneously, alone, in four months

### Claim 2  [PENDING] ✅
> I work backwards from what the business needs to understand into the data model and validation layer that produces it

- I translated an ill-defined ask into a data model, a technical architecture, and a working pipeline
- The final pipeline reconciles cleanly against the customer-level output the business had been using, which required me to define a customer-level rollup from my subscriber-grain output as the validation layer
  - I had to work backwards from the business's existing customer-level output to determine what subscriber-grain logic would reconcile against it

### Claim 3  [PENDING] ✅
> I had accountability for metric definition and data integrity at a level that is rare — I owned both the business logic and the technical architecture with no existing standard to defer to

*Contexts: employer: BritBox*

- I did the requirements work myself with no gold standard existed to validate against
  - no existing validation target meant I had to define what correctness meant before I could build
- I built the specification as I built the system — architectural decisions and business logic decisions made simultaneously, alone, in four months

**Conclusion:** This is work where the business need is real but the specification is incomplete — getting to a trustworthy output requires reconstructing the scope, defining the grain and boundaries, and building the validation layer simultaneously with the pipeline itself.

---

## Data Engineer / CBA Clock
*hash: 0219c003bf47...*  

**Paragraph:**
> CBA Clock is built around a specific understanding of how collective bargaining works:
> leverage is information, and most unions go into negotiations without it. A union that can
> trace each clause through successive contract cycles -- seeing what language was proposed and
> rejected, what concessions were made and under what conditions -- walks into bargaining with
> a categorically different kind of knowledge than one reading a static PDF. The application
> converts collective bargaining agreements into queryable, clause-level records so that
> language evolution can be tracked across negotiations, violations can be documented against
> the specific provisions they breach, and concessions made under temporary conditions can be
> flagged for recovery in the next round. The work I did at UNITE HERE on grievance tracking
> and contract enforcement made clear that the unions with the best outcomes were the ones who
> understood their contracts with the most precision. I built this to be the tool that makes
> that precision accessible.

### Claim 1  [PENDING] ✅
> I built CBA Clock to make contract precision accessible to unions by converting collective bargaining agreements into queryable, clause-level records

*Contexts: project: CBA Clock*

- The application enables unions to trace each clause through successive contract cycles, seeing what language was proposed and rejected, what concessions were made and under what conditions
- The tool allows language evolution to be tracked across negotiations, violations to be documented against specific provisions they breach, and concessions made under temporary conditions to be flagged for recovery in the next round

### Claim 2  [PENDING] ✅
> I understand that leverage in collective bargaining is information, and most unions go into negotiations without it

*Contexts: project: CBA Clock*

- A union that can trace each clause through successive contract cycles walks into bargaining with a categorically different kind of knowledge than one reading a static PDF

### Claim 3  [PENDING] ✅
> At UNITE HERE, my work on grievance tracking and contract enforcement showed me that the unions with the best outcomes were the ones who understood their contracts with the most precision

*Contexts: employer: UNITE HERE*

- This observation directly motivated building CBA Clock as a tool to make that precision accessible

**Conclusion:** This is work where the technical architecture — queryable clause-level records, language evolution tracking, violation documentation — IS the domain work. You cannot separate the engineering decisions from the labor organizing decisions. The precision that matters to unions is only possible through careful data modeling and access patterns.

---

## Data Engineer / CBA Clock
*hash: 2e161a41a785...*  

**Paragraph:**
> A union that understands how its contract has evolved across successive negotiations walks
> into bargaining with a categorically different kind of knowledge. CBA Clock tracks
> concessions across contract cycles: when a union gives ground on a provision under temporary
> conditions, the system flags it for recovery in the next round. When a company has
> repeatedly violated a clause, the documented history of those violations becomes the legal
> argument. When a proposal was rejected because the timing was wrong, the record exists to
> revisit it when conditions shift. Most unions go into negotiations with static PDFs and
> institutional memory that depends on who is still in the room. CBA Clock is built to give
> them structured, clause-level evidence instead -- traceable to the exact contract language,
> across every version of every agreement they have negotiated.

### Claim 1  [PENDING] ✅
> I built CBA Clock to give unions structured, clause-level evidence of how their contracts have evolved across negotiation cycles, traceable to exact contract language across every version of every agreement

*Contexts: project: CBA Clock*

- The system tracks concessions across contract cycles and flags provisions where a union gave ground under temporary conditions for recovery in the next round
- It maintains documented history of company violations of clauses, turning that record into legal argument material
- It preserves rejected proposals with context about why timing was wrong, so the record exists to revisit when conditions shift
- It replaces the static PDF + institutional memory model that most unions rely on with structured, traceable evidence
  - Most unions go into negotiations with static PDFs and institutional memory that depends on who is still in the room

### Claim 2  [PENDING] ✅
> I understand that a union walking into bargaining with knowledge of how its contract has evolved across successive negotiations has categorically different power than one relying on static documents and whoever remembers what

- When a union gives ground on a provision under temporary conditions, that concession needs to be flagged for recovery in the next round — but only if the history is structured and retrievable
- When a company has repeatedly violated a clause, the documented history of those violations becomes the legal argument — but only if it's organized by clause and traceable to exact language
- When a proposal was rejected because timing was wrong, the record needs to exist to revisit it when conditions shift — but static PDFs and memory don't preserve that context

**Conclusion:** This is work where the technical structure IS the organizing principle — how you store and retrieve contract history determines whether a union can actually use that history as leverage. The system exists because the problem is real and the stakes are material.

---

## Data Engineer / CBA Clock
*hash: fb00f1db11b0...*  

**Paragraph:**
> Unions can lose ground over successive contract negotiations without realizing it, because
> tracking how specific language has changed across years of bargaining is difficult and
> time-consuming. Many older contracts exist only as low-quality scans that standard OCR
> cannot reliably parse, and the current practice of printing contracts and comparing them
> manually is exactly the kind of work that structured data and AI-assisted extraction can
> transform. CBA Clock converts collective bargaining agreements into queryable, clause-level
> records so that researchers and union staff can analyze how provisions have evolved, prepare
> for negotiations with a full history of what has been proposed and rejected, enforce working
> contracts, and build documented cases against companies violating the agreement. Because this
> data supports legal and strategic decisions, every extracted record requires manual human
> review before it enters the system. I built the application around verified data as a hard
> requirement -- hallucinated or unverified data cannot exist in the final state, because the
> cost of acting on wrong information in this context is too high.

*No claims extracted.*

---

## Data Engineer / UNITE HERE
*hash: 3cd228e333b6...*  

**Paragraph:**
> At UNITE HERE, I worked across a broader technical scope than my title suggested because
> the organization was doing an enormous amount of technical work with very few technical
> people. Together with one colleague, I was a product owner on the Broadstripes organizing
> application -- cutting tickets, prioritizing work, running sprint planning, and designing
> features. I worked closely on a full build-out of a custom reporting engine within that
> application and unlocked features that enabled organizing directors to do advanced tracking
> they could not do before. What we learned from that build informed a new organizing
> application built on top of IMIS, a CMS customized so extensively that the build-versus-buy
> decision was genuinely difficult, and we were product owners on that build as well. I also
> worked closely with the long-tenured membership team, which put me in a position few people
> outside leadership occupied -- working across both sides of the application. Collecting
> accurate workflow requirements from local staff required working seriously and intentionally
> with people who had been doing their jobs for decades, and occasionally with staff who were
> openly resistant to the international or to technology adoption. Getting that right anyway
> mattered, because what I documented became the foundation for the software those locals had
> to use every day. I interviewed locals to gather requirements for tickets on both the
> organizing and membership software, ran data for organizing campaigns across many years,
> built tracking frameworks for them, and came to understand the friction points organizers
> face around data entry in the field. The Canadian locals I covered operated under different
> labor law than the US locals, and I was entrusted to perform the desk audit of the Canadian
> local with the most complicated dues structure in the international union, documenting and
> replicating its full financial process including fees and contributions that split across
> multiple general ledger accounts.

*No claims extracted.*

---

## Data Engineer / UNITE HERE
*hash: a1ae5a136cc0...*  

**Paragraph:**
> At UNITE HERE, the organizing data I built and maintained was the infrastructure campaigns
> ran on. For a national SkyChefs campaign spanning multiple airports, I designed the tracking
> model and trained the lead researcher on how to run it. Organizing tracking is not simple --
> each worker moves through multiple stages: contact, follow-up conversations, commitment,
> meeting attendance, and confirmation. Because this campaign used an online vote, the tracking
> also had to capture whether each person had access to a device, whether they had confirmed
> they would vote, and whether they actually had. That data was what told organizers across
> every location who still needed follow-up and where the remaining field time should go. I also
> ran card checks directly and knew their rules at a detailed level, because those rules
> determine whether the organizing counts at all.

### Claim 1  [PENDING] ✅
> At UNITE HERE, I built and maintained the organizing data infrastructure that campaigns ran on

*Contexts: employer: UNITE HERE*

- For a national SkyChefs campaign spanning multiple airports, I designed the tracking model and trained the lead researcher on how to run it

### Claim 2  [PENDING] ✅
> I designed a tracking model that captured the full worker journey through organizing stages and vote access/confirmation, which determined where organizers across every location should direct remaining field time

*Contexts: employer: UNITE HERE*

- The model tracked each worker through multiple stages: contact, follow-up conversations, commitment, meeting attendance, and confirmation
- Because the campaign used an online vote, the tracking also had to capture whether each person had access to a device, whether they had confirmed they would vote, and whether they actually had
  - This data was what told organizers across every location who still needed follow-up and where the remaining field time should go

### Claim 3  [PENDING] ✅
> I ran card checks directly and knew their rules at a detailed level, because those rules determine whether the organizing counts at all

*Contexts: employer: UNITE HERE*

- Card check rules determine whether the organizing counts at all

### Claim 4  [PENDING] ✅
> I understand that organizing tracking is not simple — it requires capturing worker progression through multiple decision and action stages, and the data model has to reflect what actually determines campaign success

- Each worker moves through multiple stages: contact, follow-up conversations, commitment, meeting attendance, and confirmation
  - For campaigns using online votes, the model must also capture device access, vote confirmation, and actual vote completion

**Conclusion:** This is data where the schema directly reflects the rules that determine whether organizing work counts — getting the model right requires understanding not just what happened, but what the organizing rules say matters.

---

## Data Engineer / UNITE HERE Financial Complexity
*hash: ec304407a98f...*  

**Paragraph:**
> The Canadian local I was assigned at UNITE HERE had the most complicated dues structure of
> any local in the entire international union: different dues rates, fees, funds, and
> contributions that split across multiple general ledger accounts, with financial processes
> that had evolved over years of local practice. UNITE HERE entrusted me with the full desk
> audit of that local -- sole responsibility to document and replicate the complete financial
> workflow, account for every fee type, and produce a model the international could work from.
> I also had to figure out metrics from scratch, repeatedly, across many locals operating
> under different labor law and different dues structures, and document them precisely enough
> that the work could survive staff turnover. Unions are heavily regulated and their financial
> processes carry direct legal obligations. Getting the numbers wrong is not a data quality
> issue -- it affects workers' dues standing, benefits eligibility, and the union's ability to
> enforce contract terms.

### Claim 1  [PENDING] ✅
> At UNITE HERE, I owned the complete financial workflow audit of the Canadian local with the most complicated dues structure in the entire international union — sole responsibility to document and replicate every fee type, account split, and process that had evolved over years of practice

*Contexts: employer: UNITE HERE*

- The Canadian local had different dues rates, fees, funds, and contributions that split across multiple general ledger accounts
  - financial processes had evolved over years of local practice
  - this was the most complicated dues structure of any local in the entire international union
- UNITE HERE entrusted me with full desk audit responsibility to produce a model the international could work from

### Claim 2  [PENDING] ✅
> I figured out metrics from scratch, repeatedly, across many locals operating under different labor law and different dues structures, and documented them precisely enough that the work could survive staff turnover

*Contexts: employer: UNITE HERE*

- Had to determine metrics across locals with different legal and structural contexts
  - each local operated under different labor law
  - each local had different dues structures
  - documentation had to be precise enough to survive staff turnover

### Claim 3  [PENDING] ✅
> I had accountability for financial data where getting the numbers wrong is not a data quality issue — it affects workers' dues standing, benefits eligibility, and the union's ability to enforce contract terms

*Contexts: employer: UNITE HERE*

- Unions are heavily regulated and their financial processes carry direct legal obligations
  - incorrect numbers affect workers' dues standing
  - incorrect numbers affect benefits eligibility
  - incorrect numbers affect the union's ability to enforce contract terms

**Conclusion:** This is financial data where the stakes are not operational convenience but workers' legal standing and union enforceability — precision and accountability are not optional, and the complexity comes from real legal and organizational constraints, not poor design.

---

## Data Engineer / Sensitive Data and Compliance
*hash: db7317260629...*  

**Paragraph:**
> Few data environments demand the combination of legal precision, sensitivity, and
> technical rigor that union data does, and I spent years inside it. At UNITE HERE I was
> part of the team that built and debugged a secure file ingestion portal processing
> employer-submitted worker rosters in every format employers could throw at us: CSVs, tab-
> delimited files, txt files, and PDFs so degraded they had to be run through secondary
> tools or rebuilt manually before a single record could be trusted. Those records included
> social security numbers and financial data for dues processing, and I wrote the migration
> scripts and reporting solutions that sat on top of them. I also supported organizing
> campaigns so sensitive the data could not be discussed openly, operated under code names,
> and required hard calls about permanent deletion: contact information and scheduling data
> came in through pictures taken in the field, I translated them into structured records,
> and anything that could be traced back to a source disappeared entirely. I worked those
> retention decisions out directly with campaign leadership, balancing data utility against
> real human risk. On the contract enforcement side, I worked closely with grievance
> officers navigating CBA-specific legal rules, where grievances could run for years across
> multiple contract versions at the same property and the documentation had to hold up to
> the procedural standards that kept a grievance alive.

### Claim 1  [PENDING] ✅
> I spent years inside union data environments where legal precision, sensitivity, and technical rigor are non-negotiable

*Contexts: employer: UNITE HERE*

- Built and debugged a secure file ingestion portal processing employer-submitted worker rosters in every format employers could throw at us
  - CSVs, tab-delimited files, txt files, and PDFs so degraded they had to be run through secondary tools or rebuilt manually before a single record could be trusted
  - Records included social security numbers and financial data for dues processing
- Wrote migration scripts and reporting solutions that sat on top of sensitive worker data
- Supported organizing campaigns so sensitive the data could not be discussed openly, operated under code names, and required hard calls about permanent deletion
  - Contact information and scheduling data came in through pictures taken in the field
  - Translated them into structured records
  - Anything that could be traced back to a source disappeared entirely
- Worked retention decisions out directly with campaign leadership, balancing data utility against real human risk

### Claim 2  [PENDING] ✅
> I work closely with domain experts navigating complex procedural and legal requirements, translating their constraints into data architecture decisions

*Contexts: employer: UNITE HERE*

- Worked closely with grievance officers navigating CBA-specific legal rules where grievances could run for years across multiple contract versions at the same property
  - Documentation had to hold up to the procedural standards that kept a grievance alive

### Claim 3  [PENDING] ✅
> I had accountability for data integrity at a level that is rare — where precision and certainty were non-negotiable because the consequences were real and human

*Contexts: employer: UNITE HERE*

- Processed worker rosters containing social security numbers and financial data where trust in the source and the schema directly affected people's dues, grievances, and organizing safety
  - Records had to be rebuilt manually before a single record could be trusted
  - Organizing data required permanent deletion decisions to protect real human risk
  - Grievance documentation had to hold up to procedural standards across years and multiple contract versions

**Conclusion:** This is data where instrumentation is imperfect, sources are uncontrolled, legal and procedural requirements are strict, and the stakes are human — getting to trustworthy output requires understanding what the source is actually recording, what the domain rules require, and what the consequences of error are before you model anything.

---

## Data Engineer / legal/compliance
*hash: 27e886399033...*  

**Paragraph:**
> At UNITE HERE, handling sensitive membership, dues, health fund, and grievance data meant
> the pipeline design was a compliance question before it was an engineering question. Files
> arrived as CSVs, tab-delimited text, and PDFs — some scans poor enough to require
> secondary cleaning before they could be used at all. None of it could move over standard
> electronic channels. I built ingestion workflows around those constraints, with protected
> and offline handling at every step, because the cost of getting it wrong was legal and
> organizational, not just technical.

### Claim 1  [PENDING] ✅
> At UNITE HERE, I built ingestion workflows where compliance and data protection were the primary design constraints, not afterthoughts to engineering

*Contexts: employer: UNITE HERE*

- The data I handled — membership, dues, health fund, and grievance records — made the pipeline design a compliance question before it was an engineering question
- I designed protected and offline handling at every step because the cost of getting it wrong was legal and organizational, not just technical

### Claim 2  [PENDING] ✅
> At UNITE HERE, I owned the ingestion layer for data arriving in multiple uncontrolled formats — CSVs, tab-delimited text, PDFs — including scans poor enough to require secondary cleaning before use

*Contexts: employer: UNITE HERE*

- Files arrived as CSVs, tab-delimited text, and PDFs — some scans poor enough to require secondary cleaning before they could be used at all
  - None of it could move over standard electronic channels

### Claim 3  [PENDING] ✅
> I work with the constraint that data governance is not separable from the technical architecture — when the stakes are legal and organizational, the pipeline design has to reflect that from the start

- At UNITE HERE, handling sensitive membership, dues, health fund, and grievance data meant the pipeline design was a compliance question before it was an engineering question
  - The cost of getting it wrong was legal and organizational, not just technical

**Conclusion:** This is data where the source of truth is controlled by external parties, arrives in uncontrolled formats, and carries legal and organizational risk — getting to trustworthy output requires building protection and compliance into the architecture itself, not bolting it on after.

---

## Data Engineer / Google-specific database technologies (BigQuery,
*hash: 15cdec9f071f...*  

**Paragraph:**
> At Universe, the entire application runs on data: parsed voterfiles and shapefiles power
> every canvas a campaign deploys, and I built the pipelines and modular generics underneath
> that on BigQuery, Prefect, dbt, and TypeScript, with mypy and strict linting so the
> infrastructure could flex across campaign configurations without rewriting core logic.
> Firebase was central to the Universe application as a live data layer driving user-facing
> functionality. As a Bluebonnets Fellow, I was placed on a live Texas campaign doing
> electoral data operations alongside other volunteers, and the Texas Secretary of State
> delivered the voterfile so late we were pulling together old files, constructing pipelines
> off incomplete data, and pushing live updates while canvassers were already in the field.
> I volunteered because Texas elections are high stakes and the data quality in electoral
> work is routinely bad enough that less technical volunteers cannot get their operations
> off the ground without someone who can build fast and build clean. GCP is the default
> infrastructure across the electoral and civic tech world, and I have done serious work
> across that stack under conditions where the data is late, the files are messy, and the
> timeline does not move.

### Claim 1  [PENDING] ✅
> At Universe, I built the pipelines and modular generics underneath the entire application on BigQuery, Prefect, dbt, and TypeScript

*Contexts: employer: Universe*

- The entire application runs on data: parsed voterfiles and shapefiles power every canvas a campaign deploys
- Built infrastructure with mypy and strict linting so the infrastructure could flex across campaign configurations without rewriting core logic
  - The infrastructure needed to support different campaign configurations without requiring rewrites to core logic

### Claim 2  [PENDING] ✅
> I work backwards from what the application needs to deliver into the data infrastructure that makes it possible

- At Universe, parsed voterfiles and shapefiles power every canvas a campaign deploys, and I built the pipelines and modular generics underneath that
  - The infrastructure was designed so that campaign-specific configurations could be supported without rewriting core logic

### Claim 3  [PENDING] ✅
> I build infrastructure that is both technically rigorous and flexible enough to handle real operational constraints

- Used mypy and strict linting to ensure the infrastructure could flex across campaign configurations without rewriting core logic
  - Strict typing and linting enabled the infrastructure to be reusable across different campaign setups
- As a Bluebonnets Fellow on a live Texas campaign, pulled together old files, constructed pipelines off incomplete data, and pushed live updates while canvassers were already in the field
  - The Texas Secretary of State delivered the voterfile so late that old files had to be used
  - Pipelines had to be constructed from incomplete data
  - Live updates were being pushed while canvassers were actively in the field

### Claim 4  [PENDING] ✅
> I had accountability for data quality in electoral operations at a level where technical rigor directly determines whether less technical volunteers can get their work done

*Contexts: employer: Bluebonnets Fellowship (Texas campaign)*

- I volunteered because Texas elections are high stakes and the data quality in electoral work is routinely bad enough that less technical volunteers cannot get their operations off the ground without someone who can build fast and build clean
  - Data quality in electoral work is routinely bad enough to prevent less technical volunteers from getting operations off the ground
  - The work requires both speed and technical cleanliness

### Claim 5  [PENDING] ✅
> I have done serious work across the GCP stack under conditions where the data is late, the files are messy, and the timeline does not move

- GCP is the default infrastructure across the electoral and civic tech world
- On a live Texas campaign, constructed pipelines off incomplete data and pushed live updates while canvassers were in the field, with the voterfile delivered late
  - The Texas Secretary of State delivered the voterfile so late that old files had to be pulled together
  - Pipelines were constructed from incomplete data
  - Live updates were pushed while canvassers were already in the field

### Claim 6  [PENDING] ✅
> I am drawn to work where technical decisions directly affect whether an organization can operate effectively under real constraints

- I volunteered for a live Texas campaign doing electoral data operations because Texas elections are high stakes and the data quality in electoral work is routinely bad enough that less technical volunteers cannot get their operations off the ground without someone who can build fast and build clean
  - Texas elections are high stakes
  - Data quality in electoral work is routinely bad enough to prevent less technical volunteers from operating
  - Technical work directly enables other volunteers to do their jobs

**Conclusion:** This is data where the source is controlled by external actors, delivery is unpredictable, and the schema is often incomplete — getting to usable output requires building infrastructure that is both technically rigorous and flexible enough to handle real operational constraints, and where the quality of the technical work directly determines whether the organization can function.

---

## Data Engineer / LLM API integration for web applications
*hash: f0a8de37e026...*  

**Paragraph:**
> CBA Clock is a full workflow application for union contract intelligence — officers can
> track grievances, map contract language across successive agreements, and query the system
> for answers grounded in the actual text of their CBA. I built the entire stack: the web
> interface, the backend routing, the RAG retrieval layer, and the API integration that
> sends structured prompts to Claude, with the system tested and interoperable across OpenAI
> models as well. A user working a grievance can move through the application, pull relevant
> contract clauses, and get LLM-generated analysis tied directly to the retrieved source
> text. I made that sourcing requirement a hard architectural constraint — in a grievance
> context, an officer who acts on a hallucination can lose a case that should have been won,
> so the interface surfaces the contract language alongside the model's response at every
> step. The LLM API integration is load-bearing here: it is the mechanism by which years of
> contract history become queryable, navigable, and actionable for someone who needs a
> defensible answer in the middle of a dispute.

### Claim 1  [PENDING] ✅
> I built the entire stack for CBA Clock: the web interface, the backend routing, the RAG retrieval layer, and the API integration that sends structured prompts to Claude

*Contexts: project: CBA Clock*

- Full-stack ownership across web interface, backend routing, RAG retrieval, and LLM API integration
  - System tested and interoperable across OpenAI models as well as Claude
  - API integration sends structured prompts to Claude

### Claim 2  [PENDING] ✅
> I made sourcing — grounding LLM responses directly in retrieved contract text — a hard architectural constraint because in a grievance context, an officer who acts on a hallucination can lose a case that should have been won

*Contexts: project: CBA Clock*

- The interface surfaces the contract language alongside the model's response at every step
  - This is a load-bearing architectural decision, not an afterthought
  - The sourcing requirement is enforced at the system level, not left to the user to verify

### Claim 3  [PENDING] ✅
> The LLM API integration is the mechanism by which years of contract history become queryable, navigable, and actionable for someone who needs a defensible answer in the middle of a dispute

*Contexts: project: CBA Clock*

- A user working a grievance can move through the application, pull relevant contract clauses, and get LLM-generated analysis tied directly to the retrieved source text
  - The system makes contract language across successive agreements queryable and mappable
  - Officers can track grievances and query the system for answers grounded in actual contract text

### Claim 4  [PENDING] ✅
> I think about system design from the constraint that the stakes of error are real — in a domain where a hallucination costs a case, the architecture itself has to enforce truthfulness

*Contexts: project: CBA Clock*

- Made sourcing a hard architectural constraint rather than a feature or guideline
  - In a grievance context, an officer who acts on a hallucination can lose a case that should have been won
  - This shaped every decision about how the LLM integration works and what the interface shows

**Conclusion:** This is work where the technical decision and the domain decision are inseparable — you cannot build a system for union contract intelligence without making the sourcing requirement non-negotiable at the architectural level, because the cost of failure is not a bad user experience but a lost grievance.

---

## Data Engineer / Supporting policymakers, regulatory/compliance
*hash: 8cf2ea50308f...*  

**Paragraph:**
> At UNITE HERE, I worked with dues records, health fund data, grievance tracking, and
> membership systems: data carrying direct legal and contractual obligations under
> collective bargaining agreements and labor law. Errors affected workers' benefits
> eligibility, grievance standing, and the union's ability to enforce contract terms. I
> built and maintained the pipelines and models that kept that data clean, traceable, and
> auditable, working closely with administrative staff who understood the legal stakes of
> every record. My CBA Clock application extends that same logic into a policy-support tool,
> helping union officers track grievance timelines and contract language across agreement
> versions: structured, rule-bound document intelligence of the kind that legal and
> compliance teams depend on.

### Claim 1  [PENDING] ✅
> I had accountability for data integrity at a level that is rare for data engineers — the data I stewarded carried direct legal and contractual obligations under collective bargaining agreements and labor law

*Contexts: employer: UNITE HERE*

- Errors in dues records, health fund data, grievance tracking, and membership systems directly affected workers' benefits eligibility, grievance standing, and the union's ability to enforce contract terms
- I worked closely with administrative staff who understood the legal stakes of every record

### Claim 2  [PENDING] ✅
> I built and maintained the pipelines and models that kept data clean, traceable, and auditable across dues records, health fund data, grievance tracking, and membership systems

*Contexts: employer: UNITE HERE*

- Owned end-to-end responsibility for data quality and auditability in systems carrying legal and contractual obligations

### Claim 3  [PENDING] ✅
> I am drawn to work where the technical decisions ARE the domain decisions — where careful data engineering makes organizations more accountable and able to enforce their obligations

- At UNITE HERE, data integrity directly enabled the union's ability to enforce contract terms and protect worker benefits
- CBA Clock extends that same logic into policy support — structured, rule-bound document intelligence that legal and compliance teams depend on

### Claim 4  [PENDING] ✅
> I built CBA Clock as a policy-support tool helping union officers track grievance timelines and contract language across agreement versions

*Contexts: project: CBA Clock*

- The application provides structured, rule-bound document intelligence of the kind that legal and compliance teams depend on

**Conclusion:** This is data where the stakes are human — where precision and auditability are non-negotiable because errors directly harm workers. That experience shaped how I think about data governance and why I'm drawn to work where technical rigor serves accountability.

---

## Data Engineer / Master's degree in relevant technical field
*hash: 3bd0f9d273fa...*  

**Paragraph:**
> My MFA was an interdisciplinary program where I took programming classes, learned C++ and
> Java, did object-oriented programming for interactive music systems in Max/MSP, and worked
> with electrical and mechanical engineering concepts for art projects. My thesis involved
> multiple pieces. One of them was a physical interface I built and programmed in C++ using
> Arduino that played audio and video clips, lit up LEDs, and moved small objects. I also
> worked in Processing, which runs on Java. I was writing code, wiring hardware, and
> building interactive systems as part of a graduate degree, and I have been building on
> those foundations ever since.

### Claim 1  [PENDING] ✅
> I built physical interfaces in C++ using Arduino that integrated audio, video, LEDs, and mechanical movement as part of my MFA thesis

*Contexts: project: MFA thesis physical interface*

- Designed and programmed a physical interface in C++ on Arduino that played audio and video clips, controlled LED lighting, and moved small objects

### Claim 2  [PENDING] ✅
> I learned object-oriented programming through interactive music systems in Max/MSP as part of my MFA coursework

*Contexts: project: MFA interdisciplinary program*

- Took programming classes in C++ and Java, did object-oriented programming for interactive music systems in Max/MSP

### Claim 3  [PENDING] ✅
> I work across hardware and software integration, combining electrical and mechanical engineering concepts with code

- MFA thesis involved wiring hardware, writing code, and building interactive systems that integrated electrical and mechanical engineering concepts
  - Worked with Processing (Java-based), C++, and Arduino across art projects
  - Built systems that required understanding both the physical and computational sides of interactive design

### Claim 4  [PENDING] ✅
> I have been building on the foundations of hardware-software integration and interactive systems design since my MFA

- Graduate degree involved writing code, wiring hardware, and building interactive systems as core practice
  - MFA was an interdisciplinary program spanning programming, electrical and mechanical engineering concepts, and interactive design

---

## Data Engineer / BBC hackathon 2025 win
*hash: a8cc9ed42858...*  

**Paragraph:**
> Winning first place in the BBC's company-wide hackathon against roughly eleven teams
> across all divisions came down to an idea I originated and a tool we actually shipped in
> three days. The problem was real: a video editor hunting for a specific spoken moment in a
> long file either had to scrub through footage manually or rely on memory. My solution was
> a semantic search engine over closed caption transcripts, synced to video timecodes, so an
> editor could search by keyword or concept and pull exact clips instantly. I built the
> Streamlit interface and the data pipeline backend; our team of three was one of the
> smallest in the field. The demo landed on a library of Bluey clips, and the ability to
> search for the strangest, most specific words and immediately assemble a mashup made the
> capability undeniable. The judges responded to the creativity and the technical execution
> together, and the energy in the room was real enough that one teammate started bolting on
> a computer vision layer mid-competition to identify objects in video. Our day-to-day work
> is driven by business requirements and top-down requests, so building something genuinely
> playful that was also technically rigorous was its own kind of proof.

*No claims extracted.*

---

## Data Engineer / BBC hackathon 2025 win
*hash: 625c7de0a879...*  

**Paragraph:**
> Semantic search over video is a harder problem than it sounds, and I learned that
> firsthand winning the BBC hackathon in 2025. The core challenge was that closed caption
> files are not precise transcripts — the text surfaces *around* when a character speaks,
> not exactly when, which means a naive timecode sync produces clips that cut in too early
> or land mid-word. To fix it, we had to test clips repeatedly to find a buffer large enough
> to catch the right moment but tight enough not to bleed into surrounding audio. The search
> itself used something in the family of Elasticsearch to match queries against chunked
> transcript text and return the relevant timecode window, with Streamlit handling video
> playback on top. By the end of three days we had a prototype that demonstrated a real
> capability: type a phrase, jump to the exact clip in the Bluey archive, and walk away with
> an asset ready for a supercut, a trailer, or anything else a social or production team
> needed to pull together.

### Claim 1  [PENDING] ✅
> I built a semantic search system over video that won the BBC hackathon in 2025

*Contexts: project: BBC hackathon 2025*

- Delivered a working prototype in three days that let users type a phrase and jump to the exact clip in the Bluey archive
  - The system produced clips ready for immediate use by social or production teams for supercuts, trailers, or other assets

### Claim 2  [PENDING] ✅
> I identified and solved the core technical problem: closed caption files surface text around when a character speaks, not exactly when, which breaks naive timecode sync

*Contexts: project: BBC hackathon 2025*

- Naive timecode sync produces clips that cut in too early or land mid-word
- Solved it by testing clips repeatedly to find a buffer large enough to catch the right moment but tight enough not to bleed into surrounding audio
  - This required understanding the precision limits of the source data before building the sync logic

### Claim 3  [PENDING] ✅
> I architected the search and playback stack: Elasticsearch-family search over chunked transcript text returning timecode windows, with Streamlit handling video playback

*Contexts: project: BBC hackathon 2025*

- Used Elasticsearch-family tool to match queries against chunked transcript text and return the relevant timecode window
- Streamlit handled video playback on top

**Conclusion:** Semantic search over video requires understanding the precision limits and timing behavior of the source data — closed captions are not precise transcripts — before you can build reliable sync logic. The harder problem is not the search itself but getting the timecode right.

---

## Data Engineer / Snowflake
*hash: 8cc574e99732...*  

**Paragraph:**
> When a project lands without a clear specification, my first move is to work backwards
> from the end state: who will use this, how will they use it, and what problem is it
> supposed to solve. From there I identify the people who can give me sharper detail about
> what they need and how they picture it helping them, and I go talk to them. In parallel I
> open a notebook — not to build anything yet, but to look at the data directly, pull
> baseline metrics, check datatypes, and get a read on cleanliness. By the time I am
> thinking about design, I already know whether what exists is sufficient to cover what was
> requested, what shape it is in, and what scale of transformation and processing the
> pipeline will need. The requirements work and the architecture work happen simultaneously,
> grounded in what the data can actually support, and that sequence is what keeps the
> engineering from running ahead of the problem.

### Claim 1  [PENDING] ✅
> I work backwards from the end state — who will use this, how will they use it, and what problem is it supposed to solve — before I think about design

- I identify the people who can give me sharper detail about what they need and how they picture it helping them, and I go talk to them
- In parallel I open a notebook to look at the data directly, pull baseline metrics, check datatypes, and get a read on cleanliness
  - This happens before building anything, grounded in what the data can actually support

### Claim 2  [PENDING] ✅
> I run requirements work and architecture work simultaneously, grounded in what the data can actually support, and that sequence keeps the engineering from running ahead of the problem

- By the time I am thinking about design, I already know whether what exists is sufficient to cover what was requested, what shape it is in, and what scale of transformation and processing the pipeline will need

**Conclusion:** This is a method for keeping technical decisions tethered to actual user need and data reality — the requirements and the architecture inform each other, not sequentially but in parallel, so you don't build something that either overshoots what the data can support or undershoots what the user actually needs.

---

## Data Engineer / Snowflake
*hash: 603b6dcf53d5...*  

**Paragraph:**
> Snowflake is Per Scholas's primary platform, and my experience with it is direct: at
> BritBox, the integration path between Snowflake and Redshift had no native connector, so
> the architecture dropped Snowflake data into S3 as parquet files and ingested from there
> into Redshift, bypassing the external table option because the latency was prohibitive. I
> worked in that Snowflake instance querying, modeling, and debugging. What I can also tell
> you is that Redshift Server is the harder system. Snowflake abstracts away decisions that
> Redshift forces you to make explicitly: sort and distribution keys, compression and
> columnar sizing, workload management queues for resource allocation, concurrency controls,
> and execution plan tracing. I have made all of those decisions under production load on
> billion-row data. An engineer who can navigate Redshift at that level and optimize jobs
> there carries that skill directly into Snowflake, with room to spare.

### Claim 1  [PENDING] ✅
> At BritBox, I worked in the Snowflake instance querying, modeling, and debugging within an architecture that moved data to Redshift via S3 parquet files because external tables had prohibitive latency

*Contexts: employer: BritBox*

- The integration path between Snowflake and Redshift had no native connector, so the architecture dropped Snowflake data into S3 as parquet files and ingested from there into Redshift
  - bypassed the external table option because the latency was prohibitive
- Worked querying, modeling, and debugging in that Snowflake instance

### Claim 2  [PENDING] ✅
> I have made explicit decisions on Redshift under production load on billion-row data: sort and distribution keys, compression and columnar sizing, workload management queues for resource allocation, concurrency controls, and execution plan tracing

*Contexts: employer: BritBox*

- Made decisions on sort and distribution keys, compression and columnar sizing, workload management queues for resource allocation, concurrency controls, and execution plan tracing
  - under production load
  - on billion-row data

### Claim 3  [PENDING] ✅
> I understand that Redshift forces you to make explicit decisions that Snowflake abstracts away, and navigating Redshift at that level of optimization carries directly into Snowflake

- Redshift abstracts away decisions that Snowflake forces you to make explicitly: sort and distribution keys, compression and columnar sizing, workload management queues for resource allocation, concurrency controls, and execution plan tracing
  - An engineer who can navigate Redshift at that level and optimize jobs there carries that skill directly into Snowflake, with room to spare

**Conclusion:** Direct experience with both systems under production constraints reveals that mastery of Redshift's explicit optimization requirements translates to Snowflake competency, not the reverse.

---

## Data Engineer / Fivetran
*hash: 5ae2200dbd0c...*  

**Paragraph:**
> Fivetran is a tool I know well — I used it at Hypedocs and on contracts pulling from
> MixPanel and Google Ads — but the more revealing thing is where I stopped reaching for it.
> Fivetran is built for connections to large enterprise platforms it has already
> productized, and it is expensive precisely because that coverage is its entire value
> proposition. For any organization pulling from sources outside that catalog, it is not a
> solution, it is a ceiling. My background is in building custom connectors and ingestion
> pipelines from scratch, which means I can cover everything Fivetran handles for the
> sources it supports, and keep building where it stops. Per Scholas would have an engineer
> who can connect to whatever the data actually lives in, not one working around the edges
> of an expensive tool.

### Claim 1  [PENDING] ✅
> I know Fivetran well — I used it at Hypedocs and on contracts pulling from MixPanel and Google Ads

*Contexts: employer: Hypedocs, employer: Contract work*

- Used Fivetran for MixPanel and Google Ads integrations

### Claim 2  [PENDING] ✅
> My background is in building custom connectors and ingestion pipelines from scratch

- Can cover everything Fivetran handles for the sources it supports, and keep building where it stops

### Claim 3  [PENDING] ✅
> I understand Fivetran's structural limitation: it is built for connections to large enterprise platforms it has already productized, and for any organization pulling from sources outside that catalog, it is not a solution, it is a ceiling

- Fivetran is expensive precisely because that coverage is its entire value proposition
- For sources outside Fivetran's catalog, the tool becomes a constraint rather than a solution

### Claim 4  [PENDING] ✅
> For Per Scholas, I would be an engineer who can connect to whatever the data actually lives in, not one working around the edges of an expensive tool

*Contexts: employer: Per Scholas*

- Custom connector and pipeline building capability covers both productized sources and non-standard data locations

**Conclusion:** This is someone who has learned the boundaries of a tool by using it, and whose actual strength — building from scratch — is precisely what organizations need when they operate outside the vendor's catalog. The claim isn't just technical capability; it's about understanding when a tool is the right choice and when it becomes a constraint.

---

## Data Engineer / dbt
*hash: a34d399b6ea3...*  

**Paragraph:**
> At Universe, weekly Tableau refreshes were failing or running for hours, and the
> dashboards waiting on the other end served the CEO and Senior Leadership Team — the
> numbers they used to run the organization. I diagnosed the root cause as transformation
> logic living in the wrong place: Tableau was carrying computational weight that belonged
> upstream. My proposed fix was to migrate business definition logic into dbt models so
> Tableau would read pre-computed results instead of grinding through raw data on every
> refresh. Executing that migration is a slow, multi-team effort still in progress, but I
> was positioned to propose and lead it because I had built the dbt environment from scratch
> — a self-hosted instance on EC2, connected to Redshift, orchestrated through Prefect with
> custom flows I wrote to handle different file cleaning and transformation requirements.

### Claim 1  [PENDING] ✅
> At Universe, I built the dbt environment from scratch — a self-hosted instance on EC2, connected to Redshift, orchestrated through Prefect with custom flows I wrote to handle different file cleaning and transformation requirements

*Contexts: employer: Universe*

- Self-hosted dbt instance on EC2 connected to Redshift
- Orchestrated through Prefect with custom flows for file cleaning and transformation

### Claim 2  [PENDING] ✅
> At Universe, I diagnosed that transformation logic was living in the wrong place — Tableau was carrying computational weight that belonged upstream

*Contexts: employer: Universe*

- Weekly Tableau refreshes were failing or running for hours, serving dashboards the CEO and Senior Leadership Team used to run the organization
  - The dashboards were critical to leadership decision-making
- Root cause: Tableau was grinding through raw data on every refresh instead of reading pre-computed results

### Claim 3  [PENDING] ✅
> At Universe, I proposed and led the migration to move business definition logic into dbt models so Tableau would read pre-computed results

*Contexts: employer: Universe*

- I was positioned to propose and lead the migration because I had built the dbt environment from scratch
  - The migration is a slow, multi-team effort still in progress

**Conclusion:** When you own the upstream infrastructure, you can see where computational work is misplaced downstream — and you have the standing to propose and lead the fix across teams.

---

## Data Engineer / Tableau
*hash: 10fe991def5a...*  

**Paragraph:**
> At Britbox, Tableau is part of my daily working environment. Refresh timeouts are a
> recurring operational reality, and when they hit, I dig into the underlying cause rather
> than waiting for someone else to triage. Beyond keeping published data sources running,
> I've worked directly with analysts to optimize their queries and have built views to
> reduce the load driving those timeouts in the first place. I understand how Tableau
> behaves under pressure, where performance breaks down, and what it takes to keep
> dashboards reliable for the people depending on them.

*No claims extracted.*

---

## Data Engineer / CI/CD pipelines
*hash: f94f01a61ed7...*  

**Paragraph:**
> My approach to CI/CD in data engineering is grounded in production systems where a bad
> deploy means corrupted data, a silent failure, or a backfill scramble at the worst
> possible time. At BritBox, where I was the sole data engineer for nearly two years, I
> built deployment and testing patterns around the failure modes I knew were real: schema
> changes, incremental loads, partial writes, and provider data that arrived incorrect or
> incomplete and had to be reprocessed cleanly. Nobody required me to ship with idempotency,
> resume logic, backfill support, and overwrite safeguards. I built those in because a
> pipeline that cannot tell you where it failed or get back online fast is a liability, and
> I was the one who would be fixing it at 2am. The control layer I built around those
> pipelines, spanning AWS Glue, Redshift, dbt, S3, and orchestration, is what made changes
> observable, reversible, and safe to deploy against production analytics.

### Claim 1  [PENDING] ✅
> At BritBox, I built deployment and testing patterns around failure modes I knew were real: schema changes, incremental loads, partial writes, and provider data that arrived incorrect or incomplete

*Contexts: employer: BritBox*

- Built idempotency, resume logic, backfill support, and overwrite safeguards into pipelines
  - These were not required — built them because a pipeline that cannot tell you where it failed or get back online fast is a liability
  - As the sole data engineer, accountability for fixing failures at 2am shaped what got built
- Built a control layer spanning AWS Glue, Redshift, dbt, S3, and orchestration
  - This control layer made changes observable, reversible, and safe to deploy against production analytics

### Claim 2  [PENDING] ✅
> I work backwards from failure modes that are real in production — schema changes, incremental loads, partial writes, provider data corruption — and build safeguards that let you know where a pipeline failed and get back online fast

- A pipeline that cannot tell you where it failed or get back online fast is a liability
- Idempotency, resume logic, backfill support, and overwrite safeguards are not optional when you own the fix at 2am

### Claim 3  [PENDING] ✅
> I had accountability for data pipeline reliability at a level that is rare — as the sole data engineer at BritBox for nearly two years, I owned the consequences of every deploy decision

*Contexts: employer: BritBox*

- Sole data engineer for nearly two years, responsible for fixing pipeline failures at 2am
  - This accountability shaped what patterns got built and what safeguards were non-negotiable

### Claim 4  [PENDING] ✅
> What draws me to this work is that a bad deploy in data engineering means corrupted data, silent failure, or a backfill scramble at the worst possible time — and that consequence is what makes the engineering matter

- A bad deploy means corrupted data, a silent failure, or a backfill scramble at the worst possible time
  - This is the real failure mode that shapes what gets built and how it gets tested

**Conclusion:** This is data engineering where the stakes are visible and immediate — you cannot separate the technical decision from the operational consequence. That clarity is what makes the control layer necessary and what makes it matter.

---

## Data Engineer / HIPAA compliance / PHI handling
*hash: 0e22292274a8...*  

**Paragraph:**
> Sensitive data handling is not new territory for me. At UNITE HERE I built ingestion
> workflows around health fund, dues, and membership data carrying direct legal obligations,
> with protected handling at every step because the cost of getting it wrong was legal and
> organizational. At BritBox, operating inside BBC's internal governance framework meant
> that before any tool touched PII, it went through a formal infosec vetting process that
> could take months. When a tool didn't clear that process, it didn't get used. The
> practical answer was often to self-host open-source tooling locked down inside our own
> domain on provisioned EC2 infrastructure, which kept the work moving without compromising
> the controls.

*No claims extracted.*

---

## Data Engineer / dbt experience
*hash: e69c120ccbaa...*  

**Paragraph:**
> At Universe, the data infrastructure ran on GCP — BigQuery, Prefect, dbt — and the core
> modeling challenge was that voterfile data arrives in specific flavors of broken. I built
> a branched and layered architecture: generic handling for standard CSVs and tab-delimited
> files, and provider-specific branches for known corruption patterns, custom escape
> characters, and formatting rules particular to a given file source. Prefect made that
> branching executable — a flow could read and inspect an incoming file to route it to the
> right path, or, when I already knew the source, I could send it directly into the model
> branch built around that format. At BritBox, the dbt environment was a different stack:
> self-hosted on EC2, connected to Redshift, orchestrated through Prefect flows I wrote to
> handle the file cleaning and transformation requirements of a production subscription data
> pipeline.

*No claims extracted.*

---

## Data Engineer / Data quality monitoring and alerting
*hash: d458b47e9bc4...*  

**Paragraph:**
> At BritBox, where event data could arrive with up to a 12-hour delay, I designed and
> calibrated threshold and timing alerts around the ingest layer so the team had a Slack
> signal the moment data behavior fell outside expected bounds. The calibration work was
> real: a pipeline processing over a billion playback events cannot use the same alerting
> logic as one processing thousands, and late-arriving events in a streaming context require
> thresholds tuned to the data's actual behavior, not generic rules. Across roles where
> providers repeatedly delivered incomplete data, I built monitoring mechanisms to catch
> shortfalls before they propagated downstream, including alerting around data availability
> and data change events. I also built SQL injection monitoring so the team had a signal
> when something suspicious hit the data layer before it could do damage.

*No claims extracted.*

---

## Data Engineer / Pull request reviews and structured
*hash: a4bc6d472db0...*  

**Paragraph:**
> At Universe, code review was a structured part of how the team worked: written comments
> went in asynchronously before we met, so by the time we sat down the conversation could go
> straight to substance. As the sole dedicated data engineer, I worked directly with the
> CEO, who was invested enough in the craft to build alongside me and push the technical bar
> on every review. Streaming approaches generated extended debate because the choice of
> tools and patterns had direct consequences for performance, idempotence, and compression,
> and a poor decision there would have been expensive to unwind. Linting rules and the
> investment in custom typing stubs were the same kind of conversation -- where does the
> team's time go, and what does the codebase cost to maintain long-term. My contribution in
> those sessions was rarely to arrive with a single answer. More often I came in having
> mapped out multiple approaches, each with its own tradeoffs, and the discussion was about
> working through those considerations together to land on something we could both build on.

*No claims extracted.*

---

## Data Engineer / Production ownership (SLAs, incidents
*hash: 48014c469c49...*  

**Paragraph:**
> At BritBox, I owned subscriber reporting end-to-end as the sole data engineer: the data
> model, the pipeline, the validation, and the delivery of the numbers senior leadership
> read each month to understand whether the product was working. The structural constraint
> was that Evergent served only current-state data to our warehouse, which made accurate
> churn and subscriber counts dependent on monthly snapshots and vendor-side logic I could
> not fully control. When new billing recovery logic caused Evergent to double-count churn,
> I identified the pattern, documented the root cause for the vendor, and validated the fix
> before the numbers went back up. When new subscription tiers broke the model again, with
> inactive subscription IDs appearing current and future ones marked active, I rebuilt the
> logic overnight with the Finance lead to hit the monthly close. There was no anomaly
> detection built in, no second engineer to review the work, and no margin for a wrong
> number reaching senior leadership. The same discipline carried into the watch-duration
> pipeline I built to replace a vendor process that failed regularly: my Spark replacement,
> processing over a billion playback events daily at subscriber grain, has had no failures
> since go-live.

*No claims extracted.*

---

## Data Engineer / System design judgment (grain
*hash: e2f99510f6d2...*  

**Paragraph:**
> Moving to subscriber grain on the watch-duration pipeline was the right call for the
> business, and it was also the decision that made the engineering significantly harder. The
> vendor had modeled at customer grain, which collapsed subscribers together and made free-
> trial status invisible. Getting to subscriber grain required joining an additional
> subscription table and evaluating free-trial status by checking whether each watch event
> fell within a seven-day date window tied to that subscriber's trial start. At over a
> billion events per day, a per-event range join against a subscription table is a serious
> performance problem. I solved it in two parts: advanced Spark partitioning to contain the
> range evaluation, and a broadcast table of free-trial subscription dates built to
> increment as new trials open, so the lookup stays tractable at scale. Moving to a finer
> grain also meant the existing customer-level output could no longer served as a validation
> target, so I built a cross-grain rollup from the subscriber output to reconstruct a
> comparable customer-level number and reconcile against it. The project landed with minimal
> oversight and no meaningful management support — I scoped it, solved it, and shipped it.

### Claim 1  [PENDING] ✅
> At BritBox, I owned the watch-duration pipeline grain decision and determined what 'subscriber grain' meant before solving the engineering

*Contexts: employer: BritBox*

- Moving to subscriber grain required joining an additional subscription table and evaluating free-trial status by checking whether each watch event fell within a seven-day date window tied to that subscriber's trial start
  - The vendor had modeled at customer grain, which collapsed subscribers together and made free-trial status invisible
  - This was the decision that made the engineering significantly harder, but was the right call for the business
- I scoped it, solved it, and shipped it with minimal oversight and no meaningful management support

### Claim 2  [PENDING] ✅
> I solve large-scale data problems by breaking them into tractable parts: I use advanced partitioning to contain expensive operations, and I build incremental lookup tables to keep joins tractable at scale

- At over a billion events per day, a per-event range join against a subscription table is a serious performance problem. I solved it in two parts: advanced Spark partitioning to contain the range evaluation, and a broadcast table of free-trial subscription dates built to increment as new trials open, so the lookup stays tractable at scale
  - The broadcast table increments as new trials open, keeping the lookup tractable at scale

### Claim 3  [PENDING] ✅
> I think about validation and reconciliation as part of the grain decision itself — when you change grain, you have to rebuild your validation target

- Moving to a finer grain meant the existing customer-level output could no longer served as a validation target, so I built a cross-grain rollup from the subscriber output to reconstruct a comparable customer-level number and reconcile against it

**Conclusion:** This is work where the business decision and the engineering decision are inseparable — you can't move to subscriber grain without understanding what that costs in performance, and you can't solve the performance problem without understanding what you're trying to measure.

---

## Data Engineer / Data modeling depth (metric definition
*hash: 3fbc6f4f3680...*  

**Paragraph:**
> When I joined BritBox as the sole data engineer, the vendor-supplied watch duration
> pipeline was failing regularly and the business was making content and product decisions
> on numbers it couldn't trust. I rebuilt it from scratch in four months, alone, while
> carrying all other DE work. The front end of the project had never been properly scoped
> before it landed on me, so I ran discovery and production build simultaneously: defining
> what "watch duration" actually meant at the metric level, deciding how to reconcile events
> across grains, and making every architectural call without senior review. At 1B+ events
> per day in PySpark, Glue, and Redshift, the margin for a bad modeling decision was zero —
> a number that looked plausible but was wrong would have been invisible until a product
> team had already acted on it. The pipeline has been 100% stable since go-live. BritBox's
> most important content metric, viewership by subscriber tier, recovery rates, premium
> adoption, now runs on a foundation I designed and own entirely.

*No claims extracted.*

---

## Data Engineer / Business impact quantified
*hash: c2d1cbf53807...*  

**Paragraph:**
> At BritBox, I owned the pipeline that processed over a billion playback events per day to
> produce the subscriber-level watch metrics the entire business ran on. When a new show
> launched, every downstream question anchored to that data: how many subscribers watched,
> how long they stayed, how the audience broke down by tier, whether the marketing spend had
> moved the needle. The vendor pipeline I replaced failed regularly and modeled at a coarser
> customer grain, which meant those questions either went unanswered or got answered wrong.
> I rebuilt it from scratch in four months as the sole dedicated data engineer, doing
> requirements discovery and production architecture simultaneously with no senior review.
> My replacement, built in PySpark on Glue and Redshift at subscriber grain with proper
> session stitching and cross-grain reconciliation, has had zero failures since go-live.

### Claim 1  [PENDING] ✅
> At BritBox, I owned the pipeline that processed over a billion playback events per day to produce the subscriber-level watch metrics the entire business ran on

*Contexts: employer: BritBox*

- Every downstream question about a new show launch anchored to that data: how many subscribers watched, how long they stayed, how the audience broke down by tier, whether the marketing spend had moved the needle
- The vendor pipeline I replaced failed regularly and modeled at a coarser customer grain, which meant those questions either went unanswered or got answered wrong

### Claim 2  [PENDING] ✅
> At BritBox, I rebuilt the playback events pipeline from scratch in four months as the sole dedicated data engineer, doing requirements discovery and production architecture simultaneously with no senior review

*Contexts: employer: BritBox*

- Built in PySpark on Glue and Redshift at subscriber grain with proper session stitching and cross-grain reconciliation
  - Moved from coarser customer grain to subscriber grain
  - Implemented proper session stitching
  - Implemented cross-grain reconciliation
- Has had zero failures since go-live

### Claim 3  [PENDING] ✅
> I work at a level where I can determine what the business needs to understand before I model the data, and then own the architecture that makes that answerable

- Did requirements discovery and production architecture simultaneously as sole dedicated data engineer with no senior review
  - Had to figure out what questions the business needed answered about show launches and audience composition
  - Had to design the grain, session logic, and reconciliation approach that would make those questions answerable and trustworthy

**Conclusion:** This is data where the grain of the model and the logic of session stitching directly determine whether the business can answer its core questions — getting it wrong means decisions get made on bad information. Owning that end-to-end, with no safety net, meant the architecture had to be right the first time.

---

## Data Engineer / Medallion architecture / Lakehouse
*hash: ea017dd35169...*  

**Paragraph:**
> At Universe, I designed and built a Medallion architecture to handle a data layer that was
> driving the entire application: voter files are not standardized, arriving in different
> formats from different state and county sources with data quality that varies enough that
> the same field can mean different things depending on the provider, and the whole app ran
> off those files alongside shapefiles. I built layered cleansing logic with branched,
> conditional routing that handled standard CSVs and tab-delimited files generically while
> gating known sources into provider-specific branches built around their particular
> corruption patterns and formatting rules. As I encountered new client files with new data
> issues, I was able to refine and extend that logic without rebuilding from scratch,
> because the architecture was designed to absorb new cases cleanly. The curated layer only
> surfaced records that had cleared validation, giving the application a clean, reliable
> analytical surface regardless of what came in upstream, and keeping organizers working in
> the field on data they could trust.

### Claim 1  [PENDING] ✅
> At Universe, I designed and built a Medallion architecture to handle a data layer that was driving the entire application

*Contexts: employer: Universe*

- voter files arriving in different formats from different state and county sources with data quality that varies enough that the same field can mean different things depending on the provider
- built layered cleansing logic with branched, conditional routing that handled standard CSVs and tab-delimited files generically while gating known sources into provider-specific branches
  - each provider-specific branch was built around their particular corruption patterns and formatting rules
- the curated layer only surfaced records that had cleared validation, giving the application a clean, reliable analytical surface regardless of what came in upstream

### Claim 2  [PENDING] ✅
> I designed the architecture to absorb new cases cleanly without rebuilding from scratch as I encountered new client files with new data issues

*Contexts: employer: Universe*

- able to refine and extend the layered cleansing logic as new data issues emerged
  - the architecture was designed to absorb new cases cleanly

### Claim 3  [PENDING] ✅
> I work backwards from what the application needs — a clean, reliable analytical surface — into the data model and validation logic that produces it

- the curated layer only surfaced records that had cleared validation, keeping organizers working in the field on data they could trust
  - this design choice prioritized what downstream users needed to do their work reliably
- built provider-specific branches around their particular corruption patterns and formatting rules rather than forcing a one-size-fits-all approach
  - this reflects understanding that the data model must match the actual source characteristics, not an idealized schema

### Claim 4  [PENDING] ✅
> I had accountability for data integrity at a level where the entire application's reliability depended on the cleansing logic I built

*Contexts: employer: Universe*

- the data layer was driving the entire application, and organizers in the field were working off the curated output
  - keeping organizers working in the field on data they could trust was a direct consequence of the architecture

**Conclusion:** This is data where the source is imperfect and controlled by third parties — getting to trustworthy output requires understanding what each provider is actually recording and how their corruption patterns differ, then building conditional logic that handles each case on its own terms rather than forcing standardization upstream.

---

## Data Engineer / Metadata management, data lineage, RBAC
*hash: abd6f255c029...*  

**Paragraph:**
> Governance and access control are areas where I have done concrete implementation work,
> not just policy acknowledgment. At BritBox, as the sole data engineer, I authored and
> provisioned IAM policies, created and managed Secrets, and built out Redshift groups and
> schemas to enforce role-based access across the data environment — decisions I owned end
> to end because there was no one else to own them. At Universe, I proposed Great
> Expectations as part of the core data infrastructure, because the application ran on
> parsed voterfiles and shapefiles powering live campaign operations, and a schema violation
> in that environment does not produce a warning — it breaks the field workflow organizers
> are depending on in real time. The same instinct drove my push to implement Great
> Expectations at BritBox, where the move toward AI-driven tooling has made data integrity a
> load-bearing requirement rather than a best practice.

### Claim 1  [PENDING] ✅
> I authored and provisioned IAM policies, created and managed Secrets, and built out Redshift groups and schemas to enforce role-based access across the data environment — decisions I owned end to end because there was no one else to own them

*Contexts: employer: BritBox*

- As the sole data engineer, owned governance and access control implementation end to end
  - authored and provisioned IAM policies
  - created and managed Secrets
  - built out Redshift groups and schemas to enforce role-based access

### Claim 2  [PENDING] ✅
> I proposed Great Expectations as part of the core data infrastructure because the application ran on parsed voterfiles and shapefiles powering live campaign operations, and a schema violation in that environment does not produce a warning — it breaks the field workflow organizers are depending on in real time

*Contexts: employer: Universe*

- Identified and implemented data validation infrastructure for mission-critical data
  - application ran on parsed voterfiles and shapefiles powering live campaign operations
  - schema violation in that environment does not produce a warning — it breaks the field workflow organizers are depending on in real time
  - proposed Great Expectations as part of core data infrastructure in response to this risk

### Claim 3  [PENDING] ✅
> I pushed to implement Great Expectations at BritBox because the move toward AI-driven tooling has made data integrity a load-bearing requirement rather than a best practice

*Contexts: employer: BritBox*

- Recognized that AI-driven tooling changes the stakes for data integrity
  - move toward AI-driven tooling has made data integrity a load-bearing requirement rather than a best practice

### Claim 4  [PENDING] ✅
> I work from the principle that in environments where data failures have immediate operational consequences, validation infrastructure is not optional — it is foundational

- Consistent pattern across employers: proposing and implementing validation where data integrity directly affects operations
  - at Universe: schema violations break live field workflows
  - at BritBox: AI-driven tooling makes data integrity load-bearing

**Conclusion:** This is data where the consequences of failure are not delayed or abstract — they are immediate and operational. Getting to trustworthy output requires building validation into the infrastructure itself, not treating it as a downstream concern.

---

## Data Engineer / Iceberg / Delta Lake file formats
*hash: c6463cdf6fd5...*  

**Paragraph:**
> I have not yet worked with Iceberg or Delta Lake directly, but the operational problems
> those formats exist to solve are ones I have been engineering around for years. At
> BritBox, I built a batch ingestion pipeline on Glue and Redshift where correctness
> required solving session-boundary stitching across date partitions, deduplication at
> subscriber grain, and safe reload behavior for a dataset with no reliable prior baseline
> to validate against. At UNITE HERE, migrating a 20-year-old membership database across
> more than 30 local chapter instances meant building repeatable validation scripts that
> checked for record count mismatches, broken relationships, and schema inconsistencies
> before any release went through. When I designed the storage layer for CBA Clock, I chose
> MinIO specifically because it kept the system interoperable and ecosystem-agnostic, which
> is the same principle Iceberg formalizes at the table format level. Incremental
> processing, schema consistency, overwrite safety, manifest tracking, and replay and
> recovery workflows are not concepts I am approaching for the first time. I am actively
> building fluency with Iceberg and Delta Lake because they give formal structure to
> patterns I have already been enforcing by hand.

*No claims extracted.*

---

## Data Engineer / Airflow
*hash: 0613ef920ff8...*  

**Paragraph:**
> For CBA Clock, my contract intelligence application for unions, I built and own a
> production Airflow pipeline that runs 8 tasks in strict sequence to take a collective
> bargaining agreement from raw PDF to structured, queryable data. The DAG, `cba_pipeline`,
> handles download and OCR extraction with a fallback for degraded scans, a quality
> checkpoint before any further processing, section parsing against a labeled taxonomy, bulk
> upsert into Elasticsearch, and a Claude-powered deadline extraction step that fires only
> against sections tagged as grievance procedure, arbitration, or contract term. Cost
> control is built into the workflow: before triggering a run, I check the section inventory
> to see exactly how many sections will hit the Claude API, and I run 2 to 4 contracts at a
> time. The whole stack runs in Docker Compose with Airflow 3.2.1, PostgreSQL,
> Elasticsearch, MinIO, and a FastAPI backend that can trigger the DAG directly over the
> internal Docker network, so a contract can go from upload to structured timing rules in a
> single API call.

*No claims extracted.*

---

## Data Engineer / precision and ownership
*hash: ebc77cfb0d12...*  

**Paragraph:**
> At UNITE HERE, I was assigned the full desk audit of the Canadian local because precision
> was the requirement and there were a lot of details to get exactly right. The Canadian
> local carried the most complicated dues structure in the entire international union, with
> different dues, fees, funds, and contributions all splitting into different GL accounts,
> and my job was to document and replicate that process completely so the new membership
> system could be configured to match it exactly. Two colleagues with decades more dues
> processing experience made that trip with me, and they were generous enough to say I
> remembered more details exactly than either of them.

*No claims extracted.*

---

## Data Engineer / Enterprise dashboard and BI tool
*hash: 9e844a3df986...*  

**Paragraph:**
> At UNITE HERE, I built and owned custom BI reports and dashboards in SSRS, Power BI, and
> Sisense, delivered across at least 40 locals throughout the entire international union.
> The audience ranged from administrative staff in individual locals to top leadership of
> the international union and local presidents, secretary treasurers, and lead financial
> staff. These were not informational reports sitting in a folder somewhere. They drove
> strategy at the leadership level and gave financial and membership staff the visibility
> they needed to audit, operate, and stay healthy. Sisense in particular is a more primitive
> and harder tool to work with than what most engineers reach for, and getting clean,
> reliable output out of it for that audience required real work. I have also worked with
> Looker in a reporting context at Roku. Across all of it, the job was the same: figure out
> what someone in a specific seat needs to understand, and build the structure that puts it
> in front of them.

*No claims extracted.*

---

## Data Engineer / Training and enablement of data
*hash: cb2b3e9c285f...*  

**Paragraph:**
> At UNITE HERE, I ran training and documentation as a standing part of my role alongside
> every other responsibility I carried. I trained organizing staff on secure data collection
> and how to use our data systems, and I trained leadership on how to run their campaigns
> effectively with data. For the Canadian local's desk audit, I wrote two versions of the
> documentation: one I used as requirements and acceptance criteria for the system, and a
> separate one I built as a baseline for Grace, the dues processor, so she could operate the
> workflow on her own. When the official application documentation from the union's training
> staff proved too hard for membership staff to follow, I rewrote it. The original was
> modular, organized by feature rather than by how staff actually worked end-to-end, and the
> result was many pages that were not logically ordered and hard to follow. I found that
> what staff actually needed was less heavy on pictures and explanations and more of a
> workflow guide. I wrote versions that reflected how the work actually moved through the
> applications.

*No claims extracted.*

---

## Data Engineer / Training and enablement of data
*hash: 9cf822da55a6...*  

**Paragraph:**
> At BritBox, I owned the subscriber reporting that told senior leadership whether the
> product was working. These were the numbers that showed how many subscribers the company
> was gaining from ad campaigns, series premieres, and offers like bundles, discounted
> memberships, and premium tier exclusives, and how well the business was retaining
> subscribers when it raised prices or introduced friction in the app. The CFO, CTO, and CEO
> read them every month. I owned the data model, the pipeline, the validation, and the
> delivery, and I performed the QA so thoroughly that by the time the numbers reached Carl
> for review, he trusted they had to be right.

*No claims extracted.*

---

## Data Engineer / Training and enablement of data
*hash: 498d04a582ad...*  

**Paragraph:**
> At BritBox, I worked directly with the CTO and a Finance manager to get the business logic
> right for subscriber metrics, and the logic was genuinely hard because Finance and data
> needed different things from the same numbers. The alignment on what the metrics should
> capture was there, but Finance had their own way of breaking down calculations for gifts,
> and their reporting date structure for free trials and payments was slightly different
> from how data wanted to report it. My job was to make both possible and clear inside the
> same data model and calculations, so neither side had to compromise on what they needed to
> see.

### Claim 1  [REJECTED] ❌ (Claim overstates agency — the source shows the person reconciled existing requirements from Finance and data, not determined what the metrics should capture)
> At BritBox, I owned the subscriber metrics logic and determined what the numbers should capture before building the data model

*Contexts: employer: BritBox*

- Worked directly with the CTO and Finance manager to align on business logic for subscriber metrics
  - Finance and data needed different things from the same numbers
  - Finance had their own way of breaking down calculations for gifts
  - Finance's reporting date structure for free trials and payments was slightly different from how data wanted to report it
- Built a single data model and calculation system that made both Finance and data reporting possible without compromise
  - Made both possible and clear inside the same data model and calculations
  - Neither side had to compromise on what they needed to see

### Claim 2  [PENDING] ✅
> I work backwards from what different stakeholders need to understand into a data model that serves all of them without forcing trade-offs

- Reconciled Finance and data's different requirements for the same metrics by understanding each side's calculation logic and reporting structure
  - Finance had their own way of breaking down calculations for gifts
  - Finance's reporting date structure for free trials and payments was slightly different from how data wanted to report it
  - The alignment on what the metrics should capture was there, but the breakdown and structure differed

**Conclusion:** This is work where the technical decisions ARE the domain decisions — you can't separate the data model from the business logic, and getting it right requires understanding what each stakeholder actually needs to see and why, then building something that doesn't force anyone to compromise.

---

## Data Engineer / Training and enablement of data
*hash: 6cebdbcd145f...*  

**Paragraph:**
> At Universe, I introduced dbt and connected it to BigQuery to build a transformation layer
> that could turn inconsistent external provider data into reliable, application-ready
> models. The raw provider files came in with different column names, missing fields, type
> mismatches, and fields that needed to be combined before they matched the application
> model, so the first decision was to normalize everything into Parquet in GCS before trying
> to model it. The dbt work was about making the transformation step explicit, testable, and
> maintainable: staging models organized by source system, ref() dependencies to control
> execution order, YAML tests, seeds for controlled values, macros for reusable
> transformation logic, and scheduled jobs connected to BigQuery via service account. The
> central design decision was to make column mapping metadata-driven. File metadata from
> Firebase included a mapping config describing how source columns should map to destination
> fields, and the transformation layer had to handle one-to-one mappings, constant fills,
> type coercion, formatting functions, and one-to-many and many-to-one relationships between
> source and model fields. The staging layer did the first pass of cleanup, renaming,
> casting, and categorization, while heavier business logic lived downstream in application-
> ready models. Universe's product depended on voter files, shapefiles, GPS data, and
> campaign data being parsed and served correctly for maps and field workflows, so the
> transformation layer had to make the data usable in the live application, and the dbt
> architecture was how we got there reliably.

### Claim 1  [PENDING] ✅
> At Universe, I introduced dbt and connected it to BigQuery to build a transformation layer that could turn inconsistent external provider data into reliable, application-ready models

*Contexts: employer: Universe*

- Raw provider files came in with different column names, missing fields, type mismatches, and fields that needed to be combined before they matched the application model
- First decision was to normalize everything into Parquet in GCS before trying to model it
- Built staging models organized by source system, ref() dependencies to control execution order, YAML tests, seeds for controlled values, macros for reusable transformation logic, and scheduled jobs connected to BigQuery via service account

### Claim 2  [PENDING] ✅
> At Universe, I made the central design decision to make column mapping metadata-driven

*Contexts: employer: Universe*

- File metadata from Firebase included a mapping config describing how source columns should map to destination fields
- The transformation layer had to handle one-to-one mappings, constant fills, type coercion, formatting functions, and one-to-many and many-to-one relationships between source and model fields

### Claim 3  [PENDING] ✅
> I work backwards from what the application needs to understand into the data model that produces it, separating cleanup and renaming work from business logic

- The staging layer did the first pass of cleanup, renaming, casting, and categorization, while heavier business logic lived downstream in application-ready models
  - This separation made the transformation step explicit, testable, and maintainable

### Claim 4  [PENDING] ✅
> I had accountability for making data usable in a live application where the technical decisions ARE the domain decisions — you can't separate them

*Contexts: employer: Universe*

- Universe's product depended on voter files, shapefiles, GPS data, and campaign data being parsed and served correctly for maps and field workflows
  - The transformation layer had to make the data usable in the live application, and the dbt architecture was how we got there reliably

**Conclusion:** This is data where the source schema is controlled by third parties and inconsistent — getting to trustworthy output requires understanding what each provider is actually sending before you can model it, and then making the transformation logic explicit enough that it can be tested and maintained as the application depends on it.

---

## Data Engineer / Python and SQL proficiency
*hash: 0039ce2273b0...*  

**Paragraph:**
> At BritBox, the largest and most complex projects I owned — subscriber metrics, the Amazon
> daily event data jobs, the ATI migration — were top-to-bottom Python implementations
> running in Glue, with SQL doing the modeling and transformation work underneath. Python
> and SQL are the two languages I am most deeply rooted in, and that holds across every
> context I work in: production data engineering, personal projects like CBA Clock, and
> open-source builds like a cover letter writer and document library assistant. Beyond the
> core languages, I have an extensive understanding of the broader ecosystem — I use
> Pydantic and Mypy for governance and type safety, boto3 for AWS integrations, and pyarrow
> for working directly with columnar data. I work across the full stack of tools where they
> are the right fit, but the foundation is always Python and SQL.

### Claim 1  [PENDING] ✅
> At BritBox, I owned the largest and most complex projects — subscriber metrics, the Amazon daily event data jobs, the ATI migration — as top-to-bottom Python implementations running in Glue

*Contexts: employer: BritBox*

- subscriber metrics project owned end-to-end in Python on Glue
- Amazon daily event data jobs owned end-to-end in Python on Glue
- ATI migration owned end-to-end in Python on Glue

### Claim 2  [PENDING] ✅
> I use SQL for modeling and transformation work underneath the Python layer

*Contexts: employer: BritBox*

- SQL doing the modeling and transformation work in the largest projects at BritBox

### Claim 3  [PENDING] ✅
> Python and SQL are the two languages I am most deeply rooted in across every context I work in

- production data engineering at BritBox uses Python and SQL as foundation
- personal projects like CBA Clock built in Python and SQL
- open-source builds like a cover letter writer and document library assistant use Python and SQL

### Claim 4  [PENDING] ✅
> I have extensive understanding of the broader Python ecosystem — Pydantic and Mypy for governance and type safety, boto3 for AWS integrations, pyarrow for working directly with columnar data

- use Pydantic and Mypy for governance and type safety
- use boto3 for AWS integrations
- use pyarrow for working directly with columnar data

### Claim 5  [PENDING] ✅
> I work across the full stack of tools where they are the right fit, but the foundation is always Python and SQL

- tool selection is driven by fit to the problem, not default choice

---

## Data Engineer / Python and SQL proficiency
*hash: a9bffd60486b...*  

**Paragraph:**
> At UNITE HERE, I trained organizing staff on data systems by first learning what each
> organizer actually needed before teaching them anything. Comfort with applications varied,
> and so did the scale of what they were tracking — some organizers needed to follow every
> house visit, every conversation, every step toward a committee or a member voting. I
> figured out where each person was starting from, then walked them through linearly what
> they needed to do to reach their goal, and asked questions that helped them walk through
> their own thinking. If an organizer couldn't track their campaign, they had no idea how
> close they were to winning or losing it, and that meant they weren't organizing to win.

### Claim 1  [PENDING] ✅
> I trained organizing staff on data systems by first learning what each organizer actually needed before teaching them anything

*Contexts: employer: UNITE HERE*

- Comfort with applications varied, and so did the scale of what they were tracking — some organizers needed to follow every house visit, every conversation, every step toward a committee or a member voting
- I figured out where each person was starting from, then walked them through linearly what they needed to do to reach their goal
- I asked questions that helped them walk through their own thinking

### Claim 2  [REJECTED] ❌ (This is a general principle stated as fact, not a specific claim about what this person did, how they work, or who they are — it needs to be reframed as a lesson learned, approach, or disposition.)
> I understand that if an organizer couldn't track their campaign, they had no idea how close they were to winning or losing it, and that meant they weren't organizing to win

*Contexts: employer: UNITE HERE*

- Campaign tracking is the difference between knowing your position in a campaign and being blind to it
  - Without tracking, organizers cannot assess proximity to victory or defeat
  - This directly affects whether organizing is effective

**Conclusion:** This is work where the technical system only matters if it serves the actual decision-making need of the person using it — and understanding that need first, before any instruction, is what makes training effective.

---

## General / Opening
*hash: c3fa00c31ca3...*  

**Paragraph:**
> I am a data engineer and developer with a nontraditional path through digital
> arts, teaching, nonprofit consulting, labor data, and production engineering. I am drawn to
> messy, consequential problem spaces where people are doing hard work with tools and data systems
> that are often older, fragmented, or under-governed.

### Claim 1  [PENDING] ✅
> I am drawn to messy, consequential problem spaces where people are doing hard work with tools and data systems that are often older, fragmented, or under-governed

- nontraditional career path through digital arts, teaching, nonprofit consulting, labor data, and production engineering

### Claim 2  [PENDING] ✅
> I have worked across domains where data and tools directly affect how people do consequential work

- experience in nonprofit consulting, labor data, and production engineering contexts

**Conclusion:** This person is oriented toward work where technical decisions have real consequences for people and organizations, and where the systems involved are often constrained by legacy, fragmentation, or governance gaps — not greenfield problems.

---

## General / Opening
*hash: 140ea0d9919c...*  

**Paragraph:**
> I discovered over my career that I am quite good at understanding people's needs even when they
> are not speaking technical language, that I can ask good questions, and deliver data with
> exacting precision. I can think end to end — the problem space, not just whether specific
> numbers are right.

*No claims extracted.*

---

## General / Strengths
*hash: 92c8eb9ee34c...*  

**Paragraph:**
> My strength is making clarity out of ambiguity: asking the right questions, understanding what
> people need from their data, and building durable infrastructure that makes those needs
> operational.

*No claims extracted.*

---

## General / Strengths
*hash: 32ab957f6dff...*  

**Paragraph:**
> I care deeply about precision, traceability, and integrity, especially when data is being used
> to support organizing, public-interest work, media, education, or communities that need better
> systems.

### Claim 1  [REJECTED] ❌ (Pure assertion of values without specific work history, employer context, or provable pattern to substantiate the claim.)
> I care deeply about precision, traceability, and integrity, especially when data is being used to support organizing, public-interest work, media, education, or communities that need better systems


---

## General / Strengths
*hash: d1bf474f282d...*  

**Paragraph:**
> I am strongest in ambiguous, business-rule-heavy data environments where source systems are
> complex and the output has to be trusted.

### Claim 1  [PENDING] ✅
> I am strongest in ambiguous, business-rule-heavy data environments where source systems are complex and the output has to be trusted


---

## General / Strengths
*hash: 0ab6f5e093a5...*  

**Paragraph:**
> One of my strongest assets is that I bring a strong data quality, governance, and modeling
> skillset to data platform work.

*No claims extracted.*

---

## General / Strengths
*hash: 5bdd71845283...*  

**Paragraph:**
> I am especially strong at building the structure underneath analytics, data products, and AI
> systems: definitions, models, validation, lineage, observability, access patterns, review
> workflows, documentation, and operational discipline.

### Claim 1  [PENDING] ✅
> I build the structure underneath analytics, data products, and AI systems: definitions, models, validation, lineage, observability, access patterns, review workflows, documentation, and operational discipline

- owns foundational infrastructure across: definitions, models, validation, lineage, observability, access patterns, review workflows, documentation, operational discipline

### Claim 2  [PENDING] ✅
> I am especially strong at building structure underneath systems rather than the systems themselves

- focus is on foundational layers: how data is defined, modeled, validated, observed, accessed, reviewed, documented, and operationalized

---

## General / Strengths
*hash: 392832fe54a6...*  

**Paragraph:**
> I am good at turning very limited direction into well-defined data work.

### Claim 1  [PENDING] ✅
> I am good at turning very limited direction into well-defined data work


---

## General / Strengths
*hash: e1a86878113f...*  

**Paragraph:**
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users do with the product. I think like a full-stack developer in terms of solution design and workflow.

*No claims extracted.*

---

## General / Closing
*hash: 55677dd9fb98...*  

**Paragraph:**
> I am most excited by work where careful engineering can make organizations more accountable,
> resilient, and effective — especially in spaces where better tooling can help good people do
> their work with more clarity and confidence.

*No claims extracted.*

---

## Data Engineer / Opening
*hash: 933f2f025965...*  

**Paragraph:**
> I am a data engineer, builder, and systems thinker with a nontraditional path through digital
> arts, teaching, nonprofit consulting, labor data, and production engineering. My strongest work
> has been at the intersection of infrastructure, analytics, and applied problem-solving — in
> environments where the source systems are complex, the requirements are ambiguous, and the
> output has to be trusted.

*No claims extracted.*

---

## Data Engineer / Opening
*hash: 771c412030a7...*  

**Paragraph:**
> I am drawn to messy, consequential problem spaces where people are doing hard work with tools
> and data systems that are often older, fragmented, or under-governed. My career has repeatedly
> brought me back to mission-driven data work: union data, political data, membership and finance
> reporting, voter roll data, and production pipelines where reliability is not optional.

*No claims extracted.*

---

## Data Engineer / BritBox Watch Events
*hash: 2aad546014da...*  

**Paragraph:**
> I am strongest in ambiguous, business-rule-heavy data environments where source systems are
> complex and the output has to be trusted absolutely. At BritBox, I was the only dedicated data
> engineer for almost two years and owned a business-critical AWS/Spark/PySpark pipeline for
> high-volume streaming viewership data. I inherited nominal and partially inaccurate
> documentation that had originally been produced by a former consultancy, so a significant part
> of my role was validating the logic, identifying where it broke down, and refining the session
> timing and duration calculations so the resulting data would be trustworthy. The raw data was
> stored in Redshift as an external table with more than 800 columns and included duplicates,
> late-arriving records, timing edge cases, and session behavior that had to be handled carefully
> to produce usable watch metrics. One of the hardest issues was that session IDs reset at
> midnight, so events had to be stitched across that boundary to calculate watch duration
> correctly. Because of the data volume involved, I also had to teach myself more advanced Spark
> concepts in PySpark in order to handle the scale efficiently. I owned the solution end to end:
> figuring out how the raw events behaved, deciding how the pipeline should model sessions and
> watch duration, building the Glue/Spark replacement, and validating that the output was correct
> enough to support core reporting. The new Spark solution ran in a fraction of the time, handled
> the source volume much better, and stopped the frequent failures we had seen with the prior
> process. It also made the logic behind the watch metrics explicit and supportable.

### Claim 1  [PENDING] ✅
> At BritBox, I owned a business-critical AWS/Spark/PySpark pipeline for high-volume streaming viewership data end to end

*Contexts: employer: BritBox*

- I was the only dedicated data engineer for almost two years
- I figured out how the raw events behaved, decided how the pipeline should model sessions and watch duration, built the Glue/Spark replacement, and validated that the output was correct enough to support core reporting
- The new Spark solution ran in a fraction of the time, handled the source volume much better, and stopped the frequent failures we had seen with the prior process

### Claim 2  [PENDING] ✅
> I work in data environments where source systems are complex and the output has to be trusted absolutely, validating logic and refining calculations so the resulting data is trustworthy

*Contexts: employer: BritBox*

- I inherited nominal and partially inaccurate documentation from a former consultancy and had to validate the logic and identify where it broke down
- The raw data was stored in Redshift as an external table with more than 800 columns and included duplicates, late-arriving records, timing edge cases, and session behavior that had to be handled carefully to produce usable watch metrics
  - Session IDs reset at midnight, so events had to be stitched across that boundary to calculate watch duration correctly
  - Because of the data volume involved, I had to teach myself more advanced Spark concepts in PySpark in order to handle the scale efficiently
- The new solution made the logic behind the watch metrics explicit and supportable

### Claim 3  [PENDING] ✅
> I am strongest in ambiguous, business-rule-heavy data environments where source systems are complex and the output has to be trusted absolutely

- At BritBox, I refined session timing and duration calculations in a high-volume streaming viewership pipeline where the raw data included duplicates, late-arriving records, timing edge cases, and session behavior that had to be handled carefully
  - Session IDs reset at midnight, so events had to be stitched across that boundary to calculate watch duration correctly

**Conclusion:** This is data where instrumentation is imperfect, the schema is controlled by a third party, and getting to trustworthy output requires understanding what the source is actually recording before you model anything.

---

## Data Engineer / BritBox DynamoDB and Business Logic
*hash: 990d19ff2977...*  

**Paragraph:**
> I also built a DynamoDB-based logging system for BritBox's event stream pipeline — one of the most business-critical data systems the company operated. I built it with proper structure, observability, and documented logic because I understood what was depending on it. Over my time at BritBox I also worked out the business logic for much of the subscription metrics the company had been reporting on for years, and I replaced one of the most business-critical event stream pipelines single-handedly — improving the logic in the process.

### Claim 1  [PENDING] ✅
> At BritBox, I built a DynamoDB-based logging system for the event stream pipeline — one of the most business-critical data systems the company operated

*Contexts: employer: BritBox*

- Built the system with proper structure, observability, and documented logic
  - understood what was depending on it and built accordingly

### Claim 2  [PENDING] ✅
> At BritBox, I owned the business logic for much of the subscription metrics the company had been reporting on for years

*Contexts: employer: BritBox*

- Worked out the business logic for subscription metrics across the company's reporting

### Claim 3  [PENDING] ✅
> At BritBox, I replaced one of the most business-critical event stream pipelines single-handedly and improved the logic in the process

*Contexts: employer: BritBox*

- Owned the replacement of a critical pipeline end-to-end
  - improved the logic as part of the replacement

### Claim 4  [PENDING] ✅
> I build systems with proper structure, observability, and documented logic because I understand what depends on them

- Approach demonstrated across BritBox work on critical systems
  - DynamoDB logging system built with this discipline
  - understanding of downstream dependencies shapes how I build

---

## Data Engineer / BritBox Live Troubleshooting
*hash: 6b44253cecc6...*  

**Paragraph:**
> At BritBox, some of the most demanding work involved pipelines I inherited rather than built. One was a business-critical cron job running off an EC2 machine that failed repeatedly due to character limit violations on fields that upstream systems were supposed to gate, compounded by volume and file size issues. I had to diagnose failures in code I did not write, under deadline pressure, while keeping a job that fed core reporting running with nominal downtime. Owning reliability on a system you did not design — in production, with no dev buffer — sharpens how you think about observability, failure modes, and what it actually means to own a pipeline.

### Claim 1  [PENDING] ✅
> I owned reliability on a system I did not design — in production, with no dev buffer — and that sharpened how I think about observability, failure modes, and what it actually means to own a pipeline

*Contexts: employer: BritBox*

- Inherited a business-critical cron job running off an EC2 machine that failed repeatedly due to character limit violations on fields that upstream systems were supposed to gate, compounded by volume and file size issues
  - Had to diagnose failures in code I did not write, under deadline pressure
  - Kept a job that fed core reporting running with nominal downtime

### Claim 2  [PENDING] ✅
> I had accountability for data pipeline reliability at a level that is rare — owning a production system under deadline with no dev buffer, where I had to diagnose and fix inherited code I did not write

*Contexts: employer: BritBox*

- Business-critical cron job with repeated failures from upstream data quality issues (character limits, volume, file size) that I had to diagnose and stabilize without downtime
  - Code was inherited, not built by me
  - Failures were under deadline pressure
  - System fed core reporting — failure had direct business impact

**Conclusion:** This is work where you cannot separate the engineering from the accountability — you inherit a system that is already critical, you have to understand failure modes you did not create, and you learn what observability and ownership actually mean when there is no buffer between diagnosis and production impact.

---

## Data Engineer / BritBox Subscriber Reporting
*hash: 3cc377088fd9...*  

**Paragraph:**
> I worked on a month-end subscriber reporting pipeline where the existing model was closer to a
> Type 3 slowly changing dimension — it could capture some current and prior subscriber
> attributes, but it did not preserve a full history of state changes over time. When product
> introduced new recovery logic and we launched a premium tier, subscription status, plan type,
> recovery state, and effective dates all became more complex than the model could handle. The
> design change was to move toward an effective-dated subscriber history model, essentially a
> Type 2 slowly changing dimension. The model preserved each version of the subscriber record
> with effective start and end dates, which made it possible to reconcile churn, recovery,
> premium-tier reporting, and month-end subscriber counts against the customer state that was
> valid for the reporting period. The tradeoff was added complexity in the model and joins,
> because the reporting logic had to select the correct subscriber version for each reporting
> date. The benefit was that discrepancies became explainable: I could trace counts back to the
> customer statuses, state changes, effective dates, and business rules that produced them.

### Claim 1  [PENDING] ✅
> At my previous employer, I owned the month-end subscriber reporting pipeline and redesigned the dimensional model to handle increasing complexity in subscription state

*Contexts: employer: None*

- The existing Type 3 SCD model could capture some current and prior subscriber attributes but did not preserve a full history of state changes over time
- When product introduced new recovery logic and launched a premium tier, subscription status, plan type, recovery state, and effective dates all became more complex than the model could handle
- I redesigned the model toward an effective-dated subscriber history model (Type 2 SCD) that preserved each version of the subscriber record with effective start and end dates
  - This made it possible to reconcile churn, recovery, premium-tier reporting, and month-end subscriber counts against the customer state that was valid for the reporting period

### Claim 2  [PENDING] ✅
> I work backwards from what needs to be reported into a data model that makes those discrepancies explainable and traceable

- The tradeoff of the redesign was added complexity in the model and joins, because reporting logic had to select the correct subscriber version for each reporting date
  - The benefit was that discrepancies became explainable: I could trace counts back to the customer statuses, state changes, effective dates, and business rules that produced them

### Claim 3  [PENDING] ✅
> I had accountability for subscriber data integrity at a level where I needed to understand and model the full lifecycle of subscription state changes

*Contexts: employer: None*

- The reporting pipeline had to reconcile churn, recovery, premium-tier reporting, and month-end subscriber counts — each requiring precise understanding of when and why customer state changed
  - Subscription status, plan type, recovery state, and effective dates all became critical dimensions that had to be modeled correctly to produce trustworthy counts

**Conclusion:** This is data where business complexity — product changes, new recovery logic, new tiers — directly drives dimensional modeling decisions. Getting to trustworthy reporting requires understanding not just the current state but the full history of how and when that state changed, and building a model that makes those changes explicit and queryable.

---

## Data Engineer / UNITE HERE
*hash: c5bc812a63d3...*  

**Paragraph:**
> At UNITE HERE, I worked with dues, health fund, grievance, financial, membership, and PII data
> across many local union chapters. I was trusted to conduct desk audits of the union's most
> complex dues-processing workflows because I had the attention to detail, respect for existing
> process flow, and seriousness required to preserve how the work functioned while identifying
> what needed to change. I worked across many local chapters, maintaining relationships with
> local staff, gathering requirements, documenting issues, and translating operational needs into
> database changes, custom reports, SQL validation scripts, and user-facing workflows.

### Claim 1  [PENDING] ✅
> I was trusted to conduct desk audits of the union's most complex dues-processing workflows because I had the attention to detail, respect for existing process flow, and seriousness required to preserve how the work functioned while identifying what needed to change

*Contexts: employer: UNITE HERE*

- Worked with dues, health fund, grievance, financial, membership, and PII data across many local union chapters
- Conducted desk audits of complex dues-processing workflows
  - Required attention to detail and respect for existing process flow to preserve how the work functioned while identifying what needed to change

### Claim 2  [PENDING] ✅
> I worked across many local chapters, maintaining relationships with local staff, gathering requirements, documenting issues, and translating operational needs into database changes, custom reports, SQL validation scripts, and user-facing workflows

*Contexts: employer: UNITE HERE*

- Maintained relationships with local staff across many chapters
- Gathered requirements and documented issues from operational context
- Translated operational needs into database changes, custom reports, SQL validation scripts, and user-facing workflows

### Claim 3  [PENDING] ✅
> I had accountability for data integrity across sensitive union data—dues, health fund, grievance, financial, membership, and PII—where precision and trustworthiness were non-negotiable

*Contexts: employer: UNITE HERE*

- Worked with dues, health fund, grievance, financial, membership, and PII data where errors directly affect member benefits and union operations
  - This is data where the stakes are high—incorrect dues calculations affect member standing, health fund eligibility, and grievance processing

---

## Data Engineer / UNITE HERE
*hash: 88739a7f600b...*  

**Paragraph:**
> I examined systems and relationships on every level — from the challenges of organizer data
> entry on different devices with spotty internet access to the full desk audit of the most
> complex dues structure in the entire international union. UNITE HERE entrusted me with this
> sole responsibility.

### Claim 1  [PENDING] ✅
> I examined systems and relationships on every level — from the challenges of organizer data entry on different devices with spotty internet access to the full desk audit of the most complex dues structure in the entire international union

*Contexts: employer: UNITE HERE*

- Conducted analysis spanning organizer data entry workflows across devices with unreliable connectivity
- Performed full desk audit of the most complex dues structure in the entire international union

### Claim 2  [PENDING] ✅
> UNITE HERE entrusted me with this sole responsibility

*Contexts: employer: UNITE HERE*

- Owned the complete examination of systems and relationships across all organizational levels

---

## Data Engineer / UNITE HERE
*hash: 03a18b88be39...*  

**Paragraph:**
> My experience with highly skilled administrative staff processing dues and stringent financial
> reporting taught me how crucial it is for systems to support human beings' ability to review
> changes and trust the validity of their records.

### Claim 1  [PENDING] ✅
> I learned from working with highly skilled administrative staff processing dues and stringent financial reporting how crucial it is for systems to support human beings' ability to review changes and trust the validity of their records

- experience with administrative staff processing dues under stringent financial reporting requirements
  - the work involved financial record-keeping where accuracy and auditability were non-negotiable
  - the staff doing this work were highly skilled and needed systems that let them verify what had changed and why

**Conclusion:** Systems that serve financial and administrative work must be designed around human review and verification — not just correctness in the abstract, but the ability for skilled people to see what changed, understand why, and trust the record.

---

## Data Engineer / UNITE HERE
*hash: 7b3a43f03980...*  

**Paragraph:**
> The most serious data quality issue I worked on at UNITE HERE came during a migration of a
> 20-year-old membership database across more than 30 local chapter instances. Early in the
> migration, we found schema mismatches, missing records, duplicated data, and corrupted or
> inconsistent records that caused errors after deployment. The deeper issue was that each local
> had been allowed to evolve in isolation, with custom fields and local practices that did not
> map cleanly to a shared data model. To address it, I helped build repeatable SQL validation
> scripts and acceptance criteria that checked migrated tables for record count mismatches,
> missing required values, broken relationships, duplicates, and other inconsistencies before
> release. The more important design work was creating custom panels and data structures that
> aligned with the common data model while still giving locals a controlled place to store data
> specific to their own workflows. The tradeoff was allowing customization, but only inside a
> more governed structure.

### Claim 1  [PENDING] ✅
> At UNITE HERE, I owned the data quality strategy for a 20-year-old membership database migration across 30+ local chapter instances

*Contexts: employer: UNITE HERE*

- Found and had to resolve schema mismatches, missing records, duplicated data, and corrupted or inconsistent records that caused errors after deployment
  - Root cause was that each local had been allowed to evolve in isolation, with custom fields and local practices that did not map cleanly to a shared data model

### Claim 2  [PENDING] ✅
> I built repeatable SQL validation scripts and acceptance criteria that checked migrated tables before release

*Contexts: employer: UNITE HERE*

- Validation checked for record count mismatches, missing required values, broken relationships, duplicates, and other inconsistencies

### Claim 3  [PENDING] ✅
> I designed custom panels and data structures that aligned with a common data model while giving locals a controlled place to store data specific to their own workflows

*Contexts: employer: UNITE HERE*

- The design allowed customization, but only inside a more governed structure
  - This was the tradeoff: enabling local flexibility without sacrificing the integrity of the shared model

### Claim 4  [PENDING] ✅
> I had accountability for data integrity at a level that is rare — working on a migration where the source data itself was the constraint, not just the pipeline

*Contexts: employer: UNITE HERE*

- The migration required understanding and reconciling 20 years of divergent local practices and custom schema evolution before any code could be written
  - This is data where the organizational structure and local autonomy created the schema — getting to trustworthy output required understanding what each local was actually recording and why before modeling anything

**Conclusion:** This is data where the organizational structure and local autonomy created the schema — getting to trustworthy output required understanding what each local was actually recording and why before modeling anything. The technical solution had to be inseparable from the governance solution.

---

## Data Engineer / CBA Clock
*hash: 7f7353c0634b...*  

**Paragraph:**
> CBA Clock is my independently designed AI-assisted contract intelligence application for unions.
> The app scans PDF copies of collective bargaining agreements and converts key contract
> provisions into structured JSON records that can be reviewed, corrected, and approved by users
> before being used operationally. The initial focus is on time-sensitive contract rules:
> grievance filing deadlines, escalation windows, arbitration deadlines, contract expiration
> dates, negotiation notice periods, and reopener windows. Once extracted and verified, these
> rules can be used to generate custom calendars, reminders, and timeline views so union officers
> can track which contractual deadlines apply to specific grievances and upcoming bargaining
> events. I am building it around structured extraction, retrieval, user verification, and a real
> data model because I do not think AI output is useful until someone can review it, trace it,
> and decide whether it belongs in the workflow.

*No claims extracted.*

---

## Data Engineer / CBA Clock
*hash: c728ba860c1b...*  

**Paragraph:**
> Union officers may need to track multiple active grievances under different versions of a
> contract, with different deadlines, escalation rules, and procedural requirements. Missing a
> filing or escalation window can have serious consequences, so the app is designed around
> human-verified AI extraction rather than fully automated legal interpretation. Longer term, I
> am interested in adding comparative analysis features that allow unions to evaluate contract
> language across agreements — identifying missing protections, comparing grievance procedures or
> reopener language, and helping unions understand where current language may be weaker than
> language they have secured elsewhere. The goal is to turn dense contract language into
> structured, auditable, time-aware data that helps unions preserve rights, avoid missed
> deadlines, and prepare more strategically for negotiations. I built it because CBAs are some of
> the most important documents a union possesses, and I wanted to create something that could
> support more critical analysis, more effective organization, and more intentional planning
> around case building.

*No claims extracted.*

---

## Data Engineer / Current Projects
*hash: 44c31c2ffc1f...*  

**Paragraph:**
> I am currently building RAG and agentic applications, and I am especially interested in
> applying those patterns in environments where accuracy and human judgment are especially consequential. One project uses Claude to read over a GitHub repository, targets AWS Glue jobs with certain build
> patterns, and grades each job's capacity and probability of failure based on forecasted data
> volumes. One of the features I am most excited about is evaluating, based on how data is read
> and updated, a forecasted point at which a failure might become likely — and making a
> recommendation about when to increase resources or when to have the job refactored. I am
> focused on how data governance and data quality enforced by data engineering flow through AI
> applications.

### Claim 1  [PENDING] ✅
> I build RAG and agentic applications in environments where accuracy and human judgment are especially consequential

- One project uses Claude to read over a GitHub repository, targets AWS Glue jobs with certain build patterns, and grades each job's capacity and probability of failure based on forecasted data volumes

### Claim 2  [PENDING] ✅
> I evaluate how data is read and updated to forecast a point at which a failure might become likely, and make recommendations about when to increase resources or when to have the job refactored

*Contexts: project: AWS Glue job capacity and failure forecasting*

- The feature evaluates, based on how data is read and updated, a forecasted point at which a failure might become likely
  - Makes a recommendation about when to increase resources or when to have the job refactored

### Claim 3  [PENDING] ✅
> I am focused on how data governance and data quality enforced by data engineering flow through AI applications

- This orientation shapes what I build — the connection between upstream data engineering decisions and downstream AI system reliability

**Conclusion:** This work sits at the intersection of data engineering rigor and AI system design — where the quality and governance decisions made upstream directly determine whether an AI application can make trustworthy recommendations in high-stakes contexts.

---

## Data Engineer / LLM and AI Judgment
*hash: 3bc17be579c2...*  

**Paragraph:**
> I am actively building AI tools, and I have a skeptical but optimistic view of LLMs because I
> see both their value and the ways they can create friction when requirements are specific. LLMs
> often need more context and constraint than people expect. They can miss, override, or
> inconsistently apply requirements while still producing fluent output that looks plausible.
> This is especially risky with large general-purpose models trained on broad, opaque datasets,
> where publishers often do not make model weights or training data public. For data engineers,
> the infrastructure around the model is critical. Governance, observation, testing, and
> evaluation are imperative when doing anything with AI related to data. A product needs to
> control what context the model receives, what data it can access, how output quality is
> checked, and how failures are caught before they affect the user. Otherwise, an LLM-powered
> product can easily become a system that looks helpful while making the human do more work to
> correct it.

*No claims extracted.*

---

## Data Engineer / LLM and AI Judgment
*hash: 616dca5cb0b2...*  

**Paragraph:**
> One of the most difficult parts of integrating AI into realms of work and documents is that it
> creates ambiguity around validity, so human-in-the-loop review is especially important.

### Claim 1  [REJECTED] ❌ (Pure assertion of belief with no specific evidence, employer, project, or work pattern to substantiate it)
> I recognize that integrating AI into work and documents creates ambiguity around validity, making human-in-the-loop review especially important

- AI integration introduces validity ambiguity that requires human oversight

---

## Data Engineer / LLM and AI Judgment
*hash: dc05890b533a...*  

**Paragraph:**
> In engineering we are faced with systems interoperability problems that are complicated by
> integrating new technologies that are also evolving. This realm of complexity and how humans
> can interact and engage with technologies as part of a well designed data system — understanding
> how work can be improved and how analysis and decision making can be something that the
> technology exposes and assists — is where I want to be building.

### Claim 1  [PENDING] ✅
> I am drawn to work where the technical design of data systems directly enables how humans interact with technology and make decisions

- I want to build in the space where systems interoperability problems meet evolving technologies, and where understanding how work can be improved means designing for how analysis and decision-making are exposed and assisted by the technology itself

### Claim 2  [PENDING] ✅
> I find meaning in designing data systems where the technical choices are inseparable from how humans will actually use them to understand and decide

- The realm of complexity I want to work in is understanding how humans can interact and engage with technologies as part of a well-designed data system
  - This includes recognizing that integrating new and evolving technologies creates interoperability problems that require thinking about the human side of the system, not just the technical side

**Conclusion:** This person is oriented toward work where technical architecture and human decision-making are treated as a unified problem — where you cannot separate the engineering from the usability, and where the goal is to make analysis and decision-making something the system actively enables rather than just provides raw capability for.

---

## Data Engineer / LLM and AI Judgment
*hash: 7d991e355fc6...*  

**Paragraph:**
> My dream for this technology is that it can produce meaningful learning experiences as well as
> encourage inquiry and deeper thinking.

*No claims extracted.*

---

## Data Engineer / LLM and AI Judgment
*hash: cc618bf7e243...*  

**Paragraph:**
> As generative AI companies accelerate towards higher levels of compute, much of what they are
> claiming and advertising as "intelligence" is really aspirational — particularly because the
> breadth of what these models claim to do makes precise alignment with a user's specific
> constraints and requirements unreliable. The way these systems classify and route prompts into
> tools or skills is a further limiting factor that operates opaquely — it shapes what the model
> can actually do with a given request in ways the user has no visibility into or control over.

### Claim 1  [PENDING] ✅
> The opacity of how generative AI systems classify and route prompts into tools shapes what the model can actually do with a given request in ways the user has no visibility into or control over

- Prompt classification and routing operates as a limiting factor that is opaque to users
  - Users have no visibility into how prompts are being classified
  - Users have no control over the routing decisions that determine what tools or skills are available to a given request

### Claim 2  [REJECTED] ❌ (Pure assertion about technology/industry, not a claim about what this person did, owns, approaches, or is characterized by — cannot substantiate with evidence from their work history)
> Much of what generative AI companies are claiming and advertising as 'intelligence' is aspirational rather than reliably delivered

- The breadth of what these models claim to do makes precise alignment with a user's specific constraints and requirements unreliable

**Conclusion:** This is a domain where the gap between marketing claims and actual, reliable capability — particularly around constraint satisfaction and user control — creates a fundamental trust problem that engineering needs to address directly.

---

## Data Engineer / Worker and Teammate
*hash: b93112bf9450...*  

**Paragraph:**
> People who have worked with me know me as a forward thinker and a creative thinker. The last
> few years I have done serious work largely on my own — proposing architecture, owning decisions,
> debugging what broke, and advancing through honest analysis of what I built and why. I very
> much enjoy building relationships with people and understanding their needs around data, and I
> am ready to work somewhere with strong engineers around me where the collaboration and feedback
> match the level of work I am doing and want to do.

*No claims extracted.*

---

## Data Engineer / Worker and Teammate
*hash: c46c8f29eb78...*  

**Paragraph:**
> I am good at honing in on the questions and concerns people most want to get at, especially
> when the existing system is hard to explain or the business rules are still taking shape.

*No claims extracted.*

---

## Data Engineer / Worker and Teammate
*hash: 779ad2f88500...*  

**Paragraph:**
> I have spent much of my career in roles where I wore a lot of hats and had to coordinate
> information with stakeholders who were not always technical and translate their needs into work.
> I have worked closely with BI, analytics, and engineering teams, and I have experience in
> front-end work, UX design, testing, and evaluation. I take intense pride in data integrity.

*No claims extracted.*

---

## Data Engineer / Worker and Teammate
*hash: 96fb0baace76...*  

**Paragraph:**
> I bring rigorous documentation, quality checks, and scalability thinking to my work regardless of whether they are formally required — and I advocate for those standards on the work around me. At BritBox, where the engineering culture did not prioritize documentation, ticketing, or quality review, I documented my own changes, ran validation, raised concerns about design and scalability decisions, and continued to do so even when those concerns were not always taken up — because I understood what the pipelines were supporting and who was depending on the output.

### Claim 1  [PENDING] ✅
> I bring rigorous documentation, quality checks, and scalability thinking to my work regardless of whether they are formally required

- At BritBox, where the engineering culture did not prioritize documentation, ticketing, or quality review, I documented my own changes and ran validation

### Claim 2  [PENDING] ✅
> I advocate for standards on the work around me even when those concerns are not always taken up

*Contexts: employer: BritBox*

- I raised concerns about design and scalability decisions and continued to do so even when those concerns were not always taken up

### Claim 3  [PENDING] ✅
> I understood what the pipelines were supporting and who was depending on the output

*Contexts: employer: BritBox*

- This understanding motivated me to maintain documentation, validation, and raise scalability concerns despite cultural resistance
  - The pipelines had downstream dependents whose needs justified the rigor even when not formally required

### Claim 4  [PENDING] ✅
> I had accountability for data integrity and pipeline reliability at a level that required me to act independently of organizational process

*Contexts: employer: BritBox*

- I maintained standards unilaterally — documentation, validation, and design review — in an environment that did not enforce them
  - This was not a formal responsibility but a professional obligation I recognized based on understanding the downstream impact

**Conclusion:** This is someone who grounds rigor in purpose — not in process or credit, but in understanding who depends on the work and what they need to trust it. That orientation persists even when the organization doesn't reinforce it.

---

## Data Engineer / Mission-Driven Work
*hash: 79508c9e791e...*  

**Paragraph:**
> My career has repeatedly brought me back to mission-driven data work, including union data,
> political data, membership and finance reporting, voter roll data, and stakeholder-facing
> systems.

### Claim 1  [PENDING] ✅
> My career has repeatedly brought me back to mission-driven data work

- Work across union data, political data, membership and finance reporting, voter roll data, and stakeholder-facing systems
  - Union data
  - Political data
  - Membership and finance reporting
  - Voter roll data
  - Stakeholder-facing systems

### Claim 2  [PENDING] ✅
> I am drawn to work where data serves organizational accountability and mission clarity

- Pattern of choosing roles in mission-driven contexts: unions, political organizations, membership organizations, voter data

---

## Data Engineer / Mission-Driven Work
*hash: fca6b17d67a9...*  

**Paragraph:**
> My first job was with Gateways Program for Incarcerated Youth, where I managed a mentorship
> program for young men in a juvenile maximum-security facility. I later spent years working in
> the labor sector, where access to stable employment, dignity at work, and the practical needs
> of working people were always central to the mission.

### Claim 1  [PENDING] ✅
> I managed a mentorship program for young men in a juvenile maximum-security facility

*Contexts: employer: Gateways Program for Incarcerated Youth*

- Owned and operated mentorship program in high-security youth detention setting

### Claim 2  [PENDING] ✅
> I spent years working in the labor sector where access to stable employment, dignity at work, and the practical needs of working people were always central to the mission

- Sustained focus across labor sector roles on employment stability, worker dignity, and meeting practical needs of working people

### Claim 3  [PENDING] ✅
> I am oriented toward work where the practical needs and dignity of people — especially those with fewer resources or fewer choices — are the actual mission, not an afterthought

- Career pattern: mentorship work with incarcerated youth, then years in labor sector with worker dignity and access as core mission
  - This is not a stated conclusion but a disposition claim that emerges from the pattern described

---

## Data Engineer / Mission-Driven Work
*hash: 509e4b23b4b3...*  

**Paragraph:**
> Thinking together with a team on what tools and features can best serve the needs of people
> doing hard work on the ground is one of the things that has given me the greatest sense of
> purpose in my career.

*No claims extracted.*

---

## Data Engineer / Mission-Driven Work
*hash: add6158dba2b...*  

**Paragraph:**
> I have also managed large, ambiguous projects end to end: defining scope, translating
> requirements, leading technical conversations, building the implementation, and validating
> that the result was correct enough to support strategic decisions.

### Claim 1  [PENDING] ✅
> I manage large, ambiguous projects end to end: defining scope, translating requirements, leading technical conversations, building the implementation, and validating that the result was correct enough to support strategic decisions

- defining scope on ambiguous projects
- translating requirements across stakeholder groups
- leading technical conversations
- building the implementation
- validating that the result was correct enough to support strategic decisions

---

## Data Engineer / Mission-Driven Work
*hash: 04f61aa5a9ff...*  

**Paragraph:**
> I have owned large production data projects end to end, worked extensively in AWS-heavy
> environments, and built pipelines where reliability, governance, backfills, validation, and
> observability mattered.

### Claim 1  [PENDING] ✅
> I have owned large production data projects end to end

- Managed complete lifecycle of production data projects from conception through delivery

### Claim 2  [PENDING] ✅
> I worked extensively in AWS-heavy environments

- Deep experience building and operating systems on AWS infrastructure

### Claim 3  [PENDING] ✅
> I built pipelines where reliability, governance, backfills, validation, and observability mattered

- Designed and implemented pipelines with explicit attention to reliability, governance, backfills, validation, and observability as core requirements
  - Reliability: ensured pipelines could run consistently in production
  - Governance: implemented controls and accountability for data quality and access
  - Backfills: built capability to reprocess historical data when needed
  - Validation: integrated data quality checks into pipeline execution
  - Observability: instrumented pipelines to understand their behavior and catch failures

---

## Data Engineer / Mission-Driven Work
*hash: 0649ea9be276...*  

**Paragraph:**
> In my last role, I supported analytics and data science teams by building production pipelines,
> improving workflow reliability, and pushing for stronger validation, governance, and
> infrastructure-as-code practices.

### Claim 1  [PENDING] ✅
> I supported analytics and data science teams by building production pipelines

*Contexts: employer: None*

- built production pipelines for analytics and data science teams

### Claim 2  [PENDING] ✅
> I improved workflow reliability

*Contexts: employer: None*

- improved workflow reliability in production systems

### Claim 3  [PENDING] ✅
> I pushed for stronger validation, governance, and infrastructure-as-code practices

*Contexts: employer: None*

- advocated for and implemented stronger validation practices
- advocated for and implemented stronger governance practices
- advocated for and implemented infrastructure-as-code practices

---

## Data Engineer / Why This Role
*hash: 95094f0c529c...*  

**Paragraph:**
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users can do with a product or with their decisions. The engineering decisions closest to the data are the ones that determine whether the output is trustworthy, and trustworthy output is what I care about building. I want to be in roles where getting the data right is what makes the product work.

*No claims extracted.*

---

## Data Engineer / Values
*hash: ad0cd7f820ae...*  

**Paragraph:**
> I care about privacy and the open web because I have spent years in spaces where technology is
> supposed to help people learn, organize, build, and do hard work with more agency, but it so
> often does the opposite. I do not think the internet should be rooted in deceptive user
> agreements or corporations mining people's behavior, attention, and data while undervaluing the
> rights, contributions, and expertise of people.

### Claim 1  [PENDING] ✅
> I care about privacy and the open web because I have spent years in spaces where technology is supposed to help people learn, organize, build, and do hard work with more agency, but it so often does the opposite

- Direct observation across multiple contexts that technology frequently undermines rather than enables human agency in learning, organizing, building, and work

### Claim 2  [PENDING] ✅
> I do not think the internet should be rooted in deceptive user agreements or corporations mining people's behavior, attention, and data while undervaluing the rights, contributions, and expertise of people

- Conviction that current internet business models — built on deceptive terms, behavioral extraction, and undervaluation of user contribution — are fundamentally misaligned with human interests

**Conclusion:** This person's orientation toward privacy and open web work is rooted not in abstract principle but in concrete experience watching technology fail to serve the people it claims to help — and a clear-eyed view of why that failure happens.

---

## Data Engineer / Values
*hash: ec5a2768e3c5...*  

**Paragraph:**
> In my consulting work and years in the labor sector, I worked repeatedly with organizations running very old systems — schemas that had evolved in isolation across dozens of instances, data living in multiple legacy formats that did not interoperate, and migration risk that had been accumulating for years. I am genuinely drawn to those environments. Nasty data structures are puzzles, and the work of making fragmented, under-governed systems legible and reliable is the kind of problem I find most satisfying to solve.

*No claims extracted.*

---

## Senior Data Engineer / First DE / Sole DE
*hash: ef1c58a69ec1...*  

**Paragraph:**
> I am proud of the backend data work I shipped at Universe because it was my first data
> engineering role, at a seed-stage startup, as the first data engineer. There was no mature
> data infrastructure already in place, but the product depended on backend data being correct.
> Universe was building a data-driven down-ballot canvassing app, and my work powered the live
> application used to run campaigns. I parsed, modeled, and served voter files, shapefiles, GPS
> data, and campaign data so organizers could use maps and field workflows in the field. If that
> data was wrong, the product was wrong: the voter universe, the boundaries, the field workflow,
> and the organizer's trust in the tool. With guidance from the CEO, I worked from a strong
> TypeScript backend, learned generics and linting, improved the quality of my Python code,
> researched and suggested infrastructure, wrote RFCs, and helped build the data-serving layer
> the product needed almost entirely from scratch. We shipped quickly, my backend work ran in
> the live application, and the app was used in real campaigns.

### Claim 1  [PENDING] ✅
> At Universe, I owned the data-serving layer end-to-end as the first data engineer, building it almost entirely from scratch for a product where correctness was non-negotiable

*Contexts: employer: Universe*

- Parsed, modeled, and served voter files, shapefiles, GPS data, and campaign data so organizers could use maps and field workflows in the field
  - If that data was wrong, the product was wrong: the voter universe, the boundaries, the field workflow, and the organizer's trust in the tool
- Built the data-serving layer the product needed almost entirely from scratch at a seed-stage startup with no mature data infrastructure in place
- Shipped quickly with backend work running in the live application used in real campaigns

### Claim 2  [PENDING] ✅
> I approach data work by understanding what the product actually needs to be correct, then building infrastructure to serve that requirement

- At Universe, the product depended on backend data being correct, and I worked to ensure voter universe, boundaries, field workflow, and organizer trust were all grounded in reliable data
  - If that data was wrong, the product was wrong

### Claim 3  [PENDING] ✅
> I had accountability for data integrity at a level that is rare — in a seed-stage startup where the live application's reliability depended directly on my work

*Contexts: employer: Universe*

- As the first data engineer at Universe, there was no mature data infrastructure already in place, but the product depended on backend data being correct
  - The app was used in real campaigns

### Claim 4  [PENDING] ✅
> I learned to write solid, well-typed Python and TypeScript by working from a strong backend, learning generics and linting, and improving code quality under guidance

*Contexts: employer: Universe*

- With guidance from the CEO, I worked from a strong TypeScript backend, learned generics and linting, improved the quality of my Python code

### Claim 5  [PENDING] ✅
> I research infrastructure options, write RFCs, and help teams make deliberate choices about how to build data systems

*Contexts: employer: Universe*

- Researched and suggested infrastructure, wrote RFCs, and helped build the data-serving layer

**Conclusion:** This is data where the stakes are direct and visible — if the infrastructure fails, the product fails and organizers lose trust. That experience shaped how I think about data integrity and the relationship between backend correctness and product reliability.

---

## Backend Engineer / Opening
*hash: 97b633bd9187...*  

**Paragraph:**
> I am a data engineer and builder with production experience across the full stack — data pipelines, infrastructure, APIs, and user-facing data services. I think like a full-stack developer in terms of solution design: the data model, the API contract, the ingestion logic, and the serving layer are a connected system. At Universe, a seed-stage down-ballot canvassing application, I was the first dedicated data engineer and built the data infrastructure from the ground up — parsing voter files, GPS and shapefile data, and campaign data. I worked from a strong TypeScript backend with generics and linting, and built the Python data layer with nox and mypy. The data I built and served powered the core functionality of a live application used in real campaigns.

### Claim 1  [PENDING] ✅
> At Universe, I was the first dedicated data engineer and built the data infrastructure from the ground up

*Contexts: employer: Universe*

- parsed voter files, GPS and shapefile data, and campaign data
- built the Python data layer with nox and mypy alongside a strong TypeScript backend with generics and linting
  - worked from a strong TypeScript backend with generics and linting
  - built the Python data layer with nox and mypy
- the data I built and served powered the core functionality of a live application used in real campaigns

### Claim 2  [PENDING] ✅
> I think like a full-stack developer in terms of solution design: the data model, the API contract, the ingestion logic, and the serving layer are a connected system

- at Universe, designed and built data infrastructure where parsing, modeling, and serving were integrated into a live application's core functionality
  - the data model, the API contract, the ingestion logic, and the serving layer are a connected system

### Claim 3  [PENDING] ✅
> I have production experience across the full stack — data pipelines, infrastructure, APIs, and user-facing data services

*Contexts: employer: Universe*

- built data pipelines (voter files, GPS, shapefile, campaign data ingestion), infrastructure (Python data layer with nox and mypy), and served data to a live application

---

## Backend Engineer / Technical
*hash: 3063933e6857...*  

**Paragraph:**
> At Universe I worked from a strong TypeScript backend, learned generics and linting, improved the quality of my Python code, researched and suggested infrastructure, wrote RFCs, and helped build the data-serving layer the product needed almost entirely from scratch. I parsed voter files, GPS and shapefile data, and campaign data so organizers could use the field workflows in the field. If that data was wrong, the product was wrong. I have also built REST APIs in FastAPI, worked with Elasticsearch, Docker, and Terraform, and built data-centric applications where the model and serving logic are tightly integrated with the product.

### Claim 1  [PENDING] ✅
> At Universe, I built the data-serving layer the product needed almost entirely from scratch

*Contexts: employer: Universe*

- Parsed voter files, GPS and shapefile data, and campaign data so organizers could use the field workflows in the field
  - If that data was wrong, the product was wrong — data integrity was non-negotiable to product function

### Claim 2  [PENDING] ✅
> I work backwards from what the product needs to understand into the data model and serving logic that produces it

- Built data-centric applications where the model and serving logic are tightly integrated with the product
- Parsed voter files, GPS and shapefile data, and campaign data to enable specific field workflows
  - The data parsing was directly tied to what organizers needed to do in the field

### Claim 3  [PENDING] ✅
> At Universe, I had accountability for data integrity at a level where product correctness depended on it

*Contexts: employer: Universe*

- If that data was wrong, the product was wrong
  - This was the operating constraint for the data-serving layer built from scratch

### Claim 4  [PENDING] ✅
> I learned to write solid, well-typed Python and TypeScript, informed by strong backend practices

*Contexts: employer: Universe*

- Worked from a strong TypeScript backend, learned generics and linting, improved the quality of my Python code

### Claim 5  [PENDING] ✅
> At Universe, I researched and suggested infrastructure, wrote RFCs, and contributed to technical decision-making

*Contexts: employer: Universe*

- Researched and suggested infrastructure, wrote RFCs

### Claim 6  [PENDING] ✅
> I have built REST APIs in FastAPI, worked with Elasticsearch, Docker, and Terraform

*Contexts: employer: Universe*

- Built REST APIs in FastAPI, worked with Elasticsearch, Docker, and Terraform

**Conclusion:** This is data where the source schema is controlled by external systems (voter files, GPS, shapefiles, campaign data) and product correctness depends entirely on parsing and serving it correctly — getting to trustworthy output requires understanding what the source is actually recording before you model anything.

---

## Backend Engineer / Why This Role
*hash: 44dca902673a...*  

**Paragraph:**
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users do with the product. At Universe, how I parsed and structured voter files, GPS data, and campaign data was what made the organizer's field workflows function. I am drawn to backend roles where the problem space has real complexity. Cleaning and structuring messy, nuanced data across union locals, organizing campaigns, and research contexts is work I have repeatedly excelled at throughout my career.

### Claim 1  [PENDING] ✅
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users do with the product

- At Universe, how I parsed and structured voter files, GPS data, and campaign data was what made the organizer's field workflows function

### Claim 2  [PENDING] ✅
> I am drawn to backend roles where the problem space has real complexity

- Cleaning and structuring messy, nuanced data across union locals, organizing campaigns, and research contexts is work I have repeatedly excelled at throughout my career

### Claim 3  [PENDING] ✅
> I have repeatedly excelled at cleaning and structuring messy, nuanced data across union locals, organizing campaigns, and research contexts

*Contexts: employer: Universe*

- Parsed and structured voter files, GPS data, and campaign data
  - This work directly enabled organizer field workflows to function

**Conclusion:** The work that matters most is where technical decisions about data structure and flow directly determine what users can accomplish — not abstracted away from the domain, but inseparable from it.

---

## Analytics Engineer / Background
*hash: bb81604a69d2...*  

**Paragraph:**
> Before I became a Data Engineer I spent almost seven full years as a Data Analyst in high pressure, complex campaigns delivering mission critical reports, producing workflows, developing tooling, product ownership as well as end-to-end testing. At one point I was entrusted to produce an over forty step report every morning before 7AM 6 days a week for over six months and a weekly report that also required me to hand-kern numbers into an illustrator file and print on special paper.  I also regularly assigned the most complicated of the SSRS report builds because of my knack for solving hard and complex SQL logic problems on financial data.  At Unite Here I was the only person in our department to bridge both organizing and membership sides of application building and deployment and I was entrusted to perform desk audits on the most complicated dues processing workflows in the entire international union because I have such an incredible care and interest in building efficient workflows for administrative staff who care greatly about precision.

*No claims extracted.*

---

## General / Background
*hash: 422d7aade8c3...*  

**Paragraph:**
> Before becoming a full-time data engineer, I spent more than 13 years working across arts,
> education, and technology. Between 2009 and 2016, I taught at a variety of schools, nonprofits,
> art organizations including Eyebeam in New York, and conferences like the AMC in Detroit. I
> taught STEAM and creative coding as a Teaching Artist with organizations including Brooklyn
> College, Global Action Project, Eyebeam Art + Technology, and iD Tech Camps, where I worked
> with students using tools such as Unity and Minecraft. I also developed original curriculum and
> projects, including work connected to organizations such as Eyebeam and the Mozilla Foundation
> and researchers such as Daniela Rosner. I did my master's in fine art, where we did a lot of
> physical computing and programming: Arduino, Raspberry Pi, circuit bending, interactive systems
> with performance.

*No claims extracted.*

---

## General / Background
*hash: d428f9ac5feb...*  

**Paragraph:**
> I designed many workshops myself, sourced materials, and had people making things or performing
> or both. I participated in Mozilla's Hive network for many years, attended events, and taught
> workshops. My whole thing going into teaching and creative technology was to empower people to
> become tinkerers and thoughtful experimenters.

*No claims extracted.*

---

## General / Engineering Applied to Education
*hash: ade337bc7ffb...*  

**Paragraph:**
> I have worked as the sole dedicated data engineer at two companies, owning large projects
> from early problem definition through production. At BritBox, I built production pipelines,
> worked through ambiguous requirements, and developed test-forward approaches to data
> reliability. At Universe, I helped build backend data infrastructure from scratch for a
> down-ballot canvassing application, using typed, linted, object-oriented Python patterns
> to support a production-grade product.

*No claims extracted.*

---

## General / CS Education Philosophy
*hash: db96a10e4531...*  

**Paragraph:**
> Programming is a way to build, test, revise, imagine, and make something that reflects
> your own thinking.

*No claims extracted.*

---

## General / AI Stance
*hash: a1840554e199...*  

**Paragraph:**
> I do not believe AI should be introduced to students as a shortcut around thinking. Used
> well, it can support exploration, debugging, reflection, and creative iteration; used
> poorly, it can flatten the learning process and hide the decisions students most need to
> practice. I have been developing my own Claude-based coding agent to support learning and
> project development in a way that keeps the user in control of the reasoning, decisions,
> and design. I am also building AI applications with reviewable outputs and human decision
> points, which has made me think carefully about how AI systems can support learning without
> replacing the work of learning.

### Claim 1  [PENDING] ✅
> I have been developing my own Claude-based coding agent to support learning and project development in a way that keeps the user in control of the reasoning, decisions, and design

*Contexts: project: Claude-based coding agent*

- Built a Claude-based coding agent for learning and project development
  - Designed to keep the user in control of the reasoning, decisions, and design

### Claim 2  [PENDING] ✅
> I am building AI applications with reviewable outputs and human decision points

- Constructing AI applications that include reviewable outputs and human decision points

### Claim 3  [PENDING] ✅
> I think carefully about how AI systems can support learning without replacing the work of learning

- Experience building AI applications with reviewable outputs and human decision points has informed this thinking
  - This work has made me think carefully about the distinction between supporting learning and replacing it

### Claim 4  [PENDING] ✅
> I believe AI used well can support exploration, debugging, reflection, and creative iteration; used poorly, it can flatten the learning process and hide the decisions students most need to practice

- Distinction between supportive and harmful uses of AI in learning contexts
  - Used well: supports exploration, debugging, reflection, and creative iteration
  - Used poorly: flattens the learning process and hides the decisions students most need to practice

**Conclusion:** This person approaches AI tooling with a clear pedagogical framework: the tool's value is measured by whether it keeps the learner in control of reasoning and decision-making, not by how much work it removes. Building systems with reviewable outputs and human decision points is not a constraint they work around—it's the core design principle.

---

## General / Closing
*hash: 68c7de7ea9a1...*  

**Paragraph:**
> I would welcome the opportunity to share curriculum samples I have personally developed.

*No claims extracted.*

---

## General / Programming Languages and Learning
*hash: ee5d862fdd78...*  

**Paragraph:**
> I have a long history of both learning and teaching programming languages across Python,
> Java through Processing, C++ through Arduino, Max/MSP, HTML/CSS, and some JavaScript and
> React. I have already started reading about Elixir and would welcome the opportunity to
> implement in it significantly. I learn new technical material quickly, and that pattern of
> picking up languages across very different paradigms is consistent across my career.

### Claim 1  [PENDING] ✅
> I learn new technical material quickly, and that pattern of picking up languages across very different paradigms is consistent across my career

- Long history of learning and teaching programming languages across Python, Java through Processing, C++ through Arduino, Max/MSP, HTML/CSS, and some JavaScript and React
  - Languages span very different paradigms — imperative (Python, Java, C++), visual/dataflow (Max/MSP), markup/styling (HTML/CSS), functional (JavaScript/React)
- Already started reading about Elixir and would welcome the opportunity to implement in it significantly
  - Demonstrates proactive engagement with new paradigms beyond current expertise

### Claim 2  [PENDING] ✅
> I have a history of both learning and teaching programming languages

- Experience across Python, Java through Processing, C++ through Arduino, Max/MSP, HTML/CSS, JavaScript and React — in both learning and teaching contexts

---

## General / Motivation and Fit
*hash: f7b172f10eaa...*  

**Paragraph:**
> I watched Animal Farm before I knew about this opening, and Angel's model of prioritizing
> audience participation and direct supporter relationships is a specific reason I want this
> role. I have wanted to work at a film production or animation studio for a long time, and
> this position connects that interest with the work I do best: backend systems, data
> quality, reporting readiness, and long-term maintainability in a media company.

### Claim 1  [PENDING] ✅
> I work best on backend systems, data quality, reporting readiness, and long-term maintainability in a media company context


### Claim 2  [PENDING] ✅
> I have wanted to work at a film production or animation studio for a long time


### Claim 3  [PENDING] ✅
> Angel's model of prioritizing audience participation and direct supporter relationships is a specific reason I want this role

- I watched Animal Farm before knowing about this opening, which shaped my interest in this particular studio's approach

---

## Data Engineer / DBT and Airflow expertise
*hash: 7acd8bfb1b0c...*  

**Paragraph:**
> For my personal project CBA Clock, I built an 8-task Airflow DAG that takes a collective
> bargaining agreement from raw PDF to structured, queryable data, choosing Airflow because
> data teams recognize it and the graph view made a complex sequential ingest easier to
> reason about during development. On the dbt side, I built the dbt environment from scratch
> at Universe, connected to BigQuery, with staging models organized by source system, ref()
> dependencies controlling execution order, YAML tests, macros for reusable logic, and
> metadata-driven column mapping to handle variability across voter file providers. At
> BritBox, dbt ran on a different stack: self-hosted on EC2, connected to Redshift,
> orchestrated through Prefect. I also find Prefect more Python-native, but I reach for
> Airflow when a team context calls for it because it is the tool most data teams already
> know, and I can work in it without friction.

*No claims extracted.*

---

## Data Engineer / GCP and AWS proficiency, cross-platform proficiency
*hash: 021629af77c9...*  

**Paragraph:**
> At BritBox I had full admin access in AWS, setting up EC2 machines, building a prototype
> AI chatbot with Bedrock, creating and assigning IAM roles, and orchestrating Glue jobs
> with DynamoDB tables for metadata tracking. At Universe the stack was fully GCP with
> BigQuery running where Redshift would otherwise sit, and the work was directly
> translatable. I have also worked in Snowflake on client projects and in an Azure ecosystem
> at Unite Here using Azure Data Studio. Each of these environments has its own shape and I
> have been able to figure myself out and get up to speed in all of them.

*No claims extracted.*

---

## Data Engineer / Data catalog maintenance
*hash: 237a10557894...*  

**Paragraph:**
> At Unite Here, I started building data catalogs to track distinct definitions across
> locals on national campaigns where the same term could mean different things depending on
> the local. At Universe, I formalized that practice by introducing Great Expectations
> alongside dbt so documentation, definitions, and lineage were connected in one place. In
> that pipeline, dbt held the canonical transformation logic and model documentation,
> Prefect orchestrated the steps from normalizing raw files through running validations and
> publishing outputs, and Great Expectations sat at key checkpoints to validate schema,
> required fields, accepted values, row counts, and business rules before any downstream
> model or application workflow could depend on the data. The Universe application is
> entirely data driven and runs on parsed voterfiles, which means everyone using the app
> relied on the correctness of my mapping and validation to do their work.

*No claims extracted.*

---

## Data Engineer / Card Check Data Systems
*hash: bac55db99669...*  

**Paragraph:**
> At UNITE HERE I was given very little direction on what to do. I was taught the legal framework of card checks and elections but it was up to me to design a working system to track the organizing as well as the actual cards and to ensure that the NLRB had everything they needed in order, perfectly organized, in order to certify the card check. I was covering massive workplaces, at casinos, often also partnerships with other unions so there was sometimes collection and tracking that happened with more than just our union to ensure that the other union got their cards. I also covered the razor thin departmental organizing for the graduate students at Yale when their elections were certified with wins sometimes in the single digits. This entailed my having to wake up before 7 in the morning 6 days a week and compile a 40 something step excel report on the state of the organizing every morning. In all of these cases I was given very loose guidance and then I figured out the system and documented it but I was also responsible for training all of the staff in the campaign including the organizing directors on how the system worked, how to enter data into the system, and how we handled the reporting with the meeting schedules. I was working with a lot of organizers and staff members who were not technical but had a desire to win and my role was supportive. My system was so good the president of the local received a letter that one of my card checks was the most organized card check he had ever certified. I was also formally thanked by the president of that local for doing such a good job.

### Claim 1  [PENDING] ✅
> At UNITE HERE, I owned the end-to-end system design for tracking organizing campaigns, card check documentation, and NLRB certification requirements with no template to follow

*Contexts: employer: UNITE HERE*

- I was given very little direction on what to do and had to design a working system from scratch to track the organizing, the actual cards, and ensure the NLRB had everything they needed in order, perfectly organized, in order to certify the card check
- The system I built was recognized as exceptionally well-organized — the president of the local received a letter saying one of my card checks was the most organized card check he had ever certified

### Claim 2  [PENDING] ✅
> I designed systems that worked across complex, multi-union organizing contexts where card collection and tracking happened with more than one union to ensure each union got their cards properly accounted for

*Contexts: employer: UNITE HERE*

- I covered massive workplaces at casinos, often in partnerships with other unions, which meant collection and tracking that happened with more than just our union to ensure that the other union got their cards

### Claim 3  [PENDING] ✅
> I built a system capable of handling razor-thin margin organizing where wins sometimes came in single digits, requiring precision and daily accountability

*Contexts: employer: UNITE HERE*

- I covered the razor thin departmental organizing for the graduate students at Yale when their elections were certified with wins sometimes in the single digits
- This entailed waking up before 7 in the morning 6 days a week and compiling a 40-something step excel report on the state of the organizing every morning
  - The daily reporting requirement was a 40-step Excel report that had to be compiled before 7 AM, six days a week, to track the state of organizing

### Claim 4  [PENDING] ✅
> I take responsibility for making systems usable and understandable to non-technical staff and organizers who are focused on winning, not on the mechanics of data entry

*Contexts: employer: UNITE HERE*

- I was responsible for training all of the staff in the campaign including the organizing directors on how the system worked, how to enter data into the system, and how we handled the reporting with the meeting schedules
  - I was working with a lot of organizers and staff members who were not technical but had a desire to win and my role was supportive
- I figured out the system and documented it so that others could use it

### Claim 5  [PENDING] ✅
> I was formally recognized by the president of the local for the quality and impact of my work

*Contexts: employer: UNITE HERE*

- The president of that local formally thanked me for doing such a good job

**Conclusion:** This is work where the system itself determines whether a union can certify a win — there is no margin for error, the stakes are real, and the people using the system are organizers, not data people. Building something that works in that context means understanding what actually needs to happen on the ground and making it possible for people focused on organizing to do their jobs without becoming data entry specialists.

---

## Data Engineer / Application Development and Requirements
*hash: f5ac39e97b7a...*  

**Paragraph:**
> Even when at UNITE HERE I was working on application development and testing and gathering requirements and doing demos of software I was taking in feedback from organizers and membership staff and translating it into requirements and acceptance criteria for the applications' further development on multiple applications including an electronic membership card, a bargaining unit list processing portal, the dues processing system, as well as relational organizing apps, both of them.

### Claim 1  [PENDING] ✅
> At UNITE HERE, I owned the translation of organizer and membership staff feedback into requirements and acceptance criteria across multiple applications

*Contexts: employer: UNITE HERE*

- Gathered feedback directly from organizers and membership staff during application development, testing, and demos
- Translated that feedback into requirements and acceptance criteria for further development
- Worked across multiple applications: electronic membership card, bargaining unit list processing portal, dues processing system, and relational organizing apps

### Claim 2  [PENDING] ✅
> I work by taking in feedback from end users and translating it into technical requirements and acceptance criteria that guide development

- At UNITE HERE, consistently gathered feedback from organizers and membership staff and converted it into requirements and acceptance criteria across multiple applications

---
