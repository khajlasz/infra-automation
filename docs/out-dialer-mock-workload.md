# Out-Dialer Synthetic Workload Design

## 1. Purpose

This document defines the synthetic application workload used by the
Out-Dialer reference platform.

The workload exists to provide realistic distributed application behaviour
for infrastructure automation and observability exercises.

The Out-Dialer is not intended to implement a production calling platform.
Its business operations are deliberately simulated.

The guiding principle is:

> **Synthetic workload, real service interactions and telemetry mechanisms.**

The workload should therefore be simple enough to understand while still
providing meaningful asynchronous behaviour across multiple services.

---

## 2. Component Responsibilities

The synthetic workload consists of three application components.

### Portal

The Portal owns the external API boundary.

Responsibilities:

- accept campaign creation requests;
- expose campaign status queries;
- forward campaign operations to Campaign Manager;
- return Campaign Manager responses to the client.

The Portal does not own campaign state or execution logic.

### Campaign Manager

Campaign Manager owns campaign identity, lifecycle, state, and scheduling.

Responsibilities:

- generate a unique `campaign_id`;
- resolve campaign templates;
- maintain campaign state;
- queue accepted campaigns for execution;
- execute campaigns asynchronously;
- dispatch campaign work to Call Simulator;
- record the execution result.

For the initial implementation, campaign state is stored in memory.

### Call Simulator

Call Simulator owns synthetic call execution.

Responsibilities:

- accept campaign execution requests from Campaign Manager;
- simulate processing the supplied phone numbers;
- simulate successful and failed calls;
- return an execution summary.

Call Simulator does not own campaign scheduling or lifecycle state.

---

## 3. Campaign Template

A campaign creation request references a previously defined campaign template.

Example:

```text
customer-renewal-v1
```

The template represents reusable campaign configuration.

For the initial synthetic implementation, Campaign Manager maintains a small
predefined mapping between template IDs and prompt sources.

Conceptually:
```text
template_id
    |
    v
campaign template
    |
    +-- prompt_source
```
Example:

```text
customer-renewal-v1
    -> /prompts/customer-renewal-v1.wav
```
No persistent template store is required in this milestone.

## 4. Prompt Source
`prompt_source` identifies the prompt that would be used when executing the
campaign.

Example:
```text
/prompts/customer-renewal-v1.wav
```

The value is treated as an opaque resource reference.

It may eventually represent a resource located on shared storage such as NFS,
or another storage mechanism.

The initial implementation does not fetch, mount, read, or validate the
resource.

Campaign Manager resolves the template into a `prompt_source` and passes that
reference to Call Simulator.

## 5. Campaign Identity and Lifecycle

A campaign template and a campaign execution are different concepts.

A template is reusable:
```text
template_id = customer-renewal-v1
```
Each request creates a new campaign execution with its own identity:
```text
campaign_id = <generated unique ID>
```
Multiple campaigns may therefore reference the same template.

The initial campaign lifecycle is:
```text
queued
   |
   v
running
   |
   +------> completed
   |
   +------> failed
```
Campaign Manager owns all lifecycle transitions.

## 6. Asynchronous Execution Model

Campaign creation is asynchronous from the client's perspective.

The client does not wait for campaign execution to finish.
```text
Client
  |
  | POST /campaigns
  v
Portal
  |
  | POST /campaigns
  v
Campaign Manager
  |
  | create campaign_id
  | resolve template
  | store campaign
  | status = queued
  |
  +---------------------> return 202 Accepted
  |
  | background execution
  v
status = running
  |
  v
Call Simulator
  |
  | synthetic execution
  v
Campaign Manager
  |
  +--> status = completed / failed
```
Campaign Manager may use a simple Python background worker or thread for this
milestone.

No external message broker or task queue is required.

The Campaign Manager to Call Simulator HTTP request may remain synchronous.
The asynchronous boundary is between campaign submission and campaign
execution.

## 7. HTTP Contracts
### 7.1 Create Campaign

Public request:
```http
POST /campaigns
Content-Type: application/json
```

Request body:
```JSON
{
  "template_id": "customer-renewal-v1",
  "numbers": [
    "+48111111111",
    "+48222222222",
    "+48333333333"
  ]
}
```
Portal forwards the campaign creation request to Campaign Manager.

Campaign Manager:

