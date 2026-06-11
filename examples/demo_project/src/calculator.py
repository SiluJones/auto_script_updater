"""Calculadora simples — arquivo-alvo da demo."""


class Calculator:
    """Operações aritméticas básicas."""

    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        """Divide a por b, com proteção contra divisão por zero."""
        if b == 0:
            raise ValueError("Divisão por zero não é permitida")
        return a / b


def greet():
    return "Olá da calculadora"
