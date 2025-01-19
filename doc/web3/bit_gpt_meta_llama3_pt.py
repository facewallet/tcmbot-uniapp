import torch
import torch.nn.functional as F
from torch import nn
import math
from dataclasses import dataclass
from typing import Optional, Tuple

# 定义模型参数
@dataclass
class ModelArgs:
    dim: int = 4096
    # n_layers: int = 32
    n_layers: int = 1
    n_heads: int = 32
    n_kv_heads: Optional[int] = None
    vocab_size: int = -1
    multiple_of: int = 256
    ffn_dim_multiplier: Optional[float] = None
    norm_eps: float = 1e-5
    rope_theta: float = 500000
    max_batch_size: int = 32
    max_seq_len: int = 2048


class RMSNorm(torch.nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def _norm(self, x):
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)

    def forward(self, x):
        output = self._norm(x.float()).type_as(x)
        return output * self.weight


def precompute_freqs_cis(dim: int, end: int, theta: float = 10000.0):
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2)[: (dim // 2)].float() / dim))
    t = torch.arange(end, device=freqs.device, dtype=torch.float32)
    freqs = torch.outer(t, freqs)
    freqs_cis = torch.polar(torch.ones_like(freqs), freqs)  # complex64
    return freqs_cis


def reshape_for_broadcast(freqs_cis: torch.Tensor, x: torch.Tensor):
    ndim = x.ndim
    assert 0 <= 1 < ndim
    assert freqs_cis.shape == (x.shape[1], x.shape[-1])
    shape = [d if i == 1 or i == ndim - 1 else 1 for i, d in enumerate(x.shape)]
    return freqs_cis.view(*shape)


def apply_rotary_emb(
    xq: torch.Tensor,
    xk: torch.Tensor,
    freqs_cis: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    xq_ = torch.view_as_complex(xq.float().reshape(*xq.shape[:-1], -1, 2))
    xk_ = torch.view_as_complex(xk.float().reshape(*xk.shape[:-1], -1, 2))
    freqs_cis = reshape_for_broadcast(freqs_cis, xq_)
    xq_out = torch.view_as_real(xq_ * freqs_cis).flatten(3)
    xk_out = torch.view_as_real(xk_ * freqs_cis).flatten(3)
    return xq_out.type_as(xq), xk_out.type_as(xk)


def repeat_kv(x: torch.Tensor, n_rep: int) -> torch.Tensor:
    """torch.repeat_interleave(x, dim=2, repeats=n_rep)"""
    bs, slen, n_kv_heads, head_dim = x.shape
    if n_rep == 1:
        return x
    return (
        x[:, :, :, None, :]
      .expand(bs, slen, n_kv_heads, n_rep, head_dim)
      .reshape(bs, slen, n_kv_heads * n_rep, head_dim)
    )


class Attention(nn.Module):
    def __init__(self, args: ModelArgs):
        super().__init__()
        self.n_kv_heads = args.n_heads if args.n_kv_heads is None else args.n_kv_heads
        self.n_local_heads = args.n_heads
        self.n_local_kv_heads = self.n_kv_heads
        self.n_rep = 1
        self.head_dim = args.dim // args.n_heads

        self.wq = nn.Linear(
            args.dim, args.n_heads * self.head_dim, bias=False
        )
        self.wk = nn.Linear(
            args.dim, self.n_kv_heads * self.head_dim, bias=False
        )
        self.wv = nn.Linear(
            args.dim, self.n_kv_heads * self.head_dim, bias=False
        )
        self.wo = nn.Linear(
            args.n_heads * self.head_dim, args.dim, bias=False
        )

        self.cache_k = torch.zeros(
            (args.max_batch_size, args.max_seq_len, self.n_local_kv_heads, self.head_dim)
        )
        self.cache_v = torch.zeros(
            (args.max_batch_size, args.max_seq_len, self.n_local_kv_heads, self.head_dim)
        )

    def forward(
        self,
        x: torch.Tensor,
        start_pos: int,
        freqs_cis: torch.Tensor,
        mask: Optional[torch.Tensor],
    ):
        bsz, seqlen, _ = x.shape
        xq, xk, xv = self.wq(x), self.wk(x), self.wv(x)

        xq = xq.view(bsz, seqlen, self.n_local_heads, self.head_dim)
        xk = xk.view(bsz, seqlen, self.n_local_kv_heads, self.head_dim)
        xv = xv.view(bsz, seqlen, self.n_local_kv_heads, self.head_dim)

        xq, xk = apply_rotary_emb(xq, xk, freqs_cis=freqs_cis)

        self.cache_k[:bsz, start_pos : start_pos + seqlen] = xk
        self.cache_v[:bsz, start_pos : start_pos + seqlen] = xv

        keys = self.cache_k[:bsz, : start_pos + seqlen]
        values = self.cache_v[:bsz, : start_pos + seqlen]

        # repeat k/v heads if n_kv_heads < n_heads
        keys = repeat_kv(
            keys, self.n_rep
        )  # (bs, cache_len + seqlen, n_local_heads, head_dim)
        values = repeat_kv(
            values, self.n_rep
        )  # (bs, cache_len + seqlen, n_local_heads, head_dim)

        xq = xq.transpose(1, 2)  # (bs, n_local_heads, seqlen, head_dim)
        keys = keys.transpose(1, 2)  # (bs, n_local_heads, cache_len + seqlen, head_dim)
        values = values.transpose(
            1, 2
        )  # (bs, n_local_heads, cache_len + seqlen, head_dim)
        scores = torch.matmul(xq, keys.transpose(2, 3)) / math.sqrt(self.head_dim)
        if mask is not None:
            scores = scores + mask  # (bs, n_local_heads, seqlen, cache_len + seqlen)
        scores = F.softmax(scores.float(), dim=-1).type_as(xq)
        output = torch.matmul(scores, values)  # (bs, n_local_heads, seqlen, head_dim)
        output = output.transpose(1, 2).contiguous().view(bsz, seqlen, -1)
        return self.wo(output)


class FeedForward(nn.Module):
    def __init__(
        self,
        dim: int,
        hidden_dim: int,
        multiple_of: int,
        ffn_dim_multiplier: Optional[float],
    ):
        super().__init__()
        hidden_dim = int(2 * hidden_dim / 3)
        # custom dim factor multiplier
        if ffn_dim_multiplier is not None:
            hidden_dim = int(ffn_dim_multiplier * hidden_dim)
        hidden_dim = multiple_of * ((hidden_dim + multiple_of - 1) // multiple_of)

        self.w1 = nn.Linear(dim, hidden_dim, bias=False)
        self.w2 = nn.Linear(hidden_dim, dim, bias=False)
        self.w3 = nn.Linear(dim, hidden_dim, bias=False)

    def forward(self, x):
        return self.w2(F.silu(self.w1(x))) * self.w3(x)


class TransformerBlock(nn.Module):
    def __init__(self, layer_id: int, args: ModelArgs):
        super().__init__()
        self.n_heads = args.n_heads
        self.dim = args.dim
        self.head_dim = args.dim // args.n_heads
        self.attention = Attention(args)
        self.feed_forward = FeedForward(
            dim=args.dim,
            hidden_dim=4 * args.dim,
            multiple_of=args.multiple_of,
            ffn_dim_multiplier=args.ffn_dim_multiplier,
        )
        self.layer_id = layer_id
        self.attention_norm = RMSNorm(args.dim, eps=args.norm_eps)
        self.ffn_norm = RMSNorm(args.dim, eps=args.norm_eps)

    def forward(
        self,
        x: torch.Tensor,
        start_pos: int,
        freqs_cis: torch.Tensor,
        mask: Optional[torch.Tensor],
    ):
        h = x + self.attention(self.attention_norm(x), start_pos, freqs_cis, mask)
        out = h + self.feed_forward(self.ffn_norm(h))
        return out


class BitGPT(nn.Module):
    def __init__(self, args: ModelArgs):
        super().__init__()
        self.args = args
        # 自定义 Embedding 层
        self.embedding = nn.Linear(5, args.dim)
        self.transformer_blocks = nn.ModuleList(
            [TransformerBlock(i, args) for i in range(args.n_layers)]
        )
        self.output = nn.Linear(args.dim, 5)

    def forward(self, x):
        # 嵌入层
        x = self.embedding(x)
        for block in self.transformer_blocks:
            x = block(x, 0, None)
        # 输出层
        x = self.output(x)
        return x


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def data_preprocessing(data, min_price, max_price, min_volume, max_volume):
    # 对价格进行缩放
    data[:, :, :4] = (data[:, :, :4] - min_price) / (max_price - min_price)
    # 对成交量进行缩放
    data[:, :, 4] = (data[:, :, 4] - min_volume) / (max_volume - min_volume)
    return data


def train(model, data, optimizer, criterion, min_price, max_price, min_volume, max_volume):
    model.train()
    data = data_preprocessing(data, min_price, max_price, min_volume, max_volume)
    optimizer.zero_grad()
    # 自回归预测下一个时间步
    input_data = data[:, :-1, :]
    target_data = data[:, 1:, :]
    output = model(input_data)
    loss = criterion(output, target_data)
    loss.backward()
    optimizer.step()
    return loss.item()


def inference(model, input_data, min_price, max_price, min_volume, max_volume):
    model.eval()
    input_data = data_preprocessing(input_data, min_price, max_price, min_volume, max_volume)
    with torch.no_grad():
        output = model(input_data)
    # 对结果进行缩放回去
    output[:, :, :4] = output[:, :, :4] * (max_price - min_price) + min_price
    output[:, :, 4] = output[:, :, 4] * (max_volume - min_volume) + min_volume
    return output


def main():
    # 初始化模型参数
    args = ModelArgs()
    model = BitGPT(args)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    criterion = nn.MSELoss()
    # 假设输入数据的形状为 (batch_size, seq_length, feature_size)
    batch_size = 10
    seq_length = 120
    feature_size = 5
    data = torch.randn(batch_size, seq_length, feature_size)
    min_price = torch.min(data[:, :, :4])
    max_price = torch.max(data[:, :, :4])
    min_volume = torch.min(data[:, :, 4])
    max_volume = torch.max(data[:, :, 4])
    # 计算模型参数量
    num_params = count_parameters(model)
    print(f"Total number of trainable parameters: {num_params}")
    # 训练模型
    # num_epochs = 10
    # for epoch in range(num_epochs):
    #     loss = train(model, data, optimizer, criterion, min_price, max_price, min_volume, max_volume)
    #     print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {loss}")
    # # 推理模型
    # input_data = torch.randn(1, seq_length, feature_size)
    # output = inference(model, input_data, min_price, max_price, min_volume, max_volume)
    # print(output)


if __name__ == "__main__":
    main()