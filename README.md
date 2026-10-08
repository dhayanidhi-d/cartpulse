# CartPulse

**Real-Time Inventory & Pricing Engine for a Multi-Vendor E-Commerce Platform**

A Django + DRF backend where multiple vendors sell overlapping products, stock
is tracked per-vendor, and prices auto-adjust in near-real-time based on
stock levels and demand — with every change pushed live to clients over
WebSockets instead of requiring a page refresh or polling.

---

## 1. Architecture

```
┌────────────┐      REST (JWT)      ┌──────────────────────────┐
│  Client /  │ ───────────────────► │        Django + DRF        │
│  Frontend  │ ◄─────────────────── │  vendors / products /      │
└────────────┘                      │  inventory / pricing /     │
      ▲                             │  orders                    │
      │  WebSocket (live push)      └───────────┬────────────────┘
      │                                          │ post_save signal
┌─────┴──────────┐                               ▼
│ Django Channels │◄──── group_send ────  transaction.on_commit
│ (ASGI, Redis    │                               │
│  channel layer) │                               ▼
└─────────────────┘                     Celery task: recalculate_price
                                                   │
                                                   ▼
                                        PricingEngine.evaluate()
                                        (inventory + demand signals,
                                         clamped to vendor's price band)
                                                   │
                                                   ▼
                                     VendorListing.price updated +
                                     PriceHistory row + WS broadcast
```

**Flow in one sentence:** a stock change (sale, restock, manual adjustment)
saves an `InventoryItem` → a signal fires after the DB commit → it (1)
broadcasts the new stock level over WebSocket and (2) queues a Celery task
that re-runs the pricing engine → if the price moved, it's saved, logged,
and broadcast too. A shopper watching the product page sees "3 left" and
then the price tick up, live, with no polling.

### Apps
| App         | Responsibility |
|-------------|-----------------|
| `vendors`   | Seller accounts / storefronts |
| `products`  | Shared catalog + per-vendor `VendorListing` (price band: `min_price` ≤ `price` ≤ `max_price`) |
| `inventory` | Stock (`InventoryItem`), audit trail (`InventoryLog`), WebSocket consumer + broadcast helper |
| `pricing`   | The engine (`engine.py`), Celery tasks, `PriceHistory` |
| `orders`    | Atomic multi-line checkout that reserves stock and can't oversell |

### Why these tools
- **Django Channels + Redis** — real WebSocket push beats a client polling
  every few seconds; Redis channel layer means it works across multiple
  server processes, not just one.
- **Celery + Redis** — pricing recalculation shouldn't block the request/response
  cycle (a stock update or checkout should return fast); it also lets the
  same logic run on a **schedule** (`recalculate_all_prices`), not just on events.
- **`select_for_update` in checkout** — the classic "two shoppers, one unit
  left" race condition is solved with a row lock inside one DB transaction,
  not with application-level locking.
- **`min_price` / `max_price` per listing** — the algorithm can be aggressive
  without ever pricing a vendor's product below cost or above what they've
  approved. Business rule stays with the vendor; the engine just optimizes
  inside the band.

---

## 2. Setup

### Option A — Local (fastest to demo, uses SQLite + no Docker)
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data          # optional: 2 vendors, 3 products, stock

python manage.py runserver               # HTTP + WebSocket in one process (Daphne/ASGI)
```
Note: without Redis running locally, set `CHANNELS_USE_INMEMORY=True` and
`CELERY_TASK_ALWAYS_EAGER=True` in `.env` — real-time broadcast and pricing
recalculation still work in-process, just without cross-process fan-out.

To run the real thing (separate worker, real broadcast across processes),
in three terminals:
```bash
redis-server
celery -A cartpulse worker --loglevel=info
python manage.py runserver
```

### Option B — Docker (closer to how this would run in production)
```bash
docker compose up --build
```
Spins up Postgres, Redis, the Daphne web process, a Celery worker, and Celery
beat. Migrations + demo seed run automatically on `web` startup.

### Try it
```bash
# Get a token
curl -X POST http://localhost:8000/api/auth/token/ -d "username=techbazaar&password=demopass123"

# Browse the catalog (no auth needed)
curl http://localhost:8000/api/catalog/products/

# Watch it live: open scripts/ws_demo.html in a browser, then in another
# terminal, adjust stock and watch the page update instantly:
curl -X POST http://localhost:8000/api/inventory/items/1/adjust-stock/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"change_qty": -18, "reason": "SALE", "note": "manual demo"}'
```

### Tests
```bash
pytest
```
Covers the pricing engine in isolation (no HTTP, no Celery — just the
scoring logic) and the checkout flow end-to-end (stock decremented,
overselling rejected, transaction rolled back on failure).

---

## 3. Key API endpoints

| Method & path | Purpose |
|---|---|
| `POST /api/auth/token/` | Obtain JWT access/refresh pair |
| `GET /api/catalog/products/?search=&category=` | Browse catalog, filter/search |
| `GET/POST /api/catalog/listings/?mine=true` | A vendor's own listings (price band) |
| `POST /api/inventory/items/{id}/adjust-stock/` | Restock / sell / adjust, always audited |
| `GET /api/pricing/history/?listing=<id>` | Price change history for a listing |
| `POST /api/pricing/history/recalculate/{listing_id}/` | Manually trigger a re-price (demo/debug) |
| `POST /api/orders/checkout/` | Atomic multi-item checkout |
| `ws://.../ws/inventory/` | Live stock + price events |

