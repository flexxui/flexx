import os

def test_that_tests_dont_have_multiple_functions_with_same_name():
    dir = os.path.dirname(__file__)
    for fname in os.listdir(dir):
        if not (fname.startswith('test_') and fname.endswith('.py')):
            continue
        print(fname)
        text = open(os.path.join(dir, fname), 'rb').read().decode()
        func_names = set()

        for line in text.splitlines():
            line = line.split('(')[0].strip()
            if line.startswith('def '):
                func_name = line[4:]
                if func_name.startswith('test_'):
                    print(func_name)
                    assert func_name not in func_names, (fname, func_name)
                    func_names.add(func_name)


if __name__ == '__main__':
    test_that_tests_dont_have_multiple_functions_with_same_name()
