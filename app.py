from flask import Flask, request, jsonify
import jwt
import datetime
from functools import wraps
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

logging.basicConfig(filename='transactions.log', level=logging.INFO,
                    format='%(asctime)s %(message)s')

accounts = {}
next_account_id = 1

SECRET_KEY = "*&)HD@bh7!DIUS*&DY!@IHPD!PD@D!D@DDSAKHS"

exchange_rates = {
    "USD": {"USD": 1, "EUR": 0.85, "GBP": 0.75},
    "EUR": {"EUR": 1, "USD": 1.18, "GBP": 0.88},
    "GBP": {"GBP": 1, "USD": 1.33, "EUR": 1.14}
}

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


def log_transaction(action, details):
    logging.info(f"{action}: {details}")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-tokens')
        if not token:
            return jsonify({"error": "Token is missing!"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['user']
        except:
            return jsonify({"error": "Invalid token!"}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def convert_currency(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return amount
    rate = exchange_rates[from_currency][to_currency]
    return amount * rate


def get_account(account_id):
    account = accounts.get(account_id)
    if account is None:
        return None
    return account


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data['username'] == 'admin' and data['password'] == 'password':
        token = jwt.encode({
            'user': data['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
            SECRET_KEY, algorithm="HS256")
        return jsonify({'token': token})
    return jsonify({"error": "Invalid credentials!"}), 401


@app.route('/create-account', methods=['POST'])
@limiter.limit("10 per minute")
@token_required
def create_account(current_user):
    global next_account_id
    data = request.get_json()

    if 'name' not in data or 'initial_balance' not in data or 'currency' not in data:
        return jsonify({"error": "Invalid input"}), 400

    name = data['name']
    initial_balance = float(data['initial_balance'])
    currency = data['currency']

    if currency not in exchange_rates:
        return jsonify({"error": "Unsupported currency"}), 400

    account = {
        'id': next_account_id,
        'name': name,
        'balance': initial_balance,
        'currency': currency
    }
    accounts[next_account_id] = account
    next_account_id += 1

    return jsonify(account), 201


@app.route('/deposit', methods=['POST'])
@limiter.limit("20 per minute")
@token_required
def deposit(current_user):
    data = request.get_json()

    if 'account_id' not in data or 'amount' not in data:
        return jsonify({"error": "Invalid input"}), 400

    account_id = int(data['account_id'])
    amount = float(data['amount'])

    account = get_account(account_id)
    if account is None:
        return jsonify({"error": "Account not found"}), 404

    account['balance'] += amount
    log_transaction('Deposit', f"Account {account_id}: +{amount}")
    return jsonify({"account_id": account_id, "new_balance": account['balance']}), 200


@app.route('/withdraw', methods=['POST'])
@limiter.limit("10 per minute")
@token_required
def withdraw(current_user):
    data = request.get_json()

    if 'account_id' not in data or 'amount' not in data:
        return jsonify({"error": "Invalid input"}), 400

    account_id = int(data['account_id'])
    amount = float(data['amount'])

    account = get_account(account_id)
    if account is None:
        return jsonify({"error": "Account not found"}), 404

    if account['balance'] < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    account['balance'] -= amount
    log_transaction('Withdraw', f"Account {account_id}: -{amount}")
    return jsonify({"account_id": account_id, "new_balance": account['balance']}), 200


@app.route('/transfer', methods=['POST'])
@limiter.limit("10 per minute")
@token_required
def transfer(current_user):
    data = request.get_json()

    from_account_id = int(data['from_account_id'])
    to_account_id = int(data['to_account_id'])
    amount = float(data['amount'])

    from_account = get_account(from_account_id)
    to_account = get_account(to_account_id)

    if from_account is None or to_account is None:
        return jsonify({"error": "One or both accounts not found"}), 404

    if from_account['balance'] < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    converted_amount = convert_currency(amount, from_account['currency'], to_account['currency'])

    from_account['balance'] -= amount
    to_account['balance'] += converted_amount

    log_transaction('Transfer', f"From {from_account_id} to {to_account_id}: {amount}")
    return jsonify({
        "from_account_id": from_account_id,
        "from_account_balance": from_account['balance'],
        "to_account_id": to_account_id,
        "to_account_balance": to_account['balance']
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
