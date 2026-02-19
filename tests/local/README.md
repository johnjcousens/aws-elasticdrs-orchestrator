# Local Development Testing

Run the Lambda and frontend locally to test changes without deploying.

## Quick Start

```bash
# 1. Test Lambda logic locally
python tests/local/test_regional_capacity.py

# 2. Run frontend dev server (in another terminal)
cd frontend
npm run dev

# 3. Update frontend to use local mock API
# Edit frontend/public/aws-config.local.json to point to local mock server
```

## Benefits

- **Instant feedback**: See changes immediately without 5-minute deployments
- **No AWS costs**: Test without hitting AWS APIs
- **Faster iteration**: Fix bugs in seconds, not hours
- **Debug easily**: Use breakpoints and print statements

## Local Lambda Testing

The `test_regional_capacity.py` script:
- Imports the actual Lambda handler code
- Mocks AWS API responses
- Prints formatted output showing what the API would return
- Validates expected values

Run it after making changes to `lambda/query-handler/index.py`:

```bash
python tests/local/test_regional_capacity.py
```

## Frontend Dev Server

The frontend dev server runs on `http://localhost:5173` with hot reload:

```bash
cd frontend
npm run dev
```

Changes to React components update instantly in the browser.

## Mock API Server (Future)

To fully test the frontend locally, we can add a mock API server that:
- Serves the Lambda responses as HTTP endpoints
- Allows testing the full frontend without AWS
- Can be extended with different test scenarios

This would require adding a simple Express/Flask server that imports the Lambda handlers.
