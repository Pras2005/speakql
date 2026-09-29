# SpeakQL Frontend Design Brief

## Purpose

This document is a design handoff for the SpeakQL frontend. It explains what the product is, what the frontend now covers, what kind of visual system it needs, and how each major screen should behave. The designer should treat this as a control-plane product, not a marketing site and not a generic BI dashboard.

The current frontend has been refactored to cover the real backend surface. The next step is to raise the design quality so the UI feels deliberate, premium, fast, and operationally trustworthy.

## Product Summary

SpeakQL is a governed analytics workbench. It lets users:

- connect databases
- generate SQL from natural language
- inspect and edit SQL
- run queries through policy, risk, approval, masking, and audit controls
- save reusable query assets into workflow
- publish semantic catalog entries, glossary terms, and metrics
- manage governance policies and sensitivity rules
- approve or deny risky executions
- schedule and inspect governed reports
- inspect audit events and connector health

This is not a casual analytics toy. The interface should communicate:

- control
- traceability
- seriousness
- operational clarity
- human review over automated output

## Design Goal

The design should feel like:

- a modern data governance control plane
- premium but not flashy
- dense but readable
- strong hierarchy without clutter
- confident and technical without looking developer-only

Avoid:

- default SaaS templates
- overly soft “friendly dashboard” design
- purple-heavy AI styling
- giant empty cards with little information
- excessive glassmorphism
- novelty motion that slows down operations

Target feeling:

- mission control for governed data work
- editorially sharp
- high signal
- serious but elegant

## Core Product Themes

The interface should consistently reinforce these product truths:

1. Queries are not just executed, they are governed.
2. Reusable assets move through workflow and review.
3. Workspace context matters.
4. Policy, audit, and approvals are first-class, not secondary admin panels.
5. The system has both AI-assisted generation and human-controlled execution.

## Primary Users

### Analyst

Needs:

- fast prompt-to-SQL workflow
- confidence in what will execute
- clear visibility into policy/risk outcomes
- query history
- ability to save useful work

### Compliance / Governance Admin

Needs:

- policy and sensitivity rule management
- approval queue review
- audit inspection
- health visibility
- confidence that actions are scoped and explainable

### Admin / Platform Operator

Needs:

- database connection management
- workspace switching context
- reporting setup
- connector refresh and operational health

## Product Structure

The current app structure is:

- `Workbench`
- `Workflow`
- `Reports`
- `Databases`
- `Catalog`
- `Governance`
- `Approvals`
- `Audit`

These should feel like one coherent system, not eight separate mini-products.

## Current Frontend Reality

The frontend is now functionally wired to backend APIs and exposes real features. The design layer still needs stronger visual language and more intentional composition.

Important implementation note:

- the app already supports the backend surface
- the design work is now primarily UX/UI improvement, not discovery of missing product areas

## Design Direction

### Visual Tone

Use a visual language closer to:

- enterprise operations software
- quantitative research terminals
- modern observability products

Less like:

- consumer productivity apps
- low-density CRUD admin kits
- playful AI copilots

### Layout Behavior

The layout should support:

- dense information
- wide desktop workflows
- strong section framing
- clear active context

The workbench should feel like the center of gravity. Everything else should feel connected back to it.

### Typography

Typography should do real work.

Use:

- a strong sans family for navigation, labels, and body
- a clear mono family for SQL, IDs, JSON, timestamps, and technical payloads

Recommended approach:

- compact uppercase labels for system framing
- restrained but confident page titles
- smaller descriptive copy that stays readable under density

Avoid oversized consumer-style headings.

### Color

Current direction is warm amber + blue + graphite. That is acceptable, but it should be refined.

Suggested semantic model:

- amber: review, caution, governed action, pending approval
- blue: technical context, schema, system metadata, neutral active state
- green: success, allowed, healthy
- red: denied, failure, destructive action
- purple: optional, only for secondary semantic labeling if needed, not as primary brand color

Avoid making the app look like a dark purple AI product.

### Motion

Use motion sparingly:

