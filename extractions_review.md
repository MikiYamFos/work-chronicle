# Extraction Review — 2026-06-01
Model: claude-haiku-4-5-20251001
Judge alignment: 85%
114 paragraph(s)

Open the Streamlit app to review and insert:
  uv run streamlit run coverletter/label_evals.py

---

## General / Opening
*hash: f13ae3ddabfa...*  

**Paragraph:**
> I have worked across disparate datasets in multiple domains, each with its own rules,
> stakeholders, and regulatory environment.

### Claim 1  [REJECTED] ❌ (This is a pure summary statement with no specific evidence — it names domains and constraints in the abstract but makes no claim about what the person DID, owned, or how they work; it is resume-speak that could apply to anyone who has held multiple jobs.)
> I have worked across disparate datasets in multiple domains, each with its own rules, stakeholders, and regulatory environment

- Operated across multiple domains with distinct data governance, stakeholder requirements, and regulatory constraints
  - Each domain had its own rules, stakeholders, and regulatory environment
  - Datasets were disparate across these contexts

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

### Claim 1  [REJECTED] ❌ (Claim describes an observed market condition, not what the person did, built, owns, or how they work — no personal agency or accountability assertion to substantiate)
> Across every domain I have worked in, organizations are making decisions with worse data than they could have, and the gap between what they are seeing and what they could see is almost always an engineering problem

- Pattern observed consistently across labor organizing, streaming media, electoral data, and civic tech

### Claim 2  [PENDING] ✅
> I know metrics — how they break down, where the business rules are hidden in the logic, and what it takes to produce a number someone can act on without second-guessing it

- Understanding of metric construction, hidden business logic, and the conditions required for actionable numbers
  - knows how metrics break down
  - identifies where business rules are hidden in logic
  - understands what produces a number someone can act on without second-guessing

### Claim 3  [PENDING] ✅
> I think in workflows, systems, and interfaces

- Consistent mental model across problem-solving: workflows, systems, and interfaces as the frame

### Claim 4  [PENDING] ✅
> The work I find most satisfying is translating a fuzzy stakeholder need into a data model that answers it cleanly, then building the infrastructure that keeps answering it correctly for as long as someone depends on it

- Core professional satisfaction comes from two linked activities: translating vague requirements into clean data models, and building durable infrastructure
  - translating fuzzy stakeholder need into data model
  - building infrastructure that keeps answering correctly over time
  - sustained accountability to dependents

**Conclusion:** This person sees data engineering as a bridge between organizational decision-making and technical capability — they are drawn to work where careful engineering removes ambiguity and creates lasting accountability.

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
> I am both deeply thoughtful about non-technical users and stakeholders, and serious about building solid, well-typed, tested Python

- Distinguishes this person as an engineer — the combination of stakeholder fluency and technical rigor

### Claim 2  [PENDING] ✅
> I spent many years caring for data on the frontlines of large campaigns, where data had to have precision and certainty

- Worked in high-stakes environments where data integrity was non-negotiable
  - Large campaigns context — data precision and certainty were operational requirements

### Claim 3  [PENDING] ✅
> I did extremely well with what would be considered an overwhelming amount of accountability for the numbers I delivered

- Carried rare levels of accountability for data integrity as a data and backend engineer
  - This level of accountability is especially rare for data and backend engineers
  - Operated under high-stakes conditions where delivery accuracy was directly measurable

### Claim 4  [PENDING] ✅
> My intensive experience of responsibility around data integrity has informed my abilities and focus in data governance

- Data governance orientation shaped by frontline accountability experience
  - Rare combination: backend/data engineer with deep accountability for data integrity
  - This experience directly informs approach to data governance work

**Conclusion:** This person brings an unusual combination for a data engineer: stakeholder empathy paired with technical rigor, and — most distinctively — a rare depth of accountability for data integrity that has become their professional orientation.

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
> For the last fourteen years, I have often worked in environments where I was one of very few people, and sometimes the only person, responsible for my job function

- Operated as sole or near-sole owner of job function across multiple roles over fourteen years

### Claim 2  [PENDING] ✅
> I have had to work through ambiguity, limited direction, and high expectations without waiting for someone else to define the path

- Figured out the work independently under real constraints — ambiguity, limited direction, high expectations — without waiting for someone to define the path

### Claim 3  [REJECTED] ❌ (Pure assertion of character traits without specific reference to what was owned, built, or decided — resume-speak that names qualities rather than proving them through work.)
> I have always been a problem solver, an enthusiastic project manager, and a self-starter

- Consistent pattern of problem-solving, project management, and self-directed work across career

### Claim 4  [PENDING] ✅
> My best abilities come from curiosity and creativity around systems design, workflow efficiency, and intricate but well-structured data models

- Finds meaningful work in systems design, workflow efficiency, and data model architecture
  - Driven by curiosity and creativity in these domains
  - Strength lies in intricate but well-structured data models

**Conclusion:** This person operates best when given high autonomy and real accountability — they thrive in ambiguity, think systematically about structure and efficiency, and are energized by the design work itself rather than external direction.

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
  - Required deep understanding of decades-old processes to translate into data structures
  - Requirements work preceded any engineering
- At BritBox, the watch-duration work started with no specification: I had to determine what 'watch duration' meant at the subscriber grain, what constituted a valid session, and how cross-midnight plays should be handled -- before the engineering could begin
  - Defined metric at subscriber grain
  - Determined session validity rules
  - Resolved cross-midnight play handling
  - All decisions made before engineering began
- In both cases the technical decisions were downstream of the requirements decisions

### Claim 2  [PENDING] ✅
> I think in workflows, systems, and interfaces -- what the data needs to do, who needs to use it, what they need to see, and what stands between the raw source and a number someone can act on

- The work I find most satisfying is closing that gap: figuring out what the data should say, building the infrastructure that makes it say that reliably, and making sure the people who depend on it can actually trust it
  - Figuring out what the data should say
  - Building infrastructure for reliable output
  - Ensuring downstream users can trust it

### Claim 3  [PENDING] ✅
> I have been consistently surprised by how much room there is for data quality to be substantially better across all the places I have worked

- The pipelines that have caused the most downstream trust problems, at every place I have worked, were the ones where the requirements phase was skipped
  - Pattern observed across multiple employers
  - Skipped requirements phase correlates with downstream trust problems

### Claim 4  [REJECTED] ❌ (This is a statement about organizational behavior and industry practice, not a claim about what this person did, how they work, or who they are as an engineer — it cannot be substantiated with evidence of their specific actions or approach.)
> Building systems that produce trustworthy, well-governed data at the right level of detail requires sustained, careful engineering work that organizations routinely underinvest in

- Organizations routinely underinvest in the sustained, careful engineering work required to produce trustworthy, well-governed data
  - Data quality and governance are underinvested areas
  - Requires sustained effort, not one-time work

**Conclusion:** This person's professional orientation is toward closing the gap between raw data and trustworthy, actionable information — a gap they see as systematically underinvested in. They approach data work as a requirements and governance problem first, engineering problem second, and find meaning in making that invisible work visible and reliable.

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
> I am released into ambiguous contexts and expected to find the problems, define them, and build end-to-end solutions while keeping stakeholders oriented to what I am doing and why

- This pattern has held across every domain: labor organizing, streaming media, electoral data, civic tech
- The same underlying conditions keep appearing: bad data, poorly structured tooling, and organizations that have been sold on what technology can do without being told what it requires

### Claim 2  [PENDING] ✅
> I work by surfacing constraints and failure modes proactively, giving visibility to decision points that exist whether or not anyone names them, and creating shared ownership of the more precise problem space

- My first real boss taught me that honesty and directness build trust and cut through wasted effort, and I applied that to technical work in a way most of my technical peers did not
- When I surface a constraint or a failure mode before anyone asked, I am doing two things at once: giving visibility to a decision point that exists whether or not anyone names it, and creating shared ownership of the more precise problem space

### Claim 3  [PENDING] ✅
> I have built a reputation across every environment I have worked in for providing clarity on technical constraints before stakeholders have to ask for it

- The people depending on the work have known they would get that clarity from me before they had to ask for it
- What happens next depends on the risk — sometimes more time is afforded to work around it, sometimes a plan is built to address it before it becomes inevitable, sometimes the stakeholder accepts it. All three of those are better outcomes than an emergency no one saw coming

### Claim 4  [PENDING] ✅
> I am motivated by work where honesty about technical constraints and clear communication prevent emergencies and build shared ownership of problems

- All three outcomes — more time afforded, a plan built before it becomes inevitable, or stakeholder acceptance — are better than an emergency no one saw coming

**Conclusion:** This person operates at the intersection of technical autonomy and stakeholder communication — they find and define problems independently, but their core method is making constraints visible and building shared ownership rather than solving in isolation.

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
> I am consistently brought into the conversation before the build—where you work out what the problem is, what the data can and cannot do, and what the solution requires

- In that conversation I am listening, asking follow-up questions that follow the shape of the thing I am already building in my head, pulling in the right people—a vendor, a data owner, a stakeholder whose requirements no one else has collected yet
  - Proactively identifies and brings in stakeholders whose requirements have not been collected
  - Asks follow-up questions shaped by emerging understanding of the problem structure
- Sorting out what is baseline from what is nice-to-have when the people asking have not necessarily talked to each other
  - Mediates between stakeholders with unaligned priorities
  - Distinguishes critical requirements from optional features

### Claim 2  [PENDING] ✅
> I have a consistent orientation toward problems that are complicated, stuck, and where the path is not obvious—and I stay with them across different domains

- Every environment I have worked in has handed me the same problem in a different form: something complicated, something stuck, something where the path is not obvious and someone has to stay with it
  - Domains: digital arts, teaching, nonprofit consulting, labor data, production engineering
  - Pattern is consistent across domains—the orientation did not change
- I did not put it down until it worked
  - Sustained accountability through complex, multi-faceted problems to resolution

### Claim 3  [PENDING] ✅
> I hold the whole thing in my head at once—managing multi-faceted projects from conception through production and presentation end to end

- Walking students through project conception to production and presentation end to end
  - Full lifecycle ownership from problem definition to delivery
- Getting multi-faceted art projects off the ground by holding the whole thing in my head at once
  - Mental model of entire project structure and dependencies
  - Ability to coordinate across multiple facets simultaneously

### Claim 4  [PENDING] ✅
> When the technical problem is hard—complex queries, joins across decades of data that do not map cleanly to exact calculations—I get handed whatever stopped the person next to me and I work it until it works

- When the SSRS queries were too complex, when the joins across decades of membership data did not map cleanly to calculations that had to be exact, I got handed whatever stopped the person next to me, and I did not put it down until it worked
  - SSRS query complexity
  - Multi-decade membership data with non-standard join logic
  - Calculations requiring exactness
  - Implicit accountability for unblocking others

**Conclusion:** This person is brought in to solve problems where the path is unclear because they combine the ability to hold complex systems in mind, ask the right questions to surface hidden requirements, and stay accountable through to working solutions—across technical and organizational boundaries.

---

## Data Engineer / BritBox Subscriber Reporting
*hash: c89544e7b9b6...*  

**Paragraph:**
> The monthly subscriber reporting at BritBox went directly to the CTO and CEO

### Claim 1  [PENDING] ✅
> At BritBox, I owned monthly subscriber reporting that went directly to the CTO and CEO

*Contexts: employer: BritBox*

- The monthly subscriber reporting went directly to the CTO and CEO

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
> I owned subscriber reporting at BritBox where the data model was unstable and failures had to be found, diagnosed, and fixed each time they appeared

*Contexts: employer: BritBox*

- Subscriber reporting didn't come with a stable data model — it came with failures that had to be found, diagnosed, and fixed each time they appeared
- The Evergent system served only current-state data, which made accurate churn and subscriber counts dependent on monthly snapshots and vendor-side processing I couldn't fully inspect
  - subscriber records reflected the latest state rather than their history
  - accurate churn and subscriber count calculations dependent on monthly snapshots and vendor-side logic we could not fully control or validate

### Claim 2  [PENDING] ✅
> When new billing recovery logic caused Evergent to double-count churn, I identified the pattern, documented the root cause for the vendor, and validated the fix before the numbers went back up

*Contexts: employer: BritBox*

- New recovery logic in billing caused the Evergent system to count churn more than once for the same records, so our churn numbers were massively overcounted and subscriber counts were no longer reconciling against billing
  - churn numbers were massively overcounted
  - subscriber counts were no longer reconciling against billing
- I had to analyze the problem, make a recommendation to the vendor, get it fixed, and do QA to confirm it was resolved

### Claim 3  [PENDING] ✅
> When new subscription tiers broke the model again, I rebuilt the logic overnight with the Finance lead to hit the monthly close, and those numbers went to the CFO, CTO, and CEO

*Contexts: employer: BritBox*

- New subscription tiers broke the model — subscription ID lineages where inactive records were current and active records were future, no anomaly detection built in
  - long lineages of subscription IDs under a single customer ID
  - subscriptions marked inactive that were actually current
  - future subscriptions marked active
  - none of the new anomalies had been worked out ahead of time
- I rebuilt the logic overnight with the Finance lead to hit the monthly close
- The CFO, CTO, and CEO read those numbers the next morning for meetings about the direction of the business
  - those numbers shaped how the company understood its own health and trajectory

### Claim 4  [PENDING] ✅
> I worked closely with the US reporting lead in Finance each month to ensure the numbers were correct before they went up, and sometimes that meant working until midnight to get new logic validated in time

*Contexts: employer: BritBox*

- I worked closely with the US reporting lead in Finance each month to ensure the numbers were correct before they went up, and sometimes that meant working until midnight to get new logic validated in time

### Claim 5  [PENDING] ✅
> Getting those numbers wrong was not an option — they shaped how the CFO, CTO, and CEO understood the company's health and trajectory

*Contexts: employer: BritBox*

- Getting those numbers wrong was not an option
- Those numbers went to the CFO, CTO, and CEO and shaped how the company understood its own health and trajectory

