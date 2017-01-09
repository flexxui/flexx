"""
Manual test. Should be run on each supported platform.
"""

from flexx import dialite

PREFIX = 'DIALITE TEST: '

# Calibrate

res = dialite.ask(PREFIX + 'yes-no',
                  'Do you see two buttons saying "Yes and "no"? '
                  'If not this test failed before it really started ...')
assert res is True

res = dialite.ask(PREFIX + 'yes-no', 'Make me a sandwich.')
assert res is False

res = dialite.ask(PREFIX + 'yes-no', 'Sudo make me a sandwich.')
assert res is True

# Unicode

res = dialite.ask(PREFIX + 'unicode',
                  'Do you see "double quotes", \'single quotes\', '
                  'a euro symbol (€), pi symbol (π), an A with a roof (Â)?')
assert res is True

# Three message boxes

res = dialite.inform(PREFIX + 'info', 'Awesome! '
                     'We will now show three dialogs: info, warn, error. '
                     'This is the first one; an info dialog.')
assert res is None

res = dialite.warn(PREFIX + 'warn', 'This is the second one; a warning.')
assert res is None

res = dialite.fail(PREFIX + 'error', 'This is the third one; an error.')
assert res is None

# Check results

res = dialite.ask(PREFIX + 'check',
                  'Did the past three boxes only have 1 OK button?')
assert res is True

res = dialite.ask(PREFIX + 'check',
                  'Did the past three boxes look something like an info, '
                  'warning, and error dialog?')
assert res is True

# Check verify

res = dialite.verify(PREFIX + 'verify',
                     'Great, I am going to asume all tests passed then!'
                     'Press OK to continue.')
assert res is True

res = dialite.ask(PREFIX + 'check',
                  'Did you just see two buttons saying "OK" and "Cancel"?')
assert res is True

res = dialite.verify(PREFIX + 'verify',
                     'This one is a bit weird. I want you to press Cancel, '
                     'but I don\'t want you to agree and accidentally press '
                     'OK. Therefore, imagine this:\n\nWe will now proceed '
                     'with erasing all your data.')
assert res is False

# Done

res = dialite.inform(PREFIX + 'done',
                     'This was the test, it looks like it passed!')
