"""
Pure PyTorch fallback for flash_attn.bert_padding.
Provides: index_first_axis, pad_input, rearrange, unpad_input
Used when flash_attn is not installed (e.g., no CUDA compilation environment).
"""

import torch

try:
    from einops import rearrange
except ImportError:
    rearrange = None


def index_first_axis(src: torch.Tensor, index: torch.Tensor) -> torch.Tensor:
    """Gather elements from src using index along the first axis.

    Args:
        src: (*, hidden) - source tensor
        index: (num_valid,) - indices to gather
    Returns:
        (num_valid, hidden) - gathered tensor
    """
    return src[index]


def unpad_input(hidden_states: torch.Tensor, attention_mask: torch.Tensor):
    """Remove padding from hidden_states using attention_mask.

    Args:
        hidden_states: (batch, seq_len, ...) or (batch*seq_len, ...)
        attention_mask: (batch, seq_len), 1 for valid tokens, 0 for padding

    Returns:
        output: (total_valid, ...) - unpadded hidden states
        indices: (total_valid,) - indices of valid tokens in flattened input
        cu_seqlens: (batch+1,) - cumulative sequence lengths
        max_seqlen_in_batch: int - max sequence length in batch
    """
    batch_size, seq_len = attention_mask.shape
    mask = attention_mask.bool().flatten()  # (batch * seq_len,)

    # Flatten hidden_states along batch and seq dims
    if hidden_states.dim() >= 2 and hidden_states.shape[0] == batch_size:
        # (batch, seq_len, ...) -> (batch * seq_len, ...)
        hidden_flat = hidden_states.reshape(-1, *hidden_states.shape[2:])
    else:
        hidden_flat = hidden_states

    # Gather valid tokens
    indices = mask.nonzero(as_tuple=True)[0]
    output = hidden_flat[indices]

    # Compute cumulative sequence lengths
    seqlens = attention_mask.sum(dim=1)  # (batch,)
    cu_seqlens = torch.zeros(
        batch_size + 1, dtype=torch.int32, device=hidden_states.device
    )
    cu_seqlens[1:] = seqlens.cumsum(dim=0).to(torch.int32)
    max_seqlen_in_batch = seqlens.max().item()

    return output, indices, cu_seqlens, max_seqlen_in_batch


def pad_input(
    hidden_states: torch.Tensor,
    indices: torch.Tensor,
    batch_size: int,
    seq_len: int,
) -> torch.Tensor:
    """Restore padding to hidden_states.

    Args:
        hidden_states: (total_valid, ...) - unpadded tensor
        indices: (total_valid,) - original indices of valid tokens
        batch_size: int
        seq_len: int

    Returns:
        (batch_size, seq_len, ...) - padded tensor
    """
    output_shape = (batch_size * seq_len, *hidden_states.shape[1:])
    output = torch.zeros(
        output_shape, dtype=hidden_states.dtype, device=hidden_states.device
    )
    output[indices] = hidden_states
    return output.reshape(batch_size, seq_len, *hidden_states.shape[1:])
