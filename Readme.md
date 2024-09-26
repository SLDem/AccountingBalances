App to create accounts and perform operations with it.

Use Postman to test:
1. Send POST request to http://127.0.0.1:5000/login with json: `{"username": "admin", "password": "password"}` to get your auth token. Example response:
`{"token": "your.token.here"}`
   
2. Add token to headers like this: `x-access-tokens: your.token.here`
3. Send POST request to http://127.0.0.1:5000/create-account with json: `{"name": "John", "initial_balance": 1000, "currency": "USD"}` you should see response with account id.
4. Send POST request to http://127.0.0.1:5000/deposit with json: `{"account_id": 1, "amount": 200}` you should see response with new balance.
5. Send POST request to http://127.0.0.1:5000/withdraw with json: `{"account_id": 1, "amount": 100}` you should see updated balance.
6. Send POST request to http://127.0.0.1:5000/create-account with json: `{"name": "Jack", "initial_balance": 2000, "currency": "USD"}` you should see response with second account id.
7. Send POST request to http://127.0.0.1:5000/transfer with json: `{"from_account_id": 1, "to_account_id": 2, "amount": 50}` you should see response with info about transfer.
