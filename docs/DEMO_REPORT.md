# MarketGrid Demo Report

Prepared for: demo and viva study material
Application URL: https://ecommerce.ananthadev.online
Frontend stack: React + Vite + Tailwind
Backend stack: FastAPI + SQLAlchemy + Alembic
Databases: PostgreSQL + MongoDB

## 1. Project summary

MarketGrid is a full-stack e-commerce application built to demonstrate core DBMS concepts in a realistic application. The app supports user registration and login, product browsing, cart management, checkout, wishlist, reviews, seller features, admin analytics, and database-backed logging.

The project uses PostgreSQL as the source of truth for transactional and relational data such as users, roles, products, inventory, carts, orders, payments, and reviews. MongoDB is used for flexible event and telemetry logging such as product views, recommendation logs, user activity logs, support chat logs, and audit-style application events.

## 2. Why this architecture is used

### PostgreSQL

PostgreSQL is used where data correctness is critical.

- User accounts need unique emails and role mappings.
- Orders and payments need ACID transactions.
- Inventory updates must be consistent even under concurrency.
- Triggers, views, constraints, indexes, and SQL functions are all strong relational features that support a DBMS lab demonstration.

### MongoDB

MongoDB is used for semi-structured, append-heavy, flexible data.

- Product view logs and recommendation logs are event-like and schema-flexible.
- Support chat logs are naturally document-shaped.
- Activity logs can change shape over time without forcing relational migrations.

### FastAPI

FastAPI is used because it exposes a clean REST API quickly, supports dependency-based authorization, and integrates well with SQLAlchemy and Pydantic models.

### React frontend

React is used to show an actual end-user workflow instead of a database-only prototype. This makes it easy to demonstrate how database design decisions appear in a real application.

## 3. Core concepts covered in the app

### 3.1 ER modeling

The app includes these main entities:

- users
- roles
- permissions
- user_roles
- role_permissions
- sellers
- categories
- products
- inventory
- carts
- cart_items
- addresses
- orders
- order_items
- payments
- reviews
- notifications
- coupons
- wishlist_items
- sql_audit_log

This model demonstrates common one-to-many and many-to-many relationships:

- one user can place many orders
- one product belongs to one category
- one order contains many order items
- one user can have many roles through a bridge table

### 3.2 Normalization

The schema demonstrates normalization up to 3NF.

- User roles are stored in separate role tables instead of redundant role text in the users table.
- Inventory is separated from products because stock is an operational concern and changes more frequently.
- Payments are separated from orders because payment lifecycle is different from order lifecycle.
- Reviews, wishlist items, and cart items are separate relation tables because they represent user-product interactions.

Why used:

- reduces redundancy
- avoids update anomalies
- keeps schema maintainable
- allows proper foreign key relationships

### 3.3 Constraints

The schema uses relational constraints to enforce correctness.

- primary keys for row identity
- foreign keys for referential integrity
- unique constraints on fields like `users.email`, `products.slug`, `payments.order_id`
- check constraints for non-negative prices, valid ratings, and positive quantities

Why used:

- moves validation into the database layer
- prevents invalid data even if application code fails
- demonstrates DBMS integrity rules clearly

### 3.4 Transactions and ACID

Checkout is the strongest ACID demonstration in the project.

In checkout:

1. the cart is validated
2. inventory rows are locked
3. the order is created
4. order items are inserted
5. payment is inserted
6. cart items are deleted
7. the transaction commits only if all steps succeed

If any step fails, everything is rolled back.

Why used:

- prevents partial order creation
- avoids stock inconsistency
- shows atomicity and consistency in a real flow

### 3.5 Concurrency control

The checkout service locks inventory rows using `SELECT ... FOR UPDATE`.

Why used:

- prevents two users from buying the same last unit simultaneously
- demonstrates pessimistic locking
- gives a concrete concurrency-control example for the demo

### 3.6 Triggers