**Conclusion:** This person operated under extreme accountability for data integrity at a level rare for a data engineer — not just building systems but owning whether the numbers were right when they reached the C-suite, and fixing structural problems under real time pressure.

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

- Sole dedicated data engineer for nearly two years
- Pipeline processed over a billion playback events daily
- Produced subscriber-level watch metrics that the business ran on

### Claim 2  [PENDING] ✅
> I inherited a four-month-old stub with no session logic, no enrichments, and no stitching, handed off from a data scientist with only vague direction to 'work on it,' and had four months and one hard deadline to make it production-ready

*Contexts: employer: BritBox*

- Project came as a column selection with no session logic, no enrichments, and no stitching
- Handed off from a data scientist who had been told only to 'work on it'
- Four months and one hard deadline

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
> At BritBox, I was the only dedicated data engineer for nearly two years, which meant full ownership wasn't a title — it was the operating reality

*Contexts: employer: BritBox*

- Solo data engineering role with end-to-end accountability for all data infrastructure and pipelines

### Claim 2  [PENDING] ✅
> I delivered the company's subscriber-level watch-duration pipeline, processing over a billion daily playback events, in four months from a cold start

*Contexts: employer: BritBox*

- Built a production pipeline handling 1B+ daily events in four months starting from no existing infrastructure
  - Handoff received was a partial column selection with no session logic and no enrichments

### Claim 3  [PENDING] ✅
> Correctness was mine to define: I designed the subscriber-level metric grain, built the cross-midnight session-stitching logic, created a cross-grain reconciliation framework to validate against the old customer-level output, and self-directed the Spark optimization for billion-row scale

*Contexts: employer: BritBox*

- Owned metric definition and validation logic end-to-end
  - Designed subscriber-level metric grain from first principles
  - Built cross-midnight session-stitching logic to handle session boundaries
  - Created cross-grain reconciliation framework to validate against legacy customer-level output
  - Self-directed Spark optimization for billion-row scale processing

### Claim 4  [PENDING] ✅
> The vendor it replaced failed regularly. Mine hasn't gone down once

*Contexts: employer: BritBox*

- Pipeline reliability in production: zero downtime versus regular failures from predecessor system

**Conclusion:** Operating as the sole data engineer forced me to own not just execution but the definition of correctness itself — metric design, validation, and reliability became inseparable from the engineering work.

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

*No claims extracted.*

---

## Data Engineer / BritBox Watch-Duration Pipeline
*hash: cfb9261c361c...*  

**Paragraph:**
> The replacement has been 100% stable since go-live. The vendor's version failed regularly.
> That delta is the work.

*No claims extracted.*

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
> At BritBox, I owned the watch-duration metrics pipeline that the company used to understand subscriber behavior and make content spend decisions

*Contexts: employer: BritBox*

- The metrics drove decisions about content spend and catalog direction across the entire company
  - which content was holding viewers
  - how engagement broke down by subscription tier
  - what watch patterns looked like across the catalog
- A billion playback events came in daily at subscriber level

### Claim 2  [PENDING] ✅
> I replaced a vendor pipeline that failed regularly and operated at customer grain with a system built at subscriber grain that has had no failures since go-live

*Contexts: employer: BritBox*

- The vendor pipeline modeled at the customer level, a coarser signal that also could not be trusted
- My replacement built at subscriber grain, with proper session stitching and cross-grain reconciliation validation
  - session stitching logic
  - cross-grain reconciliation validation

### Claim 3  [REJECTED] ❌ (Describes what the system achieved, not what the person owned or decided — should be reframed as a claim about the engineer's work, not the pipeline's properties.)
> For the first time, the viewership numbers were granular enough to be actionable and reliable enough to be trusted

*Contexts: employer: BritBox*

- The previous system could not be trusted and operated at a coarser grain that did not support decision-making

**Conclusion:** This person took ownership of a high-stakes metric that directly influenced company strategy, diagnosed why the existing system failed, and rebuilt it with the technical rigor required to make it both reliable and actionable — moving from a system nobody could trust to one the company depended on.

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

*No claims extracted.*

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
> I built CBA Clock around the insight that leverage in collective bargaining is information, and most unions negotiate without it

*Contexts: project: CBA Clock*

- A union that can trace each clause through successive contract cycles — seeing what language was proposed and rejected, what concessions were made and under what conditions — walks into bargaining with a categorically different kind of knowledge than one reading a static PDF

### Claim 2  [PENDING] ✅
> I designed CBA Clock to convert collective bargaining agreements into queryable, clause-level records so that language evolution can be tracked across negotiations, violations can be documented against specific provisions, and concessions made under temporary conditions can be flagged for recovery

*Contexts: project: CBA Clock*

- The application converts collective bargaining agreements into queryable, clause-level records
  - language evolution can be tracked across negotiations
  - violations can be documented against the specific provisions they breach
  - concessions made under temporary conditions can be flagged for recovery in the next round

### Claim 3  [PENDING] ✅
> My work at UNITE HERE on grievance tracking and contract enforcement showed me that unions with the best outcomes were the ones who understood their contracts with the most precision

*Contexts: employer: UNITE HERE*

- The unions with the best outcomes were the ones who understood their contracts with the most precision
  - This insight came from work on grievance tracking and contract enforcement

### Claim 4  [PENDING] ✅
> I am drawn to work where careful information architecture makes organizations more powerful in high-stakes negotiations

- I built this to be the tool that makes that precision accessible
  - The tool addresses a structural information asymmetry in collective bargaining

**Conclusion:** This person identifies structural problems in how organizations operate, builds tools that shift the information balance in favor of underresourced actors, and is motivated by making precision and leverage accessible where it was previously unavailable.

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

*No claims extracted.*

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

*No claims extracted.*

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
> I owned the complete financial workflow audit of the most complicated dues structure in the entire UNITE HERE international union, sole responsibility to document and replicate every fee type across multiple general ledger accounts

*Contexts: employer: UNITE HERE*

- The Canadian local had the most complicated dues structure of any local in the entire international union: different dues rates, fees, funds, and contributions that split across multiple general ledger accounts, with financial processes that had evolved over years of local practice
  - multiple dues rates, fees, and funds
  - split across multiple general ledger accounts
  - processes evolved over years of local practice
- UNITE HERE entrusted me with the full desk audit of that local -- sole responsibility to document and replicate the complete financial workflow, account for every fee type, and produce a model the international could work from
  - sole responsibility
  - document and replicate complete financial workflow
  - account for every fee type
  - produce a model the international could work from

### Claim 2  [PENDING] ✅
> I figured out metrics from scratch, repeatedly, across many locals operating under different labor law and different dues structures, and documented them precisely enough that the work could survive staff turnover

*Contexts: employer: UNITE HERE*

- I had to figure out metrics from scratch, repeatedly, across many locals operating under different labor law and different dues structures
  - metrics figured out from scratch
  - across many locals
  - different labor law contexts
  - different dues structures
- document them precisely enough that the work could survive staff turnover
  - precision required for institutional continuity
  - documentation must outlast individual contributors

### Claim 3  [PENDING] ✅
> I understood that union financial processes carry direct legal obligations and that getting the numbers wrong affects workers' dues standing, benefits eligibility, and the union's ability to enforce contract terms -- not a data quality issue but a legal and worker-facing accountability

*Contexts: employer: UNITE HERE*

- Unions are heavily regulated and their financial processes carry direct legal obligations
- Getting the numbers wrong is not a data quality issue -- it affects workers' dues standing, benefits eligibility, and the union's ability to enforce contract terms
  - direct impact on workers' dues standing
  - direct impact on benefits eligibility
  - direct impact on union's ability to enforce contract terms
  - reframes accuracy from technical metric to legal and worker-facing obligation

**Conclusion:** This person operates at the intersection of technical rigor and institutional accountability — they understand that precision in financial systems is not an engineering preference but a legal and human obligation, and they document work to outlast themselves.

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
> I built and debugged a secure file ingestion portal processing employer-submitted worker rosters in every format employers could throw at us

*Contexts: employer: UNITE HERE*

- Processed CSVs, tab-delimited files, txt files, and PDFs so degraded they had to be run through secondary tools or rebuilt manually before a single record could be trusted
  - PDFs so degraded they had to be run through secondary tools or rebuilt manually

### Claim 2  [PENDING] ✅
> I wrote the migration scripts and reporting solutions that sat on top of records containing social security numbers and financial data for dues processing

*Contexts: employer: UNITE HERE*

- Records included social security numbers and financial data for dues processing

### Claim 3  [PENDING] ✅
> I worked retention decisions out directly with campaign leadership, balancing data utility against real human risk

*Contexts: employer: UNITE HERE*

- Supported organizing campaigns so sensitive the data could not be discussed openly, operated under code names, and required hard calls about permanent deletion
  - Contact information and scheduling data came in through pictures taken in the field
  - Translated them into structured records
  - Anything that could be traced back to a source disappeared entirely

### Claim 4  [PENDING] ✅
> I worked closely with grievance officers navigating CBA-specific legal rules where grievances could run for years across multiple contract versions and documentation had to hold up to procedural standards

*Contexts: employer: UNITE HERE*

- On the contract enforcement side, grievances could run for years across multiple contract versions at the same property and the documentation had to hold up to the procedural standards that kept a grievance alive
  - CBA-specific legal rules governed grievance procedures

### Claim 5  [PENDING] ✅
> I operate in data environments that demand the combination of legal precision, sensitivity, and technical rigor that union data requires

*Contexts: employer: UNITE HERE*

- Few data environments demand the combination of legal precision, sensitivity, and technical rigor that union data does, and I spent years inside it

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
> I built ingestion workflows around compliance constraints, with protected and offline handling at every step, because the cost of getting it wrong was legal and organizational, not just technical

*Contexts: employer: UNITE HERE*

- Handling sensitive membership, dues, health fund, and grievance data meant the pipeline design was a compliance question before it was an engineering question
  - Data included membership records, dues information, health fund data, and grievance records
  - Compliance requirements drove architecture decisions before technical considerations
- Files arrived as CSVs, tab-delimited text, and PDFs — some scans poor enough to require secondary cleaning before they could be used at all
  - Multiple input formats: CSV, tab-delimited text, PDF
  - PDF scans required secondary cleaning step due to quality issues
- None of it could move over standard electronic channels
  - Data transfer constraints required non-standard handling

### Claim 2  [PENDING] ✅
> I approached pipeline design by starting with compliance and legal constraints, not technical convenience

*Contexts: employer: UNITE HERE*

- The pipeline design was a compliance question before it was an engineering question
  - Regulatory and legal requirements were the primary design driver
  - Technical implementation followed from compliance needs, not the reverse

### Claim 3  [PENDING] ✅
> I had accountability for data handling at a level where the consequences were legal and organizational, not just technical

*Contexts: employer: UNITE HERE*

- The cost of getting it wrong was legal and organizational, not just technical
  - Failures would have legal consequences for the organization
  - Failures would have organizational consequences beyond system downtime
  - This elevated the stakes beyond typical engineering accountability

**Conclusion:** This person understands that some engineering work is fundamentally about risk management and legal compliance, not optimization — and designs systems accordingly, starting from constraints rather than convenience.

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
> I built the pipelines and modular generics underneath the entire application on BigQuery, Prefect, dbt, and TypeScript, with mypy and strict linting so the infrastructure could flex across campaign configurations without rewriting core logic

*Contexts: employer: Universe*

- The entire application runs on data: parsed voterfiles and shapefiles power every canvas a campaign deploys
- Built infrastructure with mypy and strict linting so the infrastructure could flex across campaign configurations without rewriting core logic
  - Used BigQuery, Prefect, dbt, and TypeScript
  - Designed for modularity and reusability across different campaign setups

### Claim 2  [REJECTED] ❌ (Describes what a system did, not what the person owned, built, or decided — should be a supporting detail, not a standalone claim)
> Firebase was central to the Universe application as a live data layer driving user-facing functionality

*Contexts: employer: Universe*

- Firebase served as the live data layer that powered user-facing functionality in the application

### Claim 3  [PENDING] ✅
> I was placed on a live Texas campaign doing electoral data operations, and the Texas Secretary of State delivered the voterfile so late we were pulling together old files, constructing pipelines off incomplete data, and pushing live updates while canvassers were already in the field

*Contexts: employer: Bluebonnets Fellowship (Texas campaign)*

- Pulled together old files, constructed pipelines off incomplete data, and pushed live updates while canvassers were already in the field
  - Texas Secretary of State delivered the voterfile late
  - Had to work with incomplete data under live operational pressure

### Claim 4  [PENDING] ✅
> I volunteered because Texas elections are high stakes and the data quality in electoral work is routinely bad enough that less technical volunteers cannot get their operations off the ground without someone who can build fast and build clean

*Contexts: employer: Bluebonnets Fellowship (Texas campaign)*

- Texas elections are high stakes and the data quality in electoral work is routinely bad enough that less technical volunteers cannot get their operations off the ground without someone who can build fast and build clean
  - Recognized that technical infrastructure was a bottleneck for campaign operations
  - Motivated by enabling non-technical volunteers to execute effectively

### Claim 5  [PENDING] ✅
> I have done serious work across the GCP stack under conditions where the data is late, the files are messy, and the timeline does not move

*Contexts: employer: Universe, employer: Bluebonnets Fellowship (Texas campaign)*

- GCP is the default infrastructure across the electoral and civic tech world
- Built and operated under conditions where the data is late, the files are messy, and the timeline does not move
  - Demonstrated ability to deliver under real operational constraints
  - Worked with incomplete, late-arriving data in production

**Conclusion:** This person builds data infrastructure that is both technically rigorous and operationally resilient — designed to flex across configurations and survive the chaos of real campaigns where data arrives late and incomplete. They are motivated by enabling others to operate effectively under high stakes, and they have proven they can execute at speed without sacrificing quality.

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

