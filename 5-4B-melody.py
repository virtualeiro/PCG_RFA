import pygame.midi
import time
import random

# Initialize MIDI
pygame.midi.init()
player = pygame.midi.Output(0)
instrument = 0  # piano
player.set_instrument(instrument)

# Define symbols
notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C
durations = [0.25, 0.5, 1]  # quarter, half, whole notes

# Grammar rules
# Melody -> Note Melody | Note
def generate_melody(length=8):
    melody = []
    for _ in range(length):
        note = random.choice(notes)
        duration = random.choice(durations)
        melody.append((note, duration))
    return melody

melody = generate_melody()

# Play the melody
for note, duration in melody:
    player.note_on(note, 127)  # play note at full velocity
    time.sleep(duration)
    player.note_off(note, 127)

player.close()
pygame.midi.quit()