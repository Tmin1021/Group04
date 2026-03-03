import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def plot_equity_curve(csv_path, output_dir=None, title="Equity Curve"):
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    
    # Tính equity từ net_ret
    equity = (1.0 + df["net_ret"]).cumprod()
    equity.name = "Equity (starting from 1.0)"  # Để legend tự nhận
    
    # Tính drawdown
    running_max = equity.cummax()
    drawdown = (equity / running_max - 1) * 100
    
    # Vẽ biểu đồ
    fig, ax1 = plt.subplots(figsize=(12, 7))  # Tăng kích thước cho đẹp slide
    
    # Đường Equity (trục trái, màu xanh dương)
    ax1.plot(equity.index, equity, color='navy', linewidth=2.5, label='Equity Curve')
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Equity (starting from 1.0)", color='navy', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='navy')
    ax1.grid(True, linestyle='--', alpha=0.4)
    
    # Trục phụ cho Drawdown (màu đỏ)
    ax2 = ax1.twinx()
    ax2.plot(drawdown.index, drawdown, color='red', linewidth=1.8, linestyle='--', 
             label='Drawdown (%)')
    ax2.set_ylabel("Drawdown (%)", color='red', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='red')
    
    # Đặt giới hạn trục drawdown để dễ nhìn (từ min-5 đến 5 hoặc 0)
    ax2.set_ylim(drawdown.min() - 5, max(drawdown.max(), 5))
    
    # Legend chung (kết hợp cả hai đường)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', 
               fontsize=10, frameon=True, edgecolor='gray')
    
    # Tiêu đề và layout
    plt.title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Lưu file
    if output_dir is None:
        output_dir = Path(csv_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plot_path = output_dir / f"{Path(csv_path).stem}_equity_curve.png"
    plt.savefig(plot_path, dpi=200, bbox_inches='tight')  # dpi cao hơn cho slide đẹp
    plt.close()
    print(f"Saved: {plot_path}")

if __name__ == "__main__":
    plot_equity_curve("data/processed/result_in_sample/baseline_returns.csv", 
                      title="In-Sample Baseline Equity Curve (2021-2022)")
    plot_equity_curve("data/processed/result_out_sample/baseline_returns.csv", 
                      title="Out-of-Sample Baseline Equity Curve (2023)")
    plot_equity_curve("data/processed/result_out_sample/best_returns.csv", 
                      title="Out-of-Sample Best Equity Curve (2023)")