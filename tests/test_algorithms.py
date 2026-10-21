
from ml_pipeline.algorithms import (
    bubble_sort,
    quick_sort,
    linear_search,
    binary_search,
)
# =========================
# BUBBLE SORT
# =========================

def test_bubble_sort_normal_list():
    assert bubble_sort([5, 2, 8, 1, 3]) == [1, 2, 3, 5, 8]


def test_bubble_sort_already_sorted():
    assert bubble_sort([1, 2, 3, 4]) == [1, 2, 3, 4]


def test_bubble_sort_empty_list():
    assert bubble_sort([]) == []


def test_bubble_sort_duplicates():
    assert bubble_sort([4, 2, 2, 1, 4]) == [1, 2, 2, 4, 4]


# =========================
# QUICK SORT
# =========================

def test_quick_sort_normal_list():
    assert quick_sort([5, 2, 8, 1, 3]) == [1, 2, 3, 5, 8]


def test_quick_sort_already_sorted():
    assert quick_sort([1, 2, 3, 4]) == [1, 2, 3, 4]


def test_quick_sort_empty_list():
    assert quick_sort([]) == []


def test_quick_sort_duplicates():
    assert quick_sort([4, 2, 2, 1, 4]) == [1, 2, 2, 4, 4]


# =========================
# LINEAR SEARCH
# =========================

def test_linear_search_found():
    assert linear_search([10, 20, 30, 40], 30) == 2


def test_linear_search_not_found():
    assert linear_search([10, 20, 30, 40], 50) == -1


def test_linear_search_empty_list():
    assert linear_search([], 10) == -1


# =========================
# BINARY SEARCH
# =========================

def test_binary_search_found():
    assert binary_search([10, 20, 30, 40, 50], 30) == 2


def test_binary_search_first_element():
    assert binary_search([10, 20, 30, 40, 50], 10) == 0


def test_binary_search_last_element():
    assert binary_search([10, 20, 30, 40, 50], 50) == 4


def test_binary_search_not_found():
    assert binary_search([10, 20, 30, 40, 50], 35) == -1


def test_binary_search_empty_list():
    assert binary_search([], 10) == -1
