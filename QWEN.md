# IndexTTS2 Project Context

## Project Overview

IndexTTS2 is a breakthrough in emotionally expressive and duration-controlled auto-regressive zero-shot text-to-speech (TTS) system developed by the Bilibili IndexTTS Team. The project introduces a novel method for speech duration control in autoregressive TTS models, supporting both controllable and uncontrollable generation modes. It achieves disentanglement between emotional expression and speaker identity, enabling independent control over timbre and emotion.

### Key Features
- **Duration Control**: First autoregressive TTS model with precise synthesis duration control
- **Emotion Control**: Supports multiple emotion control methods including reference audio, emotion vectors, and text-based emotion descriptions
- **Voice Cloning**: Zero-shot voice cloning capability using reference audio
- **Multilingual Support**: Works with Chinese and English text
- **High Naturalness**: Achieves state-of-the-art results in word error rate, speaker similarity, and emotional fidelity

## Architecture and Components

The system consists of several key components:
- **GPT-based Autoregressive Model**: For text-to-semantic token generation
- **Semantic Codec**: For converting semantic representations to acoustic features
- **S2Mel Module**: For speech-to-mel conversion with duration modeling
- **BigVGAN Vocoder**: For high-quality audio synthesis
- **Emotion Control System**: Using Qwen3-based emotion detection and control
- **Voice Encoder**: Using CAMPPlus for speaker embedding extraction

## Project Structure

```
/Volumes/SSD/workspaces/index-tts/
├── app.py                 # Tkinter GUI application
├── webui.py              # Gradio web interface
├── pyproject.toml        # Project dependencies and configuration
├── README.md             # Main project documentation
├── indextts/             # Main TTS module
│   ├── infer_v2.py       # IndexTTS2 main inference class
│   ├── infer.py          # Legacy IndexTTS1 inference class
│   ├── gpt/              # GPT model implementation
│   ├── s2mel/            # Speech-to-mel conversion module
│   ├── BigVGAN/          # BigVGAN vocoder implementation
│   └── utils/            # Utility functions
├── checkpoints/          # Model weights and configuration files
├── examples/             # Example audio files and test cases
├── tools/                # Utility scripts
├── assets/               # Project assets and images
└── archive/              # Legacy project versions
```

## Building and Running

### Environment Setup
1. Ensure Git and Git-LFS are installed:
```bash
git lfs install
```

2. Clone the repository:
```bash
git clone https://github.com/index-tts/index-tts.git && cd index-tts
git lfs pull
```

3. Install the `uv` package manager:
```bash
pip install -U uv
```

4. Install dependencies:
```bash
uv sync --all-extras
```

5. Download required models:
```bash
uv tool install "huggingface-hub[cli,hf_xet]"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints
```

### Running the System

#### Web Interface
```bash
uv run webui.py
```
Then open http://127.0.0.1:7860 in your browser.

#### Command Line Usage
```bash
# Basic usage
from indextts.infer_v2 import IndexTTS2
tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints", use_fp16=False)
text = "Translate for me, what is a surprise!"
tts.infer(spk_audio_prompt='examples/voice_01.wav', text=text, output_path="gen.wav", verbose=True)
```

#### GUI Application
```bash
uv run app.py
```

### Available Options

The system supports multiple emotion control methods:
1. **Same as speaker**: Use the same emotion as the voice reference audio
2. **Emotion reference audio**: Use a separate audio file to control emotion
3. **Emotion vector control**: Specify emotion intensity via 8-dimensional vector [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
4. **Emotion text control**: Use text description to guide emotion synthesis

## Development Conventions

### Dependencies Management
- Uses `uv` for dependency management (required)
- Dependencies are defined in `pyproject.toml`
- Supports optional extras: `webui` and `deepspeed`

### Code Structure
- Main inference logic in `indextts/infer_v2.py`
- Model implementations in respective submodules
- Configuration managed via OmegaConf with YAML files
- Internationalization support for Chinese/English

### GPU Support
- Supports CUDA, AMD ROCm, Intel XPU, and Apple MPS
- FP16 inference available for reduced VRAM usage
- DeepSpeed support for acceleration (optional)

## Testing and Validation

The project includes:
- Example test cases in `examples/cases.jsonl`
- GUI application for manual testing
- Web interface with comprehensive controls
- Performance metrics including RTF (Real-Time Factor) reporting

## Key Files and Functions

### indextts/infer_v2.py
- `IndexTTS2` class: Main inference interface
- `infer()` method: Primary synthesis function
- `normalize_emo_vec()`: Emotion vector normalization
- `QwenEmotion` class: Text-based emotion analysis

### Configuration
- `checkpoints/config.yaml`: Main model configuration
- `checkpoints/bpe.model`: BPE tokenization model
- `checkpoints/glossary.yaml`: Custom term pronunciation

## Performance Notes

- Uses multiple stages of processing for high-quality synthesis
- Supports chunked text processing for long-form content
- Includes various optimization techniques (FP16, CUDA kernels, torch.compile)
- Reports detailed timing information for each processing stage
- RTF (Real-Time Factor) metrics for performance evaluation