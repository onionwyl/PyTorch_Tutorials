from __future__ import print_function
import argparse  # 命令项选项与参数解析
import torch
import torch.nn as nn # 网络层
import torch.nn.functional as F # 激活函数、代价函数等
import torch.optim as optim
from torchvision import datasets, transforms


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)  # 卷积层，输入通道数 1，输出通道数 10，过滤器边长
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()  # dropout 正则化
        self.fc1 = nn.Linear(320, 50)  # 使用线性变换的全连接层 Full Connect
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):  # x is Tensor
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        # conv1卷积，最大池化（kernel_size=2），relu

        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        # conv2卷积，dropout正则化（p=0.5），最大池化（kernel_size=2），relu

        x = x.view(-1, 320)  # 调整尺寸，-1表示从其他维度推断
        x = F.relu(self.fc1(x))  # 全连接，relu
        x = F.dropout(x, training=self.training)  # dropout正则化（p=0.5）
        x = self.fc2(x)  # 全连接
        return F.log_softmax(x, dim=1)


def train(args, model, device, train_loader, optimizer, epoch):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)  # 转移到指定设备
        optimizer.zero_grad()  # 清零梯度
        output = model(data)
        loss = F.nll_loss(output, target)  # negative log-likelihood loss
        loss.backward()  # 反向传播
        optimizer.step()
        if batch_idx % args.log_interval == 0:  # 日志间隙
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                       100. * batch_idx / len(train_loader), loss.item()))


def test(args, model, device, test_loader):
    model.eval()  # 评估
    test_loss = 0
    correct = 0
    with torch.no_grad():  # 不累积梯度
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)  # 转移设备
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction='sum').item()  # sum up batch loss
            pred = output.max(1, keepdim=True)[1]  # 多分类问题，获得最大对数概率值的索引
            correct += pred.eq(
                target.view_as(pred)).sum().item()  # view_as是将target转换为pred的大小；如果匹配，eq生成的张量在对应位置为1，否则为0；sum用于求和；item将单元素张量转换为数字；最终所得是正确样本数

    test_loss /= len(test_loader.dataset)  # 计算的是平均损失
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset), 100. * correct / len(test_loader.dataset)))


def main():
    # 训练设置
    parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
    parser.add_argument(
        '--batch-size',
        type=int,
        default=64,
        metavar='N',
        help='input batch size for training (default: 64)')
    parser.add_argument(
        '--test-batch-size',
        type=int,
        default=1000,
        metavar='N',
        help='input batch size for testing (default: 1000)')
    parser.add_argument(
        '--epochs',
        type=int,
        default=10,
        metavar='N',
        help='number of epochs to train (default: 10)')
    parser.add_argument(
        '--lr',  # 学习率
        type=float,
        default=0.01,
        metavar='LR',
        help='learning rate (default: 0.01)')
    parser.add_argument(
        '--momentum',
        type=float,
        default=0.5,
        metavar='M',
        help='SGD momentum (default: 0.5)')
    parser.add_argument(
        '--no-cuda',
        action='store_true',
        default=False,
        help='disables CUDA training')
    parser.add_argument(
        '--seed',
        type=int,
        default=1,
        metavar='S',
        help='random seed (default: 1)')
    parser.add_argument(
        '--log-interval',
        type=int,
        default=10,
        metavar='N',
        help='how many batches to wait before logging training status')
    args = parser.parse_args()
    use_cuda = not args.no_cuda and torch.cuda.is_available()  # 是否使用 cuda

    torch.manual_seed(args.seed)

    device = torch.device("cuda" if use_cuda else "cpu")

    kwargs = {'num_workers': 1, 'pin_memory': True} if use_cuda else {}

    train_loader = torch.utils.data.DataLoader(
        datasets.MNIST('../data', train=True, download=True,
                       transform=transforms.Compose([
                           transforms.ToTensor(),
                           transforms.Normalize((0.1307,), (0.3081,))
                       ])),
        batch_size=args.batch_size, shuffle=True, **kwargs)  # 训练数据

    test_loader = torch.utils.data.DataLoader(
        datasets.MNIST('../data', train=False, transform=transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ])),
        batch_size=args.test_batch_size, shuffle=True, **kwargs)  # 测试数据

    model = Net().to(device)  # 在指定设备上创建网络
    optimizer = optim.SGD(
        model.parameters(), lr=args.lr, momentum=args.momentum)  # 随机梯度下降

    for epoch in range(1, args.epochs + 1):
        train(args, model, device, train_loader, optimizer, epoch)
        test(args, model, device, test_loader)


if __name__ == '__main__':
    main()
