# scoring API
Алгоритм принимает запрос формата,
указанного в Request example или Admin request structure

## Usage example

```python
>>> python api.py
```

## Request structure

```python
>>> curl -X POST -H "Content-Type: application/json" -d '{"account": "company name", "login": "user login", "method": "clients_interests", "token": "23bjxn38en2x37exn2exn29r46srtx23644gydh265bx19xfncb", "arguments": {"phone": "79027462301", "email": "example@otus.ru", "first_name": "Name", "last_name": "Lname", "birthday": "01.02.1910", "gender": 1}}' http://127.0.0.1:8080/method/
```

## Admin request structure

```python
>>> curl -X POST -H "Content-Type: application/json" -d '{"account": "company name", "login": "admin", "method": "online_score", "token": "89seg1g36rtfeda273xbe8ex6v43em89251ixmehf35exu2430r6f44w71e8uen", "arguments": {"client_ids": [102, 105, 4, 2], "date": "01.02.2009"}}' http://127.0.0.1:8080/method/
```