---

## 4. Resume bullet points

Pick 2–3 that best match the job description you're applying to:

- Designed and built **CartPulse**, a multi-vendor e-commerce backend
  (Django, DRF, PostgreSQL) supporting independent vendor storefronts,
  shared product catalog, and per-vendor pricing.
- Implemented a **rule-based dynamic pricing engine** that adjusts prices in
  real time from stock-level and demand signals, clamped to vendor-defined
  price bands, with a full price-change audit trail.
- Built a **real-time layer with Django Channels + Redis** to push live
  inventory and price updates to connected clients over WebSockets,
  eliminating polling.
- Offloaded pricing recalculation to **Celery**, triggered both by inventory
  events (via Django signals + `transaction.on_commit`) and a periodic
  scheduled sweep (`django-celery-beat`).
- Prevented overselling under concurrent checkouts using **row-level
  locking (`select_for_update`)** inside atomic transactions across
  multi-line orders.
- Secured the API with **JWT authentication** (SimpleJWT), per-user
  throttling, and object-level permission checks (vendors can only edit
  their own listings).
- Wrote a **pure, dependency-free pricing algorithm module** decoupled from
  Django/Celery specifics, enabling fast unit testing without a database
  or broker in most cases (only DB fixtures needed here for realism).

---

## 5. Interview prep — likely questions & how to answer them

**Q: Walk me through what happens when a customer buys the last unit of a product.**
A: `orders.views.OrderViewSet.checkout` opens one DB transaction. For each
cart line it takes a row lock on that listing's `InventoryItem`
(`select_for_update`), checks `available_quantity`, and only then
decrements it and creates the `OrderItem`. Saving the `InventoryItem`
fires a `post_save` signal; on commit, it broadcasts the new stock count
over WebSocket and enqueues a Celery task that re-runs the pricing engine
(stock just dropped, possibly into "low stock" territory → scarcity
markup). If a concurrent request tries to buy more than what's left, the
lock forces it to wait, then it fails cleanly with a 400 and the whole
transaction rolls back — no oversold order is ever created.

**Q: Why Celery instead of just recalculating the price synchronously in the request?**
A: Repricing can involve extra queries (recent order counts, other rules)
and shouldn't add latency to a checkout or stock-adjustment request. It also
needs to run on a **schedule**, not only on events — demand can drift
without any single stock change, so a periodic sweep re-evaluates every
active listing.

**Q: What stops the pricing engine from spiraling a price to ₹0 or to something absurd?**
A: Every listing has vendor-set `min_price`/`max_price`. The engine computes
a candidate price from `base_price × multiplier` and always clamps to that
band before saving — see `PricingEngine.evaluate()`. The vendor, not the
algorithm, owns the acceptable range.

**Q: How would you scale the WebSocket layer to many servers?**
A: That's already the reason Channels uses the **Redis channel layer**
instead of the in-memory one: `group_send` publishes to Redis, and every
Django/Daphne process subscribed to that group (across however many
instances are running behind a load balancer) receives and forwards the
event to its own connected clients. The in-memory layer (used in tests) only
works within a single process, which is why it's test-only here.

**Q: How do you avoid a race condition between two shoppers buying the same last item?**
A: `select_for_update()` inside `transaction.atomic()` — the first request
to reach that row locks it until its transaction commits or rolls back; the
second request blocks until then and re-reads the now-updated quantity, so
it correctly sees "not enough stock" instead of both requests reading the
same stale quantity and both succeeding.

**Q: Why separate `VendorListing.price` (current) from `base_price`?**
A: `base_price` is the vendor's own anchor — what they consider "list
price." `price` is what's actually charged, adjusted by the engine within
the vendor's band. Without this split, every automated repricing would
compound on top of the previous automated repricing rather than the
vendor's actual intent, and the vendor would lose a stable reference point.

**Q: What would you add with more time?**
A: Competitor-price scraping as a third pricing signal (the `PricingRule`
model already has a `COMPETITOR_BASED` type as groundwork); reservation
holds during checkout (currently a straight decrement) so an abandoned cart
releases stock after a timeout; per-vendor commission settlement; and
caching the product list endpoint (Redis) since it's the highest-read path.

**Q: What's the hardest part of this project to get right?**
A: Ordering of side effects around a single DB write — making sure the
WebSocket broadcast and the Celery repricing trigger only fire **after**
the transaction actually commits (`transaction.on_commit`), so a rolled-back
stock change never causes a phantom price update or a false "in stock"
push to a connected client.

---

## 6. Project layout
```
cartpulse/
├── cartpulse/          # settings, urls, asgi (Channels), celery app
├── vendors/            # seller storefronts
├── products/           # catalog + VendorListing (price band)
├── inventory/          # stock, audit log, WebSocket consumer, signals
├── pricing/            # engine.py, Celery tasks, PriceHistory
├── orders/             # atomic checkout
├── tests/               # pricing engine unit tests + checkout integration tests
├── scripts/ws_demo.html # zero-dependency live demo page
├── docker-compose.yml
└── Dockerfile
```