- Full-stack ownership across web interface, backend routing, RAG retrieval, and Claude API integration
  - System tested and interoperable across OpenAI models as well

### Claim 2  [PENDING] ✅
> I made sourcing a hard architectural constraint because in a grievance context, an officer who acts on a hallucination can lose a case that should have been won

*Contexts: project: CBA Clock*

- The interface surfaces the contract language alongside the model's response at every step
  - Architectural decision driven by high-stakes context where hallucinations have real consequences

### Claim 3  [PENDING] ✅
> The LLM API integration is the mechanism by which years of contract history become queryable, navigable, and actionable for someone who needs a defensible answer in the middle of a dispute

*Contexts: project: CBA Clock*

- A user working a grievance can move through the application, pull relevant contract clauses, and get LLM-generated analysis tied directly to the retrieved source text
  - System enables officers to track grievances and map contract language across successive agreements
  - Query system returns answers grounded in actual CBA text

### Claim 4  [PENDING] ✅
> I work backwards from the stakes of the user's context into the architecture that makes hallucination impossible

*Contexts: project: CBA Clock*

- In a grievance context, an officer who acts on a hallucination can lose a case that should have been won, so the interface surfaces the contract language alongside the model's response at every step
  - Sourcing requirement became a hard architectural constraint, not a feature

**Conclusion:** This person builds systems where the technical architecture is inseparable from the stakes of the user's work — they think in terms of what can go wrong and make that impossible at the design level, not as an afterthought.

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

*No claims extracted.*

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
> I built physical interfaces that integrated hardware, firmware, and interactive behavior—wiring, programming in C++, and coordinating audio, video, LEDs, and mechanical movement as a unified system

*Contexts: project: MFA thesis physical interface*

- Built a physical interface in C++ using Arduino that played audio and video clips, lit up LEDs, and moved small objects
  - programmed in C++
  - used Arduino platform
  - coordinated audio playback, video playback, LED control, and mechanical actuation
- Writing code, wiring hardware, and building interactive systems as part of a graduate degree

### Claim 2  [PENDING] ✅
> I approach systems thinking by integrating across disciplines—electrical, mechanical, and software—to create coherent interactive behavior

*Contexts: project: MFA interdisciplinary work*

- MFA was an interdisciplinary program where I took programming classes, learned C++ and Java, did object-oriented programming for interactive music systems in Max/MSP, and worked with electrical and mechanical engineering concepts for art projects
  - learned C++ and Java
  - object-oriented programming in Max/MSP for interactive music systems
  - worked with electrical and mechanical engineering concepts
  - thesis involved multiple pieces

### Claim 3  [PENDING] ✅
> I have sustained and built on foundations in systems integration, hardware-software coordination, and interactive design since my graduate work

- I have been building on those foundations ever since

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

### Claim 1  [PENDING] ✅
> I originated the idea for a semantic search engine over closed caption transcripts synced to video timecodes, solving a real problem video editors faced when hunting for specific spoken moments in long files

*Contexts: project: BBC Hackathon Semantic Search Tool*

- The problem was real: a video editor hunting for a specific spoken moment in a long file either had to scrub through footage manually or rely on memory
- Solution enabled editors to search by keyword or concept and pull exact clips instantly

### Claim 2  [PENDING] ✅
> I built the Streamlit interface and the data pipeline backend for a tool shipped in three days with a team of three, one of the smallest teams in the competition

*Contexts: project: BBC Hackathon Semantic Search Tool*

- Built both the Streamlit interface and data pipeline backend
- Shipped in three days with a team of three, one of the smallest in the field

### Claim 3  [PENDING] ✅
> The demo on Bluey clips proved the capability by allowing search for the strangest, most specific words and immediately assembling mashups, which made the judges respond to both creativity and technical execution

*Contexts: project: BBC Hackathon Semantic Search Tool*

- The ability to search for the strangest, most specific words and immediately assemble a mashup made the capability undeniable
- Won first place against roughly eleven teams across all divisions

### Claim 4  [PENDING] ✅
> I find meaningful work in building something genuinely playful that is also technically rigorous, as a counterpoint to day-to-day work driven by business requirements and top-down requests

*Contexts: project: BBC Hackathon Semantic Search Tool*

- Our day-to-day work is driven by business requirements and top-down requests, so building something genuinely playful that was also technically rigorous was its own kind of proof

**Conclusion:** This person operates with autonomy to identify real problems, executes with technical rigor under constraints, and is energized by work that combines creativity with engineering precision.

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
> I identified that closed caption files are not precise transcripts — the text surfaces *around* when a character speaks, not exactly when — which means a naive timecode sync produces clips that cut in too early or land mid-word

*Contexts: project: BBC hackathon 2025 semantic video search*

- Recognized the core technical constraint that closed captions have inherent timing imprecision relative to actual speech
  - Text surfaces *around* when a character speaks, not exactly when
  - Naive timecode sync produces clips that cut in too early or land mid-word

### Claim 2  [PENDING] ✅
> I solved the timecode alignment problem by testing clips repeatedly to find a buffer large enough to catch the right moment but tight enough not to bleed into surrounding audio

*Contexts: project: BBC hackathon 2025 semantic video search*

- Developed an iterative testing approach to calibrate buffer size for precise clip extraction
  - Buffer had to be large enough to catch the right moment but tight enough not to bleed into surrounding audio
  - Required repeated testing to find the right threshold

### Claim 3  [PENDING] ✅
> I built a semantic search system using Elasticsearch to match queries against chunked transcript text and return the relevant timecode window, with Streamlit handling video playback

*Contexts: project: BBC hackathon 2025 semantic video search*

- Implemented the full search and playback pipeline in three days
  - Used Elasticsearch-family tool to match queries against chunked transcript text
  - Returned relevant timecode window
  - Streamlit handled video playback on top

### Claim 4  [PENDING] ✅
> I delivered a prototype that demonstrated a real capability: type a phrase, jump to the exact clip in the Bluey archive, and walk away with an asset ready for a supercut, a trailer, or anything else a social or production team needed to pull together

*Contexts: project: BBC hackathon 2025 semantic video search*

- Won the BBC hackathon by building a working prototype that solved a real production workflow problem
  - Type a phrase, jump to the exact clip in the Bluey archive
  - Walk away with an asset ready for a supercut, a trailer, or anything else a social or production team needed to pull together

### Claim 5  [PENDING] ✅
> I am drawn to problems where the technical constraint is not obvious until you test it, and where solving it unlocks a capability that production teams can actually use

*Contexts: project: BBC hackathon 2025 semantic video search*

- Chose to focus on semantic search over video despite it being 'a harder problem than it sounds'
  - Learned the core challenge firsthand by building the solution
  - Delivered something that production teams could use immediately

**Conclusion:** This person identifies non-obvious technical constraints, solves them through iterative testing, and builds systems that translate technical capability into immediate production value.

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
> I work backwards from the end state—who will use this, how will they use it, and what problem is it supposed to solve—before designing anything

- When a project lands without a clear specification, my first move is to work backwards from the end state
- I identify the people who can give me sharper detail about what they need and how they picture it helping them, and I go talk to them

### Claim 2  [PENDING] ✅
> I ground architecture decisions in direct examination of the data—baseline metrics, datatypes, and cleanliness—before committing to a design

- In parallel I open a notebook—not to build anything yet, but to look at the data directly, pull baseline metrics, check datatypes, and get a read on cleanliness
- By the time I am thinking about design, I already know whether what exists is sufficient to cover what was requested, what shape it is in, and what scale of transformation and processing the pipeline will need

### Claim 3  [PENDING] ✅
> I run requirements work and architecture work simultaneously, grounded in what the data can actually support, which keeps engineering from running ahead of the problem

- The requirements work and the architecture work happen simultaneously, grounded in what the data can actually support, and that sequence is what keeps the engineering from running ahead of the problem

**Conclusion:** This person's method prevents misalignment between what is requested and what is technically feasible by making data reality and user need visible before design begins.

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

*No claims extracted.*

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
> I know Fivetran well enough to recognize where it stops being useful — I used it at Hypedocs and on contracts pulling from MixPanel and Google Ads, but I stopped reaching for it when sources fell outside its productized catalog

*Contexts: employer: Hypedocs, employer: Contract work*

- Fivetran is built for connections to large enterprise platforms it has already productized, and it is expensive precisely because that coverage is its entire value proposition
- For any organization pulling from sources outside that catalog, it is not a solution, it is a ceiling

### Claim 2  [PENDING] ✅
> My background is in building custom connectors and ingestion pipelines from scratch, which means I can cover everything Fivetran handles for the sources it supports, and keep building where it stops

- I can cover everything Fivetran handles for the sources it supports, and keep building where it stops
  - Built custom connectors and ingestion pipelines from scratch across multiple employers

### Claim 3  [PENDING] ✅
> Per Scholas would have an engineer who can connect to whatever the data actually lives in, not one working around the edges of an expensive tool

- This is a statement of what the person brings to the role — the ability to solve the actual problem rather than adapt to tool constraints
  - Implies orientation toward solving the real data connectivity problem, not the tool-constrained version of it

**Conclusion:** This person has deep enough knowledge of a standard tool to know its boundaries, and has built the complementary skill — custom connectors and pipelines — that makes them useful precisely where that tool fails. They are oriented toward solving the actual problem, not working within tool constraints.

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
> At Universe, I diagnosed that transformation logic living in Tableau was causing weekly dashboard refreshes to fail or run for hours, blocking the CEO and Senior Leadership Team from the numbers they used to run the organization

*Contexts: employer: Universe*

- Weekly Tableau refreshes were failing or running for hours, serving dashboards the CEO and Senior Leadership Team relied on to run the organization
  - The dashboards served the CEO and Senior Leadership Team
  - The numbers they used to run the organization
- Root cause was transformation logic living in the wrong place — Tableau was carrying computational weight that belonged upstream

### Claim 2  [PENDING] ✅
> At Universe, I proposed and led the migration of business definition logic from Tableau into dbt models so Tableau would read pre-computed results instead of grinding through raw data on every refresh

*Contexts: employer: Universe*

- I was positioned to propose and lead the migration because I had built the dbt environment from scratch
- The fix was to migrate business definition logic into dbt models so Tableau would read pre-computed results instead of grinding through raw data on every refresh
  - A slow, multi-team effort still in progress

### Claim 3  [PENDING] ✅
> At Universe, I built the dbt environment from scratch — a self-hosted instance on EC2, connected to Redshift, orchestrated through Prefect with custom flows I wrote to handle different file cleaning and transformation requirements

*Contexts: employer: Universe*

- Built a self-hosted dbt instance on EC2, connected to Redshift, orchestrated through Prefect
  - Custom flows written to handle different file cleaning and transformation requirements

**Conclusion:** This person has the technical depth to diagnose infrastructure problems at the system level, the autonomy to build foundational data infrastructure from scratch, and the standing to lead cross-team migrations because they own the systems those migrations depend on.

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

### Claim 1  [PENDING] ✅
> I understand how Tableau behaves under pressure, where performance breaks down, and what it takes to keep dashboards reliable for the people depending on them

*Contexts: employer: BritBox*

- Refresh timeouts are a recurring operational reality, and when they hit, I dig into the underlying cause rather than waiting for someone else to triage
- Worked directly with analysts to optimize their queries and built views to reduce the load driving those timeouts in the first place
  - Proactive approach: built views to prevent timeouts rather than only responding to them

### Claim 2  [PENDING] ✅
> At BritBox, I own the operational reliability of published data sources in Tableau

*Contexts: employer: BritBox*

- Beyond keeping published data sources running, I've worked directly with analysts to optimize their queries
  - Responsible for both uptime and performance optimization of data sources

### Claim 3  [PENDING] ✅
> I work backwards from what analysts need to understand into the query and view design that produces reliable output

*Contexts: employer: BritBox*

- Worked directly with analysts to optimize their queries and built views to reduce the load driving those timeouts
  - Optimization was driven by understanding analyst needs, not just technical constraints
  - Built views as a solution to both performance and usability

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

*No claims extracted.*

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

### Claim 1  [PENDING] ✅
> I built ingestion workflows around health fund, dues, and membership data carrying direct legal obligations, with protected handling at every step because the cost of getting it wrong was legal and organizational

*Contexts: employer: UNITE HERE*

- Owned ingestion workflows for health fund, dues, and membership data with direct legal obligations
  - Protected handling at every step because the cost of getting it wrong was legal and organizational

### Claim 2  [PENDING] ✅
> Operating inside BBC's internal governance framework, I understood that before any tool touched PII, it went through a formal infosec vetting process that could take months, and when a tool didn't clear that process, it didn't get used

*Contexts: employer: BritBox*

- Worked within BBC's formal infosec vetting process for any tool touching PII, which could take months
  - When a tool didn't clear that process, it didn't get used

### Claim 3  [PENDING] ✅
> When formal infosec processes blocked tools, I solved the constraint by self-hosting open-source tooling locked down inside our own domain on provisioned EC2 infrastructure, which kept the work moving without compromising the controls

*Contexts: employer: BritBox*

- Self-hosted open-source tooling locked down inside our own domain on provisioned EC2 infrastructure
  - This approach kept the work moving without compromising the controls
  - Used when formal infosec vetting blocked standard tools

**Conclusion:** This person operates with rare clarity about the difference between compliance theater and actual control — they understand that constraints exist for real reasons, work within them without resentment, and solve around them only when the constraint itself is the problem, not the requirement.

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
> I determined that moving to subscriber grain was the right architectural decision for the business, even though it made the engineering significantly harder

*Contexts: employer: BritBox*

- The vendor had modeled at customer grain, which collapsed subscribers together and made free-trial status invisible — a business requirement that couldn't be met without changing the grain
  - Customer grain collapsed subscribers together
  - Free-trial status was invisible at that grain
- I owned the decision to move to subscriber grain despite knowing it would create a serious performance problem at over a billion events per day
  - Over a billion events per day
  - Per-event range join against a subscription table is a serious performance problem

