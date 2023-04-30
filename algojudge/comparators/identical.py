from algojudge.comparators import comparator
from algojudge.comparators._compare import compare_identical


@comparator(name='identical')
def compare(fa, fb):
    return compare_identical(fa, fb)
