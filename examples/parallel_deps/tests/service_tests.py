"""
This is just a simple test file meant to show and test dependency chains.
"""

import time


from proboscis.asserts import assert_equal
from proboscis.asserts import assert_false
from proboscis.asserts import assert_raises
from proboscis.asserts import assert_true
from proboscis import SkipTest
from proboscis import test


"""
This structure seems simple but has already proven worthwhile by unearthing
an initial bug where the nested suite would start with ga1, include ga2 but
not ga3 as ga1 didn't have a marked dependent on ga3.
"""

counter = 0

@test(groups=["GA"])
def ga1():
    time.sleep(1)
    global counter
    counter += 1
    assert_equal(1, counter)


@test(groups=["GA"], depends_on=[ga1])
def ga2():
    time.sleep(1)
    global counter
    counter += 1
    assert_equal(2, counter)


@test(groups=["GA"], depends_on=[ga2])
def ga3():
    time.sleep(1)
    global counter
    counter += 1
    assert_equal(3, counter)


@test(groups=["GB"])
def gb1():
    time.sleep(1)
    global counter
    counter += 1
    assert_equal(1, counter)


@test(groups=["GB"], depends_on=[gb1])
def gb2():
    time.sleep(1)
    global counter
    counter += 1
    import sys
    assert_equal(200, counter)


@test(groups=["GB"], depends_on=[gb2])
def gb3():
    time.sleep(1)
    global counter
    counter += 1
    assert_equal(3, counter)

@test(groups=["GC"])
def gc1():
    time.sleep(1)
    global counter
    counter += 1
    assert_equal(1, counter)


@test(groups=["GC"], depends_on=[gc1])
def gc2():
    time.sleep(1)
    global counter
    counter += 1
    assert_equal(200, counter)


@test(groups=["GC"], depends_on=[gc2])
def gc3():
    time.sleep(1)
    global counter
    counter += 1
    assert_equal(3, counter)

@test(groups=["GC"], depends_on=[gc3])
def gc4():
    time.sleep(1)
    global counter
    counter += 1
    assert_equal(4, counter)


@test(groups=["GABC"], depends_on=[ga3, gb3, gc3], enabled=False)
def ga3b3c3():
    pass