### Claim 2  [PENDING] ✅
> I work backwards from what the business needs to understand into the data model and performance architecture that makes it possible

- I identified that free-trial status needed to be evaluated per-event by checking whether each watch event fell within a seven-day date window tied to that subscriber's trial start
  - Seven-day date window tied to subscriber's trial start
  - Evaluation required per-event granularity
- I solved the billion-event-per-day range join problem in two parts: advanced Spark partitioning to contain the range evaluation, and a broadcast table of free-trial subscription dates built to increment as new trials open
  - Advanced Spark partitioning to contain the range evaluation
  - Broadcast table of free-trial subscription dates built to increment as new trials open
  - Lookup stays tractable at scale

### Claim 3  [PENDING] ✅
> I had accountability for data integrity and validation at a level that required me to solve the validation problem myself when the existing approach became obsolete

*Contexts: employer: BritBox*

- Moving to a finer grain meant the existing customer-level output could no longer serve as a validation target, so I built a cross-grain rollup from the subscriber output to reconstruct a comparable customer-level number and reconcile against it
  - Built cross-grain rollup from subscriber output
  - Reconstructed comparable customer-level number
  - Reconciled against it for validation

### Claim 4  [PENDING] ✅
> I scoped, solved, and shipped a major architectural change to the watch-duration pipeline with minimal oversight and no meaningful management support

*Contexts: employer: BritBox*

- The project landed with minimal oversight and no meaningful management support — I scoped it, solved it, and shipped it

**Conclusion:** This person makes hard architectural tradeoffs in service of business requirements, owns the full technical and validation problem end-to-end, and operates with complete autonomy under real accountability.

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

### Claim 1  [PENDING] ✅
> I owned the watch duration pipeline end-to-end at BritBox — rebuilt it from scratch in four months alone while carrying all other DE work, defined the metric at the modeling level, made every architectural call without senior review, and have maintained 100% stability since go-live

*Contexts: employer: BritBox*

- When I joined, the vendor-supplied pipeline was failing regularly and the business was making content and product decisions on numbers it couldn't trust
- Rebuilt the pipeline from scratch in four months, alone, while carrying all other DE work
- The front end of the project had never been properly scoped before it landed on me, so I ran discovery and production build simultaneously
- Defined what 'watch duration' actually meant at the metric level, decided how to reconcile events across grains, and made every architectural call without senior review
  - 1B+ events per day in PySpark, Glue, and Redshift
  - The margin for a bad modeling decision was zero — a number that looked plausible but was wrong would have been invisible until a product team had already acted on it
- The pipeline has been 100% stable since go-live
- BritBox's most important content metric — viewership by subscriber tier, recovery rates, premium adoption — now runs on a foundation I designed and own entirely

### Claim 2  [PENDING] ✅
> I work backwards from what the business needs to understand into the metric definition and data model that produces it, treating metric correctness as a non-negotiable constraint on architecture

*Contexts: employer: BritBox*

- I ran discovery and production build simultaneously: defining what 'watch duration' actually meant at the metric level before making architectural decisions
  - Decided how to reconcile events across grains
  - Made every architectural call with the constraint that a plausible-but-wrong number would be invisible to product teams until they had already acted on it

### Claim 3  [PENDING] ✅
> I had accountability for metric integrity at a level where the cost of being wrong was immediate and visible to the business — a standing that is rare for a data engineer

*Contexts: employer: BritBox*

- The business was making content and product decisions on numbers it couldn't trust before I rebuilt the pipeline
- At 1B+ events per day, the margin for a bad modeling decision was zero — a number that looked plausible but was wrong would have been invisible until a product team had already acted on it
- BritBox's most important content metrics — viewership by subscriber tier, recovery rates, premium adoption — now depend entirely on the foundation I designed

**Conclusion:** This person operates at the intersection of technical depth and business accountability — they don't just build pipelines, they own whether the numbers the business acts on are true, and they have the autonomy and judgment to make that call alone under real constraints.

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

- Every downstream question anchored to that data: how many subscribers watched, how long they stayed, how the audience broke down by tier, whether the marketing spend had moved the needle
  - The pipeline was the source of truth for business-critical metrics across the organization
- The vendor pipeline I replaced failed regularly and modeled at a coarser customer grain, which meant those questions either went unanswered or got answered wrong
  - Vendor pipeline had reliability issues
  - Coarser grain meant loss of fidelity in business answers

### Claim 2  [PENDING] ✅
> I rebuilt the pipeline from scratch in four months as the sole dedicated data engineer, doing requirements discovery and production architecture simultaneously with no senior review

*Contexts: employer: BritBox*

- Sole dedicated data engineer responsible for both requirements discovery and production architecture without senior oversight
  - Four-month timeline for complete rebuild
  - No senior review or guidance during execution

### Claim 3  [PENDING] ✅
> I work backwards from what the business needs to understand into the data model and architecture that produces it

*Contexts: employer: BritBox*

- Requirements discovery was done in parallel with production architecture design, grounded in the specific questions the business needed answered
  - Identified that subscriber-grain modeling was required, not coarser customer grain
  - Designed for session stitching and cross-grain reconciliation to ensure answer correctness

### Claim 4  [REJECTED] ❌ (Claim describes the system's technical properties and performance, not the person's ownership or decision-making; should be reframed to center the engineer's action and accountability.)
> My replacement pipeline, built in PySpark on Glue and Redshift at subscriber grain with proper session stitching and cross-grain reconciliation, has had zero failures since go-live

*Contexts: employer: BritBox*

- Zero failures since go-live demonstrates both the correctness of the architecture and the reliability of the implementation
  - Built in PySpark on Glue and Redshift
  - Implemented at subscriber grain
  - Included proper session stitching logic
  - Included cross-grain reconciliation

### Claim 5  [PENDING] ✅
> I had accountability for data integrity at a level that is rare for a data engineer — the entire business's understanding of subscriber behavior depended on the correctness of this pipeline

*Contexts: employer: BritBox*

- Every downstream question anchored to that data, and the vendor pipeline it replaced either went unanswered or got answered wrong
  - Marketing spend attribution depended on accurate watch metrics
  - Audience segmentation by tier depended on correct subscriber-level data
  - Show performance assessment depended on accurate watch duration and subscriber counts

**Conclusion:** This person operates at the intersection of technical depth and business accountability — they don't just build pipelines, they own whether the organization's understanding of its own business is correct.

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

*No claims extracted.*

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
> I have done concrete implementation work in governance and access control, not just policy acknowledgment

*Contexts: employer: BritBox, employer: Universe*

- At BritBox, as the sole data engineer, I authored and provisioned IAM policies, created and managed Secrets, and built out Redshift groups and schemas to enforce role-based access across the data environment
  - IAM policies authored and provisioned
  - Secrets created and managed
  - Redshift groups and schemas built to enforce role-based access
- These were decisions I owned end to end because there was no one else to own them

### Claim 2  [PENDING] ✅
> I work backwards from operational risk into data infrastructure choices — when the application runs on parsed voterfiles and shapefiles powering live campaign operations, a schema violation does not produce a warning, it breaks the field workflow organizers are depending on in real time

*Contexts: employer: Universe*

- I proposed Great Expectations as part of the core data infrastructure at Universe because the application ran on parsed voterfiles and shapefiles powering live campaign operations
  - Great Expectations proposed for core data infrastructure
  - Application dependency: parsed voterfiles and shapefiles
  - Use case: live campaign operations
- a schema violation in that environment does not produce a warning — it breaks the field workflow organizers are depending on in real time

### Claim 3  [PENDING] ✅
> I recognize when data integrity moves from best practice to load-bearing requirement and act accordingly

*Contexts: employer: BritBox, employer: Universe*

- The same instinct that drove my push to implement Great Expectations at Universe drove my push to implement it at BritBox, where the move toward AI-driven tooling has made data integrity a load-bearing requirement rather than a best practice
  - At BritBox: move toward AI-driven tooling identified as inflection point
  - Data integrity status shift: from best practice to load-bearing requirement

**Conclusion:** This person does not separate governance from operational reality — they implement access control and data quality infrastructure because they understand the specific failure modes of the systems they support and who depends on them working.

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

### Claim 1  [PENDING] ✅
> I was assigned the full desk audit of the Canadian local because precision was the requirement and there were a lot of details to get exactly right

*Contexts: employer: UNITE HERE*

- Selected for a high-stakes audit specifically because the work demanded precision and exact detail management

### Claim 2  [PENDING] ✅
> I owned documenting and replicating the Canadian local's dues structure completely so the new membership system could be configured to match it exactly

*Contexts: employer: UNITE HERE*

- The Canadian local carried the most complicated dues structure in the entire international union, with different dues, fees, funds, and contributions all splitting into different GL accounts
  - Multiple dues, fees, funds, and contributions splitting into different GL accounts
  - Most complex structure across the entire international union
- My job was to document and replicate that process completely so the new membership system could be configured to match it exactly

### Claim 3  [PENDING] ✅
> I retained more details exactly than colleagues with decades more dues processing experience

*Contexts: employer: UNITE HERE*

- Two colleagues with decades more dues processing experience made that trip with me, and they were generous enough to say I remembered more details exactly than either of them

**Conclusion:** This person has rare precision and detail retention in complex financial systems work — they were trusted with the most intricate audit in the union and outperformed veterans in exact recall of a complicated multi-account structure.

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

### Claim 1  [PENDING] ✅
> I built and owned custom BI reports and dashboards in SSRS, Power BI, and Sisense, delivered across at least 40 locals throughout the entire international union

*Contexts: employer: UNITE HERE*

- Owned end-to-end delivery of BI infrastructure across a distributed, multi-stakeholder organization
  - SSRS, Power BI, and Sisense as primary tools
  - 40+ locals as distribution footprint
  - International union structure requiring coordination across administrative and leadership levels

### Claim 2  [PENDING] ✅
> The audience ranged from administrative staff in individual locals to top leadership of the international union and local presidents, secretary treasurers, and lead financial staff

*Contexts: employer: UNITE HERE*

- Designed and maintained reporting systems for audiences with radically different technical literacy and decision-making authority
  - Administrative staff in individual locals (operational users)
  - Top leadership of international union (strategic users)
  - Local presidents, secretary treasurers, lead financial staff (mixed technical/non-technical decision-makers)

### Claim 3  [REJECTED] ❌ (Claim describes what the reports did, not what the person built or owned — should be reframed to center the person's agency and accountability for the impact.)
> These were not informational reports sitting in a folder somewhere. They drove strategy at the leadership level and gave financial and membership staff the visibility they needed to audit, operate, and stay healthy

*Contexts: employer: UNITE HERE*

- Reports were mission-critical infrastructure, not artifacts
  - Drove strategy at leadership level
  - Enabled financial and membership staff to audit, operate, and stay healthy
  - High-stakes visibility for organizational health

### Claim 4  [REJECTED] ❌ (Describes the tool's difficulty, not what the person did, owned, or how they work — should be supporting evidence for a real claim, not a claim itself)
> Sisense in particular is a more primitive and harder tool to work with than what most engineers reach for, and getting clean, reliable output out of it for that audience required real work

*Contexts: employer: UNITE HERE*

- Mastered a difficult, non-standard BI tool to meet organizational constraints
  - Sisense characterized as more primitive and harder than standard tools
  - Extracted clean, reliable output despite tool limitations
  - Solved a real technical problem rather than choosing easier path

### Claim 5  [PENDING] ✅
> I work backwards from what someone in a specific seat needs to understand, and build the structure that puts it in front of them

*Contexts: employer: UNITE HERE, employer: Roku*

- Consistent method: requirements-first design, starting from user need rather than tool capability
  - Applied across SSRS, Power BI, Sisense at UNITE HERE
  - Applied to Looker in reporting context at Roku
  - Inverts typical BI workflow — output requirements determine data structure, not vice versa

**Conclusion:** This person owns BI infrastructure end-to-end for complex, multi-stakeholder organizations, and has a rare ability to translate between technical constraints and non-technical decision-making needs. They choose difficult tools when necessary and extract reliable output from them. Their method is consistent across employers and tools: start with what the user needs to understand, then build backwards into the data structure.

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

### Claim 1  [PENDING] ✅
> I ran training and documentation as a standing part of my role alongside every other responsibility I carried

*Contexts: employer: UNITE HERE*

- Training and documentation were integrated into my responsibilities without being my sole focus

### Claim 2  [PENDING] ✅
> I trained organizing staff on secure data collection and how to use our data systems, and I trained leadership on how to run their campaigns effectively with data

*Contexts: employer: UNITE HERE*

- Delivered training to two distinct audiences—organizing staff and leadership—on different aspects of data work
  - Organizing staff training focused on secure data collection and system operation
  - Leadership training focused on campaign effectiveness with data

### Claim 3  [PENDING] ✅
> I wrote documentation that served dual purposes: one version as requirements and acceptance criteria for the system, and a separate one as a baseline for Grace to operate the workflow on her own

*Contexts: employer: UNITE HERE*

- For the Canadian local's desk audit, I created two distinct documentation artifacts tailored to different uses
  - One version functioned as requirements and acceptance criteria for system development
  - A separate version served as operational baseline for dues processor Grace to work independently

### Claim 4  [PENDING] ✅
> When the official application documentation from the union's training staff proved too hard for membership staff to follow, I rewrote it to reflect how the work actually moved through the applications

*Contexts: employer: UNITE HERE*

- The original documentation was modular, organized by feature rather than by how staff actually worked end-to-end, resulting in many pages that were not logically ordered and hard to follow
  - Original structure was feature-based rather than workflow-based
  - Result was pages that lacked logical ordering
- I found that what staff actually needed was less heavy on pictures and explanations and more of a workflow guide
  - Shifted from visual/explanatory approach to task-flow orientation
- I wrote versions that reflected how the work actually moved through the applications
  - Reorganized documentation around actual user workflows rather than system features

