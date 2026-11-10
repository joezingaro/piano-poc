"""Write the starter songs as MusicXML into ../songs/ (plus songs/index.json).

Songs are public-domain melodies typed in here. A note is "E4", "F#4", "Bb3";
a chord is a list of notes; "r" is a rest. Durations are in quarter notes.
Run:  python tools/make_songs.py
"""
import json, os, re
from xml.sax.saxutils import escape

DIV = 4  # divisions per quarter
TYPES = {0.25: ('16th', 0), 0.5: ('eighth', 0), 0.75: ('eighth', 1), 1: ('quarter', 0),
         1.5: ('quarter', 1), 2: ('half', 0), 3: ('half', 1), 4: ('whole', 0)}


def pitch_xml(n):
    m = re.fullmatch(r'([A-G])([#b]?)(\d)', n)
    step, acc, octv = m.groups()
    alter = {'#': 1, 'b': -1}.get(acc)
    a = f'<alter>{alter}</alter>' if alter else ''
    return f'<pitch><step>{step}</step>{a}<octave>{octv}</octave></pitch>'


def notes_xml(events, staff, voice):
    """events: (notes, dur, fingers) with optional 4th item 'tie' (tie to next)."""
    out = []
    for ev in events:
        n, dur = ev[0], ev[1]
        fingers = ev[2] if len(ev) > 2 else None
        tie = len(ev) > 3 and ev[3]
        typ, dots = TYPES[dur]
        d = int(dur * DIV)
        if n == 'r':
            out.append(f'<note><rest/><duration>{d}</duration><voice>{voice}</voice>'
                       f'<type>{typ}</type>{"<dot/>" * dots}<staff>{staff}</staff></note>')
            continue
        chord = n if isinstance(n, list) else [n]
        fl = fingers if isinstance(fingers, list) else ([fingers] * len(chord) if fingers else [None] * len(chord))
        for k, p in enumerate(chord):
            tie_xml = ''
            nota = []
            if fl[k]:
                nota.append(f'<technical><fingering>{fl[k]}</fingering></technical>')
            if tie in ('start', 'both'):
                tie_xml += '<tie type="start"/>'; nota.append('<tied type="start"/>')
            if tie in ('stop', 'both'):
                tie_xml = '<tie type="stop"/>' + tie_xml; nota.insert(0, '<tied type="stop"/>')
            out.append('<note>' + ('<chord/>' if k else '') + pitch_xml(p) +
                       f'<duration>{d}</duration>{tie_xml}<voice>{voice}</voice><type>{typ}</type>' +
                       '<dot/>' * dots + f'<staff>{staff}</staff>' +
                       (f'<notations>{"".join(nota)}</notations>' if nota else '') + '</note>')
    return ''.join(out)


def split_bars(events, beats):
    bars, cur, t = [], [], 0
    for ev in events:
        cur.append(ev); t += ev[1]
        if abs(t - beats) < 1e-6:
            bars.append(cur); cur, t = [], 0
        elif t > beats:
            raise ValueError(f'event crosses a barline: {ev}')
    if cur:
        raise ValueError('last bar incomplete')
    return bars


def song_xml(title, composer, rh, lh=None, beats=4, fifths=0, tempo=90):
    rb = split_bars(rh, beats)
    lb = split_bars(lh, beats) if lh else None
    if lb and len(lb) != len(rb):
        raise ValueError(f'{title}: hands have {len(rb)} vs {len(lb)} bars')
    staves = 2 if lh else 1
    bars = []
    for i, r in enumerate(rb):
        attrs = ''
        if i == 0:
            clefs = '<clef number="1"><sign>G</sign><line>2</line></clef>'
            if lh:
                clefs += '<clef number="2"><sign>F</sign><line>4</line></clef>'
            attrs = (f'<attributes><divisions>{DIV}</divisions><key><fifths>{fifths}</fifths></key>'
                     f'<time><beats>{beats}</beats><beat-type>4</beat-type></time>'
                     f'<staves>{staves}</staves>{clefs}</attributes>'
                     f'<direction placement="above"><direction-type><metronome><beat-unit>quarter</beat-unit>'
                     f'<per-minute>{tempo}</per-minute></metronome></direction-type><sound tempo="{tempo}"/></direction>')
        body = notes_xml(r, 1, 1)
        if lh:
            body += f'<backup><duration>{beats * DIV}</duration></backup>' + notes_xml(lb[i], 2, 5)
        bars.append(f'<measure number="{i + 1}">{attrs}{body}</measure>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" '
            '"http://www.musicxml.org/dtds/partwise.dtd">\n'
            f'<score-partwise version="3.1"><work><work-title>{escape(title)}</work-title></work>'
            f'<identification><creator type="composer">{escape(composer)}</creator></identification>'
            '<part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list>'
            f'<part id="P1">{"".join(bars)}</part></score-partwise>\n')


