# Architectural Rules

Every pull request must respect the following principles.

## Services

Services contain business logic.

They never print.

---

## Renderers

Renderers only display information.

No business logic.

---

## Providers

Providers communicate with external APIs.

No decision making.

---

## Domain

Domain objects are immutable.

No side effects.

---

## Tests

Every new feature requires tests.

No exceptions.

---

## AI

AI explains.

AI does not decide.