- subtle route/page reveals
- panel loading state transitions
- hover emphasis
- approval / success / error state transitions

Do not add decorative motion to data-heavy areas.

## Global UX Principles

### 1. Show Context Early

Every major screen should make these visible quickly:

- active workspace
- active database where relevant
- current asset or queue item where relevant
- status and last update information

### 2. Make Status Legible

Status is core to this product. The UI must strongly distinguish:

- draft
- submitted
- approved
- rejected
- archived
- pending approval
- success
- denied
- error
- healthy / unhealthy

Status should never be visually ambiguous.

### 3. Balance Density and Focus

The app should support high information density, but avoid visual noise.

Good density:

- grouped information
- strong whitespace rhythm
- repeated card logic where useful
- compact metadata rows

Bad density:

- many borders with no hierarchy
- too many competing accent colors
- oversized controls
- tables with weak scanning structure

### 4. Respect Technical Content

SQL, JSON payloads, schema data, audit details, and risk outputs are central. These need strong display treatment:

- excellent mono typography
- clearly framed code/data regions
- copyability
- overflow handling
- clear contrast

### 5. Review-Oriented UX

Approvals, policy outcomes, and workflow review should feel like review tools, not simple forms.

Review surfaces should emphasize:

- what happened
- why it matters
- what is risky
- what action is available

## Page-by-Page Direction

## 1. Workbench

### Role

This is the primary product surface. It should feel like the place where work begins and where governance becomes visible.

### Must Communicate

- active database and provider context
- prompt to SQL generation flow
- editable SQL
- clear execute/explain/export actions
- governance metadata as a first-class result
- history and schema as supporting context

### Recommended Composition

- top band with key metrics and active context
- dominant left/center work area for prompt and SQL
- right rail or secondary panels for explainability / governance / save-to-workflow
- lower or adjacent panels for results and history
- schema explorer as a strong secondary section, not a hidden afterthought

### Important Design Requirement

The workbench should not look like a generic SQL editor pasted into a dashboard. It should look like governed query operations.

### Key UX States

- no database selected
- prompt entered, no SQL yet
- SQL generated
- executing
- success with result set
- approval required
- denied
- explainability loaded without execution

### Designer Focus

- make the generated SQL area feel premium and precise
- make governance output easier to scan than raw payloads
- give result tables strong readability
- make history selection feel connected to current work

## 2. Workflow

### Role

This is the asset lifecycle surface for reusable queries.

### Must Communicate

- saved queries are durable assets
- assets move through review states
- replay and diff are operational controls
- comments are part of collaboration and review

### Recommended Composition

- left column: asset inventory
- main panel: selected asset detail
- side utilities: replay, review actions, comments
- separate lower or tabbed region: SQL diff and run diff

### Critical UI Behaviors

- state badge prominence
- easy understanding of visibility
- clear distinction between submit, approve, reject, archive, delete
- reviewer notes / reason capture should feel deliberate

## 3. Reports

### Role

Scheduled governed execution over saved queries.

### Must Communicate

- reports are built on approved or reusable query assets
- schedules and delivery configuration are operational settings
- runs are auditable

### Recommended Composition

- report list
- create/edit form
- run history panel
- selected report summary with delivery config

### Design Priority

The screen should make scheduled automation feel controlled, not magical.

## 4. Databases

### Role

Operational inventory for connected data sources.

### Must Communicate

- each database is a governed execution target
- MCP key rotation is sensitive
- refresh catalog is an operational action
- deletion is high risk

### Design Priority

This page should feel operational and trusted. Avoid playful styling.

### Important UX Details

- reveal latest rotated key cleanly
- emphasize destructive action boundaries
- clearly show host, port, db user, and create time

## 5. Catalog

### Role

Semantic layer for tables, terms, and metrics.

### Must Communicate

- catalog entries are published, intentional data assets
- glossary terms provide semantic grounding
- metrics are reusable business logic

### Recommended Composition

- top section: published entries
- lower split: glossary and metrics
- creation forms should feel structured, not cramped

