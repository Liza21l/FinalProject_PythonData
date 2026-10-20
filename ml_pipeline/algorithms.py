from collections import deque


# ==================================================
# 1. FIFO QUEUE — черга
# ==================================================

class Queue:
    def __init__(self):
        self.items = deque()

    def enqueue(self, item):
        """Додає елемент у кінець черги."""
        self.items.append(item)

    def dequeue(self):
        """Видаляє та повертає перший елемент."""
        if self.is_empty():
            raise IndexError("Черга порожня")

        return self.items.popleft()

    def peek(self):
        """Показує перший елемент без видалення."""
        if self.is_empty():
            raise IndexError("Черга порожня")

        return self.items[0]

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)


# ==================================================
# 2. LIFO STACK — стек
# ==================================================

class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        """Додає елемент на вершину стека."""
        self.items.append(item)

    def pop(self):
        """Видаляє та повертає верхній елемент."""
        if self.is_empty():
            raise IndexError("Стек порожній")

        return self.items.pop()

    def peek(self):
        """Показує верхній елемент без видалення."""
        if self.is_empty():
            raise IndexError("Стек порожній")

        return self.items[-1]

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)


# ==================================================
# 3. BUBBLE SORT — сортування бульбашкою
# ==================================================

def bubble_sort(arr):
    """Повертає новий список, відсортований за зростанням."""
    result = arr.copy()
    n = len(result)

    for i in range(n):
        swapped = False

        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = (
                    result[j + 1],
                    result[j]
                )
                swapped = True

        # Якщо обмінів не було, список уже відсортований.
        if not swapped:
            break

    return result


# ==================================================
# 4. QUICK SORT — швидке сортування
# ==================================================

def quick_sort(arr):
    """Повертає новий список, відсортований за зростанням."""
    if len(arr) <= 1:
        return arr.copy()

    pivot = arr[len(arr) // 2]

    less = []
    equal = []
    greater = []

    for item in arr:
        if item < pivot:
            less.append(item)
        elif item > pivot:
            greater.append(item)
        else:
            equal.append(item)

    return quick_sort(less) + equal + quick_sort(greater)


# ==================================================
# 5. LINEAR SEARCH — лінійний пошук
# ==================================================

def linear_search(arr, target):
    """
    Повертає індекс першого знайденого елемента.
    Якщо елемент не знайдено, повертає -1.
    """
    for index in range(len(arr)):
        if arr[index] == target:
            return index

    return -1


# ==================================================
# 6. BINARY SEARCH — бінарний пошук
# ==================================================

def binary_search(arr, target):
    """
    Шукає елемент у відсортованому списку.
    Повертає індекс елемента або -1, якщо його немає.
    """
    left = 0
    right = len(arr) - 1

    while left <= right:
        middle = (left + right) // 2

        if arr[middle] == target:
            return middle

        elif arr[middle] < target:
            left = middle + 1

        else:
            right = middle - 1

    return -1


# ==================================================
# ТЕСТУВАННЯ АЛГОРИТМІВ
# ==================================================

if __name__ == "__main__":

    print("=== FIFO QUEUE ===")

    queue = Queue()

    queue.enqueue("Операція 1")
    queue.enqueue("Операція 2")
    queue.enqueue("Операція 3")

    print("Перший елемент:", queue.peek())
    print("Видалено:", queue.dequeue())
    print("Розмір черги:", queue.size())

    print("\n=== LIFO STACK ===")

    stack = Stack()

    stack.push("Транзакція 1")
    stack.push("Транзакція 2")
    stack.push("Транзакція 3")

    print("Верхній елемент:", stack.peek())
    print("Видалено:", stack.pop())
    print("Розмір стека:", stack.size())

    print("\n=== BUBBLE SORT ===")

    numbers = [64, 34, 25, 12, 22, 11, 90]

    print("Початковий список:", numbers)
    print("Відсортований:", bubble_sort(numbers))

    print("\n=== QUICK SORT ===")

    print("Початковий список:", numbers)
    print("Відсортований:", quick_sort(numbers))

    print("\n=== LINEAR SEARCH ===")

    print("Індекс числа 22:", linear_search(numbers, 22))
    print("Індекс числа 100:", linear_search(numbers, 100))

    print("\n=== BINARY SEARCH ===")

    sorted_numbers = quick_sort(numbers)

    print("Відсортований список:", sorted_numbers)
    print("Індекс числа 22:", binary_search(sorted_numbers, 22))
    print("Індекс числа 100:", binary_search(sorted_numbers, 100))

    print("\nУсі демонстраційні тести виконано!")
