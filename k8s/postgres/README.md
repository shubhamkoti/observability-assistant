## Create PostgreSQL Secret

Run this before applying the PostgreSQL deployment to create k8s secret:

```bash
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=<your-password> \
  --from-literal=POSTGRES_DB=ecommerce \
  -n ecommerce
```