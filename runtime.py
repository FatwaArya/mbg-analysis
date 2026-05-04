#!/usr/bin/env python3
"""
Runtime configuration shared across MBG pipeline scripts.
"""

import os
from dataclasses import dataclass

try:
    import torch
except ModuleNotFoundError:
    # FIX: allow non-ML utility scripts to import runtime without torch installed.
    class _CudaStub:
        @staticmethod
        def is_available() -> bool:
            return False

    class _TorchStub:
        cuda = _CudaStub()

    torch = _TorchStub()


@dataclass(frozen=True)
class RuntimeConfig:
    runtime_mode: str
    data_dir: str
    model_dir: str
    logs_dir: str
    device: str
    hf_device: int
    inference_batch_size: int
    sentiment_batch_size: int
    embedding_batch_size: int
    model_save_dir: str

    @property
    def processed_dir(self) -> str:
        return f"{self.data_dir}/processed"

    @property
    def output_dir(self) -> str:
        return f"{self.data_dir}/output"

    @property
    def raw_dir(self) -> str:
        return f"{self.data_dir}/raw"


def get_runtime_config() -> RuntimeConfig:
    mode = os.getenv("RUNTIME_MODE", "droplet").strip().lower()
    if mode not in {"droplet", "colab"}:
        raise ValueError("RUNTIME_MODE must be either 'droplet' or 'colab'")

    if mode == "colab":
        if not torch.cuda.is_available():
            # FIX: colab mode must force CUDA for heavy compute runs.
            raise RuntimeError("RUNTIME_MODE=colab requires CUDA, but no GPU was detected")
        data_dir = "/content/drive/MyDrive/mbg/data"
        model_dir = "/content/drive/MyDrive/mbg/model"
        logs_dir = "/content/drive/MyDrive/mbg/logs"
        device = "cuda"
        hf_device = 0
        inference_batch_size = 128
        sentiment_batch_size = 64
        embedding_batch_size = 128
    else:
        data_dir = "/opt/mbg/data"
        model_dir = "/opt/mbg/model"
        logs_dir = "/opt/mbg/logs"
        use_cuda = torch.cuda.is_available()
        # FIX: droplet mode auto-detects CUDA availability.
        device = "cuda" if use_cuda else "cpu"
        hf_device = 0 if use_cuda else -1
        inference_batch_size = 64
        sentiment_batch_size = 32
        embedding_batch_size = 64

    model_save_dir = f"{data_dir}/output/bertopic_model"
    return RuntimeConfig(
        runtime_mode=mode,
        data_dir=data_dir,
        model_dir=model_dir,
        logs_dir=logs_dir,
        device=device,
        hf_device=hf_device,
        inference_batch_size=inference_batch_size,
        sentiment_batch_size=sentiment_batch_size,
        embedding_batch_size=embedding_batch_size,
        model_save_dir=model_save_dir,
    )


RUNTIME = get_runtime_config()