The project uses PostgreSQL triggers for automation.

- after inserting into `order_items`, inventory quantity is reduced
- after inventory quantity update, low-stock notifications are inserted
- after successful payment insert or update, order status becomes confirmed
- before deleting a product, an audit row is written into `sql_audit_log`

Why used:

- keeps business rules close to the data
- ensures important actions happen automatically
- demonstrates database-side automation

### 3.7 Views

The app uses analytical views:

- `v_top_selling_products`
- `v_monthly_sales`
- `v_active_customers`

Why used:

- simplifies repeated analytics queries
- gives clean reusable reporting structures
- demonstrates abstraction in SQL

### 3.8 SQL function

The project defines:

- `fn_order_item_subtotal(order_id, product_id)`

Why used:

- encapsulates a reusable computation
- demonstrates custom SQL routines

### 3.9 RBAC

Role-based access control is implemented with:

- `users`
- `roles`
- `permissions`
- `user_roles`
- `role_permissions`

The API then enforces role checks using FastAPI dependencies.

Why used:

- admin routes should not be accessible to normal customers
- seller routes should only be accessible to sellers
- demonstrates mapping of conceptual DB roles into an application

### 3.10 Polyglot persistence

This app uses both PostgreSQL and MongoDB.

Why used:

- PostgreSQL handles strict relational data and transactions
- MongoDB handles flexible logs and event documents
- shows why one database is not always ideal for every problem

## 4. Demo flow to present in order

### Step 1: Open the deployed app

Open:

- `https://ecommerce.ananthadev.online`

Explain:

- frontend is served publicly
- backend is consumed through `/api`
- the app is deployed using Docker containers

### Step 2: Show login

Use seeded demo accounts:

- admin: `admin@example.com / Admin123!`
- seller: `seller@example.com / Seller123!`
- buyer: `buyer@example.com / Buyer123!`

Explain:

- login proves user authentication
- the returned JWT token enables protected routes
- different roles unlock different screens

### Step 3: Show product catalog

Demonstrate:

- search
- category filter
- product detail page

Explain:

- products are fetched from PostgreSQL
- categories and products show relational modeling
- recommendations are logged in MongoDB

### Step 4: Add item to cart

Login as buyer and add a product to the cart.

Explain:

- cart is stored relationally
- cart items create a user-product transactional relationship
- API authorization ensures only logged-in users can modify carts

### Step 5: Checkout

Proceed with checkout using the default seeded address and coupon `SAVE10`.

Explain:

- this is the main ACID demo
- inventory validation and order creation happen in one transaction
- payment and order confirmation are tied together

### Step 6: Explain rollback path

Mention that the API supports a simulated failure path during checkout.

Explain:

- if simulated failure is triggered before commit, order and payment do not persist
- this proves atomicity and rollback

### Step 7: Show seller features

Login as seller and show seller dashboard.

Explain:

- seller can create listings
- admin moderation protects catalog quality
- seller inventory updates are separate from product metadata

### Step 8: Show admin features

Login as admin and show:

- dashboard analytics
- top products
- monthly sales
- active customers
- pending product moderation
- SQL audit log

Explain:

- analytics use SQL views and aggregates
- audit log demonstrates trigger-based auditing
- moderation demonstrates RBAC

### Step 9: Explain MongoDB usage

Mention that MongoDB stores:

- product view logs
- recommendation logs
- user activity logs
- support chat logs

Explain:

- these are flexible document-style collections
- they are useful for analytics and logging but not ideal as core transactional source of truth

## 5. PostgreSQL study material and demo queries

### 5.1 Connect to PostgreSQL inside Docker

```sql
sudo docker exec -it ec_postgres psql -U ecuser -d ecommerce
```

Why:

- your container is named `ec_postgres`
- the database user is `ecuser`
- the database name is `ecommerce`

### 5.2 List all tables

```sql
\dt
```

