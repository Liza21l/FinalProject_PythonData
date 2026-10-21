
import pytest

from web_app.structures import Queue, Stack


def test_queue_fifo_order():
    queue = Queue()

    queue.enqueue("Перша")
    queue.enqueue("Друга")
    queue.enqueue("Третя")

    assert queue.dequeue() == "Перша"
    assert queue.dequeue() == "Друга"
    assert queue.dequeue() == "Третя"


def test_queue_peek_and_size():
    queue = Queue()

    queue.enqueue("Операція 1")
    queue.enqueue("Операція 2")

    assert queue.peek() == "Операція 1"
    assert queue.size() == 2
    assert queue.is_empty() is False

    # peek не повинен видаляти елемент
    assert queue.size() == 2


def test_empty_queue():
    queue = Queue()

    assert queue.is_empty() is True
    assert queue.size() == 0

    with pytest.raises(IndexError):
        queue.dequeue()

    with pytest.raises(IndexError):
        queue.peek()


def test_stack_lifo_order():
    stack = Stack()

    stack.push("Перша")
    stack.push("Друга")
    stack.push("Третя")

    assert stack.pop() == "Третя"
    assert stack.pop() == "Друга"
    assert stack.pop() == "Перша"


def test_stack_peek_and_size():
    stack = Stack()

    stack.push("Транзакція 1")
    stack.push("Транзакція 2")

    assert stack.peek() == "Транзакція 2"
    assert stack.size() == 2
    assert stack.is_empty() is False

    # peek не повинен видаляти елемент
    assert stack.size() == 2


def test_empty_stack():
    stack = Stack()

    assert stack.is_empty() is True
    assert stack.size() == 0

    with pytest.raises(IndexError):
        stack.pop()

    with pytest.raises(IndexError):
        stack.peek()
