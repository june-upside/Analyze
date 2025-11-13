"""
Chart generation for visualization of wallet flows and kimchi premiums
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from typing import Dict, List

from config import DATA_DIR, CHART_DIR


class ChartGenerator:
    """Generates various charts for analysis visualization"""
    
    def __init__(self):
        self.wallet_data = None
        self.premium_data = None
        self.merged_data = None
        self.correlation_data = None
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (14, 8)
        plt.rcParams['font.size'] = 10
        
        # Create charts directory
        os.makedirs(CHART_DIR, exist_ok=True)
    
    def load_data(self):
        """Load all necessary data"""
        print("Loading data for visualization...")
        
        # Load wallet data
        wallet_file = os.path.join(DATA_DIR, "wallet_transfers_hourly.csv")
        if os.path.exists(wallet_file):
            self.wallet_data = pd.read_csv(wallet_file)
            self.wallet_data["timestamp"] = pd.to_datetime(self.wallet_data["timestamp"])
            print(f"  Loaded wallet data: {len(self.wallet_data)} records")
        
        # Load premium data
        premium_file = os.path.join(DATA_DIR, "kimchi_premiums_hourly.csv")
        if os.path.exists(premium_file):
            self.premium_data = pd.read_csv(premium_file)
            self.premium_data["timestamp"] = pd.to_datetime(self.premium_data["timestamp"])
            print(f"  Loaded premium data: {len(self.premium_data)} records")
        
        # Merge data
        if self.wallet_data is not None and self.premium_data is not None:
            self.merged_data = self.wallet_data.merge(self.premium_data, on="timestamp", how="inner")
            print(f"  Merged data: {len(self.merged_data)} records")
        
        # Load correlation data
        corr_file = os.path.join(DATA_DIR, "correlation_results.csv")
        if os.path.exists(corr_file):
            self.correlation_data = pd.read_csv(corr_file)
            print(f"  Loaded correlation data: {len(self.correlation_data)} records")
    
    def create_main_timeline_chart(self, interactive: bool = True):
        """
        Create main timeline chart with dual axis:
        - Primary: Wallet net flow (bar chart)
        - Secondary: Kimchi premiums (line charts)
        
        Args:
            interactive: If True, create interactive Plotly chart, else Matplotlib
        """
        if self.merged_data is None:
            self.load_data()
        
        if self.merged_data is None or self.merged_data.empty:
            print("Error: No data available for timeline chart")
            return
        
        print("\nCreating main timeline chart...")
        
        if interactive:
            self._create_plotly_timeline()
        else:
            self._create_matplotlib_timeline()
    
    def _create_plotly_timeline(self):
        """Create interactive timeline chart using Plotly"""
        df = self.merged_data
        
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add bar chart for net flow
        fig.add_trace(
            go.Bar(
                x=df["timestamp"],
                y=df["net_flow"],
                name="Net Flow (USDT)",
                marker_color=df["net_flow"].apply(lambda x: "green" if x > 0 else "red"),
                opacity=0.6,
                hovertemplate="<b>%{x}</b><br>Net Flow: %{y:,.0f} USDT<extra></extra>"
            ),
            secondary_y=False
        )
        
        # Add line charts for premiums
        premium_cols = [col for col in df.columns if col.endswith("_premium")]
        colors = {"BTC_premium": "blue", "ETH_premium": "purple", "USDT_premium": "orange"}
        
        for col in premium_cols:
            if col in df.columns:
                coin_name = col.replace("_premium", "")
                fig.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df[col],
                        name=f"{coin_name} Premium",
                        mode="lines",
                        line=dict(color=colors.get(col, "gray"), width=2),
                        hovertemplate=f"<b>%{{x}}</b><br>{coin_name} Premium: %{{y:.2f}}%<extra></extra>"
                    ),
                    secondary_y=True
                )
        
        # Update layout
        fig.update_layout(
            title={
                "text": "Upbit Hot Wallet USDT Flow vs Kimchi Premium<br><sub>6-Month Analysis</sub>",
                "x": 0.5,
                "xanchor": "center"
            },
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=700,
            template="plotly_white"
        )
        
        # Update axes
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Net Flow (USDT)", secondary_y=False)
        fig.update_yaxes(title_text="Premium (%)", secondary_y=True)
        
        # Save as HTML
        output_file = os.path.join(CHART_DIR, "timeline_chart_interactive.html")
        fig.write_html(output_file)
        print(f"  Saved interactive timeline chart to {output_file}")
        
        # Also save as static image
        try:
            output_png = os.path.join(CHART_DIR, "timeline_chart.png")
            fig.write_image(output_png, width=1400, height=700)
            print(f"  Saved static timeline chart to {output_png}")
        except Exception as e:
            print(f"  Note: Could not save static image (requires kaleido): {e}")
    
    def _create_matplotlib_timeline(self):
        """Create static timeline chart using Matplotlib"""
        df = self.merged_data
        
        fig, ax1 = plt.subplots(figsize=(16, 8))
        
        # Plot net flow as bars
        colors = ['green' if x > 0 else 'red' for x in df["net_flow"]]
        ax1.bar(df["timestamp"], df["net_flow"], alpha=0.6, color=colors, label="Net Flow")
        ax1.set_xlabel("Date", fontsize=12)
        ax1.set_ylabel("Net Flow (USDT)", fontsize=12, color="black")
        ax1.tick_params(axis='y', labelcolor="black")
        ax1.grid(True, alpha=0.3)
        
        # Create secondary y-axis for premiums
        ax2 = ax1.twinx()
        
        # Plot premiums as lines
        premium_cols = [col for col in df.columns if col.endswith("_premium")]
        colors_map = {"BTC_premium": "blue", "ETH_premium": "purple", "USDT_premium": "orange"}
        
        for col in premium_cols:
            if col in df.columns:
                coin_name = col.replace("_premium", "")
                ax2.plot(df["timestamp"], df[col], 
                        label=f"{coin_name} Premium",
                        color=colors_map.get(col, "gray"),
                        linewidth=2)
        
        ax2.set_ylabel("Premium (%)", fontsize=12)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.3, linewidth=1)
        
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
        
        plt.title("Upbit Hot Wallet USDT Flow vs Kimchi Premium\n6-Month Analysis", 
                 fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Save
        output_file = os.path.join(CHART_DIR, "timeline_chart_matplotlib.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  Saved matplotlib timeline chart to {output_file}")
        plt.close()
    
    def create_correlation_scatter_plots(self):
        """Create scatter plots showing correlation between flows and premiums"""
        if self.merged_data is None:
            self.load_data()
        
        if self.merged_data is None or self.merged_data.empty:
            print("Error: No data available for scatter plots")
            return
        
        print("\nCreating correlation scatter plots...")
        
        df = self.merged_data
        premium_cols = [col for col in df.columns if col.endswith("_premium")]
        
        # Create figure with subplots
        n_coins = len(premium_cols)
        fig, axes = plt.subplots(n_coins, 1, figsize=(12, 6 * n_coins))
        
        if n_coins == 1:
            axes = [axes]
        
        for idx, col in enumerate(premium_cols):
            ax = axes[idx]
            coin_name = col.replace("_premium", "")
            
            # Create scatter plot
            scatter = ax.scatter(df["net_flow"], df[col], 
                               alpha=0.5, s=20, c=df[col], cmap='RdYlGn_r')
            
            # Add trend line
            z = np.polyfit(df["net_flow"].dropna(), df[col].dropna(), 1)
            p = np.poly1d(z)
            x_line = np.linspace(df["net_flow"].min(), df["net_flow"].max(), 100)
            ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label=f"Trend: y={z[0]:.2e}x+{z[1]:.2f}")
            
            # Calculate correlation
            from scipy.stats import pearsonr
            corr, pval = pearsonr(df["net_flow"].dropna(), df[col].dropna())
            
            ax.set_xlabel("Net Flow (USDT)", fontsize=12)
            ax.set_ylabel(f"{coin_name} Premium (%)", fontsize=12)
            ax.set_title(f"{coin_name}: Net Flow vs Premium (r={corr:.4f}, p={pval:.4f})", 
                        fontsize=13, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
            ax.axvline(x=0, color='black', linestyle='--', alpha=0.3)
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Premium (%)', rotation=270, labelpad=20)
        
        plt.tight_layout()
        
        # Save
        output_file = os.path.join(CHART_DIR, "correlation_scatter_plots.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  Saved scatter plots to {output_file}")
        plt.close()
    
    def create_lag_correlation_heatmap(self):
        """Create heatmap showing correlation at different time lags"""
        print("\nCreating lag correlation heatmap...")
        
        # Load lag correlation data
        lag_data = {}
        coins = ["BTC", "ETH", "USDT"]
        
        for coin in coins:
            lag_file = os.path.join(DATA_DIR, f"lag_correlation_{coin.lower()}.csv")
            if os.path.exists(lag_file):
                df = pd.read_csv(lag_file)
                lag_data[coin] = df
        
        if not lag_data:
            print("  Error: No lag correlation data found")
            return
        
        # Create heatmap data
        all_lags = lag_data[list(lag_data.keys())[0]]["lag"].values
        correlations = np.zeros((len(lag_data), len(all_lags)))
        
        for idx, (coin, df) in enumerate(lag_data.items()):
            correlations[idx, :] = df["correlation"].values
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(16, 6))
        
        im = ax.imshow(correlations, cmap='RdBu_r', aspect='auto', vmin=-0.5, vmax=0.5)
        
        # Set ticks
        ax.set_yticks(range(len(lag_data)))
        ax.set_yticklabels(list(lag_data.keys()))
        
        # Show only every 6th lag on x-axis for readability
        x_tick_indices = range(0, len(all_lags), 6)
        ax.set_xticks(x_tick_indices)
        ax.set_xticklabels([f"{all_lags[i]}h" for i in x_tick_indices], rotation=45)
        
        ax.set_xlabel("Time Lag (hours)", fontsize=12)
        ax.set_ylabel("Coin", fontsize=12)
        ax.set_title("Lag Correlation Heatmap: Net Flow vs Premium\n" + 
                    "(Positive lag = Flow leads Premium, Negative lag = Premium leads Flow)",
                    fontsize=13, fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Correlation Coefficient', rotation=270, labelpad=20)
        
        # Add vertical line at lag=0
        zero_idx = np.where(all_lags == 0)[0][0]
        ax.axvline(x=zero_idx, color='black', linestyle='--', linewidth=2, alpha=0.7)
        
        plt.tight_layout()
        
        # Save
        output_file = os.path.join(CHART_DIR, "lag_correlation_heatmap.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  Saved lag correlation heatmap to {output_file}")
        plt.close()
    
    def create_individual_lag_plots(self):
        """Create individual line plots for lag correlations"""
        print("\nCreating individual lag correlation plots...")
        
        coins = ["BTC", "ETH", "USDT"]
        colors = {"BTC": "blue", "ETH": "purple", "USDT": "orange"}
        
        fig, axes = plt.subplots(len(coins), 1, figsize=(14, 4 * len(coins)))
        
        if len(coins) == 1:
            axes = [axes]
        
        for idx, coin in enumerate(coins):
            lag_file = os.path.join(DATA_DIR, f"lag_correlation_{coin.lower()}.csv")
            
            if not os.path.exists(lag_file):
                continue
            
            df = pd.read_csv(lag_file)
            ax = axes[idx]
            
            # Plot correlation vs lag
            ax.plot(df["lag"], df["correlation"], 
                   color=colors.get(coin, "gray"), linewidth=2, marker='o', markersize=3)
            
            # Highlight significant correlations (p < 0.05)
            significant = df[df["p_value"] < 0.05]
            if not significant.empty:
                ax.scatter(significant["lag"], significant["correlation"], 
                         color='red', s=50, zorder=5, alpha=0.6, label='Significant (p<0.05)')
            
            # Find and mark best correlation
            best_idx = df["correlation"].abs().idxmax()
            best_lag = df.loc[best_idx, "lag"]
            best_corr = df.loc[best_idx, "correlation"]
            
            ax.scatter([best_lag], [best_corr], color='darkred', s=200, 
                      marker='*', zorder=10, label=f'Best: lag={best_lag}h, r={best_corr:.3f}')
            
            ax.axhline(y=0, color='black', linestyle='--', alpha=0.3)
            ax.axvline(x=0, color='black', linestyle='--', alpha=0.3, linewidth=2)
            ax.grid(True, alpha=0.3)
            
            ax.set_xlabel("Time Lag (hours)", fontsize=11)
            ax.set_ylabel("Correlation Coefficient", fontsize=11)
            ax.set_title(f"{coin}: Lag Correlation Analysis", fontsize=12, fontweight='bold')
            ax.legend(loc='best')
            
            # Add text annotation
            if best_lag > 0:
                direction = f"Flow leads Premium by {best_lag}h"
            elif best_lag < 0:
                direction = f"Premium leads Flow by {abs(best_lag)}h"
            else:
                direction = "Simultaneous"
            
            ax.text(0.02, 0.98, direction, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        # Save
        output_file = os.path.join(CHART_DIR, "lag_correlation_plots.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  Saved individual lag plots to {output_file}")
        plt.close()
    
    def create_all_charts(self):
        """Create all visualization charts"""
        print("\n" + "="*60)
        print("GENERATING VISUALIZATIONS")
        print("="*60)
        
        self.load_data()
        
        # Main timeline chart
        self.create_main_timeline_chart(interactive=True)
        
        # Correlation scatter plots
        self.create_correlation_scatter_plots()
        
        # Lag correlation heatmap
        self.create_lag_correlation_heatmap()
        
        # Individual lag plots
        self.create_individual_lag_plots()
        
        print("\n" + "="*60)
        print(f"All charts saved to {CHART_DIR}/")
        print("="*60)


if __name__ == "__main__":
    generator = ChartGenerator()
    generator.create_all_charts()