### Designer Focus

- make semantic objects feel curated
- visually distinguish tables, business terms, and metrics
- avoid looking like a generic documentation CMS

## 6. Governance

### Role

Policy and sensitivity rule management.

### Must Communicate

- policy JSON drives runtime behavior
- sensitivity rules affect masking and role access
- these are high-trust configuration surfaces

### Recommended Composition

- left: existing policies/rules
- right: creation/editor surfaces
- strong code/data blocks for policy JSON

### Design Priority

This screen should look exact and controlled. Think configuration control plane, not consumer preferences page.

## 7. Approvals

### Role

Human review queue for risky or low-confidence execution requests.

### Must Communicate

- why the request exists
- who requested it
- how risky it is
- what SQL is being reviewed
- what decision the reviewer can make

### Recommended Composition

- list or stack of requests
- request detail with SQL and prompt
- prominent approve / deny actions
- denial reason capture

### Design Priority

The reviewer should be able to scan, judge, and act with minimal hesitation.

## 8. Audit

### Role

Operational audit inspection and connector health.

### Must Communicate

- audit trail is real and important
- filters matter
- event details must be inspectable
- connector health is operational telemetry

### Recommended Composition

- left/main: filtered audit event stream
- right: connector health and verification tools

### Design Priority

Do not make this page look like a log dump. It needs structure and legibility.

## Shared Component Direction

The following components need a coherent design system:

### Navigation

- stronger section identity
- active route clarity
- workspace context always visible

### Status Tags

- highly legible
- compact
- consistent semantics

### Data Cards

- reusable framing pattern
- clear title / metadata / actions zones

### SQL / JSON Panels

- excellent mono typesetting
- strong contrast
- refined padding and line rhythm

### Tables

- clear header hierarchy
- row scanning support
- hover states that do not distract
- support for wide technical values

### Forms

- compact but not cramped
- strong field grouping
- clear primary action hierarchy

## Information Hierarchy Rules

Use a consistent hierarchy:

1. Page identity
2. Active context
3. Primary action area
4. Main data / asset content
5. Secondary operational metadata

Avoid pages where every card has equal visual weight.

## Suggested Visual References

The designer should think in terms of:

- observability tooling density
- financial operations interfaces
- technical control surfaces
- data IDEs with better editorial structure

Not literal copies, but directional references.

## What Needs the Most Design Attention

These are the highest-value design targets:

1. Workbench SQL + governance composition
2. Workflow review and replay experience
3. Approvals queue clarity
4. Policy and sensitivity management layout
5. Global visual identity and navigation coherence

## What the Designer Should Not Change Blindly

The designer should understand these product realities before proposing drastic UX changes:

- the backend API surface is already broad and real
- governance outputs are not decorative; they are core product content
- technical payloads like SQL, JSON, diffs, and audit metadata must remain visible
- workspace context matters to almost every screen
- approval and audit are not edge cases

## Backend Constraints to Keep in Mind

Known backend limitations that affect UI planning:

- reports currently support create, list, manual run, and run history
- report enable/disable update flow is not exposed as a backend route yet
- SQL generation accepts provider and model selection
- execution and some replay/report paths are still backend-controlled on provider selection

Design around these constraints rather than assuming missing controls can be added immediately.

## Deliverables Requested From Designer

Ask the designer to provide:

- a refined global visual system
- redesigned navigation and shell
- a complete workbench redesign
- redesigned workflow screen
- redesigned approvals screen
- redesigned governance screen
- supporting layouts for reports, databases, catalog, and audit
- component specs for tables, tags, forms, code blocks, and technical cards
- responsive behavior for desktop and laptop widths

Optional but useful:

- motion guidance
- empty/loading/error state guidelines
- accessibility notes

## Final Direction

If the designer remembers only one thing, it should be this:

SpeakQL should look like a governed data operations product where AI generation exists inside a serious human-controlled review and execution system.

It should feel sharper, more intentional, and more operational than a standard dashboard. It should not look like a template, and it should never hide the technical truth of what the system is doing.
