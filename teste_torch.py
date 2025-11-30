import torch, torchaudio
print("torch:", torch.__version__)
print("torchaudio:", torchaudio.__version__)
print("cuda available:", torch.cuda.is_available())
print("torch.version.cuda:", torch.version.cuda)
if torch.cuda.is_available():
    print("device name:", torch.cuda.get_device_name(0))
    print("total memory (MB):", torch.cuda.get_device_properties(0).total_memory // 1024 // 1024)
