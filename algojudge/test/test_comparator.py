from algojudge.comparators import COMPARATORS
from io import BytesIO
from unittest import main, TestCase


def compare_bytes(type):
    def compare(a, b):
        return COMPARATORS[type](BytesIO(a), BytesIO(b))
    return compare


class ComparatorTest(TestCase):
    def test_identical(self):
        compare = compare_bytes('identical')

        self.assertTrue(compare(b'', b''))
        self.assertTrue(compare(b'a', b'a'))
        self.assertTrue(compare(b'a\nb\n', b'a\nb\n'))
        self.assertTrue(compare(b'\0\t\n\f\r ', b'\0\t\n\f\r '))
        self.assertTrue(compare(b'a'*10**5, b'a'*10**5))

        self.assertFalse(compare(b'', b'\0'))
        self.assertFalse(compare(b'a', b'b'))
        self.assertFalse(compare(b'a\r', b'a\n'))
        self.assertFalse(compare(b'a\r\n', b'a\n'))
        self.assertFalse(compare(b'a'*10**5+b'a', b'a'*10**5+b'b'))

    def test_standard(self):
        compare = compare_bytes('standard')

        self.assertTrue(compare(b'', b''))
        self.assertTrue(compare(b'', b'  '))
        self.assertTrue(compare(b'', b' \n\n\t\t\n  '))
        self.assertTrue(compare(b'a b', b'a b'))
        self.assertTrue(compare(b'a b', b'a b\n'))
        self.assertTrue(compare(b'a\nb\n', b'a\nb\n  \t\n\n '))
        self.assertTrue(compare(b'a\nb\n', b'a \nb'))
        self.assertTrue(compare(b'a'*10**5, b'a'*10**5))
        self.assertTrue(compare(b'a'*10**5+b' \n', b'a'*10**5+b'\n '))
        self.assertTrue(compare(b' '*10**5, b'\n'*10**5))

        self.assertFalse(compare(b'a', b''))
        self.assertFalse(compare(b'a b', b' a b'))
        self.assertFalse(compare(b'a b', b'\na b'))
        self.assertFalse(compare(b'a b', b'a\nb'))
        self.assertFalse(compare(b'a b', b'a \nb'))
        self.assertFalse(compare(b'a b', b'a b\r'))
        self.assertFalse(compare(b'a b', b'a b\n\r'))
        self.assertFalse(compare(b'a  \n b', b'a\nb'))
        self.assertFalse(compare(b'  a\nb', b' a\n\n'))
        self.assertFalse(compare(b'a b c', b'a bc'))
        self.assertFalse(compare(b'a  b c', b'a  b  c'))
        self.assertFalse(compare(b'a'*10**5+b'a', b'a'*10**5+b'b'))
        self.assertFalse(compare(b' '*10**5+b'a', b'\n'*10**5+b'a'))



if __name__ == '__main__':
    from algojudge.comparators import load_comparators

    load_comparators()

    main()
