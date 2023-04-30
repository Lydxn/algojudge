from algojudge.comparators import comparator
from algojudge.comparators._compare import compare_standard


@comparator(name='standard')
def compare(fa, fb):
    return compare_standard(fa, fb)