### Claim 5  [PENDING] ✅
> I work backwards from how staff actually do their work into the structure and presentation of documentation

*Contexts: employer: UNITE HERE*

- Diagnosed that feature-based documentation failed because it did not match how work actually moved through systems
  - Recognized the gap between system organization and user workflow
  - Rewrote to align documentation with actual task sequences

**Conclusion:** This person takes ownership of making complex systems legible to non-technical users by understanding their actual workflows first, then building documentation and training that matches how they work rather than how the system is organized.

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

### Claim 1  [PENDING] ✅
> At BritBox, I owned the subscriber reporting that told senior leadership whether the product was working

*Contexts: employer: BritBox*

- The CFO, CTO, and CEO read them every month
- These were the numbers that showed how many subscribers the company was gaining from ad campaigns, series premieres, and offers like bundles, discounted memberships, and premium tier exclusives, and how well the business was retaining subscribers when it raised prices or introduced friction in the app

### Claim 2  [PENDING] ✅
> At BritBox, I owned the data model, the pipeline, the validation, and the delivery end-to-end

*Contexts: employer: BritBox*

- I owned the data model, the pipeline, the validation, and the delivery

### Claim 3  [PENDING] ✅
> I performed QA so thoroughly that by the time the numbers reached Carl for review, he trusted they had to be right

*Contexts: employer: BritBox*

- I performed the QA so thoroughly that by the time the numbers reached Carl for review, he trusted they had to be right

### Claim 4  [PENDING] ✅
> I had accountability for data integrity at a level that is rare for a data engineer — the numbers I produced determined how the business understood its own performance

*Contexts: employer: BritBox*

- The CFO, CTO, and CEO read them every month and made decisions based on them
  - These numbers showed subscriber acquisition from campaigns, premieres, and offers
  - These numbers showed retention impact from price increases and app friction

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

*No claims extracted.*

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

*No claims extracted.*

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

*No claims extracted.*

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

*No claims extracted.*

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

- Career path through digital arts, teaching, nonprofit consulting, labor data, and production engineering demonstrates consistent engagement with complex, under-resourced domains

### Claim 2  [PENDING] ✅
> I bring a nontraditional perspective to data engineering shaped by work across digital arts, teaching, nonprofit consulting, labor data, and production engineering

- Diverse background across creative, educational, civic, and technical domains
  - digital arts
  - teaching
  - nonprofit consulting
  - labor data
  - production engineering

**Conclusion:** This person is motivated by high-impact work in under-resourced or technically fragmented environments and brings cross-disciplinary perspective to data problems.

---

## General / Opening
*hash: 140ea0d9919c...*  

**Paragraph:**
> I discovered over my career that I am quite good at understanding people's needs even when they
> are not speaking technical language, that I can ask good questions, and deliver data with
> exacting precision. I can think end to end — the problem space, not just whether specific
> numbers are right.

### Claim 1  [PENDING] ✅
> I am quite good at understanding people's needs even when they are not speaking technical language

- Discovered over career that I can ask good questions and translate across technical/non-technical boundary

### Claim 2  [PENDING] ✅
> I deliver data with exacting precision

- Commitment to precision in data delivery as a consistent professional standard

### Claim 3  [PENDING] ✅
> I think end to end — the problem space, not just whether specific numbers are right

- Approach to work is holistic: understanding the full problem space rather than isolated correctness
  - Distinguishes between local correctness (specific numbers) and systemic correctness (problem space fit)

**Conclusion:** This person operates at the intersection of technical precision and stakeholder understanding — they are rare because they combine exacting execution with the ability to see what the work is actually for.

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

*No claims extracted.*

---

## General / Strengths
*hash: d1bf474f282d...*  

**Paragraph:**
> I am strongest in ambiguous, business-rule-heavy data environments where source systems are
> complex and the output has to be trusted.

### Claim 1  [REJECTED] ❌ (Pure assertion with no specific evidence — names a work environment preference but provides no named project, employer, episode, or pattern that could substantiate it.)
> I am strongest in ambiguous, business-rule-heavy data environments where source systems are complex and the output has to be trusted

- Preference for work where complexity comes from business logic and source system ambiguity rather than scale or tooling
- Drawn to environments where data integrity and correctness are non-negotiable — where the output is relied upon for decisions

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

*No claims extracted.*

---

## General / Strengths
*hash: 392832fe54a6...*  

**Paragraph:**
> I am good at turning very limited direction into well-defined data work.

### Claim 1  [REJECTED] ❌ (This is pure assertion with no specific evidence — it restates the source paragraph verbatim without naming any employer, project, episode, or concrete outcome that would allow substantiation.)
> I am good at turning very limited direction into well-defined data work


---

## General / Strengths
*hash: e1a86878113f...*  

**Paragraph:**
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users do with the product. I think like a full-stack developer in terms of solution design and workflow.

### Claim 1  [PENDING] ✅
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users do with the product

- Finds meaning in end-to-end data work that has direct user impact — not isolated infrastructure but the full chain from model through serving

### Claim 2  [PENDING] ✅
> I think like a full-stack developer in terms of solution design and workflow

- Approaches data problems holistically across the entire stack rather than in isolated layers
  - Considers data model, ingestion, enrichment, and serving as an integrated system
  - Designs solutions with awareness of how each layer affects downstream user experience

**Conclusion:** This person is motivated by data work that has visible product impact and approaches problems with full-stack thinking — not just building components but understanding how they connect to user behavior.

---

## General / Closing
*hash: 55677dd9fb98...*  

**Paragraph:**
> I am most excited by work where careful engineering can make organizations more accountable,
> resilient, and effective — especially in spaces where better tooling can help good people do
> their work with more clarity and confidence.

### Claim 1  [PENDING] ✅
> I am most excited by work where careful engineering can make organizations more accountable, resilient, and effective — especially in spaces where better tooling can help good people do their work with more clarity and confidence

- careful engineering as a lever for organizational accountability, resilience, and effectiveness
- belief that better tooling enables good people to work with more clarity and confidence

---

## Data Engineer / Opening
*hash: 933f2f025965...*  

**Paragraph:**
> I am a data engineer, builder, and systems thinker with a nontraditional path through digital
> arts, teaching, nonprofit consulting, labor data, and production engineering. My strongest work
> has been at the intersection of infrastructure, analytics, and applied problem-solving — in
> environments where the source systems are complex, the requirements are ambiguous, and the
> output has to be trusted.

### Claim 1  [PENDING] ✅
> I work at the intersection of infrastructure, analytics, and applied problem-solving in environments where source systems are complex, requirements are ambiguous, and output has to be trusted

- Nontraditional path through digital arts, teaching, nonprofit consulting, labor data, and production engineering demonstrates comfort operating across domains where ambiguity and complexity are structural
- Strongest work has been where source systems are complex, requirements are ambiguous, and output has to be trusted

### Claim 2  [PENDING] ✅
> I am a systems thinker who builds infrastructure and analytics solutions

- Self-identified as builder and systems thinker across multiple domains

### Claim 3  [PENDING] ✅
> I am drawn to work where careful engineering and data integrity directly enable organizational accountability and decision-making

- Career pattern shows sustained engagement with labor data, nonprofit consulting, and production systems — domains where data quality directly affects stakeholder trust and outcomes

**Conclusion:** This person operates effectively in high-ambiguity environments where technical rigor and cross-domain thinking are prerequisites — not a specialist in one tool or domain, but someone who builds trustworthy systems under structural uncertainty.

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
> I am strongest in ambiguous, business-rule-heavy data environments where source systems are complex and the output has to be trusted absolutely

- At BritBox, owned a business-critical AWS/Spark/PySpark pipeline for high-volume streaming viewership data where the output had to be trustworthy
- Raw data was stored in Redshift as an external table with more than 800 columns and included duplicates, late-arriving records, timing edge cases, and session behavior that had to be handled carefully

### Claim 2  [PENDING] ✅
> At BritBox, I was the only dedicated data engineer for almost two years and owned the viewership pipeline end to end

*Contexts: employer: BritBox*

- Owned the solution end to end: figuring out how the raw events behaved, deciding how the pipeline should model sessions and watch duration, building the Glue/Spark replacement, and validating that the output was correct enough to support core reporting
- Sole dedicated data engineer responsible for a business-critical pipeline serving core reporting

### Claim 3  [PENDING] ✅
> I work backwards from what the output needs to be into the logic and data model that produces it, validating assumptions and refining calculations until the result is trustworthy

*Contexts: employer: BritBox*

- Inherited nominal and partially inaccurate documentation from a former consultancy, so a significant part of my role was validating the logic, identifying where it broke down, and refining the session timing and duration calculations so the resulting data would be trustworthy
  - Session IDs reset at midnight, so events had to be stitched across that boundary to calculate watch duration correctly
  - One of the hardest issues was handling this session boundary crossing
- Decided how the pipeline should model sessions and watch duration before building the replacement

### Claim 4  [PENDING] ✅
> I have deep technical ownership of Spark and PySpark at scale, including advanced concepts needed to handle high-volume data efficiently

*Contexts: employer: BritBox*

- Had to teach myself more advanced Spark concepts in PySpark in order to handle the scale efficiently
  - Data volume required optimization beyond basic Spark usage
- Built a Glue/Spark replacement that ran in a fraction of the time and handled the source volume much better than the prior process

### Claim 5  [PENDING] ✅
> I make the logic behind complex data pipelines explicit and supportable, not just functional

*Contexts: employer: BritBox*

- The new Spark solution made the logic behind the watch metrics explicit and supportable
  - Replaced a process with unclear or poorly documented logic with one where the reasoning was transparent
- Stopped the frequent failures we had seen with the prior process

### Claim 6  [PENDING] ✅
> I have accountability for data integrity at a level that is rare — I validate that output is correct enough to support core business reporting, not just that the pipeline runs

*Contexts: employer: BritBox*

- Validating that the output was correct enough to support core reporting
  - Owned validation of watch metrics used in core business reporting
- A significant part of my role was validating the logic, identifying where it broke down, and refining calculations so the resulting data would be trustworthy

**Conclusion:** This person operates independently under high accountability in technically complex, ambiguous environments where data integrity is non-negotiable. They work backwards from business requirements into technical solutions, own the full lifecycle of critical systems, and are driven by the need to make complex data trustworthy and transparent.

---

## Data Engineer / BritBox DynamoDB and Business Logic
*hash: 990d19ff2977...*  

**Paragraph:**
> I also built a DynamoDB-based logging system for BritBox's event stream pipeline — one of the most business-critical data systems the company operated. I built it with proper structure, observability, and documented logic because I understood what was depending on it. Over my time at BritBox I also worked out the business logic for much of the subscription metrics the company had been reporting on for years, and I replaced one of the most business-critical event stream pipelines single-handedly — improving the logic in the process.

### Claim 1  [PENDING] ✅
> At BritBox, I built a DynamoDB-based logging system for one of the most business-critical data systems the company operated

*Contexts: employer: BritBox*

- Built the system with proper structure, observability, and documented logic because I understood what was depending on it
  - DynamoDB-based implementation
  - Logging system for event stream pipeline
  - Proactive documentation and observability design driven by understanding of downstream dependencies

### Claim 2  [PENDING] ✅
> At BritBox, I worked out the business logic for much of the subscription metrics the company had been reporting on for years

*Contexts: employer: BritBox*

- Determined the underlying business logic for subscription metrics that had been in use for years
  - Reverse-engineered or clarified metric definitions
  - Owned the logical foundation of reporting the company relied on

### Claim 3  [PENDING] ✅
> At BritBox, I replaced one of the most business-critical event stream pipelines single-handedly and improved the logic in the process

*Contexts: employer: BritBox*

- Owned the full replacement of a business-critical pipeline without support
  - Single-handed execution on high-stakes system
  - Improved the logic during replacement — not just a lift-and-shift but an optimization

**Conclusion:** Across BritBox's most critical data systems, this person operated with both technical depth and business accountability — building systems others depended on, clarifying the logic underneath years of reporting, and improving high-stakes pipelines under solo ownership.

---

## Data Engineer / BritBox Live Troubleshooting
*hash: 6b44253cecc6...*  

**Paragraph:**
> At BritBox, some of the most demanding work involved pipelines I inherited rather than built. One was a business-critical cron job running off an EC2 machine that failed repeatedly due to character limit violations on fields that upstream systems were supposed to gate, compounded by volume and file size issues. I had to diagnose failures in code I did not write, under deadline pressure, while keeping a job that fed core reporting running with nominal downtime. Owning reliability on a system you did not design — in production, with no dev buffer — sharpens how you think about observability, failure modes, and what it actually means to own a pipeline.

### Claim 1  [PENDING] ✅
> I owned reliability on a system I did not design — in production, with no dev buffer — which sharpened how I think about observability, failure modes, and what it actually means to own a pipeline

*Contexts: employer: BritBox*

- Inherited a business-critical cron job running off an EC2 machine that failed repeatedly due to character limit violations on fields that upstream systems were supposed to gate, compounded by volume and file size issues
  - Character limit violations on fields from upstream systems
  - Volume and file size issues compounding failures
  - Business-critical job feeding core reporting
- Had to diagnose failures in code I did not write, under deadline pressure, while keeping a job that fed core reporting running with nominal downtime
  - Diagnosed inherited code under deadline pressure
  - Maintained nominal downtime on core reporting dependency

### Claim 2  [PENDING] ✅
> I work backwards from failure modes and observability constraints when inheriting production systems

*Contexts: employer: BritBox*

- Owning reliability on a system you did not design — in production, with no dev buffer — sharpens how you think about observability, failure modes, and what it actually means to own a pipeline

**Conclusion:** This person has rare experience taking accountability for inherited production systems under real constraints, which has built a specific discipline around observability and failure-mode thinking that most engineers only develop when building from scratch.

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
> I owned the month-end subscriber reporting pipeline and determined what the data model needed to be before redesigning it

*Contexts: employer: None*

