# Nginx connects to Gunicorn over loopback and relays the ALB's client scheme.
forwarded_allow_ips = "127.0.0.1,::1"
secure_scheme_headers = {"X-FORWARDED-PROTO": "https"}
