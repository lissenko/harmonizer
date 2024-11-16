from music21 import converter, note, scale, pitch, stream, chord, duration
import sys
import random

NOTES_SHARP = ["do", "do#", "ré", "ré#", "mi", "fa", "fa#", "sol", "sol#", "la", "la#", "si"]
NOTES_FLAT = ["do", "réb", "ré", "mib", "mi", "fa", "solb", "sol", "lab", "la", "sib", "si"]
DEGREE = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII' ]
STRENGTH_TRESHOLD = 0.25
I = 1
II = 2
III = 3
IV = 4
V = 5
VI = 6
VII = 7

GRAMMAR = {
        I:   [I, II, III, IV, V, VII, VII],
        II:  [V, VII],
        III: [IV, VI],
        IV:  [I, II, V, VII],
        V:   [I, VI, VII],
        VI:  [II, IV],
        VII: [I]
        }

def create_chord(init, add_list):
    chord = [init % 12]
    for n in add_list:
        chord.append( (init + n) % 12 )
    return chord

def get_chords(tonic, mode):
    chords = []
    if mode == 'major':
        chords.append( create_chord(tonic, [4, 7])  ) # I
        chords.append( create_chord(tonic + 2, [3, 7])  ) # II
        chords.append( create_chord(tonic + 4, [3, 7])  ) # III
        chords.append( create_chord(tonic + 5, [4, 7])  ) # IV
        # chords.append( create_chord(tonic + 7, [4, 7]) ) # V
        chords.append( create_chord(tonic + 7, [4, 7, 10]) ) # V7
        chords.append( create_chord(tonic + 9, [3, 7])  ) # VI
        chords.append( create_chord(tonic + 11, [3, 6])  ) # VII (3 tierces mineures superposées)
        # chords.append( create_chord(tonic + 11, [3, 6, 9])  ) # VII7 (3 tierces mineures superposées)
    elif mode == 'minor':
        chords.append( create_chord(tonic, [3, 7])  ) # I
        chords.append( create_chord(tonic + 2, [3, 6])  ) # II
        chords.append( create_chord(tonic + 3, [4, 7])  ) # III
        chords.append( create_chord(tonic + 5, [3, 7])  ) # IV
        # chords.append( create_chord(tonic + 7, [4, 7])  ) # V: le 7e degré (la tierce) est augmentée d'un demi-ton pour rendre l'accord majeur pour qu'il aie une fonction de dominante
        chords.append( create_chord(tonic + 7, [4, 7, 10])  ) # V7: le 7e degré (la tierce) est augmentée d'un demi-ton pour rendre l'accord majeur pour qu'il aie une fonction de dominante
        chords.append( create_chord(tonic + 8, [4, 7])  ) # VI
        chords.append( create_chord(tonic + 11, [3, 6])  ) # VII: le 7e degré (la fondamentale) est augmenté d'un demi-ton pour rendre l'accord diminué
        # chords.append( create_chord(tonic + 11, [3, 6, 9])  ) # VII7: le 7e degré (la fondamentale) est augmenté d'un demi-ton pour rendre l'accord diminué
    else:
        print(f'Mode {mode} not supported')
    return chords

def get_info(midi_file_path):
    midi_stream = converter.parse(midi_file_path)
    score = midi_stream.flatten()
    time_signature = score.getElementsByClass('TimeSignature')[0]
    if not time_signature:
        time_signature = stream.TimeSignature('4/4')
    key_signature = score.analyze('key')

    durations = []
    notes = []
    beat_strength = []
    for element in score.notesAndRests:
        if isinstance(element, note.Note):
            notes.append(element.pitch.midi)
            beat_strength.append(element.beatStrength)
            durations.append(element.duration)
    tonic = key_signature.tonic.midi % 12
    mode = key_signature.mode
    use_flats = True if key_signature.sharps < 0 else False
    return notes, tonic, mode, time_signature, use_flats, beat_strength, midi_stream

