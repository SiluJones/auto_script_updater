"""Calculadora simples — arquivo-alvo da demo."""


class Calculator:
    """Operações aritméticas básicas."""

    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        # versão ingênua: não trata divisão por zero
        return a / b


def greet():
    return "Olá da calculadora"