- The existing Type 3 slowly changing dimension model could capture some current and prior subscriber attributes but did not preserve a full history of state changes over time
  - When product introduced new recovery logic and launched a premium tier, subscription status, plan type, recovery state, and effective dates all became more complex than the model could handle
- I redesigned the model to move toward an effective-dated subscriber history model, essentially a Type 2 slowly changing dimension
  - The model preserved each version of the subscriber record with effective start and end dates
  - This made it possible to reconcile churn, recovery, premium-tier reporting, and month-end subscriber counts against the customer state that was valid for the reporting period

### Claim 2  [PENDING] ✅
> I work backwards from what needs to be reported into the data model that makes it possible to reconcile and explain discrepancies

- I could trace counts back to the customer statuses, state changes, effective dates, and business rules that produced them
  - The reporting logic had to select the correct subscriber version for each reporting date
  - Discrepancies became explainable rather than opaque

### Claim 3  [PENDING] ✅
> I had accountability for data integrity at a level where I owned whether reported subscriber counts were correct and traceable to the business logic that produced them

- The tradeoff was added complexity in the model and joins, because the reporting logic had to select the correct subscriber version for each reporting date
  - The benefit was that discrepancies became explainable: I could trace counts back to the customer statuses, state changes, effective dates, and business rules that produced them

**Conclusion:** This person does not just build pipelines but owns whether the data model is right for the business problem — they think backwards from what needs to be true about the output into the structure that makes it provable.

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

- Conducted desk audits of complex dues-processing workflows across the union
  - Worked with dues, health fund, grievance, financial, membership, and PII data
  - Audits spanned many local union chapters
- Trusted with this work because of attention to detail, respect for existing process flow, and seriousness required to preserve how the work functioned while identifying what needed to change

### Claim 2  [PENDING] ✅
> I work across operational boundaries—maintaining relationships with local staff, gathering requirements, documenting issues, and translating operational needs into database changes, custom reports, SQL validation scripts, and user-facing workflows

*Contexts: employer: UNITE HERE*

- Maintained relationships with local staff across many local chapters
- Gathered requirements and documented issues from operational staff
- Translated operational needs into database changes, custom reports, SQL validation scripts, and user-facing workflows
  - Worked across many local chapters
  - Handled sensitive data: dues, health fund, grievance, financial, membership, and PII

### Claim 3  [PENDING] ✅
> I had accountability for preserving the integrity of complex union workflows while making them more auditable and correct

*Contexts: employer: UNITE HERE*

- Trusted to audit the union's most complex dues-processing workflows
  - Required to preserve how the work functioned while identifying what needed to change
  - Worked with high-stakes union data across multiple chapters

---

## Data Engineer / UNITE HERE
*hash: 88739a7f600b...*  

**Paragraph:**
> I examined systems and relationships on every level — from the challenges of organizer data
> entry on different devices with spotty internet access to the full desk audit of the most
> complex dues structure in the entire international union. UNITE HERE entrusted me with this
> sole responsibility.

*No claims extracted.*

---

## Data Engineer / UNITE HERE
*hash: 03a18b88be39...*  

**Paragraph:**
> My experience with highly skilled administrative staff processing dues and stringent financial
> reporting taught me how crucial it is for systems to support human beings' ability to review
> changes and trust the validity of their records.

### Claim 1  [PENDING] ✅
> I learned from working with highly skilled administrative staff that systems must support human ability to review changes and trust the validity of their records

- Worked with highly skilled administrative staff processing dues and stringent financial reporting
  - Staff were processing dues
  - Financial reporting was stringent
- Systems must support human beings' ability to review changes and trust the validity of their records

### Claim 2  [PENDING] ✅
> I am oriented toward building systems that make it possible for non-technical staff to verify and trust what they're working with

- Recognizes that skilled administrative staff need systems designed for human review and verification, not just technical correctness
  - This orientation emerged from direct experience with financial reporting workflows
  - Understands the gap between what systems do and what humans need to see

**Conclusion:** This person builds systems with the end user's need for transparency and verifiability as a first-class concern, not an afterthought.

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

*No claims extracted.*

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

### Claim 1  [PENDING] ✅
> I designed an AI-assisted contract intelligence application that converts unstructured contract PDFs into structured, verifiable data that union officers can operationalize

*Contexts: project: CBA Clock*

- The app scans PDF copies of collective bargaining agreements and converts key contract provisions into structured JSON records
  - Extracts time-sensitive contract rules: grievance filing deadlines, escalation windows, arbitration deadlines, contract expiration dates, negotiation notice periods, and reopener windows
- Records can be reviewed, corrected, and approved by users before being used operationally
- Once extracted and verified, these rules can be used to generate custom calendars, reminders, and timeline views so union officers can track which contractual deadlines apply to specific grievances and upcoming bargaining events

### Claim 2  [PENDING] ✅
> I built the application around structured extraction, retrieval, user verification, and a real data model because I do not think AI output is useful until someone can review it, trace it, and decide whether it belongs in the workflow

*Contexts: project: CBA Clock*

- Architecture prioritizes human verification and traceability over raw AI output
  - Structured extraction ensures data can be reviewed
  - Retrieval layer enables tracing back to source
  - User verification gate before operational use
  - Real data model enforces schema compliance
- I do not think AI output is useful until someone can review it, trace it, and decide whether it belongs in the workflow

### Claim 3  [PENDING] ✅
> I identified a specific operational need in union contract management — tracking time-sensitive deadlines across grievances and bargaining events — and built a system to solve it end-to-end

*Contexts: project: CBA Clock*

- The initial focus is on time-sensitive contract rules: grievance filing deadlines, escalation windows, arbitration deadlines, contract expiration dates, negotiation notice periods, and reopener windows
  - These are the rules union officers need to track operationally
- The system generates custom calendars, reminders, and timeline views so union officers can track which contractual deadlines apply to specific grievances and upcoming bargaining events
  - Output is designed for how union officers actually work

**Conclusion:** This person builds systems where AI is a tool for extraction but human judgment and verification are non-negotiable gates before operational use. They think about data integrity and auditability as foundational, not optional. They identify real problems in specific domains and own the full stack from problem definition through user-facing output.

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

### Claim 1  [PENDING] ✅
> I built a system designed around human-verified AI extraction rather than fully automated legal interpretation, because missing a filing or escalation window in grievance tracking can have serious consequences

*Contexts: project: Union grievance tracking and contract analysis system*

- The app is designed around human-verified AI extraction rather than fully automated legal interpretation
  - Union officers need to track multiple active grievances under different versions of a contract, with different deadlines, escalation rules, and procedural requirements
  - Missing a filing or escalation window can have serious consequences

### Claim 2  [PENDING] ✅
> I am interested in turning dense contract language into structured, auditable, time-aware data that helps unions preserve rights, avoid missed deadlines, and prepare more strategically for negotiations

*Contexts: project: Union grievance tracking and contract analysis system*

- The goal is to turn dense contract language into structured, auditable, time-aware data that helps unions preserve rights, avoid missed deadlines, and prepare more strategically for negotiations
- Longer term, I am interested in adding comparative analysis features that allow unions to evaluate contract language across agreements
  - Identifying missing protections, comparing grievance procedures or reopener language
  - Helping unions understand where current language may be weaker than language they have secured elsewhere

### Claim 3  [PENDING] ✅
> I built this because CBAs are some of the most important documents a union possesses, and I wanted to create something that could support more critical analysis, more effective organization, and more intentional planning around case building

*Contexts: project: Union grievance tracking and contract analysis system*

- CBAs are some of the most important documents a union possesses
- I wanted to create something that could support more critical analysis, more effective organization, and more intentional planning around case building

**Conclusion:** This person builds systems where the stakes of failure are high and the consequences of human error are serious — and they design for that reality by centering human judgment and verification rather than automation for its own sake. They are motivated by structural inequality and the tools that help organizations defend their rights.

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
> I build RAG and agentic applications in domains where accuracy and human judgment are especially consequential

- Currently building RAG and agentic applications with focus on high-stakes decision contexts

### Claim 2  [PENDING] ✅
> I own a system that uses Claude to analyze GitHub repositories, targets AWS Glue jobs with specific build patterns, and grades capacity and failure probability based on forecasted data volumes

*Contexts: project: AWS Glue job capacity and failure forecasting system*

- Built a system using Claude to read over a GitHub repository, targets AWS Glue jobs with certain build patterns, and grades each job's capacity and probability of failure based on forecasted data volumes
  - Uses Claude for repository analysis
  - Targets AWS Glue jobs with specific build patterns
  - Grades capacity and failure probability
  - Incorporates forecasted data volumes

### Claim 3  [PENDING] ✅
> I work backwards from failure modes and data patterns into predictive recommendations about resource scaling and refactoring

*Contexts: project: AWS Glue job capacity and failure forecasting system*

- Evaluating, based on how data is read and updated, a forecasted point at which a failure might become likely — and making a recommendation about when to increase resources or when to have the job refactored
  - Analyzes data read and update patterns
  - Forecasts failure likelihood at specific points
  - Recommends resource increases or refactoring decisions

### Claim 4  [PENDING] ✅
> I am focused on how data governance and data quality enforced by data engineering flow through AI applications

- Focused on how data governance and data quality enforced by data engineering flow through AI applications

**Conclusion:** This person builds AI systems in high-stakes domains by working backwards from failure modes into predictive recommendations, with a consistent orientation toward ensuring that data engineering rigor and governance flow through AI decision-making.

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

### Claim 1  [PENDING] ✅
> I see both the value and the ways LLMs can create friction when requirements are specific

- LLMs often need more context and constraint than people expect
- They can miss, override, or inconsistently apply requirements while still producing fluent output that looks plausible

### Claim 2  [PENDING] ✅
> I am skeptical of large general-purpose models trained on broad, opaque datasets where publishers do not make model weights or training data public

- The opacity of training data and closed model weights creates risk when requirements are specific

### Claim 3  [PENDING] ✅
> For data engineers, the infrastructure around the model is critical — governance, observation, testing, and evaluation are imperative when doing anything with AI related to data

- A product needs to control what context the model receives, what data it can access, how output quality is checked, and how failures are caught before they affect the user
  - Context control is a requirement, not optional
  - Data access must be governed
  - Output quality checking must be built in
  - Failure detection must happen before user impact

### Claim 4  [PENDING] ✅
> An LLM-powered product can easily become a system that looks helpful while making the human do more work to correct it without proper infrastructure controls

- Fluent output that is incorrect creates hidden work for users rather than reducing it

**Conclusion:** This person approaches AI infrastructure with skepticism grounded in technical reality — they understand that LLM capability and fluency can mask requirement failures, and they are motivated by building systems where governance and observation prevent that failure mode from reaching users.

---

## Data Engineer / LLM and AI Judgment
*hash: 616dca5cb0b2...*  

**Paragraph:**
> One of the most difficult parts of integrating AI into realms of work and documents is that it
> creates ambiguity around validity, so human-in-the-loop review is especially important.

### Claim 1  [PENDING] ✅
> Human-in-the-loop review is especially important when integrating AI into work and documents because it creates ambiguity around validity

- Recognizes that AI integration introduces validity ambiguity that requires human oversight

**Conclusion:** This person thinks about AI integration with accountability for correctness — they see human review not as optional but as structurally necessary when validity is at stake.

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
> I am drawn to work where careful system design makes analysis and decision-making visible and assisted by technology

- The complexity of systems interoperability — integrating new, evolving technologies — is where I want to build
- I am interested in how humans can interact and engage with technologies as part of a well-designed data system
- I find meaning in understanding how work can be improved and how analysis and decision-making can be something that technology exposes and assists

### Claim 2  [PENDING] ✅
> I approach system design by centering how humans will interact with and understand the technology

- I think about systems interoperability problems by considering how humans engage with the resulting technology
  - The focus is on making analysis and decision-making visible through the system design

**Conclusion:** This person is motivated by the intersection of technical complexity and human usability — they want to build systems where technology actively enables better decision-making, not just processes data.

---

## Data Engineer / LLM and AI Judgment
*hash: 7d991e355fc6...*  

**Paragraph:**
> My dream for this technology is that it can produce meaningful learning experiences as well as
> encourage inquiry and deeper thinking.

### Claim 1  [REJECTED] ❌ (The source paragraph contains only a stated aspiration with no specific evidence, episodes, or named work that could substantiate the claim.)
> I see technology as a vehicle for producing meaningful learning experiences and encouraging inquiry and deeper thinking

- This is an explicit statement of what the person finds meaningful in technology work
  - The dream centers on learning outcomes, not just technical delivery
  - Emphasis on inquiry and deeper thinking suggests orientation toward cognitive development, not surface-level engagement

**Conclusion:** This person is motivated by technology that serves human development and intellectual growth, not just functional outcomes.

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
> The opacity of how generative AI systems classify and route prompts into tools shapes what models can actually do with a request in ways users have no visibility into or control over

- Prompt routing and classification operates as a limiting factor that is opaque to users
  - This mechanism determines what the model can actually do with a given request
  - Users have no visibility into or control over this routing behavior

### Claim 2  [PENDING] ✅
> Much of what generative AI companies claim as 'intelligence' is aspirational rather than reliable, particularly because the breadth of claimed capabilities makes precise alignment with specific user constraints unreliable

- The breadth of what these models claim to do makes precise alignment with a user's specific constraints and requirements unreliable
  - This unreliability is a direct consequence of the scope of claimed capabilities
  - The gap between aspiration and actual reliable performance is significant

**Conclusion:** This person understands generative AI systems at a level that distinguishes between marketing claims and actual technical constraints — they see the architectural and operational limits that create gaps between what these systems advertise and what they can reliably deliver to users with specific requirements.

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

### Claim 1  [PENDING] ✅
> I am known as a forward thinker and a creative thinker

- People who have worked with me know me this way

### Claim 2  [PENDING] ✅
> I have done serious work largely on my own — proposing architecture, owning decisions, debugging what broke

