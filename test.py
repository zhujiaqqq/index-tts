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

	text = "你好,欢迎使用IndexTTS。这是一个测试文本，用于演示如何将长文本拆分成较小的块，以便进行语音合成处理。希望你喜欢这个示例！"

	try:
		from indextts.infer_v2 import IndexTTS2
		tts = IndexTTS2(cfg_path='checkpoints/config.yaml', model_dir='checkpoints', use_fp16=False, use_cuda_kernel=False, use_deepspeed=False)
	except Exception as e:
		print('Failed to initialize IndexTTS2:', e)
		sys.exit(1)

	out_dir = Path('tts_outputs')
	out_dir.mkdir(exist_ok=True)
	out_path = out_dir / 'output.wav'
	tts.infer(spk_audio_prompt='voices/ssr.WAV', text=text, output_path=str(out_path), verbose=True)

if __name__ == '__main__':
	main()