1. validates the required request fields;
2. generates a unique `campaign_id`;
3. resolves `template_id` to its configured `prompt_source`;
4. creates the in-memory campaign state;
5. sets the campaign state to `queued`;
6. schedules asynchronous execution.

Successful response:
```http
HTTP/1.1 202 Accepted
```
```JSON
{
  "campaign_id": "8f03c5...",
  "status": "queued"
}
```
The `202 Accepted` response indicates that the campaign was accepted but its
execution has not necessarily completed.

### 7.2 Query Campaign Status

Public request:
```http
GET /campaigns/{campaign_id}
```
Portal queries Campaign Manager and returns the current campaign state.

Example response while executing:
```JSON
{
  "campaign_id": "8f03c5...",
  "status": "running"
}
```
Example terminal response:
```JSON
{
  "campaign_id": "8f03c5...",
  "status": "completed"
}
```
An unknown campaign ID returns:
```http
HTTP/1.1 404 Not Found
```
```JSON
{
  "error": "campaign_not_found"
}
```
### 7.3 Execute Campaign

This is an internal API used by Campaign Manager.
```http
POST /execute
Content-Type: application/json
```
Request:
```JSON
{
  "campaign_id": "8f03c5...",
  "numbers": [
    "+48111111111",
    "+48222222222",
    "+48333333333"
  ],
  "prompt_source": "/prompts/customer-renewal-v1.wav"
}
```
Call Simulator performs synthetic execution and returns an aggregate result.

Example:
```http
HTTP/1.1 200 OK
```
```JSON
{
  "campaign_id": "8f03c5...",
  "results": {
    "successful": 2,
    "failed": 1
  }
}
```
Individual per-number results are not required for the initial implementation.

## 8. Service Interaction

The intended dependency direction is:
```text
Client
  |
  v
Portal
  |
  v
Campaign Manager
  |
  v
Call Simulator
```
Portal knows how to reach Campaign Manager.

Campaign Manager knows how to reach Call Simulator.

Call Simulator has no dependency on Portal or Campaign Manager.

Campaign Manager remains the authoritative owner of campaign state.

## 9. Synthetic Execution

Call Simulator should simulate work rather than generate arbitrary telemetry.

For each campaign it receives, it should process the supplied numbers and
produce synthetic call outcomes.

The implementation may introduce small execution delays and bounded random
success/failure outcomes to make campaign execution observable over time.

The simulated behaviour is the source of later telemetry.

Metrics, logs, and traces should eventually describe these synthetic events
rather than being generated independently from them.

## 10. Milestone 1B Scope

This milestone includes:

- campaign creation through Portal;
- unique campaign IDs;
- predefined campaign template resolution;
- in-memory campaign state;
- asynchronous campaign execution;
- campaign status queries;
- Campaign Manager to Call Simulator HTTP communication;
- synthetic call execution;
- basic request and error handling.

This milestone deliberately excludes:

- PostgreSQL persistence;
- persistent campaign templates;
- real telephony;
- prompt retrieval or validation;
- NFS integration;
- external task queues or message brokers;
- authentication;
- retries and sophisticated failure recovery;
- detailed per-number execution history;
- new business Prometheus metrics;
- distributed tracing.

Existing health endpoints and Prometheus exposition endpoints must remain
functional.

## 11. Observability Relationship

The synthetic workload provides the behaviour that later observability
milestones will measure.

Examples include:
```text
Portal request duration
        !=
Campaign execution duration
```
and:
```text
API traffic
    |
    v
campaign queue
    |
    v
campaign execution
    |
    v
individual simulated calls
```
Later milestones can derive meaningful metrics from actual workload events,
including:

- Portal request rate and duration;
- campaign queue depth;
- active campaigns;
- campaign outcomes;
- campaign execution duration;
- call outcomes;
- concurrent calls;
- call duration.

The initial workload should not generate random metric values independently of
application behaviour.

## 12. Design Principle

The reference workload intentionally prioritizes architectural clarity over
business completeness.

The objective is not to build a complete Out-Dialer product.

The objective is to create a small distributed system in which:

- service boundaries are meaningful;
- asynchronous behaviour is visible;
- failures can be introduced deliberately;
- telemetry can be generated from real application events;
- metrics, logs, and traces can later describe the same synthetic workflow.

In short:

> Mock the business workload, not the observability mechanisms.
