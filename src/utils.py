# ==========================================
# EXPORT UTILITIES & ARTIFACT GENERATOR
# ==========================================

import io
import imageio.v2 as imageio
import matplotlib.pyplot as plt

def export_results_and_generate_artifacts(results_df):
    """
    Saves optimization results to CSV, creates static plots, and compiles an animated GIF.
    """
    csv_path = "german_bess_optimization_results.csv"
    results_df.to_csv(csv_path)
    
    # Static Graph 1: Peak Shaving
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(results_df.index, results_df["Industrial_Load_MW"], label="Original Load", color="#B6E880", linewidth=2)
    ax1.plot(results_df.index, results_df["Net_Grid_Load_MW"], label="Net Grid Load", color="#EF553B", linestyle="--", linewidth=2)
    ax1.set_title("BESS Peak Shaving & Grid Load Profile")
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Power (MW)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    fig1.savefig("graph1_peak_shaving.png", bbox_inches="tight")
    plt.close(fig1)

    # Static Graph 2: Market Prices
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.plot(results_df.index, results_df["DA_Price"], label="DA Price (€/MWh)", color="#FFA15A", linewidth=2)
    ax2.set_title("EPEX Day-Ahead Market Prices")
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Price (€/MWh)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    fig2.savefig("graph2_market_prices.png", bbox_inches="tight")
    plt.close(fig2)

    # Animated GIF
    frames = []
    for i in range(1, len(results_df) + 1):
        fig_g, ax_g = plt.subplots(figsize=(7, 4))
        ax_g.plot(results_df.index[:i], results_df["Industrial_Load_MW"][:i], label="Original Load", color="#B6E880")
        ax_g.plot(results_df.index[:i], results_df["Net_Grid_Load_MW"][:i], label="Net Grid Load", color="#EF553B", linestyle="--")
        ax_g.set_xlim(results_df.index[0], results_df.index[-1])
        ax_g.set_ylim(0, results_df["Industrial_Load_MW"].max() * 1.2)
        ax_g.set_title(f"BESS Dispatch Animation - Step {i}/24")
        ax_g.set_ylabel("Power (MW)")
        ax_g.grid(True, alpha=0.3)
        
        frame_buf = io.BytesIO()
        fig_g.savefig(frame_buf, format="png", bbox_inches="tight")
        frame_buf.seek(0)
        frames.append(imageio.imread(frame_buf))
        plt.close(fig_g)

    imageio.mimsave("bess_dispatch_animation.gif", frames, format="GIF", duration=150)
