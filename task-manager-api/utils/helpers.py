"""Utilitários puros, sem estado e sem acesso a banco. Só o que é usado pela aplicação."""
import re

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return bool(isinstance(email, str) and EMAIL_PATTERN.match(email))


def is_valid_color(color):
    return bool(isinstance(color, str) and len(color) == 7 and color[0] == '#')
