import io
import sys
import pytest
from studio5 import run


def test_skip_after_raise():
    code = """
    try {
        print(1);
        raise 99;
        print(2);
    } catch(e) {
        print("caught", e);
    }
    print(3);
    """

    backup = sys.stdout
    sys.stdout = io.StringIO()

    run(code)
    output = sys.stdout.getvalue().strip().splitlines()

    sys.stdout = backup

    assert output == [
        "1",
        "caught 99",
        "3"
    ]


def test_nested_try_catch():
    code = """
    try {
        try {
            raise "X";
        } catch(inner) {
            raise inner;
        }
    } catch(outer) {
        print("handled:", outer);
    }
    """

    backup = sys.stdout
    sys.stdout = io.StringIO()

    run(code)
    output = sys.stdout.getvalue().strip()

    sys.stdout = backup

    assert output == "handled: X"


def test_uncaught_exception():
    with pytest.raises(RuntimeError) as excinfo:
        run("raise 10;")

    assert str(excinfo.value) == "Uncaught exception: 10"

def test_array_creation_and_read():
    code = """
    a = [1, 2, 3];
    a[1];
    """
    assert run(code) == 2

def test_string_literal_and_index_read():
    code = '''
    s = "hello";
    s[1];
    '''
    assert run(code) == "e"

def test_array_write_and_mutability():
    code = """
    a = [10, 20, 30];
    a[1] = 99;
    a[1];
    """
    assert run(code) == 99

def test_len_builtin_on_array_and_string():
    code = """
    x = [1,2,3,4];
    y = "abc";
    lx = len(x);
    ly = len(y);
    lx;
    """
    assert run(code) == 4
    # ensure string len works too
    code2 = 'y = "abc"; len(y);'
    assert run(code2) == 3

def test_index_assign_type_error_on_non_array():
    code = """
    x = 5;
    x[0] = 1;
    """
    with pytest.raises(TypeError):
        run(code)

def test_index_non_integer_error():
    code = """
    a = [1,2,3];
    i = "notint";
    a[i] = 5;
    """
    with pytest.raises(TypeError):
        run(code)