# Equity Leadership Events — regulator-filed continuity evidence

**Status: built 2026-08-18. Decision-neutral.** No business-quality
factor moved, no analyst or committee was added, and no decision field can
reach this slice. No model is asked.

```bash
movrvest acquire-leadership ADBE       # explicit SEC read and cache write
movrvest leadership ADBE --evidence   # stored evidence; no fetch
```

## 1. The investor story

Adobe demonstrated the gap. Its financial statements can still describe a
strong business while the investment case contains two different questions:

1. the long-serving CEO announced a transition and no permanent successor
   was named in that event; and
2. the company is navigating a technology change that makes execution during
   that transition unusually important.

Business Quality cannot answer the first question. Price momentum can show a
decline and cannot establish why it happened. A generic news score would mix
the event, somebody's explanation of the event, and a judgment about the
company into one unauditable number.

The smallest useful slice is therefore narrower: **retain regulator-filed
executive transitions as dated evidence, and decide nothing from them.** Adobe
is the first acceptance case, not a ticker-specific rule.

## 2. The source and its boundary

For SEC-registered issuers, Form 8-K **Item 5.02** is the regulator-indexed
surface for departures, appointments and related officer matters. The SEC
submissions index identifies candidate filings before their documents are
fetched. The filing itself is then located at its typeset Item 5.02 heading.

Item 5.02 is deliberately broader than leadership continuity. It also carries
director elections and executive compensation. An indexed report therefore
becomes a leadership event only where one filed sentence contains all three:

- a covered office: CEO, CFO, COO or President;
- a transition action: succession transition, departure or appointment; and
- the named person taking that action.

Missing any one declines the report. The parser never converts an award,
director election or generic search statement into a management event.

The first live acquisition on 2026-08-18 read **six of six** recent Adobe Item
5.02 reports. It retained three events from two reports and declined four
reports whose Item 5.02 text stated no covered transition:

| Filed event | Canonical outcome |
|---|---|
| Shantanu Narayen notified Adobe of his decision to transition from CEO; Adobe is searching; he remains CEO until a successor is appointed | `SUCCESSION_SEARCH · CHIEF_EXECUTIVE` |
| Daniel Durn notified Adobe of his decision to resign as CFO, effective 2026-06-15 | `DEPARTURE · CHIEF_FINANCIAL` |
| Steven Day was appointed interim CFO | `INTERIM_APPOINTMENT · CHIEF_FINANCIAL` |

The CEO event occurred on 2026-03-09 and was filed on 2026-03-12. The two dates
stay separate. That temporal boundary prevents a March event from being used
to explain price behaviour that preceded it.

## 3. The canonical object

```text
LeadershipEvent
  identity       accession | role | kind | person
  subject        symbol + company
  role           CEO | CFO | COO | President
  kind           planned transition | succession search | departure |
                 interim appointment | appointment
  occurred_on    the date stated by the filed sentence, else the filing date
  effective_on   only where the sentence states it
  facts          exact filed sentences; never a generated summary
  source         regulator, form, item, accession, filing date, URL, authority
```

One filing can produce several events. Adobe's CFO departure and interim CFO
appointment remain two identities because they describe different people and
different changes. No event overwrites another.

`PLANNED_TRANSITION`, `SUCCESSION_SEARCH` and `INTERIM_APPOINTMENT` say that
**that event names no permanent successor**. A planned transition becomes a
succession search only when its filed facts name a search or successor; the
word *transition* alone is not enough. None claims the company remains
unresolved forever: a later permanent appointment is another event. Current
continuity is a future assessment over the event sequence, not a mutable status
stored on an old filing.

## 4. Acquisition and read purity

`LeadershipEventService.acquire()` is the only provider-reaching door. It:

1. resolves the ticker through the SEC company list;
2. selects recent 8-K/8-K/A reports whose submissions row names Item 5.02;
3. fetches and locates only those filed items;
4. retains the conjunctively supported events; and
5. stores the feed and surface health under cache schema 1.

`LeadershipEventService.stored().established()` reads that record and cannot
call the provider. `movrvest leadership` uses this door. An empty stored feed,
a source that answered with no qualifying event, an intentionally declined
report and an unreadable filing remain different outcomes.

Coverage is presently **SEC-listed issuers only**. A non-U.S. issuer is a
stated source-coverage gap, not a company with no leadership events.

## 5. What this slice refuses

- It does not grade a leader or a succession plan.
- It does not infer that an executive departure is adverse.
- It does not infer the reason for a stock-price move.
- It does not use press reports to introduce an event.
- It does not parse every officer named in Item 5.02; the first role vocabulary
  is the one measured on the acceptance case.
- It does not reach Business Quality, a committee, an assessment or a decision.

The structural guard checks the import graph for those boundaries, including
model-provider access.

## 6. What comes next

The event feed earns the raw material but not yet a **Management Continuity
assessment**. That assessment should be a separate slice, activated only by a
material event and tested over a broader company corpus. It must determine,
from positive evidence, whether the current transition is:

- a planned succession with a permanent appointment;
- an active search;
- an interim arrangement; or
- not supportably classifiable.

It must never infer “leadership is strong” from the absence of an event, and it
must offer a course to the CIO rather than naming a verdict. The Adobe event
sequence is now available to measure that contract without allowing this first
slice to decide its own meaning.