# ---------------- songs ----------------
Q = 1
ode_a = [('E4', Q, 3), ('E4', Q, 3), ('F4', Q, 4), ('G4', Q, 5), ('G4', Q, 5), ('F4', Q, 4), ('E4', Q, 3), ('D4', Q, 2),
         ('C4', Q, 1), ('C4', Q, 1), ('D4', Q, 2), ('E4', Q, 3)]
ode_rh = (ode_a + [('E4', 1.5, 3), ('D4', .5, 2), ('D4', 2, 2)] +
          ode_a + [('D4', 1.5, 2), ('C4', .5, 1), ('C4', 2, 1)] +
          [('D4', Q, 2), ('D4', Q, 2), ('E4', Q, 3), ('C4', Q, 1),
           ('D4', Q, 2), ('E4', .5, 3), ('F4', .5, 4), ('E4', Q, 3), ('C4', Q, 1),
           ('D4', Q, 2), ('E4', .5, 3), ('F4', .5, 4), ('E4', Q, 3), ('D4', Q, 2),
           ('C4', Q, 1), ('D4', Q, 2), ('G3', 2, 1)] +
          ode_a + [('D4', 1.5, 2), ('C4', .5, 1), ('C4', 2, 1)])
ode_lh = [('C3', 4), ('G2', 4), ('C3', 4), ('C3', 2), ('G2', 2),
          ('C3', 4), ('G2', 4), ('C3', 4), ('G2', 2), ('C3', 2),
          ('G2', 4), ('C3', 2), ('G2', 2), ('C3', 2), ('G2', 2), ('C3', 2), ('G2', 2),
          ('C3', 4), ('G2', 4), ('C3', 4), ('G2', 2), ('C3', 2)]

C, F, G = ['C4', 'E4', 'G4'], ['C4', 'F4', 'A4'], ['B3', 'D4', 'G4']
chords_rh = [(C, 2, [1, 3, 5]), (F, 2, [1, 4, 5]), (G, 2, [1, 2, 5]), (C, 2, [1, 3, 5]),
             (C, 1, [1, 3, 5]), (F, 1, [1, 4, 5]), (G, 1, [1, 2, 5]), (C, 1, [1, 3, 5]),
             (C, 4, [1, 3, 5])]

tw1 = [('C4', Q, 1), ('C4', Q, 1), ('G4', Q, 5), ('G4', Q, 5), ('A4', Q, 5), ('A4', Q, 5), ('G4', 2, 5),
       ('F4', Q, 4), ('F4', Q, 4), ('E4', Q, 3), ('E4', Q, 3), ('D4', Q, 2), ('D4', Q, 2), ('C4', 2, 1)]
tw2 = [('G4', Q, 5), ('G4', Q, 5), ('F4', Q, 4), ('F4', Q, 4), ('E4', Q, 3), ('E4', Q, 3), ('D4', 2, 2)]
twinkle_rh = tw1 + tw2 + tw2 + tw1

E = .5
minuet_rh = [('D5', Q, 5), ('G4', E, 1), ('A4', E, 2), ('B4', E, 3), ('C5', E, 4),
             ('D5', Q, 5), ('G4', Q, 1), ('G4', Q, 1),
             ('E5', Q, 3), ('C5', E, 1), ('D5', E, 2), ('E5', E, 3), ('F#5', E, 4),
             ('G5', Q, 5), ('G4', Q, 1), ('G4', Q, 1),
             ('C5', Q, 4), ('D5', E, 5), ('C5', E, 4), ('B4', E, 3), ('A4', E, 2),
             ('B4', Q, 3), ('C5', E, 4), ('B4', E, 3), ('A4', E, 2), ('G4', E, 1),
             ('F#4', Q, 2), ('G4', E, 1), ('A4', E, 2), ('B4', E, 3), ('G4', E, 1),
             ('A4', 3, 2)]

SONGS = [
    ('ode-to-joy', 'Ode to Joy', 'L. van Beethoven', dict(rh=ode_rh, lh=ode_lh, tempo=96)),
    ('twinkle', 'Twinkle, Twinkle, Little Star', 'Traditional', dict(rh=twinkle_rh, tempo=100)),
    ('chord-check', 'Chord check: C, F, G, C', 'Exercise', dict(rh=chords_rh, tempo=72)),
    ('minuet-in-g', 'Minuet in G (first 8 bars)', 'C. Petzold', dict(rh=minuet_rh, beats=3, fifths=1, tempo=100)),
]

if __name__ == '__main__':
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'songs')
    os.makedirs(root, exist_ok=True)
    index = []
    for slug, title, composer, kw in SONGS:
        data = song_xml(title, composer, **kw).encode('utf-8')  # encode before opening
        with open(os.path.join(root, slug + '.musicxml'), 'wb') as f:
            f.write(data)
        index.append({'file': f'songs/{slug}.musicxml', 'title': title, 'composer': composer})
        print('wrote', slug, len(data), 'bytes')
    data = json.dumps(index, indent=2).encode('utf-8')
    with open(os.path.join(root, 'index.json'), 'wb') as f:
        f.write(data)
