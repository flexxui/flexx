from flexx import dialite

# dialite.inform('Flexx info', 'Hey, just calling to say hi ...')
dialite.inform('Flexx info', 'Do \' and \" and € work?...')

dialite.warn('Flexx warning', 'Oops, this does not look good ...')

dialite.fail('Flexx error', 'Oh oh... fail!')

dialite.verify('Proceed', 'We will now erase your computer.')

dialite.ask('Flexx needs some info', 'Do you like Flexx'*10 + '\n' + 'asdasdasas' + '\n\n' + 'asdasasd')


