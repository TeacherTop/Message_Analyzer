from sklearn.cluster import KMeans

def cluster_sessions(X_scaled, scaler, session_df):
    kmeans = KMeans(
        n_clusters=4,
        random_state=42
    )

    clusters = kmeans.fit_predict(X_scaled)

    session_df["cluster"] = clusters

    clusters = session_df.groupby("cluster").mean(numeric_only=True)
    amount = session_df["cluster"].value_counts()


    return clusters, amount




def plot_clusters_umap(X_scaled, session_df):
    import base64
    import io

    import matplotlib.pyplot as plt
    import umap

    reducer = umap.UMAP(
        n_neighbors=15,
        min_dist=0.1,
        random_state=42
    )

    X_2d = reducer.fit_transform(X_scaled)
    fig, ax = plt.subplots(figsize=(8, 6))

    scatter = ax.scatter(
        X_2d[:, 0],
        X_2d[:, 1],
        c=session_df["cluster"],
        alpha=0.7
    )

    ax.set_title("Кластеры (UMAP)")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")

    # save figure to PNG bytes and return base64 string
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("ascii")
    return img_b64


