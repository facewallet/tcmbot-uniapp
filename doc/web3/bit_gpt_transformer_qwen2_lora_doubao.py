# 以下是具体的代码文件内容
import torch
import torch.nn as nn
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModel, AutoTokenizer
from torch.optim import Adam
import torch.nn.functional as F


# 自定义数据集类
class StockDataset(Dataset):
    def __init__(self, csv_file, seq_length=120, feature_size=5):
        self.data = pd.read_csv(csv_file)
        self.seq_length = seq_length
        self.feature_size = feature_size
        self.open = torch.tensor(self.data['Open'].values, dtype=torch.float32)
        self.high = torch.tensor(self.data['High'].values, dtype=torch.float32)
        self.low = torch.tensor(self.data['Low'].values, dtype=torch.float32)
        self.close = torch.tensor(self.data['Close'].values, dtype=torch.float32)
        self.volume = torch.tensor(self.data['Volume_(BTC)'].values, dtype=torch.float32)
        self.num_samples = len(self.data) - seq_length

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        start = idx
        end = idx + self.seq_length
        inputs = torch.stack([
            self.open[start:end],
            self.high[start:end],
            self.low[start:end],
            self.close[start:end],
            self.volume[start:end]
        ], dim=1)
        target = torch.tensor([
            self.open[end],
            self.high[end],
            self.low[end],
            self.close[end],
            self.volume[end]
        ], dtype=torch.float32)
        return inputs, target


# 自定义模型类
class BitGPT(nn.Module):
    def __init__(self, dim_size=4096):
        super(BitGPT, self).__init__()
        # 加载 qwen2 模型结构
        self.qwen2 = AutoModel.from_pretrained("path_to_qwen2_model")
        # 冻结 qwen2 模型的参数
        for param in self.qwen2.parameters():
            param.requires_grad = False
        # 自定义 Embedding 层
        self.embedding = nn.Linear(5, dim_size)
        # 输出层
        self.output = nn.Linear(dim_size, 5)
        # LoRA 微调部分，这里简单示例，可根据具体 LoRA 实现修改
        self.lora_A = nn.Linear(dim_size, 16)
        self.lora_B = nn.Linear(16, dim_size)

    def forward(self, x):
        x = self.embedding(x)
        # 应用 LoRA 微调
        x = x + self.lora_B(self.lora_A(x))
        x = self.qwen2(inputs_embeds=x).last_hidden_state
        x = self.output(x[:, -1, :])  # 只取最后一个位置的输出
        return x


def data_preprocessing(data, min_values, max_values):
    """
    数据预处理，对输入的价格和成交量进行最大值最小值缩放
    :param data: 输入数据张量
    :param min_values: 最小值张量
    :param max_values: 最大值张量
    :return: 缩放后的数据张量
    """
    data[:, :, :4] = (data[:, :, :4] - min_values[:4]) / (max_values[:4] - min_values[:4])
    data[:, :, 4] = (data[:, :, 4] - min_values[4]) / (max_values[4] - min_values[4])
    return data


def train(model, dataloader, optimizer, criterion, min_values, max_values, num_epochs=10):
    """
    自回归模型训练过程
    :param model: 要训练的模型
    :param dataloader: 数据加载器
    :param optimizer: 优化器
    :param criterion: 损失函数
    :param min_values: 数据的最小值张量
    :param max_values: 数据的最大值张量
    :param num_epochs: 训练的轮数
    """
    model.train()
    for epoch in range(num_epochs):
        total_loss = 0.0
        for inputs, targets in dataloader:
            optimizer.zero_grad()
            inputs = data_preprocessing(inputs, min_values, max_values)
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {total_loss / len(dataloader)}")


def inference(model, input_data, min_values, max_values):
    """
    模型推理部分
    :param model: 训练好的模型
    :param input_data: 输入数据张量
    :param min_values: 数据的最小值张量
    :param max_values: 数据的最大值张量
    :return: 推理结果
    """
    model.eval()
    with torch.no_grad():
        input_data = data_preprocessing(input_data, min_values, max_values)
        output = model(input_data)
        output[:, :4] = output[:, :4] * (max_values[:4] - min_values[:4]) + min_values[:4]
        output[:, 4] = output[:, 4] * (max_values[4] - min_values[4]) + min_values[4]
        return output


def main():
    # 读取数据
    dataset = StockDataset('bitstampUSD_1-min_data_2012-01-01_to_2020-12-31.csv')
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    # 初始化模型
    model = BitGPT()
    # 定义优化器和损失函数
    optimizer = Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-4)
    criterion = F.mse_loss
    # 计算最大值和最小值
    min_values = torch.tensor([
        dataset.open.min(),
        dataset.high.min(),
        dataset.low.min(),
        dataset.close.min(),
        dataset.volume.min()
    ])
    max_values = torch.tensor([
        dataset.open.max(),
        dataset.high.max(),
        dataset.low.max(),
        dataset.close.max(),
        dataset.volume.max()
    ])
    # 训练模型
    train(model, dataloader, optimizer, criterion, min_values, max_values)
    # 假设输入数据
    input_data = torch.randn(1, 120, 5)
    # 推理
    output = inference(model, input_data, min_values, max_values)
    print(output)
    # 计算参数量
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total number of trainable parameters: {num_params}")


if __name__ == "__main__":
    main()