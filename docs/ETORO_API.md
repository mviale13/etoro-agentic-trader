# eToro API Inventory
## MOVRvest Evidence Acquisition Layer

**Status:** Draft v0.1
**Purpose:** Living inventory of all information that MOVRvest can potentially collect from the eToro API.

---

# Philosophy

MOVRvest follows one simple principle:

> **Capture everything. Throw nothing away.**

The Artificial CIO should never be limited because we failed to collect information that was already available.

Raw broker evidence is immutable.

Normalization happens later.

Reasoning happens later.

AI happens later.

---

# Architecture

eToro API
        │
        ▼
Evidence Collector
        │
        ▼
Immutable Evidence Store
        │
        ▼
Normalizers
        │
        ▼
MOVRvest Domain Model
        │
        ▼
Artificial CIO

---

# 1. ACCOUNT

Potential information:

- account id
- user id
- account type
- demo / real
- available cash
- equity
- invested amount
- buying power
- unrealized pnl
- realized pnl
- balance history
- account currency
- margin information
- leverage permissions
- pending cash
- external costs
- account status
- permissions
- API scopes

---

# 2. PORTFOLIO

Open positions:

- position id
- instrument id
- symbol
- display name
- quantity
- invested amount
- average entry price
- current market value
- current market price
- unrealized pnl
- realized pnl
- leverage
- stop loss
- take profit
- open date
- fees
- financing costs
- copy relationship
- smart portfolio relationship
- notes
- broker metadata

---

# 3. ORDERS

- order id
- position id
- instrument
- side
- quantity
- requested price
- executed price
- order type
- status
- timestamps
- stop loss
- take profit
- execution details
- rejection reason

---

# 4. CLOSED POSITIONS

- closing date
- opening date
- duration
- realized profit
- realized loss
- invested amount
- fees
- financing
- execution details

---

# 5. TRANSACTIONS

- deposits
- withdrawals
- transfers
- dividends
- coupons
- interest
- financing
- commissions
- taxes
- adjustments
- cash movements

---

# 6. WATCHLISTS

- watchlist id
- name
- description
- instruments
- order
- creation date
- modification date
- public/private
- default watchlist

---

# 7. INSTRUMENTS

- instrument id
- ticker
- name
- ISIN
- exchange
- country
- currency
- sector
- industry
- asset class
- subtype
- logo
- description
- market hours
- tradable status
- leverage limits

---

# 8. MARKET DATA

- bid
- ask
- last price
- open
- high
- low
- close
- volume
- candles
- volatility
- spreads
- timestamps

---

# 9. SOCIAL

Potentially available:

- investor profile
- public investor data
- copy relationships
- rankings
- popularity
- comments
- feeds
- likes
- discussions

---

# 10. SMART PORTFOLIOS

- portfolio id
- holdings
- weights
- allocation
- performance
- composition
- history

---

# 11. ALERTS

- price alerts
- triggered alerts
- notifications
- reminder configuration

---

# 12. USER PROFILE

- public profile
- country
- language
- risk score
- profile metadata
- settings
- preferences

---

# 13. API METADATA

Every API call should preserve:

- endpoint
- request method
- query parameters
- request id
- response headers
- response status
- response body
- latency
- captured timestamp
- schema version
- environment
- pagination
- rate limits

---

# Evidence Capture Principle

Every successful response should be stored exactly as returned.

Nothing should be discarded.

Evidence must remain immutable.

---

# Future Evidence Sources

The Evidence Store is broker-agnostic.

Future connectors may include:

- Interactive Brokers
- Saxo
- Degiro
- SEC EDGAR
- Companies House
- Yahoo Finance
- Polygon
- Alpha Vantage
- Earnings transcripts
- News feeds
- SEC filings
- Investor diary
- Analyst reports
- Macroeconomic indicators

---

# Long-Term Vision

The Artificial CIO should reason over evidence rather than API calls.

Broker APIs are temporary.

Evidence is permanent.

The quality of the Artificial CIO will depend less on how much data it can fetch in real time and more on the quality, completeness and history of the evidence it has accumulated over time.

