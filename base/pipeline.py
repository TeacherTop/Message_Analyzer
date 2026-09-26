import pandas as pd

from base.parser import build_df
from base.feature_engineering import build_features
from analytics.analytics import basic_stats
from base.sessionization import make_sessions
from ML.prepare_for_clustering import prepare_sessions_for_clustering
from ML.clustering import cluster_sessions, plot_clusters_umap
from semantic_topics.behavior import describe_behavior_clusters
def process_chat(data, include_umap=True, include_behavior=True):
    # парсинг
    df = build_df(data)

    # Деление непрерывного диалога на диалоговые сессии
    df = make_sessions(df)

    # feature engineering
    df_features, session_df = build_features(df)

    # аналитика сообщений
    stats = basic_stats(df_features,session_df)

    if not include_behavior:
        return stats, pd.DataFrame(), pd.Series(dtype="int64"), None, []

    # Подготавливает session_df для кластеризации
    X_scaled, scaler, session_df = prepare_sessions_for_clustering(session_df)

    # Кластеризация сессий диалогов
    clusters, amount, labeled_sessions = cluster_sessions(X_scaled, scaler, session_df)

    behavior_clusters = describe_behavior_clusters(clusters, amount)

    viz = None
    if include_umap:
        # Визуализация кластеров через UMAP
        viz = plot_clusters_umap(X_scaled, session_df)

    return stats, clusters, amount, viz, behavior_clusters
