"""Task runner: read ./task/taskfile.yaml and synthesize the story.

Expected taskfile format (YAML):

story:
  path: path/to/story.txt
  voice: path/to/voice.wav
  title: My Story Title

Behavior:
- Read the YAML task file
- Read story text from `story.path`
- Chunk text using `make_chunks` logic
- Use `indextts.infer_v2.IndexTTS2` to synthesize each chunk with `story.voice`
- Concatenate chunk WAVs into `./task/{sanitized_title}.wav`
"""

from pathlib import Path
import re
import os
import sys
import tempfile
import shutil
import wave
import traceback
import subprocess
import importlib.util

try:
	import yaml
except Exception:
	yaml = None


def make_chunks(raw_text, min_chars=50, max_chars=100):
	text = raw_text.replace('\n', ' ').strip()
	if not text:
		return []
	sentences = [s.strip() for s in re.split(r'(?<=[。．.!?！？])\s*', text) if s.strip()]
	chunks = []
	cur = ''
	for s in sentences:
		s = s.strip()
		if not cur:
			if len(s) >= min_chars and len(s) <= max_chars:
				chunks.append(s)
				cur = ''
			elif len(s) > max_chars:
				for i in range(0, len(s), max_chars):
					chunks.append(s[i:i+max_chars])
				cur = ''
			else:
				cur = s
		else:
			candidate = cur + ' ' + s
			if len(candidate) <= max_chars:
				cur = candidate
				if len(cur) >= min_chars:
					chunks.append(cur.strip())
					cur = ''
			else:
				if len(cur) >= min_chars:
					chunks.append(cur.strip())
					cur = ''
					if len(s) > max_chars:
						for i in range(0, len(s), max_chars):
							chunks.append(s[i:i+max_chars])
					elif len(s) >= min_chars:
						chunks.append(s)
					else:
						cur = s
				else:
					chunks.append(cur.strip())
					cur = ''
					if len(s) > max_chars:
						for i in range(0, len(s), max_chars):
							chunks.append(s[i:i+max_chars])
					elif len(s) >= min_chars:
						chunks.append(s)
					else:
						cur = s
	if cur:
		chunks.append(cur.strip())
	return chunks


def sanitize_filename(name: str) -> str:
	name = name.strip()
	name = re.sub(r'[\\/:*?"<>|]+', '', name)
	name = re.sub(r'\s+', '_', name)
	if not name:
		name = 'story'
	return name


def concatenate_wavs(wav_paths, out_path):
	if not wav_paths:
		raise ValueError('No wavs to concatenate')
	params = None
	with wave.open(wav_paths[0], 'rb') as w0:
		params = w0.getparams()

	with wave.open(out_path, 'wb') as outw:
		outw.setparams(params)
		for p in wav_paths:
			with wave.open(p, 'rb') as r:
				if r.getnchannels() != params.nchannels or r.getsampwidth() != params.sampwidth or r.getframerate() != params.framerate:
					raise RuntimeError(f'Incompatible WAV params for {p}')
				frames = r.readframes(r.getnframes())
				outw.writeframes(frames)


def run_task(taskfile_path='./task/taskfile.yaml'):
	taskfile = Path(taskfile_path)
	if not taskfile.exists():
		print(f'Task file not found: {taskfile}', file=sys.stderr)
		return 1

	if yaml is None:
		print('PyYAML is required (pip install pyyaml)', file=sys.stderr)
		return 1

	try:
		data = yaml.safe_load(taskfile.read_text(encoding='utf-8'))
	except Exception as e:
		print('Failed to parse YAML:', e, file=sys.stderr)
		return 1

	story = data.get('story') if isinstance(data, dict) else None
	if not story:
		print('Missing `story` section in taskfile', file=sys.stderr)
		return 1

	story_path = story.get('path')
	story_voice = story.get('voice')
	story_title = story.get('title') or 'story'

	if not story_path:
		print('story.path is required in taskfile', file=sys.stderr)
		return 1
	if not story_voice:
		print('story.voice is required in taskfile', file=sys.stderr)
		return 1

	sp = Path(story_path)
	if not sp.exists():
		print(f'Story text file not found: {sp}', file=sys.stderr)
		return 1

	raw = sp.read_text(encoding='utf-8')
	chunks = make_chunks(raw, min_chars=50, max_chars=100)
	if not chunks:
		print('No text chunks produced; aborting', file=sys.stderr)
		return 1

	print(f'Preparing to synthesize {len(chunks)} chunks...')

	try:
		from indextts.infer_v2 import IndexTTS2
		print('Initializing IndexTTS2...')
		tts = IndexTTS2(cfg_path='checkpoints/config.yaml', model_dir='checkpoints', use_fp16=False, use_cuda_kernel=False, use_deepspeed=False)
	except Exception as e:
		print('Failed to initialize IndexTTS2:', e, file=sys.stderr)
		traceback.print_exc()
		return 1

	task_dir = Path('task')
	task_dir.mkdir(parents=True, exist_ok=True)
	tmpdir = Path(tempfile.mkdtemp(prefix='indextts_task_', dir=str(task_dir)))
	tmp_files = []
	try:
		for i, chunk in enumerate(chunks, start=1):
			out_path = tmpdir / f'chunk_{i:03d}.wav'
			print(f'Generating chunk {i}/{len(chunks)} — preview: {chunk[:60]}')
			try:
				tts.infer(spk_audio_prompt=story_voice, text=chunk, output_path=str(out_path), verbose=False)
				tmp_files.append(str(out_path))
			except Exception as e:
				print(f'Error generating chunk {i}:', e, file=sys.stderr)
				traceback.print_exc()

		if not tmp_files:
			print('No chunk files were produced; aborting', file=sys.stderr)
			return 1

		out_dir = task_dir
		final_name = sanitize_filename(story_title) + '.wav'
		final_path = out_dir / final_name
		print(f'Concatenating {len(tmp_files)} wavs into {final_path}')
		concatenate_wavs(tmp_files, str(final_path))
		print('Done — wrote', final_path)

		# send the final audio via email using task/sendEmail.py (script contains sender creds)
		recipient = '1027158353@qq.com'
		send_script = Path('task/sendEmail.py')
		if send_script.exists():
			cmd = [sys.executable, str(send_script), recipient, '--file', str(final_path), '--subject', f'Generated audio: {final_name}', '--body', f'Please find attached {final_name}']
			print('Invoking email script to send', final_path, 'to', recipient)
			try:
				res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
				if res.returncode == 0:
					print('Email script completed successfully')
				else:
					print('Email script exited with code', res.returncode, file=sys.stderr)
					if res.stdout:
						print(res.stdout)
					if res.stderr:
						print(res.stderr, file=sys.stderr)
			except Exception as e:
				print('Failed to run email script:', e, file=sys.stderr)
		else:
			print('sendEmail.py not found in task/ — skipping email')
		return 0
	finally:
		try:
			shutil.rmtree(tmpdir)
		except Exception:
			pass


def main():
	rc = run_task()
	sys.exit(rc)


if __name__ == '__main__':
	main()
