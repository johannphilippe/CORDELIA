import abjad

values = [60, 62, 63] #Your MIDI values
notes = [abjad.Note(number - 60, (1, 4)) for number in values]
container = abjad.Container(notes) #Instead of a Container you can also use a Staff

abjad.persist.as_png(container, '/Users/j/Desktop/123.png', resolution=300)
