# Model weights

Model binaries are **not** committed to this repository — they exceed
GitHub's 100 MB per-file limit (`faster-whisper-large-v3/model.bin` alone
is ~2.9 GB). Download them into this directory before running the pipeline.

Expected layout (matches the defaults in `.env`):

```
models/
├── en_US-lessac-medium.onnx          # Piper TTS - English
├── en_US-lessac-medium.onnx.json
├── te_IN-maya-medium.onnx            # Piper TTS - Telugu
├── te_IN-maya-medium.onnx.json
└── faster-whisper-large-v3/          # STT
    ├── model.bin                     # ~2.9 GB - must be downloaded
    ├── config.json
    ├── tokenizer.json
    ├── vocabulary.json
    ├── preprocessor_config.json
    └── README.md
```

## Sources

| Model | Source |
|---|---|
| Piper voices (`en_US-lessac-medium`, `te_IN-maya-medium`) | [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) |
| `faster-whisper-large-v3` | [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) |

## Verifying

```bash
# After downloading, these should all exist:
ls models/*.onnx models/*.onnx.json
ls models/faster-whisper-large-v3/model.bin
```

If a path differs, override it in `.env` via `PIPER_EN_MODEL_PATH`,
`PIPER_TE_MODEL_PATH`, or `WHISPER_MODEL_PATH`.
