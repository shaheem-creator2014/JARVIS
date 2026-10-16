"""Deterministic, invented demo files; never touches personal folders."""
import random
from pathlib import Path

def generate(root):
    rng = random.Random(2014)
    samples = {
        'studies/revision.md': '# Grade 8 revision\nDEMONSTRATION DATA — not real progress.\nTopics: fractions, forces, ecosystems. Try short revision sessions with breaks.\nRelated: fractions.md, quiz.md, study-plan.md.',
        'studies/fractions.md': '# Fractions\nTo add fractions, use a common denominator. 1/2 + 1/4 = 3/4.\nRelated: revision.md and quiz.md.',
        'studies/quiz.md': '# Practice quiz\n1. What is 3/4 + 1/4?\n2. Explain friction.\nRelated: fractions.md, revision.md.',
        'studies/study-plan.md': '# Sample study plan\nNo invented deadlines. Review fractions, take a break, then explore a website project.\nRelated: revision.md.',
        'websites/portfolio/index.html': '<!doctype html><html lang="en"><title>Demo portfolio</title><link rel="stylesheet" href="styles.css"><h1>Sample website portfolio</h1><script src="app.js"></script></html>',
        'websites/portfolio/styles.css': '/* Demo portfolio: index.html */\nbody { font-family: system-ui; max-width: 60rem; margin: auto; padding: 2rem; }',
        'websites/portfolio/app.js': '// Sample portfolio interaction for index.html\nconsole.log("Demo portfolio ready");',
        'websites/ideas.md': '# Sample website ideas\nLocal tutoring landing page; robotics club showcase; accessible restaurant menu.\nRelated: proposal.md and portfolio/index.html.',
        'websites/proposal.md': '# Demonstration proposal\nAgree on pages, accessibility, delivery milestones and revisions before quoting.\nPrices require scope and current research. Related: ideas.md.',
        'robotics/robot.md': '# Sample robot project\nArduino, distance sensor, motor driver. Check component ratings and common ground.\nUse adult supervision for batteries and moving parts. Related: robot.ino, wiring.md.',
        'robotics/robot.ino': '// DEMO ONLY: robot.md and wiring.md\nvoid setup() { pinMode(13, OUTPUT); }\nvoid loop() { digitalWrite(13, HIGH); delay(1000); digitalWrite(13, LOW); delay(1000); }',
        'robotics/wiring.md': '# Wiring review\nNever connect a motor directly to a microcontroller output. Use a rated motor driver.\nRelated: robot.ino and robot.md. Hardware has not been physically tested.',
        'notes/project-journal.md': '# Demo journal\nExplore portfolio ideas.md and robot.md.\n' + '\n'.join(f'Sample experiment {i}: observation {rng.randrange(10,99)} (invented).' for i in range(5)),
    }
    # Extra invented documents give the demo graph a useful, connected shape.
    for i, topic in enumerate(('tutoring', 'robotics-club', 'cafe-menu', 'portfolio', 'book-club', 'science-fair', 'sports-club', 'art-gallery'), 1):
        base = f'websites/examples/{topic}'
        samples[f'{base}/{topic}.html'] = f'<!doctype html><html lang="en"><title>Demo {topic}</title><link rel="stylesheet" href="{topic}.css"><h1>Invented {topic} example</h1><script src="{topic}.js"></script></html><!-- Related: ideas.md and proposal.md -->'
        samples[f'{base}/{topic}.css'] = f'/* Demo {topic}.html. Related: styles.css */\nbody {{font-family:system-ui;padding:2rem;max-width:60rem;margin:auto;}}'
        samples[f'{base}/{topic}.js'] = f'// DEMONSTRATION ONLY: {topic}.html\nconsole.log("Sample {topic} page");'
        robot = f'example-{i}'
        samples[f'robotics/examples/{robot}.ino'] = f'// DEMONSTRATION ONLY. See {robot}-notes.md and robot.md.\nvoid setup() {{ pinMode(13, OUTPUT); }}\nvoid loop() {{ digitalWrite(13, HIGH); delay(500); digitalWrite(13, LOW); delay(500); }}'
        samples[f'robotics/examples/{robot}-notes.md'] = f'# Sample robotics experiment {i}\nInvented learning material: indicator LEDs and program timing. Related: {robot}.ino, robot.md and wiring.md. Check component ratings; hardware has not been physically tested.'
    for topic in ('forces', 'energy', 'ecosystems', 'geometry', 'electricity', 'plants', 'measurement', 'programming'):
        samples[f'studies/topics/{topic}.md'] = f'# Sample {topic} revision\nInvented study document, not a record of real school progress. List what you know, explain one example, and try two practice questions. Related: revision.md and quiz.md.'
    for i in range(1, 5):
        samples[f'robotics/examples/sensor-{i}.py'] = f'# DEMONSTRATION ONLY. Related: example-{i}-notes.md and robot.md\n# No hardware connection is configured.\nprint("Sample sensor reading: {rng.randrange(10, 90)} — invented")'
    root = Path(root)
    for name, content in samples.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding='utf-8')
    return len(samples)

if __name__ == '__main__':
    print(generate(Path(__file__).resolve().parent / 'demo'))
