#!/usr/bin/env python3
import sys
import re
from pathlib import Path

def chunk_text(text, max_chars=50):
	# Split by period-like punctuation (Chinese 。, fullwidth ．, ASCII .)
	sentences = [s.strip() for s in re.split(r'(?<=[。．.])\s*', text) if s.strip()]
	chunks = []
	cur = ''
	for s in sentences:
		if not cur:
			if len(s) <= max_chars:
				cur = s
			else:
				# sentence itself too long -> hard-split into max-sized pieces
				for i in range(0, len(s), max_chars):
					chunks.append(s[i:i+max_chars])
				cur = ''
		else:
			if len(cur) + len(s) <= max_chars:
				cur = cur + s
			else:
				chunks.append(cur)
				if len(s) <= max_chars:
					cur = s
				else:
					for i in range(0, len(s), max_chars):
						chunks.append(s[i:i+max_chars])
					cur = ''
	if cur:
		chunks.append(cur)
	return chunks

def main():
	if len(sys.argv) < 2:
		print('Usage: python test.py <text_file>')
		sys.exit(1)
	txt_path = Path(sys.argv[1])
	if not txt_path.exists():
		print('File not found:', txt_path)
		sys.exit(1)
	text = txt_path.read_text(encoding='utf-8')
	# remove internal newlines to let punctuation-based splitting work
	text = text.replace('\n', '').strip()
	chunks = chunk_text(text, max_chars=50)

	try:
		from indextts.infer_v2 import IndexTTS2
		tts = IndexTTS2(cfg_path='checkpoints/config.yaml', model_dir='checkpoints', use_fp16=False, use_cuda_kernel=False, use_deepspeed=False)
	except Exception as e:
		print('Failed to initialize IndexTTS2:', e)
		sys.exit(1)

	out_dir = Path('tts_outputs')
	out_dir.mkdir(exist_ok=True)
	for i, chunk in enumerate(chunks, start=1):
		out_path = out_dir / f'gen_{i:03d}.wav'
		preview = chunk[:40] + ('...' if len(chunk) > 40 else '')
		print(f'Generating {out_path} — "{preview}"')
		tts.infer(spk_audio_prompt='examples/voice_03.wav', text=chunk, output_path=str(out_path), verbose=True)

	print(f'Done — wrote {len(chunks)} files to {out_dir}')

if __name__ == '__main__':
	main()