- Proposing architecture without being told how
- Owning decisions end-to-end
- Debugging what broke — accountability for correctness in production

### Claim 3  [PENDING] ✅
> I advance through honest analysis of what I built and why

- Honest analysis of outcomes and reasoning — a consistent method for improving work

### Claim 4  [PENDING] ✅
> I enjoy building relationships with people and understanding their needs around data

- Actively seeks to understand what people need around data

### Claim 5  [PENDING] ✅
> I am ready to work somewhere with strong engineers around me where the collaboration and feedback match the level of work I am doing and want to do

- Seeking peer-level collaboration and feedback as a condition for doing best work
  - Values working alongside strong engineers
  - Expects feedback quality to match the work's ambition

**Conclusion:** This person operates independently at a high level but is motivated by collaborative environments where peer feedback and relationship-building around data needs are central to the work.

---

## Data Engineer / Worker and Teammate
*hash: c46c8f29eb78...*  

**Paragraph:**
> I am good at honing in on the questions and concerns people most want to get at, especially
> when the existing system is hard to explain or the business rules are still taking shape.

### Claim 1  [PENDING] ✅
> I hone in on the questions and concerns people most want to get at, especially when the existing system is hard to explain or the business rules are still taking shape

- Can identify what people actually need to understand even when systems are opaque or requirements are still forming

---

## Data Engineer / Worker and Teammate
*hash: 779ad2f88500...*  

**Paragraph:**
> I have spent much of my career in roles where I wore a lot of hats and had to coordinate
> information with stakeholders who were not always technical and translate their needs into work.
> I have worked closely with BI, analytics, and engineering teams, and I have experience in
> front-end work, UX design, testing, and evaluation. I take intense pride in data integrity.

### Claim 1  [PENDING] ✅
> I have spent much of my career in roles where I wore a lot of hats and had to coordinate information with stakeholders who were not always technical and translate their needs into work

- Operated across multiple domains without clear role boundaries, requiring independent judgment about what work needed doing and how to communicate it across technical and non-technical audiences

### Claim 2  [PENDING] ✅
> I have worked closely with BI, analytics, and engineering teams, and have experience in front-end work, UX design, testing, and evaluation

- Cross-functional exposure across data, product, and engineering domains — able to speak the language of multiple technical specialties and understand their constraints
  - BI and analytics teams
  - engineering teams
  - front-end work
  - UX design
  - testing and evaluation

### Claim 3  [PENDING] ✅
> I take intense pride in data integrity

- Data integrity is a core professional value — not a task to complete but a standard that shapes how work is approached

**Conclusion:** This person operates at the intersection of technical and non-technical work, with the ability to translate across boundaries and the discipline to maintain standards others might overlook under pressure.

---

## Data Engineer / Worker and Teammate
*hash: 96fb0baace76...*  

**Paragraph:**
> I bring rigorous documentation, quality checks, and scalability thinking to my work regardless of whether they are formally required — and I advocate for those standards on the work around me. At BritBox, where the engineering culture did not prioritize documentation, ticketing, or quality review, I documented my own changes, ran validation, raised concerns about design and scalability decisions, and continued to do so even when those concerns were not always taken up — because I understood what the pipelines were supporting and who was depending on the output.

*No claims extracted.*

---

## Data Engineer / Mission-Driven Work
*hash: 79508c9e791e...*  

**Paragraph:**
> My career has repeatedly brought me back to mission-driven data work, including union data,
> political data, membership and finance reporting, voter roll data, and stakeholder-facing
> systems.

*No claims extracted.*

---

## Data Engineer / Mission-Driven Work
*hash: fca6b17d67a9...*  

**Paragraph:**
> My first job was with Gateways Program for Incarcerated Youth, where I managed a mentorship
> program for young men in a juvenile maximum-security facility. I later spent years working in
> the labor sector, where access to stable employment, dignity at work, and the practical needs
> of working people were always central to the mission.

*No claims extracted.*

---

## Data Engineer / Mission-Driven Work
*hash: 509e4b23b4b3...*  

**Paragraph:**
> Thinking together with a team on what tools and features can best serve the needs of people
> doing hard work on the ground is one of the things that has given me the greatest sense of
> purpose in my career.

### Claim 1  [PENDING] ✅
> I find the greatest sense of purpose in thinking together with a team on what tools and features can best serve the needs of people doing hard work on the ground

- This is explicitly stated as what has given the person the greatest sense of purpose in their career
  - The work involves collaborative thinking with a team
  - The focus is on understanding and serving people doing hard work on the ground
  - The outcome is determining what tools and features best meet those needs

**Conclusion:** This person is drawn to work where they can directly improve the effectiveness of practitioners through thoughtful tool design and feature prioritization — work that requires both technical judgment and empathy for the constraints of real-world use.

---

## Data Engineer / Mission-Driven Work
*hash: add6158dba2b...*  

**Paragraph:**
> I have also managed large, ambiguous projects end to end: defining scope, translating
> requirements, leading technical conversations, building the implementation, and validating
> that the result was correct enough to support strategic decisions.

*No claims extracted.*

---

## Data Engineer / Mission-Driven Work
*hash: 04f61aa5a9ff...*  

**Paragraph:**
> I have owned large production data projects end to end, worked extensively in AWS-heavy
> environments, and built pipelines where reliability, governance, backfills, validation, and
> observability mattered.

### Claim 1  [PENDING] ✅
> I have owned large production data projects end to end

- Responsible for full lifecycle of production data systems from conception through operation

### Claim 2  [PENDING] ✅
> I worked extensively in AWS-heavy environments

- Deep operational experience across AWS infrastructure and services

### Claim 3  [PENDING] ✅
> I built pipelines where reliability, governance, backfills, validation, and observability mattered

- Designed and implemented data pipelines with explicit attention to reliability, governance, backfills, validation, and observability as first-class concerns
  - reliability: ensuring pipelines run consistently and recover from failures
  - governance: controlling data access, lineage, and compliance
  - backfills: handling historical data reprocessing
  - validation: verifying data correctness at pipeline stages
  - observability: instrumenting pipelines to surface failures and anomalies

---

## Data Engineer / Mission-Driven Work
*hash: 0649ea9be276...*  

**Paragraph:**
> In my last role, I supported analytics and data science teams by building production pipelines,
> improving workflow reliability, and pushing for stronger validation, governance, and
> infrastructure-as-code practices.

### Claim 1  [PENDING] ✅
> I built production pipelines that supported analytics and data science teams

*Contexts: employer: last role*

- owned production pipeline infrastructure serving downstream analytics and data science work

### Claim 2  [PENDING] ✅
> I improved workflow reliability through validation, governance, and infrastructure-as-code practices

*Contexts: employer: last role*

- pushed for stronger validation practices in pipeline workflows
- implemented governance practices to increase system reliability
- adopted infrastructure-as-code to make pipeline systems reproducible and maintainable

### Claim 3  [PENDING] ✅
> I advocated for engineering practices—validation, governance, infrastructure-as-code—that others were not yet prioritizing

*Contexts: employer: last role*

- pushed for stronger validation, governance, and infrastructure-as-code practices
  - these practices were not yet standard in the team's workflow

---

## Data Engineer / Why This Role
*hash: 95094f0c529c...*  

**Paragraph:**
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users can do with a product or with their decisions. The engineering decisions closest to the data are the ones that determine whether the output is trustworthy, and trustworthy output is what I care about building. I want to be in roles where getting the data right is what makes the product work.

### Claim 1  [PENDING] ✅
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users can do with a product or with their decisions

- The engineering decisions closest to the data are the ones that determine whether the output is trustworthy
- Trustworthy output is what I care about building

### Claim 2  [PENDING] ✅
> I want to be in roles where getting the data right is what makes the product work

- The engineering decisions closest to the data are the ones that determine whether the output is trustworthy, and trustworthy output is what I care about building

**Conclusion:** This person is drawn to data engineering work where technical rigor directly enables user capability and decision-making — where data integrity is not a compliance requirement but the load-bearing foundation of product value.

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
> I am drawn to work on privacy and the open web because I have seen technology fail to give people agency in spaces where it should help them learn, organize, build, and do hard work

- I have spent years in spaces where technology is supposed to help people learn, organize, build, and do hard work with more agency, but it so often does the opposite

### Claim 2  [REJECTED] ❌ (Pure values assertion with no specific work, decision, or outcome to substantiate it — belongs in a personal statement, not an argument claim)
> I believe the internet should not be rooted in deceptive user agreements or corporations mining people's behavior, attention, and data while undervaluing their rights, contributions, and expertise

- I do not think the internet should be rooted in deceptive user agreements or corporations mining people's behavior, attention, and data while undervaluing the rights, contributions, and expertise of people

**Conclusion:** This person is motivated by a specific ethical orientation: building technology that restores agency and transparency rather than extracting value from users.

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
> At Universe, I owned the data-serving layer end-to-end as the first data engineer, with no mature infrastructure in place and product correctness entirely dependent on my work being right

*Contexts: employer: Universe*

- Built data infrastructure from scratch at a seed-stage startup where the product depended on backend data being correct
  - Parsed, modeled, and served voter files, shapefiles, GPS data, and campaign data
  - If that data was wrong, the product was wrong: the voter universe, the boundaries, the field workflow, and the organizer's trust in the tool
- My backend work ran in the live application used to run real campaigns
  - Organizers used maps and field workflows powered by this data in the field

### Claim 2  [PENDING] ✅
> I work backwards from what the product needs to understand into the data model and infrastructure that produces it

*Contexts: employer: Universe*

- Researched and suggested infrastructure, wrote RFCs, and helped build the data-serving layer the product needed almost entirely from scratch
  - Worked with guidance from the CEO to understand what the product required
  - Shipped quickly with the backend work running in the live application

### Claim 3  [PENDING] ✅
> I had accountability for data integrity at a level that is rare for a first data engineer—the entire product's correctness and user trust depended on my work

*Contexts: employer: Universe*

- As the first data engineer at a seed-stage startup with no mature data infrastructure, I was solely responsible for whether voter universes, boundaries, field workflows, and organizer trust in the tool were correct
  - The product was data-driven down-ballot canvassing—if the data was wrong, the product was wrong

### Claim 4  [PENDING] ✅
> I learned to write better code and think more carefully about infrastructure by working in a strong TypeScript backend and improving my Python

*Contexts: employer: Universe*

- Worked from a strong TypeScript backend, learned generics and linting, improved the quality of my Python code

### Claim 5  [PENDING] ✅
> I find meaning in work where careful engineering makes organizations more accountable and effective

*Contexts: employer: Universe*

- I was proud of the backend data work I shipped because it powered a data-driven canvassing app used in real campaigns, where the integrity of voter data, boundaries, and field workflows directly enabled organizers to do their work
  - The app was used to run real campaigns
  - Organizers depended on the correctness of the data to trust and use the tool

**Conclusion:** This person built critical data infrastructure under high accountability as a first data engineer at a seed stage, learned to think about code quality and infrastructure rigorously, and is motivated by work where engineering directly enables organizations to function better.

---

## Backend Engineer / Opening
*hash: 97b633bd9187...*  

**Paragraph:**
> I am a data engineer and builder with production experience across the full stack — data pipelines, infrastructure, APIs, and user-facing data services. I think like a full-stack developer in terms of solution design: the data model, the API contract, the ingestion logic, and the serving layer are a connected system. At Universe, a seed-stage down-ballot canvassing application, I was the first dedicated data engineer and built the data infrastructure from the ground up — parsing voter files, GPS and shapefile data, and campaign data. I worked from a strong TypeScript backend with generics and linting, and built the Python data layer with nox and mypy. The data I built and served powered the core functionality of a live application used in real campaigns.

### Claim 1  [PENDING] ✅
> I think like a full-stack developer in terms of solution design: the data model, the API contract, the ingestion logic, and the serving layer are a connected system

- Approaches data infrastructure as an integrated system where schema, API design, ingestion, and serving are interdependent

### Claim 2  [PENDING] ✅
> At Universe, I was the first dedicated data engineer and built the data infrastructure from the ground up

*Contexts: employer: Universe*

- Sole data engineer at seed stage; owned the entire data infrastructure lifecycle with no prior data systems in place
  - Parsing voter files, GPS and shapefile data, and campaign data
  - Built Python data layer with nox and mypy
  - Worked from a strong TypeScript backend with generics and linting
- The data I built and served powered the core functionality of a live application used in real campaigns
  - Direct accountability for data correctness in production canvassing application

### Claim 3  [PENDING] ✅
> I have production experience across the full stack — data pipelines, infrastructure, APIs, and user-facing data services

- Demonstrated end-to-end ownership from ingestion through serving layer in production systems
  - Data pipelines: voter files, GPS, shapefile parsing
  - Infrastructure: Python data layer tooling (nox, mypy)
  - APIs: designed API contracts as part of integrated system
  - User-facing services: live application in real campaigns

---

## Backend Engineer / Technical
*hash: 3063933e6857...*  

**Paragraph:**
> At Universe I worked from a strong TypeScript backend, learned generics and linting, improved the quality of my Python code, researched and suggested infrastructure, wrote RFCs, and helped build the data-serving layer the product needed almost entirely from scratch. I parsed voter files, GPS and shapefile data, and campaign data so organizers could use the field workflows in the field. If that data was wrong, the product was wrong. I have also built REST APIs in FastAPI, worked with Elasticsearch, Docker, and Terraform, and built data-centric applications where the model and serving logic are tightly integrated with the product.

*No claims extracted.*

---

## Backend Engineer / Why This Role
*hash: 44dca902673a...*  

**Paragraph:**
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users do with the product. At Universe, how I parsed and structured voter files, GPS data, and campaign data was what made the organizer's field workflows function. I am drawn to backend roles where the problem space has real complexity. Cleaning and structuring messy, nuanced data across union locals, organizing campaigns, and research contexts is work I have repeatedly excelled at throughout my career.

