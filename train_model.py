import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
from db import get_connection


def train_model(host_id):
    conn = get_connection()

    query = """
    SELECT
        cpu_usage,
        memory_usage,
        disk_usage,
        network_in,
        network_out,
        process_count,
        running_processes,
        thread_count,
        load_avg_1m,
        load_avg_5m,
        load_avg_15m
    FROM model_training_features
    WHERE host_id = %s
    ORDER BY collected_at
    """

    df = pd.read_sql(query, conn, params=(host_id,))
    conn.close()

    if len(df) < 20:
        print(f"Not enough data to train model. Current rows: {len(df)}")
        return False

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42
    )

    model.fit(df)

    joblib.dump(model, "isolation_forest_model.pkl")

    print("Model trained successfully")
    print("Samples used:", len(df))
    return True


if __name__ == "__main__":
    from static_collector import get_or_create_host

    host_id = get_or_create_host()
    train_model(host_id)
