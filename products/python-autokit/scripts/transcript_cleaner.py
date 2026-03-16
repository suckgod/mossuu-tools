#!/usr/bin/env python3
"""
Transcript Cleaner - Clean subtitles and transcripts

Clean up subtitle files (SRT, VTT, ASS) and text transcripts:
- Remove filler words (um, uh, like, you know, etc.)
- Remove stutters and repetitions
- Merge fragmented sentences
- Remove non-speech markers (applause, laughter, music)
- Standardize speaker labels
- Extract pure text or cleaned subtitles
- Support batch processing

Usage:
    python transcript_cleaner.py subtitles.srt -o cleaned.srt
    python transcript_cleaner.py transcript.txt --filler-words-filler.txt --output cleaned.txt
    python transcript_cleaner.py *.vtt --mode text
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional, Set, Dict

__version__ = "1.0.0"

class SubtitleEntry:
    """Represents a single subtitle entry"""
    def __init__(self, index: int, start: str, end: str, speaker: str, text: str, raw: str = ''):
        self.index = index
        self.start = start
        self.end = end
        self.speaker = speaker
        self.text = text
        self.raw = raw

    def __repr__(self):
        return f"SubtitleEntry(index={self.index}, start={self.start}, end={self.end}, speaker={self.speaker!r}, text={self.text[:30]!r}...)"

class TranscriptCleaner:
    def __init__(self,
                 filler_words: Set[str] = None,
                 remove_applause: bool = True,
                 remove_laughter: bool = True,
                 remove_music: bool = True,
                 remove_non_speech: bool = True,
                 merge_threshold: float = 1.0,  # seconds
                 speaker_mapping: Dict[str, str] = None,
                 min_words: int = 1,
                 output_format: str = 'auto'):
        self.filler_words = filler_words or set()
        self.remove_applause = remove_applause
        self.remove_laughter = remove_laughter
        self.remove_music = remove_music
        self.remove_non_speech = remove_non_speech
        self.merge_threshold = merge_threshold
        self.speaker_mapping = speaker_mapping or {}
        self.min_words = min_words
        self.output_format = output_format

        # Default filler words (English + Chinese)
        default_fillers = {
            'um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean',
            '嗯', '呃', '那个', '这个', '就是说', ' basically', 'actually'
        }
        if not self.filler_words:
            self.filler_words = default_fillers

    def time_to_seconds(self, time_str: str) -> float:
        """Convert SRT/VTT timecode to seconds"""
        # Formats: 00:00:00,000 or 00:00:00.000 or 00:00:00
        match = re.match(r'(\d{2}):(\d{2}):(\d{2})[,.]?(\d{3})?', time_str)
        if match:
            h, m, s, ms = match.groups()
            return int(h) * 3600 + int(m) * 60 + int(s) + (int(ms) if ms else 0) / 1000.0
        return 0.0

    def seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to SRT timecode"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def normalize_speaker(self, speaker: str) -> str:
        """Normalize speaker label"""
        speaker = speaker.strip()
        # Apply mapping
        for pattern, replacement in self.speaker_mapping.items():
            if re.match(pattern, speaker, re.IGNORECASE):
                return replacement
        return speaker or 'SPEAKER'

    def clean_text(self, text: str) -> str:
        """Clean text content"""
        original = text

        # Remove non-speech markers
        if self.remove_applause:
            text = re.sub(r'\[applause\]|\(applause\)|\*applause\*', '', text, flags=re.IGNORECASE)
        if self.remove_laughter:
            text = re.sub(r'\[laughter\]|\(laughter\)|\*laughter\*', '', text, flags=re.IGNORECASE)
        if self.remove_music:
            text = re.sub(r'\[music\]|\(music\)|\*music\*', '', text, flags=re.IGNORECASE)
        if self.remove_non_speech:
            text = re.sub(r'\[.*?\]|\(.*?\)|\*.*?\*', '', text)  # Remove all bracketed annotations

        # Remove filler words (whole word matches)
        for filler in self.filler_words:
            pattern = r'\b' + re.escape(filler) + r'\b'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove if too short
        if len(text.split()) < self.min_words:
            return ''

        return text

    def parse_srt(self, content: str) -> List[SubtitleEntry]:
        """Parse SRT format"""
        entries = []
        blocks = re.split(r'\n\s*\n', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            # Index
            try:
                index = int(lines[0].strip())
            except:
                index = len(entries) + 1

            # Timecodes
            time_line = lines[1]
            time_match = re.match(r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})', time_line)
            if not time_match:
                continue
            start, end = time_match.groups()

            # Text (may include speaker: Text format)
            text_lines = lines[2:]
            text = ' '.join(text_lines).strip()

            # Extract speaker if present
            speaker = ''
            speaker_match = re.match(r'^([A-Za-z0-9_]+):\s*(.+)', text)
            if speaker_match:
                speaker = speaker_match.group(1)
                text = speaker_match.group(2)

            entry = SubtitleEntry(
                index=index,
                start=start,
                end=end,
                speaker=speaker,
                text=text,
                raw=block
            )
            entries.append(entry)

        return entries

    def parse_vtt(self, content: str) -> List[SubtitleEntry]:
        """Parse VTT format"""
        entries = []
        lines = content.split('\n')

        # Skip WEBVTT header
        i = 0
        while i < len(lines) and not re.match(r'\d{2}:\d{2}:\d{2}', lines[i]):
            i += 1

        current_entry = None
        for line_idx in range(i, len(lines)):
            line = lines[line_idx].strip()

            # Timestamp line
            time_match = re.match(r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})', line)
            if time_match:
                if current_entry:
                    entries.append(current_entry)
                start, end = time_match.groups()
                current_entry = SubtitleEntry(
                    index=len(entries) + 1,
                    start=start,
                    end=end,
                    speaker='',
                    text='',
                    raw=''
                )
            elif line and current_entry:
                # Text line, may include speaker
                if not current_entry.text:
                    speaker_match = re.match(r'<v (\S+)>(.+)', line)
                    if speaker_match:
                        current_entry.speaker = speaker_match.group(1)
                        current_entry.text = speaker_match.group(2)
                    else:
                        current_entry.text = line
                else:
                    current_entry.text += ' ' + line

        if current_entry:
            entries.append(current_entry)

        return entries

    def parse_txt(self, content: str) -> List[SubtitleEntry]:
        """Parse plain text transcript (line-based, optional speaker: format)"""
        entries = []
        lines = content.split('\n')

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            speaker = ''
            text = line
            speaker_match = re.match(r'^([A-Za-z0-9_]+):\s*(.+)', line)
            if speaker_match:
                speaker = speaker_match.group(1)
                text = speaker_match.group(2)

            entry = SubtitleEntry(
                index=idx + 1,
                start=str(idx),
                end=str(idx + 1),
                speaker=speaker,
                text=text,
                raw=line
            )
            entries.append(entry)

        return entries

    def merge_entries(self, entries: List[SubtitleEntry]) -> List[SubtitleEntry]:
        """Merge nearby entries (within threshold)"""
        if self.merge_threshold <= 0:
            return entries

        merged = []
        i = 0
        while i < len(entries):
            current = entries[i]
            j = i + 1

            while j < len(entries):
                next_entry = entries[j]
                # Check if same speaker and within time threshold
                if (current.speaker == next_entry.speaker or not current.speaker or not next_entry.speaker):
                    gap = self.time_to_seconds(next_entry.start) - self.time_to_seconds(current.end)
                    if gap <= self.merge_threshold:
                        # Merge
                        current.text += ' ' + next_entry.text
                        current.end = next_entry.end
                        current.raw += '\n' + next_entry.raw
                        j += 1
                        continue
                break

            merged.append(current)
            i = j

        return merged

    def clean_entries(self, entries: List[SubtitleEntry]) -> List[SubtitleEntry]:
        """Apply cleaning transformations"""
        cleaned = []

        for entry in entries:
            # Clean text
            cleaned_text = self.clean_text(entry.text)
            if not cleaned_text:
                continue

            # Normalize speaker
            speaker = self.normalize_speaker(entry.speaker) if entry.speaker else ''

            entry.text = cleaned_text
            entry.speaker = speaker
            cleaned.append(entry)

        return cleaned

    def save_srt(self, entries: List[SubtitleEntry], output_path: Path):
        """Save entries as SRT"""
        lines = []
        for entry in entries:
            lines.append(str(entry.index))
            lines.append(f"{entry.start} --> {entry.end}")
            if entry.speaker:
                lines.append(f"{entry.speaker}: {entry.text}")
            else:
                lines.append(entry.text)
            lines.append('')

        output_path.write_text('\n'.join(lines), encoding='utf-8')

    def save_vtt(self, entries: List[SubtitleEntry], output_path: Path):
        """Save entries as VTT"""
        lines = ['WEBVTT', '']
        for entry in entries:
            lines.append(f"{entry.start} --> {entry.end}")
            if entry.speaker:
                lines.append(f"<v {entry.speaker}>{entry.text}")
            else:
                lines.append(entry.text)
            lines.append('')

        output_path.write_text('\n'.join(lines), encoding='utf-8')

    def save_txt(self, entries: List[SubtitleEntry], output_path: Path):
        """Save as plain text transcript (with speaker labels)"""
        lines = []
        for entry in entries:
            if entry.speaker:
                lines.append(f"{entry.speaker}: {entry.text}")
            else:
                lines.append(entry.text)

        output_path.write_text('\n'.join(lines), encoding='utf-8')

    def save(self, entries: List[SubtitleEntry], output_path: Path):
        """Save cleaned transcript in appropriate format"""
        fmt = self.output_format
        if fmt == 'auto':
            suffix = output_path.suffix.lower()
            if suffix == '.srt':
                fmt = 'srt'
            elif suffix == '.vtt':
                fmt = 'vtt'
            else:
                fmt = 'txt'

        if fmt == 'srt':
            self.save_srt(entries, output_path)
        elif fmt == 'vtt':
            self.save_vtt(entries, output_path)
        else:
            self.save_txt(entries, output_path)

        print(f"✓ Saved: {output_path} ({len(entries)} entries)")

    def process_file(self, input_path: Path, output_path: Path = None):
        """Process single transcript file"""
        print(f"\nProcessing: {input_path.name}")

        if not output_path:
            output_path = input_path.with_name(f"{input_path.stem}_cleaned{input_path.suffix}")

        # Read
        content = input_path.read_text(encoding='utf-8', errors='ignore')

        # Parse based on format
        suffix = input_path.suffix.lower()
        if suffix == '.srt':
            entries = self.parse_srt(content)
        elif suffix == '.vtt':
            entries = self.parse_vtt(content)
        else:
            entries = self.parse_txt(content)

        print(f"  Parsed: {len(entries)} entries")

        # Clean
        entries = self.clean_entries(entries)
        print(f"  After cleaning: {len(entries)} entries")

        # Merge
        entries = self.merge_entries(entries)
        print(f"  After merge: {len(entries)} entries")

        # Save
        self.save(entries, output_path)

        return len(entries)

def main():
    parser = argparse.ArgumentParser(
        description="Transcript Cleaner - Clean subtitles and transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean SRT file (default settings)
  %(prog)s subtitles.srt -o cleaned.srt

  # Custom filler words list
  %(prog)s interview.txt --filler-words-filler.txt --output clean.txt

  # Merge fragmented subtitles (within 0.5s) and output as plain text
  %(prog)s video.vtt --merge 0.5 --format text -o transcript.txt

  # Batch process all vtt files
  %(prog)s *.vtt --output-dir cleaned/

  # Disable specific filters
  %(prog)s comedy.srt --no-applause --no-laughter

  # Map speaker labels (normalize)
  %(prog)s panel.vtt --speaker-map "SPEAKER 1:Host" --speaker-map "SPEAKER 2:Guest"

Features:
  - Filler word removal (um, uh, etc.)
  - Remove [applause], [laughter], [music] markers
  - Speaker label normalization/mapping
  - Merge short-gap subtitles (configurable threshold)
  - Supports SRT, VTT, and plain text formats
  - Preserves timecodes for SRT/VTT outputs
      """
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Input transcript/subtitle files"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file (single file mode) or specify output-dir for batch"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for batch processing"
    )
    parser.add_argument(
        "--format",
        choices=['auto', 'srt', 'vtt', 'txt'],
        default='auto',
        help="Output format (default: auto-detect from extension)"
    )
    parser.add_argument(
        "--filler-words",
        help="File with one filler word per line"
    )
    parser.add_argument(
        "--no-applause",
        action="store_false",
        dest='remove_applause',
        help="Don't remove [applause] markers"
    )
    parser.add_argument(
        "--no-laughter",
        action="store_false",
        dest='remove_laughter',
        help="Don't remove [laughter] markers"
    )
    parser.add_argument(
        "--no-music",
        action="store_false",
        dest='remove_music',
        help="Don't remove [music] markers"
    )
    parser.add_argument(
        "--merge",
        type=float,
        default=1.0,
        help="Merge entries within N seconds (default: 1.0, 0 to disable)"
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=1,
        help="Minimum words to keep entry (default: 1)"
    )
    parser.add_argument(
        "--speaker-map",
        action='append',
        help="Map speaker pattern to normalized name: 'PATTERN:NAME' (e.g., 'SPEAKER 1:Host')"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"transcript_cleaner {__version__}"
    )

    parser.set_defaults(remove_applause=True, remove_laughter=True, remove_music=True)

    args = parser.parse_args()

    # Load filler words
    filler_words = set()
    if args.filler_words:
        fw_path = Path(args.filler_words)
        if fw_path.exists():
            filler_words = set(line.strip() for line in fw_path.read_text().splitlines() if line.strip())
    else:
        filler_words = None  # Use defaults

    # Build speaker mapping
    speaker_mapping = {}
    if args.speaker_map:
        for mapping in args.speaker_map:
            if ':' in mapping:
                pattern, name = mapping.split(':', 1)
                speaker_mapping[pattern.strip()] = name.strip()

    # Create cleaner instance
    cleaner = TranscriptCleaner(
        filler_words=filler_words,
        remove_applause=args.remove_applause,
        remove_laughter=args.remove_laughter,
        remove_music=args.remove_music,
        merge_threshold=args.merge,
        speaker_mapping=speaker_mapping,
        min_words=args.min_words,
        output_format=args.format
    )

    try:
        # Process files
        files_processed = 0
        total_entries_before = 0
        total_entries_after = 0

        for file_pattern in args.files:
            filepath = Path(file_pattern)
            if not filepath.exists():
                print(f"File not found: {filepath}", file=sys.stderr)
                continue

            # Determine output path
            output_path = None
            if args.output and len(args.files) == 1:
                output_path = Path(args.output)
            elif args.output_dir:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{filepath.stem}_cleaned{filepath.suffix}"
            else:
                output_path = filepath.with_name(f"{filepath.stem}_cleaned{filepath.suffix}")

            entries_remaining = cleaner.process_file(filepath, output_path)
            files_processed += 1
            total_entries_after += entries_remaining

        print(f"\n✓ Processed {files_processed} file(s)")
        if total_entries_before > 0:
            reduction = total_entries_before - total_entries_after
            print(f"  Total entries: {total_entries_after} (removed {reduction})")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