### Claim 1  [PENDING] ✅
> I am most passionate about data engineering when the data model, ingestion layer, enrichment logic, and serving layer directly shape what users do with the product

- At Universe, how I parsed and structured voter files, GPS data, and campaign data was what made the organizer's field workflows function
  - voter files, GPS data, and campaign data were the specific data types
  - the parsing and structuring directly enabled organizer field workflows

### Claim 2  [PENDING] ✅
> I am drawn to backend roles where the problem space has real complexity

- Cleaning and structuring messy, nuanced data across union locals, organizing campaigns, and research contexts is work I have repeatedly excelled at throughout my career
  - union locals, organizing campaigns, and research contexts as domains with messy, nuanced data
  - pattern of repeated excellence across these contexts

### Claim 3  [PENDING] ✅
> I owned the parsing and structuring of voter files, GPS data, and campaign data at Universe, and this work directly enabled organizer field workflows

*Contexts: employer: Universe*

- How I parsed and structured voter files, GPS data, and campaign data was what made the organizer's field workflows function
  - voter files, GPS data, campaign data as the data sources
  - parsing and structuring as the technical work
  - organizer field workflows as the downstream user impact

**Conclusion:** This person finds meaning in backend data work where technical decisions directly enable user workflows, and has built a pattern of excelling at the messy, domain-specific data structuring problems that most engineers avoid.

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

### Claim 1  [PENDING] ✅
> I owned large projects from early problem definition through production as the sole dedicated data engineer

*Contexts: employer: BritBox, employer: Universe*

- Sole dedicated data engineer responsible for end-to-end project ownership
  - Problem definition phase through production deployment
  - No other dedicated data engineering resource to share the work

### Claim 2  [PENDING] ✅
> At BritBox, I built production pipelines and worked through ambiguous requirements

*Contexts: employer: BritBox*

- Built production pipelines handling real data at scale
- Worked through ambiguous requirements to clarify what needed to be built
  - Requirements were not pre-defined; required translation and discovery

### Claim 3  [PENDING] ✅
> I developed test-forward approaches to data reliability

*Contexts: employer: BritBox*

- Prioritized testing as a core part of data pipeline design and validation
  - Test-first methodology applied to data engineering problems
  - Approach to ensuring reliability through systematic validation

### Claim 4  [PENDING] ✅
> At Universe, I helped build backend data infrastructure from scratch for a production-grade product

*Contexts: employer: Universe*

- Built data infrastructure foundation for a down-ballot canvassing application
  - Infrastructure built from scratch, not inherited or incremental
  - Product-critical system supporting core application functionality

### Claim 5  [PENDING] ✅
> I used typed, linted, object-oriented Python patterns to support production-grade data systems

*Contexts: employer: Universe*

- Applied disciplined Python engineering practices: type hints, linting, object-oriented design
  - Typed Python for runtime safety and code clarity
  - Linting for consistency and error prevention
  - Object-oriented patterns for maintainability and extensibility
  - Approach enabled production-grade reliability without dedicated QA

---

## General / CS Education Philosophy
*hash: db96a10e4531...*  

**Paragraph:**
> Programming is a way to build, test, revise, imagine, and make something that reflects
> your own thinking.

### Claim 1  [REJECTED] ❌ (This is pure philosophy/assertion with no specific evidence from the person's actual work history — it makes no claim about what this person DID, how they work, or who they are as an engineer.)
> Programming is a way to build, test, revise, imagine, and make something that reflects your own thinking

- Programming as a reflective practice — building, testing, revising, and imagining in service of externalizing thought

**Conclusion:** This person sees programming not as task execution but as a medium for thought — a way to make internal reasoning visible and testable. This suggests orientation toward clarity, iteration, and intentionality in technical work.

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
> I believe AI should support exploration, debugging, reflection, and creative iteration in learning—not flatten the process by replacing the thinking students need to practice

- Used well, AI can support exploration, debugging, reflection, and creative iteration; used poorly, it can flatten the learning process and hide the decisions students most need to practice

### Claim 2  [PENDING] ✅
> I am developing a Claude-based coding agent that keeps the user in control of the reasoning, decisions, and design

*Contexts: project: Claude-based coding agent for learning*

- Built a Claude-based coding agent to support learning and project development in a way that keeps the user in control of the reasoning, decisions, and design
  - Agent designed to maintain user agency over reasoning and design decisions

### Claim 3  [PENDING] ✅
> I build AI applications with reviewable outputs and human decision points, which has shaped how I think about AI systems supporting learning without replacing the work of learning

- Building AI applications with reviewable outputs and human decision points has made me think carefully about how AI systems can support learning without replacing the work of learning
  - Intentional design of reviewable outputs
  - Explicit human decision points in AI workflows
  - Focus on preserving the learning work itself

**Conclusion:** This person approaches AI as a tool for augmenting human reasoning and learning, not automating it away—and has built systems that embody this philosophy through deliberate design choices around transparency and user control.

---

## General / Closing
*hash: 68c7de7ea9a1...*  

**Paragraph:**
> I would welcome the opportunity to share curriculum samples I have personally developed.

### Claim 1  [PENDING] ✅
> I have personally developed curriculum samples

- Created curriculum materials independently

---

## General / Programming Languages and Learning
*hash: ee5d862fdd78...*  

**Paragraph:**
> I have a long history of both learning and teaching programming languages across Python,
> Java through Processing, C++ through Arduino, Max/MSP, HTML/CSS, and some JavaScript and
> React. I have already started reading about Elixir and would welcome the opportunity to
> implement in it significantly. I learn new technical material quickly, and that pattern of
> picking up languages across very different paradigms is consistent across my career.

*No claims extracted.*

---

## General / Motivation and Fit
*hash: f7b172f10eaa...*  

**Paragraph:**
> I watched Animal Farm before I knew about this opening, and Angel's model of prioritizing
> audience participation and direct supporter relationships is a specific reason I want this
> role. I have wanted to work at a film production or animation studio for a long time, and
> this position connects that interest with the work I do best: backend systems, data
> quality, reporting readiness, and long-term maintainability in a media company.

*No claims extracted.*

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

### Claim 1  [PENDING] ✅
> I have full admin access and infrastructure ownership across multiple cloud platforms—AWS, GCP, Azure—and can figure myself out and get up to speed in each environment

*Contexts: employer: BritBox, employer: Universe, employer: Unite Here, employer: client projects*

- At BritBox, had full admin access in AWS, setting up EC2 machines, creating and assigning IAM roles, and orchestrating Glue jobs with DynamoDB tables for metadata tracking
  - EC2 machine setup
  - IAM role creation and assignment
  - Glue job orchestration
  - DynamoDB table management for metadata tracking
- At Universe, the stack was fully GCP with BigQuery running where Redshift would otherwise sit, and the work was directly translatable
  - BigQuery as data warehouse replacement for Redshift
  - Full GCP environment
- Worked in Snowflake on client projects and in an Azure ecosystem at Unite Here using Azure Data Studio
  - Snowflake client work
  - Azure Data Studio in Azure ecosystem
- Each of these environments has its own shape and I have been able to figure myself out and get up to speed in all of them

### Claim 2  [PENDING] ✅
> I built a prototype AI chatbot with Bedrock at BritBox, demonstrating ability to move into emerging AWS services without prior experience

*Contexts: employer: BritBox*

- Built a prototype AI chatbot with Bedrock at BritBox
  - AWS Bedrock service
  - Prototype-stage work

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

### Claim 1  [PENDING] ✅
> I work backwards from what definitions mean in context into systems that make those meanings explicit and enforced

*Contexts: employer: Unite Here, employer: Universe*

- At Unite Here, started building data catalogs to track distinct definitions across locals on national campaigns where the same term could mean different things depending on the local
- At Universe, formalized that practice by introducing Great Expectations alongside dbt so documentation, definitions, and lineage were connected in one place
  - dbt held the canonical transformation logic and model documentation
  - Prefect orchestrated the steps from normalizing raw files through running validations and publishing outputs
  - Great Expectations sat at key checkpoints to validate schema, required fields, accepted values, row counts, and business rules before any downstream model or application workflow could depend on the data

### Claim 2  [PENDING] ✅
> At Universe, I owned the correctness of parsed voterfile mapping and validation that the entire data-driven application depended on

*Contexts: employer: Universe*

- The Universe application is entirely data driven and runs on parsed voterfiles, which means everyone using the app relied on the correctness of my mapping and validation to do their work

### Claim 3  [PENDING] ✅
> I understand Great Expectations, dbt, and Prefect deeply enough to architect them as an integrated validation and documentation system where each tool has a specific role in the pipeline

*Contexts: employer: Universe*

- Designed a pipeline where dbt held canonical transformation logic and model documentation, Prefect orchestrated steps from normalizing raw files through running validations and publishing outputs, and Great Expectations validated at key checkpoints
  - Great Expectations validated schema, required fields, accepted values, row counts, and business rules before any downstream model or application workflow could depend on the data

---

## Data Engineer / Card Check Data Systems
*hash: bac55db99669...*  

**Paragraph:**
> At UNITE HERE I was given very little direction on what to do. I was taught the legal framework of card checks and elections but it was up to me to design a working system to track the organizing as well as the actual cards and to ensure that the NLRB had everything they needed in order, perfectly organized, in order to certify the card check. I was covering massive workplaces, at casinos, often also partnerships with other unions so there was sometimes collection and tracking that happened with more than just our union to ensure that the other union got their cards. I also covered the razor thin departmental organizing for the graduate students at Yale when their elections were certified with wins sometimes in the single digits. This entailed my having to wake up before 7 in the morning 6 days a week and compile a 40 something step excel report on the state of the organizing every morning. In all of these cases I was given very loose guidance and then I figured out the system and documented it but I was also responsible for training all of the staff in the campaign including the organizing directors on how the system worked, how to enter data into the system, and how we handled the reporting with the meeting schedules. I was working with a lot of organizers and staff members who were not technical but had a desire to win and my role was supportive. My system was so good the president of the local received a letter that one of my card checks was the most organized card check he had ever certified. I was also formally thanked by the president of that local for doing such a good job.

### Claim 1  [PENDING] ✅
> I was given very little direction on what to do, and it was up to me to design a working system to track the organizing, the cards, and ensure the NLRB had everything they needed in order, perfectly organized, to certify the card check

*Contexts: employer: UNITE HERE*

- Operated independently under high expectations to design and own the entire tracking system for card checks and elections across multiple campaigns
  - Covered massive workplaces at casinos
  - Managed partnerships with other unions requiring collection and tracking across multiple organizations
  - Covered razor thin departmental organizing for graduate students at Yale with wins sometimes in the single digits
  - System was so organized that the president of the local received a letter saying it was the most organized card check he had ever certified

### Claim 2  [PENDING] ✅
> I figured out the system and documented it, then trained all of the staff in the campaign including the organizing directors on how the system worked, how to enter data, and how we handled reporting with meeting schedules

*Contexts: employer: UNITE HERE*

- Took responsibility for translating a complex technical system to non-technical staff who had a desire to win
  - Worked with organizers and staff members who were not technical
  - My role was supportive
  - Trained on system mechanics, data entry, and reporting procedures
- figuring out whole workflows and procedures, writing documentation and training people on systems I worked out

### Claim 3  [PENDING] ✅
> I had accountability for data integrity and organizational completeness at a level that was rare — the NLRB certification depended on my system being perfect

*Contexts: employer: UNITE HERE*

- Woke up before 7 in the morning 6 days a week and compiled a 40-something step Excel report on the state of the organizing every morning
  - This was the operational backbone for all organizing decisions and NLRB compliance
- Formally thanked by the president of the local for doing such a good job

### Claim 4  [PENDING] ✅
> I work backwards from what an external authority (the NLRB) needs to understand into the system that produces it — designing data models and workflows that ensure perfect compliance and auditability

*Contexts: employer: UNITE HERE*

- Designed systems to ensure the NLRB had everything they needed in order, perfectly organized, in order to certify the card check
  - System had to handle complex multi-union partnerships and tracking
  - System had to scale from massive casino workplaces to razor-thin departmental organizing with single-digit wins

### Claim 5  [PENDING] ✅
> I find meaning in work where careful systems and documentation make organizations more accountable and enable non-technical people to win

*Contexts: employer: UNITE HERE*

- My role was supportive — working with organizers and staff members who were not technical but had a desire to win
  - Chose to build systems that enabled others rather than just execute technical work
  - Took on early morning reporting and training responsibilities to support campaign success

**Conclusion:** This person operates at the intersection of technical rigor and human-centered support — they design systems that are both technically sound and accessible to non-technical stakeholders, and they take accountability for outcomes that matter beyond the technical layer.

---

## Data Engineer / Application Development and Requirements
*hash: f5ac39e97b7a...*  

**Paragraph:**
> Even when at UNITE HERE I was working on application development and testing and gathering requirements and doing demos of software I was taking in feedback from organizers and membership staff and translating it into requirements and acceptance criteria for the applications' further development on multiple applications including an electronic membership card, a bargaining unit list processing portal, the dues processing system, as well as relational organizing apps, both of them.

### Claim 1  [PENDING] ✅
> I translated feedback from organizers and membership staff into requirements and acceptance criteria for applications' further development

*Contexts: employer: UNITE HERE*

- Worked across multiple applications including an electronic membership card, a bargaining unit list processing portal, the dues processing system, and relational organizing apps
  - electronic membership card
  - bargaining unit list processing portal
  - dues processing system
  - relational organizing apps (both of them)
- Gathered requirements and did demos of software while taking in feedback from organizers and membership staff
  - application development and testing
  - gathering requirements
  - doing demos of software

### Claim 2  [PENDING] ✅
> I worked on application development and testing across multiple systems serving union organizers and membership

*Contexts: employer: UNITE HERE*

- Owned work on electronic membership card, bargaining unit list processing portal, dues processing system, and relational organizing apps
  - application development
  - application testing
  - multiple applications

---