def harmonize(notes, tonic, mode, beat_strength, note_table):

    idx_to_harmonize = [i for i, e in enumerate(beat_strength) if e >= STRENGTH_TRESHOLD]
    size = len(idx_to_harmonize)
    degrees = {}
    for i in range(size):
        degrees[i] = []
    available_chords = get_chords(tonic, mode)

    for pos, idx in enumerate(idx_to_harmonize):
        note = notes[idx] % 12
        for chord_idx, chord in enumerate(available_chords):
            if note in chord:
                degrees[pos].append(chord_idx+1)

    for pos, i in enumerate(idx_to_harmonize):
        print(note_table[notes[i]%12])
        print(degrees[pos])

    # First chord (I)
    if I not in degrees[0]:
        print("Error: There must be I in first position")
        sys.exit(1)
    else:
        degrees[0] = [I]

    # Last chord (I)
    if I not in degrees[size-1]:
        print("Error: There must be I in last position")
        sys.exit(1)
    else:
        degrees[size-1] = [I]

    # Penultimate chord (V)
    if V not in degrees[size-2]:
        print("Error: There must be V in penultimate position")
        sys.exit(1)

    rules = []
    for k in GRAMMAR:
        for v in GRAMMAR[k]:
            rules.append([k, v])

    for pos in range(1,size-1):
        current_options = degrees[pos]
        next_options = degrees[pos+1]
        for chord in current_options:
            available_options = GRAMMAR[chord]
            keep = any(option in available_options for option in next_options)
            if not keep:
                degrees[pos].remove(chord)

        current_options = degrees[pos]
        for next_chord in next_options:
            keep = False
            for current_chord in current_options:
                if [current_chord, next_chord] in rules:
                    keep = True
            if not keep:
                next_options.remove(next_chord)
        degrees[pos+1] = next_options

    progressions = []
    def generate_progressions(pos, progression):
        if pos == size-1:
            if not is_parallel_fifths(progression, available_chords, idx_to_harmonize, notes):
                progressions.append(progression)
            return
        else:
            next_options = degrees[pos+1]
            current = progression[-1]
            for next_chord in next_options:
                if [current, next_chord] in rules and next_chord != current:
                    generate_progressions(pos+1, progression + [next_chord])

    generate_progressions(0, degrees[0])
    return progressions, available_chords, idx_to_harmonize

def is_fifth(degree, chord, top_note):
    if degree == II or degree == VII: # renversement
        bottom_note = chord[1] # third
    else:
        bottom_note = chord[0] # root
    interval = (top_note - bottom_note) % 12
    isFifth = interval == 7 or interval == 6
    return isFifth


def is_parallel_fifths(progression, available_chords, idx_to_harmonize, notes):
    for i in range(len(progression)-1): # pour chaque degré
        degree = progression[i]
        chord = available_chords[degree-1]
        top_note = notes[idx_to_harmonize[i]] % 12

        if is_fifth(degree, chord, top_note):
            next_degree = progression[i+1]
            next_chord = available_chords[next_degree-1]
            next_top_note = notes[idx_to_harmonize[i]] % 12
            if is_fifth(next_degree, next_chord, next_top_note):
                return True
    return False

def print_chords(available_chords, note_table):
    for i, c in enumerate(available_chords):
        print(f'{DEGREE[i]}', end=': ')
        for n in c:
            print(note_table[n % 12], end=" ")
        print('\n---------------')

def get_chord_notes(ref, degree, ref_notes):
    if degree == II:
        ref_notes = [ref_notes[1], ref_notes[2], ref_notes[0]]
    n = (ref // 12) - 1
    chord_notes = [ (note + n * 12) for note in ref_notes ]
    chord_notes = []
    for note in ref_notes:
        new_note = note + n * 12
        if len(chord_notes) != 0:
            while new_note <= chord_notes[-1]:
                new_note += 12
        chord_notes.append(new_note)
    return chord_notes

def output(progression, notes, available_chords, idx_to_harmonize, midi_stream, midi_file_path):
    print(progression)
    new_stream = stream.Stream()

    note_count = 0
    score = midi_stream.flatten().notes
    for i in range(len(score)):
        element = score[i]
        new_stream.insert(element.offset, element) # keep the original melody and rests
        if isinstance(element, note.Note):
            if note_count in idx_to_harmonize:
                # insert the corresponding chord into the new stream
                pos = idx_to_harmonize.index(note_count)
                degree = progression[pos]
                chord_notes = available_chords[degree-1]
                chord_notes = get_chord_notes(element.pitch.midi, degree, chord_notes)
                # duration
                if note_count == idx_to_harmonize[-1]: # last note
                    t = element.duration.quarterLength
                else:
                    next_chord_pos = idx_to_harmonize[pos+1]
                    next_chord = score[next_chord_pos]
                    t = next_chord.offset - element.offset
                dur = duration.Duration()
                dur.quarterLength = t

                new_chord = chord.Chord(chord_notes, duration=dur)
                new_stream.insert(element.offset, new_chord)
            note_count += 1
        else:
            print("Not a note")

    new_stream.write('midi', fp=midi_file_path)

if __name__ == '__main__':
    midi_file_path = sys.argv[1]
    notes, tonic, mode, time_signature, use_flats, beat_strength, midi_stream = get_info(midi_file_path)
    note_table =  NOTES_FLAT if use_flats else NOTES_SHARP
    progressions, available_chords, idx_to_harmonize = harmonize(notes, tonic, mode, beat_strength, note_table)
    progression = random.choice(progressions)
    output(progression, notes, available_chords, idx_to_harmonize, midi_stream, "test.mid")