Expected discussion:

- shows all relational entities created by SQLAlchemy and Alembic
- proves the schema is normalized across many related tables

### 5.3 Describe an important table

```sql
\d products
\d inventory
\d orders
\d order_items
```

What to explain:

- `products` stores product metadata
- `inventory` stores quantity and reorder threshold separately
- `orders` and `order_items` implement order header and line-item modeling

### 5.4 Show sample rows

```sql
SELECT id, email, full_name FROM users ORDER BY id;
SELECT id, name, slug, price, moderation_status FROM products ORDER BY id;
SELECT product_id, quantity, reorder_threshold FROM inventory ORDER BY product_id;
```

What to explain:

- users are seeded
- product catalog is seeded
- inventory levels allow the low-stock trigger demo

### 5.5 Demonstrate a simple join

```sql
SELECT
  p.id,
  p.name,
  c.name AS category_name,
  i.quantity
FROM products p
JOIN categories c ON c.id = p.category_id
JOIN inventory i ON i.product_id = p.id
ORDER BY p.id;
```

Why this query matters:

- demonstrates foreign keys and joins
- shows how normalized tables are recombined during reads

### 5.6 Demonstrate many-to-many roles

```sql
SELECT
  u.email,
  r.name AS role_name
FROM users u
JOIN user_roles ur ON ur.user_id = u.id
JOIN roles r ON r.id = ur.role_id
ORDER BY u.email, r.name;
```

Why this query matters:

- demonstrates RBAC schema
- shows how many-to-many relationships are modeled with bridge tables

### 5.7 Demonstrate aggregate analytics

```sql
SELECT
  o.user_id,
  COUNT(o.id) AS orders_count,
  COALESCE(SUM(o.total), 0) AS total_spent
FROM orders o
GROUP BY o.user_id
ORDER BY total_spent DESC;
```

Why this query matters:

- demonstrates aggregate functions
- useful for customer analytics

### 5.8 Demonstrate nested subquery

```sql
SELECT COALESCE(SUM(o.total), 0) AS revenue_completed
FROM orders o
WHERE o.id IN (
  SELECT o2.id
  FROM orders o2
  JOIN payments p ON p.order_id = o2.id
  WHERE p.status = 'completed'
);
```

Why this query matters:

- demonstrates nested subqueries
- similar logic is used in the admin dashboard revenue calculation

### 5.9 Demonstrate views

```sql
SELECT * FROM v_top_selling_products;
SELECT * FROM v_monthly_sales;
SELECT * FROM v_active_customers;
```

Why this query matters:

- demonstrates logical abstraction over complex SQL
- proves reporting can be simplified using database views

### 5.10 Demonstrate SQL function

```sql
SELECT fn_order_item_subtotal(1, 1);
```

Note:

- this returns the subtotal for a specific order item combination
- it works only when that order and product combination exists

Why this query matters:

- demonstrates reusable SQL logic inside the database

### 5.11 Demonstrate trigger-backed audit

First inspect products:

```sql
SELECT id, name FROM products ORDER BY id;
```

Then, if a product is not tied to historical orders, delete it as admin through the app or via SQL for a controlled demo.

Check audit log:

```sql
SELECT id, action, table_name, entity_id, created_at
FROM sql_audit_log
ORDER BY created_at DESC;
```

Why this query matters:

- proves the database captured a delete event automatically
- shows `BEFORE DELETE` trigger behavior

### 5.12 Demonstrate low-stock notification trigger

Use a product whose stock is close to the reorder threshold, such as the seeded smartwatch.

Check inventory first:

```sql
SELECT p.id, p.name, i.quantity, i.reorder_threshold
FROM products p
JOIN inventory i ON i.product_id = p.id
ORDER BY p.id;
```

After enough successful purchases, check:

```sql
SELECT user_id, title, body, created_at
FROM notifications
ORDER BY created_at DESC
LIMIT 10;
```

