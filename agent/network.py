from torch import nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()

        self.f = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(out_ch)
        )

        if in_ch == out_ch:
            self.s_cut = nn.Identity()
        else:
            self.s_cut = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, kernel_size=1, stride=1),
                nn.BatchNorm2d(out_ch)
            )

    def forward(self, x):
        identity = self.s_cut(x)
        f = self.f(x)
        h = F.relu(f + identity)
        return h

class TwJanggiNet(nn.Module):
    def __init__(self, in_ch, hidden_ch, num_block):
        super().__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, hidden_ch, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(hidden_ch),
            nn.ReLU()
        )

        layers = []
        for _ in range(num_block):
            layers.append(ResidualBlock(hidden_ch, hidden_ch))

        self.hidden_layer = nn.Sequential(*layers)

        self.policy_head = nn.Sequential(
            nn.Conv2d(hidden_ch, out_channels=2, kernel_size=1, stride=1),
            nn.BatchNorm2d(2),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(24, 132)
        )

        self.value_head = nn.Sequential(
            nn.Conv2d(hidden_ch, out_channels=1, kernel_size=1, stride=1),
            nn.BatchNorm2d(1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(12, hidden_ch),
            nn.ReLU(),
            nn.Linear(hidden_ch, 1),
            nn.Tanh()
        )

    def forward(self, x):
        x = self.conv(x)
        x = self.hidden_layer(x)
        policy = self.policy_head(x)
        value = self.value_head(x)
        return policy, value