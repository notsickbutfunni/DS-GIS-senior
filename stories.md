# Trade-off Stories

Decisions worth retelling in interviews. Write each one down while it's fresh, then tighten it later.

## Template

### <Short title>
- **Module:**
- **Context:** what problem, what constraint (latency, data, cost)
- **Options considered:**
- **Chosen and why:** with the number from [numbers.md](numbers.md) that backs it
- **Rejected and why:**
- **What I'd do differently at production scale:**

---

### Two stores, two Earths: the 2 km parity check
- **Module:** 0
- **Context:** The same Overture places for Almaty live in PostGIS and OpenSearch. "Restaurants within 2 km of X" must return the same set from both, or ranking features built on one store won't match what the other serves.
- **Options considered:** (a) Accept the PostGIS spheroid default and allow boundary flips. (b) Run PostGIS on the sphere (`use_spheroid => false`) so both stores agree exactly. (c) Compare with a tolerance band around the radius.
- **Chosen and why:** Kept the spheroid as the reference and made the test explain each flip instead of hiding it. 17 of 10,533 pairs differed, all within 4.6 m of 2 km, and with PostGIS on the sphere there were 0 mismatches ([numbers.md](numbers.md), 2026-11-02). The pattern matches the geometry: at 43°N the spheroid gives −1.8 m north–south and +5.4 m east–west on a 2 km distance compared with the sphere.
- **Rejected and why:** A plain tolerance band (c) passes the test without proving the cause, so a real bug, such as swapped lat/lon or a wrong SRID, could hide inside it. Switching to the sphere (b) for everything gives up accuracy to make a test pass.
- **What I'd do differently at production scale:** Pick one Earth model per product surface and write it down. Run the parity check in CI on a fixed sample. Report server time and client time apart: OpenSearch took 9 ms on the server but 56 ms at the client.

---
