#include <stdio.h>

// Функция для сложения
float add(float a, float b) {
    return a + b;
}

// Функция для вычитания
float subtract(float a, float b) {
    return a - b;
}

// Функция для умножения
float multiply(float a, float b) {
    return a * b;
}

// Функция для деления
float divide(float a, float b) {
    if (b != 0) {
        return a / b;
    } else {
        printf("Ошибка: Деление на ноль!\n");
        return 0; // Возвращаем 0 в случае деления на ноль
    }
}

int main() {
    float num1, num2;
    char operator;

    // Запрашиваем у пользователя ввод двух чисел и оператора
    printf("Введите первое число: ");
    scanf("%f", &num1);
    printf("Введите второе число: ");
    scanf("%f", &num2);
    printf("Введите оператор (+, -, *, /): ");
    scanf(" %c", &operator); // Пробел перед %c для игнорирования пробелов

    float result;

    // Выполняем операцию в зависимости от введенного оператора
    switch (operator) {
        case '+':
            result = add(num1, num2);
            printf("Результат: %.2f\n", result);
            break;
        case '-':
            result = subtract(num1, num2);
            printf("Результат: %.2f\n", result);
            break;
        case '*':
            result = multiply(num1, num2);
            printf("Результат: %.2f\n", result);
            break;
        case '/':
            result = divide(num1, num2);
            if (num2 != 0) {
                printf("Результат: %.2f\n", result);
            }
            break;
        default:
            printf("Ошибка: Неверный оператор!\n");
            break;
    }

    return 0;
}