Why this query matters:

- shows automatic side effects from trigger logic
- demonstrates how inventory changes can notify a seller

## 6. MongoDB study material and demo queries

### 6.1 Connect to MongoDB

```bash
sudo docker exec -it ec_mongo mongosh
```

Then:

```javascript
use ecommerce_logs
show collections
```

### 6.2 Inspect recommendation logs

```javascript
db.recommendation_logs.find().sort({_id: -1}).limit(5)
```

Why:

- recommendations route logs payloads in MongoDB
- demonstrates flexible JSON event storage

### 6.3 Inspect product view logs

```javascript
db.product_view_logs.find().sort({_id: -1}).limit(5)
```

Why:

- product detail page browsing creates view logs
- shows event capture outside the transactional schema

### 6.4 Inspect support chat logs

```javascript
db.chat_support_messages.find().sort({_id: -1}).limit(5)
```

Why:

- demonstrates document-style support logging
- schema can evolve without relational migrations

## 7. Important endpoints to mention in viva

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/products/`
- `GET /api/products/{id}`
- `GET /api/categories/`
- `GET /api/cart/`
- `POST /api/cart/`
- `POST /api/orders/checkout`
- `GET /api/recommendations/`
- `GET /api/admin/analytics/dashboard`
- `GET /api/admin/analytics/top-products`
- `GET /api/admin/audit/sql`

Why this matters:

- shows clear mapping between UI and backend operations
- helps explain where each concept appears in the API

## 8. Key viva answers

### Why did you use PostgreSQL?

Because the app requires strong consistency, relational joins, constraints, transactions, triggers, and analytical SQL features.

### Why did you use MongoDB if PostgreSQL already exists?

Because logs and recommendation events are semi-structured and append-heavy. MongoDB handles that better and avoids overloading the relational schema with flexible telemetry data.

### Where is ACID demonstrated?

In the checkout flow. Order creation, payment creation, inventory changes, and cart clearing happen in one transaction. If any step fails, the whole transaction rolls back.

### Where is concurrency control demonstrated?

In checkout using `SELECT ... FOR UPDATE` on inventory rows. This prevents conflicting purchases from overselling stock.

### Why are triggers used?

Triggers ensure inventory reduction, low-stock notifications, payment-based order confirmation, and audit logging happen automatically at the database layer.

### Why are views used?

Views simplify repeated analytics queries and keep reporting logic reusable and readable.

### Why is inventory a separate table from products?

Because stock data changes operationally and frequently, while product metadata is relatively stable. This separation improves normalization and maintainability.

### How is RBAC implemented?

RBAC is modeled with users, roles, permissions, and bridge tables in PostgreSQL. FastAPI dependencies then enforce access rules in the API.

## 9. Short demo script you can speak

Start by saying:

"This project is a full-stack e-commerce application built to demonstrate practical DBMS concepts. PostgreSQL stores all transactional and relational data, while MongoDB stores flexible logs and event data. The main DBMS highlights are normalization, constraints, transactions, row locking, triggers, views, SQL functions, and RBAC."

Then say:

"I will first log in as a buyer, browse products, add items to cart, and perform checkout. This demonstrates relational schema design, joins, and the ACID transaction flow. Next I will show seller and admin views, where I can demonstrate analytics views, moderation, triggers, and audit logging. Finally I will show MongoDB collections used for event logging and recommendations."

## 10. Final conclusion

MarketGrid is a good DBMS demo project because it does not show concepts in isolation. Instead, it ties them to an actual application workflow:

- normalized schema supports clean relational modeling
- constraints enforce data correctness
- transactions and locks protect checkout consistency
- triggers automate critical database reactions
- views and SQL functions support analytics
- RBAC secures application behavior
- MongoDB complements PostgreSQL for flexible event logging

This makes the app suitable both for a live demo and for explaining why each DBMS concept matters in a real system.
