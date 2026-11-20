# AIRLOCK synthetic test pack (audio + video)

All content is synthetic. Every "sensitive" value is fake or a published test value:
- AWS keys: AKIAIOSFODNN7EXAMPLE / wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY (Amazon documentation examples)
- Cards: 4111 1111 1111 1111, 4242 4242 4242 4242 (standard payment test cards)
- SSN: 987-65-4321 (range reserved for advertising)
- Phones: 555-01xx (reserved for fiction); emails: @example.com (reserved domain)
- Names, passwords and tokens are made up.

Voices are synthetic (flite text-to-speech), so transcription will be easier than real speech.
Label results from these files as "synthetic voice" on slides.
Keyboard clicks, beeps and background noise are also synthetic.

Contents
- audio/: 10 WAV files (16 kHz mono), 8 with sensitive info, 2 clean controls
- video/: 6 MP4 files (1280x720, ~10 s), 5 with sensitive info, 1 clean control; v06 has a narration track
- answer_key.csv: file, question, expected answer, sensitive items, when they appear, sounds present

Keep this folder out of the public GitHub repo (add test_media/ to .gitignore).
