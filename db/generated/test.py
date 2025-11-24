from werkzeug.security import check_password_hash

stored = "pbkdf2:sha256:600000$YmF989pR7sB8FujQ$3dd61b87e337f4657c382ea4af50da6263581a496712ab493e3346f67bfa1135"
print(check_password_hash(stored, "pass0"))