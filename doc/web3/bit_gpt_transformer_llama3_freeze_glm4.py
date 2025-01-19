# BitGPT.py

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn
from transformers import LlamaForCausalLM


# 数据预处理
def preprocess_data(file_path):
    df = pd.read_csv(file_path)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume_(BTC)']]

    scaler_price = MinMaxScaler(feature_range=(0, 1))
    scaler_volume = MinMaxScaler(feature_range=(0, 1))

    df[['Open', 'High', 'Low', 'Close']] = scaler_price.fit_transform(df[['Open', 'High', 'Low', 'Close']])
    df['Volume_(BTC)'] = scaler_volume.fit_transform(df[['Volume_(BTC)']])

    return df, scaler_price, scaler_volume


def create_dataset(dataset, seq_length=120):
    X, y = [], []
    for i in range(seq_length, len(dataset)):
        X.append(dataset[i - seq_length:i, :])
        y.append(dataset[i, :])
    return np.array(X), np.array(y)


# 自定义Embedding层
class CustomEmbedding(nn.Module):
    def __init__(self, feature_size, dim_size):
        super(CustomEmbedding, self).__init__()
        self.embedding = nn.Linear(feature_size, dim_size)

    def forward(self, x):
        return self.embedding(x)


# BitGPT模型
class BitGPT(nn.Module):
    def __init__(self, dim_size=4096):
        super(BitGPT, self).__init__()
        self.embedding = CustomEmbedding(feature_size=5, dim_size=dim_size)
        self.transformer = LlamaForCausalLM.from_pretrained('llama3', return_dict=False)
        for param in self.transformer.parameters():
            param.requires_grad = False
        self.output_layer = nn.Linear(dim_size, 5)

    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer(x)[0]  # 只取输出部分
        x = self.output_layer(x)
        return x


# 计算模型参数量
def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# 训练模型
def train_model(model, X_tensor, y_tensor):
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(100):  # 假设训练100个epoch
        for i in range(0, len(X_tensor), 32):  # 假设batch_size为32
            batch_X = X_tensor[i:i + 32]
            batch_y = y_tensor[i:i + 32]

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

        print(f'Epoch {epoch + 1}, Loss: {loss.item()}')


# 模型推理
def predict(model, input_seq, scaler_price, scaler_volume):
    model.eval()
    with torch.no_grad():
        input_seq = torch.tensor(input_seq, dtype=torch.float32)
        output = model(input_seq)
        output = output.numpy()
        predicted_scaled = scaler_price.inverse_transform(output[:, :4])
        predicted_scaled = np.concatenate((predicted_scaled, scaler_volume.inverse_transform(output[:, 4:5])), axis=1)
        return predicted_scaled


# 主函数
def main():
    file_path = 'bitstampUSD_1-min_data_2012-01-01_to_2020-12-31.csv'
    df, scaler_price, scaler_volume = preprocess_data(file_path)
    X, y = create_dataset(df.values, seq_length=120)

    X_tensor = torch.tensor(X, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.float32)

    model = BitGPT()
    print(f'Total Parameters: {count_parameters(model)}')

    train_model(model, X_tensor, y_tensor)

    last_seq = X_tensor[-1]
    predicted = predict(model, last_seq, scaler_price, scaler_volume)
    print(predicted)


if __name__ == "__main__":
    main()
